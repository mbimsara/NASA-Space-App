/**
 * Fixture-backed API for local development (VITE_USE_FIXTURES=true).
 * Owner: Shehani. Every value here is SYNTHETIC and labelled `data_kind: "synthetic"`.
 * Never relabel these as NASA observations or approved agronomic results.
 *
 * Behaviour mirrors docs/API_CONTRACTS.md closely enough to exercise the UI:
 * - farms/plans persist in localStorage so reload and plan reopening work;
 * - PATCH enforces expected_input_version (409 VERSION_CONFLICT);
 * - rotations respect seasons, priority weights and crop exclusions, and may
 *   legitimately return fewer than three candidates;
 * - scenarios recompute an illustrative water budget from the cached baseline.
 */
import demoFarmProfile from "../../../data/fixtures/farm.synthetic.json";
import { ApiClientError } from "./client";
import { asSeasonRanges } from "../utils/format";
import type { PlanRequest, RotationRequest } from "./client";
import type {
  AssistantMessage,
  AssistantRequest,
  FarmEnvelope,
  FarmProfile,
  ObservationSummary,
  RotationAnalysis,
  RotationCandidate,
  SavedPlan,
  ScenarioResult,
  ScoreComponent,
  WaterBudgetRange,
} from "../types/api";

const STORE_KEY = "agrosphere_fixture_db";
const SOURCE = "synthetic-fixture-v1";

/** Bump when fixture result shapes change; older analyses/plans are dropped, farms kept. */
const FIXTURE_DB_VERSION = 2;

interface FixtureDb {
  version?: number;
  farms: Record<string, FarmEnvelope>;
  analyses: Record<string, RotationAnalysis>;
  plans: Record<string, SavedPlan>;
  scenarios?: Record<string, ScenarioResult>;
  seq: number;
}

let memoryDb: FixtureDb | null = null;

function load(): FixtureDb {
  if (memoryDb) return memoryDb;
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) {
      const db = JSON.parse(raw) as FixtureDb;
      if (db.version !== FIXTURE_DB_VERSION) {
        db.analyses = {};
        db.plans = {};
        db.version = FIXTURE_DB_VERSION;
      }
      return (memoryDb = db);
    }
  } catch {
    /* storage unavailable or corrupt — start fresh */
  }
  return (memoryDb = { version: FIXTURE_DB_VERSION, farms: {}, analyses: {}, plans: {}, seq: 0 });
}

function save(db: FixtureDb) {
  memoryDb = db;
  try {
    localStorage.setItem(STORE_KEY, JSON.stringify(db));
  } catch {
    /* ignore quota/private-mode errors; memory copy still works */
  }
}

function nextId(db: FixtureDb, prefix: string) {
  db.seq += 1;
  return `${prefix}-${String(db.seq).padStart(3, "0")}`;
}

/** Test helper: wipe fixture state. */
export function resetFixtures() {
  memoryDb = { version: FIXTURE_DB_VERSION, farms: {}, analyses: {}, plans: {}, seq: 0 };
  try {
    localStorage.removeItem(STORE_KEY);
  } catch {
    /* ignore */
  }
}

function fail(status: number, code: string, message: string, fields?: Record<string, string>): never {
  throw new ApiClientError(status, { error: { code, message, fields } });
}

const delay = (ms: number, signal?: AbortSignal) =>
  new Promise<void>((resolve, reject) => {
    if (signal?.aborted) return reject(new DOMException("Request cancelled", "AbortError"));
    const id = setTimeout(resolve, import.meta.env.MODE === "test" ? 0 : ms);
    signal?.addEventListener("abort", () => {
      clearTimeout(id);
      reject(new DOMException("Request cancelled", "AbortError"));
    });
  });

// ---------------------------------------------------------------------------
// Farms
// ---------------------------------------------------------------------------

type ProfileInput = Omit<FarmProfile, "schema_version">;

function withSchema(profile: ProfileInput): FarmProfile {
  return { ...profile, schema_version: "0.1" };
}

export async function createFarmFixture(profile: ProfileInput, signal?: AbortSignal): Promise<FarmEnvelope> {
  await delay(300, signal);
  if (!(profile.area_ha > 0)) fail(422, "VALIDATION_ERROR", "Area must be positive.", { area_ha: "Must be greater than zero." });
  const db = load();
  const id = nextId(db, "farm");
  const env: FarmEnvelope = { id, input_version: 1, profile: withSchema(profile) };
  db.farms[id] = env;
  save(db);
  return env;
}

/** Create the documented synthetic demo farm (data/fixtures/farm.synthetic.json). */
export async function createDemoFarmFixture(signal?: AbortSignal): Promise<FarmEnvelope> {
  return createFarmFixture(demoFarmProfile as FarmProfile, signal);
}

export async function getFarmFixture(farmId: string, signal?: AbortSignal): Promise<FarmEnvelope> {
  await delay(150, signal);
  const env = load().farms[farmId];
  if (!env) fail(404, "NOT_FOUND", `Farm ${farmId} was not found.`);
  return env;
}

export async function updateFarmFixture(
  farmId: string,
  expectedVersion: number,
  profile: ProfileInput,
  signal?: AbortSignal,
): Promise<FarmEnvelope> {
  await delay(250, signal);
  const db = load();
  const current = db.farms[farmId];
  if (!current) fail(404, "NOT_FOUND", `Farm ${farmId} was not found.`);
  if (expectedVersion !== current.input_version) {
    fail(409, "VERSION_CONFLICT", "Farm was updated by another session. Reload and try again.");
  }
  const env: FarmEnvelope = { id: farmId, input_version: current.input_version + 1, profile: withSchema(profile) };
  db.farms[farmId] = env;
  save(db);
  return env;
}

// ---------------------------------------------------------------------------
// Observations (synthetic, deterministic; Matheesha's normalized shape)
// ---------------------------------------------------------------------------

/** Rough Sri Lanka bounding box; outside it the fixture reports no coverage. */
function insideDemoRegion(lat: number, lon: number) {
  return lat >= 5.8 && lat <= 9.9 && lon >= 79.5 && lon <= 82.0;
}

function seeded(seed: number) {
  let x = Math.abs(Math.round(seed)) % 2147483647 || 1;
  return () => (x = (x * 16807) % 2147483647) / 2147483647;
}

function todayUtc() {
  return new Date().toISOString().slice(0, 10);
}

export async function getObservationsFixture(
  farmId: string,
  start: string,
  end: string,
  signal?: AbortSignal,
): Promise<ObservationSummary> {
  await delay(500, signal);
  // Same validation as Dulanjaya's endpoint.
  if (start > end) fail(422, "VALIDATION_ERROR", "Start date must not be later than end date.", { start: "Must be ≤ end." });
  if (start < "1981-01-01") fail(422, "VALIDATION_ERROR", "NASA POWER historical dates start at 1981-01-01.", { start: "≥ 1981-01-01" });
  if (end >= todayUtc()) fail(422, "VALIDATION_ERROR", "End date must be before today in UTC.", { end: "Before today (UTC)" });
  const farm = load().farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", `Farm ${farmId} was not found.`);

  const days = Math.round((Date.parse(end) - Date.parse(start)) / 86_400_000) + 1;
  const { latitude, longitude } = farm.profile.location;
  const covered = insideDemoRegion(latitude, longitude);
  const rand = seeded(latitude * 1000 + longitude * 1000 + Date.parse(start) / 86_400_000);

  const daily = Array.from({ length: days }, (_, i) => {
    const date = new Date(Date.parse(start) + i * 86_400_000).toISOString().slice(0, 10);
    // Temperature is missing every 9th day to demonstrate per-variable gaps (never zero-filled).
    const tempMissing = !covered || i % 9 === 4;
    return {
      date,
      precipitation_mm_per_day: covered ? Math.round(rand() * 14 * 10) / 10 : null,
      temperature_c: tempMissing ? null : Math.round((25 + rand() * 5) * 10) / 10,
      temperature_max_c: null,
      temperature_min_c: null,
    };
  });
  const rain = daily.filter((d) => d.precipitation_mm_per_day !== null);
  const temp = daily.filter((d) => d.temperature_c !== null);
  const both = daily.filter((d) => d.precipitation_mm_per_day !== null && d.temperature_c !== null);
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
  const rainComplete = rain.length === days;
  const partialRain = rain.length ? Math.round(sum(rain.map((d) => d.precipitation_mm_per_day!)) * 10) / 10 : null;

  return {
    observation_id: `obs-${farmId}-v${farm.input_version}-${start}-${end}`,
    farm_id: farmId,
    input_version: farm.input_version,
    data_kind: "synthetic",
    provider: "Synthetic fixture (not NASA POWER)",
    period: { start, end },
    retrieved_at: null,
    source_refs: [SOURCE],
    source_url: null,
    spatial_resolution: { description: "synthetic fixture — no real grid" },
    time_standard: "UTC",
    coverage: {
      expected_days: days,
      available_days: both.length,
      precipitation_valid_days: rain.length,
      temperature_valid_days: temp.length,
    },
    summary: {
      // Full-period total is null when any rainfall day is missing; partial sum labelled separately.
      rainfall_mm: rainComplete ? partialRain : null,
      rainfall_total_mm: rainComplete ? partialRain : null,
      rainfall_available_days_mm: partialRain,
      mean_temperature_c: temp.length ? Math.round((sum(temp.map((d) => d.temperature_c!)) / temp.length) * 10) / 10 : null,
    },
    units: { precipitation_mm_per_day: "mm/day", temperature_c: "°C" },
    missing_data: {
      precipitation_mm_per_day: daily.filter((d) => d.precipitation_mm_per_day === null).map((d) => d.date),
      temperature_c: daily.filter((d) => d.temperature_c === null).map((d) => d.date),
    },
    daily,
    limitations: [
      "Invented values for interface development; not NASA data.",
      ...(covered ? [] : ["Location is outside the fixture's demonstration region, so no values are available."]),
    ],
  };
}

export async function getSoilMoistureFixture(farmId: string, signal?: AbortSignal) {
  await delay(100, signal);
  const farm = load().farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", "Farm not found.");
  return {
    schema_version: "0.1" as const,
    kind: "smap_surface_soil_moisture_series" as const,
    data_kind: "satellite_retrieval" as const,
    farm_id: farmId,
    input_version: farm.input_version,
    product: "SPL3SMP_E" as const,
    version: "006" as const,
    units: "m3/m3" as const,
    requested_point: farm.profile.location,
    farm_distance_km: 0,
    period: { start: "2025-01-01", end: "2025-01-01" },
    max_distance_km: 15,
    coverage: { expected_days: 1, supplied_granule_days: 1, accepted_AM: 0, accepted_PM: 0 },
    daily: [{ date: "2025-01-01", granule_supplied: true,
      AM: { pass: "AM" as const, accepted: false, soil_moisture_m3_m3: null, rejection_reason: "synthetic_fixture_no_retrieval" },
      PM: { pass: "PM" as const, accepted: false, soil_moisture_m3_m3: null, rejection_reason: "synthetic_fixture_no_retrieval" } }],
    source_refs: ["synthetic-fixture-not-nasa"],
    limitations: ["Synthetic fixture only; no SMAP moisture value is supplied."],
  };
}

export async function getGpmPrecipitationFixture(farmId: string, signal?: AbortSignal) {
  await delay(100, signal);
  const farm = load().farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", "Farm not found.");
  return {
    schema_version: "0.1" as const, kind: "gpm_imerg_daily_series" as const,
    data_kind: "synthetic" as const, farm_id: farmId, input_version: farm.input_version,
    product: "GPM_3IMERGDF" as const, version: "07" as const, units: "mm/day" as const,
    requested_point: farm.profile.location, farm_distance_km: 0,
    period: { start: "2025-01-01", end: "2025-01-01" }, spatial_resolution_degrees: 0.1,
    coverage: { expected_days: 1, valid_days: 0 },
    daily: [{ date: "2025-01-01", precipitation_mm: null }],
    source_refs: ["synthetic-fixture-not-nasa"], retrieved_at: null,
    limitations: ["Synthetic interface fixture; no GPM precipitation value is supplied."],
  };
}

export async function getHlsVegetationFixture(farmId: string, signal?: AbortSignal) {
  await delay(100, signal);
  const farm = load().farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", "Farm not found.");
  return {
    schema_version: "0.1" as const, kind: "hls_vegetation_series" as const,
    data_kind: "synthetic" as const, farm_id: farmId, input_version: farm.input_version,
    products: ["HLSL30" as const, "HLSS30" as const], version: "2.0" as const, index: "NDVI" as const,
    requested_point: farm.profile.location, farm_distance_km: 0, spatial_resolution_m: 30,
    period: { start: "2025-01-01", end: "2025-01-01" },
    coverage: { supplied_observations: 0, accepted_observations: 0 }, observations: [],
    source_refs: ["synthetic-fixture-not-nasa"], retrieved_at: null,
    limitations: ["Synthetic interface fixture; no HLS vegetation value is supplied."],
  };
}

export async function getClimateTwinsFixture(farmId: string, observationId: string, signal?: AbortSignal) {
  await delay(100, signal);
  const farm = load().farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", "Farm not found.");
  return { schema_version: "0.1" as const, kind: "historical_climate_twins" as const,
    farm_id: farmId, observation_id: observationId,
    period: { start: "2025-01-01", end: "2025-01-31" }, twins: [], excluded: [],
    source_refs: ["synthetic-fixture-not-nasa"],
    assumptions: ["Fixture mode does not invent comparison farms."],
    limitations: ["No real NASA POWER comparison snapshots exist in fixture mode."],
  };
}

const feedbackKey = (planId: string) => `agrosphere_fixture_feedback_${planId}`;
export async function listPlanFeedbackFixture(planId: string, signal?: AbortSignal) {
  await delay(50, signal);
  return JSON.parse(localStorage.getItem(feedbackKey(planId)) ?? "[]");
}
export async function createPlanFeedbackFixture(planId: string, body: import("../types/api").SeasonFeedbackRequest, signal?: AbortSignal) {
  await delay(50, signal);
  const item = { schema_version: "0.1" as const, feedback_id: crypto.randomUUID(), plan_id: planId,
    data_kind: "farmer_input" as const, created_at: new Date().toISOString(), ...body,
    limitations: ["Farmer-entered fixture outcome; not independently verified."] };
  const prior = await listPlanFeedbackFixture(planId);
  localStorage.setItem(feedbackKey(planId), JSON.stringify([item, ...prior]));
  return item;
}

// ---------------------------------------------------------------------------
// Rotations — synthetic implementation of rotation-score-0.1
// (docs/ROTATION_SCORING_SPEC.md, Bhagya). Crop values and seasonal rainfall
// below are INVENTED for UI development; they are not catalog or NASA values.
// ---------------------------------------------------------------------------

export const FIXTURE_MODEL_VERSION = "rotation-score-0.1 (fixture)";
const FIXTURE_WATER_MODEL = "fixture-water-range-v1";

interface FixtureCrop {
  id: string;
  name: string;
  /** Synthetic seasonal ETc range, mm per crop cycle. */
  demand_low: number;
  demand_high: number;
}

const FIXTURE_CROPS: Record<string, FixtureCrop> = {
  rice: { id: "rice", name: "Rice", demand_low: 450, demand_high: 700 },
  cowpea: { id: "cowpea", name: "Cowpea", demand_low: 250, demand_high: 350 },
  maize: { id: "maize", name: "Maize", demand_low: 400, demand_high: 550 },
  groundnut: { id: "groundnut", name: "Groundnut", demand_low: 350, demand_high: 500 },
  vegetables: { id: "vegetables", name: "Mixed vegetables", demand_low: 300, demand_high: 450 },
  soybean: { id: "soybean", name: "Soybean", demand_low: 350, demand_high: 450 },
};

/** Synthetic seasonal rainfall totals (mm) for the demo; not observations. */
const FIXTURE_SEASON_RAINFALL: Record<string, number> = { maha: 650, yala: 300, "inter-season": 150 };

const TEMPLATES: string[][] = [
  ["rice", "cowpea", "maize"],
  ["rice", "groundnut", "vegetables"],
  ["maize", "soybean", "rice"],
];

const seasonLabels = (n: number) => Array.from({ length: n }, (_, i) => (i % 2 === 0 ? "maha" : "yala"));
const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;

interface ScoreInputs {
  weights: RotationRequest["priority_weights"];
  irrigationPerSeason: number | null;
  /** null = baseline only (no scenario); otherwise 1 + pct/100. */
  scenarioFactor: number | null;
  /** Explicit season identity per season (defaults to alternating maha/yala). */
  labels?: string[];
}

/** Score one sequence per rotation-score-0.1. Unknown inputs stay null; nothing becomes 0. */
export function scoreSequence(cropIds: string[], candidateId: string, inp: ScoreInputs): RotationCandidate & { _tie: number[] } {
  const labels = inp.labels && inp.labels.length === cropIds.length ? inp.labels : seasonLabels(cropIds.length);
  const crops = cropIds.map((id) => FIXTURE_CROPS[id]);
  const factor = inp.scenarioFactor ?? 1;
  const irr = inp.irrigationPerSeason;

  const ranges: WaterBudgetRange[] = crops.map((c, i) => {
    const base = FIXTURE_SEASON_RAINFALL[labels[i]];
    const scen = base * factor;
    // A rainfall-only budget is valid only when irrigation is confirmed as zero.
    const available = irr === null ? null : scen + irr;
    return {
      season_index: i + 1,
      season_label: labels[i],
      crop_id: c.id,
      demand_low_mm: c.demand_low,
      demand_high_mm: c.demand_high,
      baseline_rainfall_mm: base,
      scenario_rainfall_mm: scen,
      irrigation_mm: irr,
      baseline_available_water_mm: irr === null ? null : base + irr,
      baseline_coverage_low_percent: irr === null ? null : ((base + irr) / c.demand_high) * 100,
      baseline_coverage_high_percent: irr === null ? null : ((base + irr) / c.demand_low) * 100,
      available_water_mm: available,
      balance_low_mm: available === null ? null : available - c.demand_high,
      balance_high_mm: available === null ? null : available - c.demand_low,
      coverage_low_percent: available === null ? null : (available / c.demand_high) * 100,
      coverage_high_percent: available === null ? null : (available / c.demand_low) * 100,
      demand_basis: "seasonal_crop_water_need_etc",
      model_version: FIXTURE_WATER_MODEL,
      source_url: null,
      assumptions: [
        "Synthetic demand range and seasonal rainfall for interface development; not catalog or NASA values.",
        "Total rainfall is used only for provisional screening; effective rainfall and field losses are not modeled.",
        inp.scenarioFactor === null
          ? "Baseline: no rainfall-change scenario applied."
          : `Hypothetical rainfall change of ${Math.round((factor - 1) * 100)}% applied; not a forecast.`,
      ],
      limitations:
        irr === null
          ? ["Irrigation supply unknown: water availability, balance, and coverage are unavailable until it is confirmed."]
          : [],
    };
  });

  const baseCov = irr === null ? [] : crops.map((c, i) => {
    const avail = FIXTURE_SEASON_RAINFALL[labels[i]] + irr;
    return avail / c.demand_high * 100;
  });
  const water = irr === null ? null : mean(baseCov.map((v) => Math.min(100, v)));
  const diversity = (new Set(cropIds).size / cropIds.length) * 100;
  const resilience =
    inp.scenarioFactor === null || irr === null
      ? null
      : mean(ranges.map((r) => Math.min(100, r.available_water_mm! / r.demand_high_mm! * 100)));

  const raw = [
    { name: "water_sufficiency", requested_weight: inp.weights.water, value: water },
    { name: "crop_diversity", requested_weight: inp.weights.soil, value: diversity },
    { name: "scenario_resilience", requested_weight: inp.weights.climate, value: resilience },
  ];
  const availableWeight = raw.filter((c) => c.value !== null).reduce((a, c) => a + c.requested_weight, 0);
  const components: ScoreComponent[] = raw.map((c) => ({
    ...c,
    effective_weight: c.value === null || !(availableWeight > 0) ? 0 : c.requested_weight / availableWeight,
    direction: "higher_is_better" as const,
  }));
  const score = availableWeight > 0 ? components.reduce((a, c) => a + (c.value ?? 0) * c.effective_weight, 0) : null;

  const demandHigh = crops.reduce((a, c) => a + c.demand_high, 0);
  const rainTotal = labels.reduce((a, l) => a + FIXTURE_SEASON_RAINFALL[l] * factor, 0);
  const irrTotal = irr === null ? null : irr * cropIds.length;

  return {
    candidate_id: candidateId,
    sequence: crops.map((c, i) => ({ season_index: i + 1, crop_id: c.id, crop_name: c.name })),
    score,
    score_components: components,
    water_budget_range: ranges,
    water_budget: {
      period: `${cropIds.length}-season aggregate`,
      demand_mm: demandHigh,
      rainfall_mm: rainTotal,
      rainfall_total_mm: rainTotal,
      effective_rainfall_mm: null,
      irrigation_supply_mm: irrTotal,
      deficit_mm: irrTotal === null ? null : Math.max(0, demandHigh - rainTotal - irrTotal),
      unit: "mm",
      assumptions: [
        "Optional aggregate of non-overlapping fixture seasons using high-end demand; see the per-season table.",
        "Effective rainfall: no approved method (null).",
      ],
    },
    reasons: ["Feasible under the currently enabled documented constraints."],
    constraint_checks: [
      { rule: "catalog_review", passed: true, note: "Fixture crops remain synthetic; the live catalog separately uses documented demo-reviewed screening proxies." },
      { rule: "season_eligibility", passed: true, note: `Seasons: ${labels.join(", ")}` },
      { rule: "farmer_exclusion", passed: true, note: null },
    ],
    _tie: [score ?? -Infinity, baseCov.length ? mean(baseCov) : -Infinity, diversity],
  };
}

/** Spec ordering: score ↓, conservative baseline coverage ↓, diversity ↓, crop-ID sequence ↑. */
function rank(cands: (RotationCandidate & { _tie: number[] })[]): RotationCandidate[] {
  return [...cands]
    .sort((a, b) => {
      for (let i = 0; i < 3; i++) if (b._tie[i] !== a._tie[i]) return b._tie[i] - a._tie[i];
      return a.sequence.map((s) => s.crop_id).join(",").localeCompare(b.sequence.map((s) => s.crop_id).join(","));
    })
    .map(({ _tie: _t, ...c }) => c);
}

export async function createRotationFixture(
  farmId: string,
  body: RotationRequest,
  signal?: AbortSignal,
): Promise<RotationAnalysis> {
  await delay(700, signal);
  if (body.seasons < 3 || body.seasons > 5) fail(422, "VALIDATION_ERROR", "Seasons must be 3–5.", { seasons: "3–5" });
  const w = body.priority_weights;
  if (![w.water, w.soil, w.climate].every((x) => Number.isFinite(x) && x >= 0) || !(w.water + w.soil + w.climate > 0)) {
    fail(422, "VALIDATION_ERROR", "Priority weights must be nonnegative with a positive total.");
  }
  const db = load();
  const farm = db.farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", `Farm ${farmId} was not found.`);
  if (farm.input_version !== body.input_version) {
    fail(409, "VERSION_CONFLICT", "The farm changed since this request was prepared. Reload and try again.");
  }

  if (body.season_labels && body.season_labels.length !== body.seasons) {
    fail(422, "VALIDATION_ERROR", "season_labels must have one label per season.", { season_labels: "One label per season" });
  }
  const excluded = new Set(farm.profile.excluded_crop_ids.map((c) => c.toLowerCase()));
  const reasons: string[] = [];
  const scored: (RotationCandidate & { _tie: number[] })[] = [];
  TEMPLATES.forEach((tpl, i) => {
    const seq = Array.from({ length: body.seasons }, (_, k) => tpl[k % tpl.length]);
    const hit = seq.find((c) => excluded.has(c));
    if (hit) {
      reasons.push(`Sequence ${seq.join(" → ")} rejected: farmer_exclusion failed ("${hit}" is excluded).`);
      return;
    }
    scored.push(
      scoreSequence(seq, `cand-${i + 1}`, {
        weights: w,
        irrigationPerSeason: farm.profile.irrigation_supply_mm_per_season,
        scenarioFactor: null,
        labels: body.season_labels,
      }),
    );
  });
  if (scored.length === 0) reasons.push("No fixture sequence remains after the farmer's exclusions.");
  else if (scored.length < 3) reasons.push(`Only ${scored.length} feasible plan(s) after applying exclusions.`);

  const analysis: RotationAnalysis = {
    analysis_id: nextId(db, "analysis"),
    farm_id: farmId,
    input_version: body.input_version,
    observation_id: body.observation_id,
    catalog_version: body.catalog_version,
    model_version: FIXTURE_MODEL_VERSION,
    data_kind: "synthetic",
    created_at: new Date().toISOString(),
    candidates: rank(scored),
    reasons,
    assumptions: [
      "All values are synthetic fixtures for UI development.",
      "Scoring follows rotation-score-0.1; scenario_resilience is null until a rainfall scenario is run, so its weight is renormalized away.",
      "Total rainfall is used for provisional screening only; effective rainfall is not modeled.",
    ],
    source_refs: [SOURCE],
    limitations: ["Heuristic comparison only; not a yield prediction or agronomic advice."],
  };
  db.analyses[analysis.analysis_id] = analysis;
  save(db);
  return analysis;
}

// ---------------------------------------------------------------------------
// Scenarios — recomputed from the SAME baseline sequences
// ---------------------------------------------------------------------------

export async function createScenarioFixture(
  analysisId: string,
  rainfallChangePct: number,
  signal?: AbortSignal,
): Promise<ScenarioResult> {
  await delay(500, signal);
  if (rainfallChangePct < -100 || rainfallChangePct > 100) {
    fail(422, "VALIDATION_ERROR", "rainfall_change_pct must be between -100 and 100.");
  }
  const db = load();
  const baseline = db.analyses[analysisId];
  if (!baseline) fail(404, "NOT_FOUND", `Analysis ${analysisId} was not found.`);
  const farm = db.farms[baseline.farm_id];
  const req = (c: RotationCandidate, name: string) => c.score_components.find((x) => x.name === name)?.requested_weight ?? 0;

  const recalculated = rank(
    baseline.candidates.map((b) =>
      scoreSequence(
        b.sequence.map((s) => s.crop_id),
        b.candidate_id,
        {
          weights: { water: req(b, "water_sufficiency"), soil: req(b, "crop_diversity"), climate: req(b, "scenario_resilience") },
          irrigationPerSeason: farm?.profile.irrigation_supply_mm_per_season ?? null,
          scenarioFactor: 1 + rainfallChangePct / 100,
          labels: asSeasonRanges(b.water_budget_range).map((r) => r.season_label ?? ""),
        },
      ),
    ),
  );

  const differences = Object.fromEntries(
    recalculated.map((s, newRank) => {
      const oldRank = baseline.candidates.findIndex((c) => c.candidate_id === s.candidate_id);
      const b = baseline.candidates[oldRank];
      return [
        s.candidate_id,
        {
          score_change: s.score === null || b.score === null ? null : s.score - b.score,
          rank_baseline: oldRank + 1,
          rank_scenario: newRank + 1,
          scenario_resilience: s.score_components.find((c) => c.name === "scenario_resilience")?.value ?? null,
        },
      ];
    }),
  );

  const scenario: ScenarioResult = {
    scenario_id: nextId(db, "scenario"),
    baseline_analysis_id: analysisId,
    parameters: { rainfall_change_pct: rainfallChangePct },
    candidates: recalculated,
    baseline_differences: differences,
    limitations: [
      `Hypothetical scenario: rainfall ${rainfallChangePct > 0 ? "+" : ""}${rainfallChangePct}% relative to the baseline. Not a weather forecast.`,
      "Synthetic fixture recalculation; Bhagya's engine will replace it.",
    ],
    data_kind: "synthetic",
    created_at: new Date().toISOString(),
  };
  db.scenarios = { ...(db.scenarios ?? {}), [scenario.scenario_id]: scenario };
  save(db);
  return scenario;

}

// ---------------------------------------------------------------------------
// Assistant (synthetic, grounded in the cached analysis numbers)
// ---------------------------------------------------------------------------

export async function sendAssistantMessageFixture(body: AssistantRequest, signal?: AbortSignal): Promise<AssistantMessage> {
  await delay(600, signal);
  // Mirrors Akash's service: only English until si/ta are implemented and reviewed.
  if (body.language !== "en") {
    fail(422, "UNSUPPORTED_LANGUAGE", `Language "${body.language}" is not supported yet. English is available.`);
  }
  const db = load();
  const analysis = db.analyses[body.analysis_id];
  if (!analysis || analysis.farm_id !== body.farm_id) {
    fail(409, "CONTEXT_MISMATCH", "The selected analysis does not belong to this farm.");
  }
  const cand = analysis.candidates.find((c) => c.candidate_id === body.candidate_id) ?? analysis.candidates[0];
  const water = cand?.score_components.find((c) => c.name === "water_sufficiency")?.value;
  const content = cand
    ? `[Fixture response] For "${body.message}": in analysis ${analysis.analysis_id}, ${cand.candidate_id} ` +
      `(${cand.sequence.map((s) => s.crop_name ?? s.crop_id).join(" → ")}) has a heuristic comparison score of ` +
      `${cand.score === null ? "unknown" : cand.score.toFixed(1)} out of 100 and water sufficiency of ` +
      `${water === null || water === undefined ? "unknown" : water.toFixed(1)}. This is a screening estimate, not a yield prediction. ` +
      `Real grounded explanations come from the assistant service (Akash).`
    : `[Fixture response] Analysis ${analysis.analysis_id} has no feasible plans, so there is nothing to explain yet.`;
  return {
    role: "assistant",
    content,
    // Mirrors Akash's respond(): coarse status plus assumptions alongside the four required fields.
    status: !cand ? "insufficient_context" : water === null || water === undefined ? "insufficient_context" : "answered",
    language: "en",
    assumptions: analysis.assumptions.slice(0, 2),
    source_ids: [analysis.analysis_id, ...(body.scenario_id ? [body.scenario_id] : []), ...(analysis.observation_id ? [analysis.observation_id] : []), SOURCE],
    limitations: [
      "Synthetic fixture response, not a model-generated answer.",
      ...(cand && cand.water_budget_range && cand.score_components.some((c) => c.value === null)
        ? ["Some score components are unavailable for this plan."]
        : []),
    ],
  };
}

// ---------------------------------------------------------------------------
// Plans
// ---------------------------------------------------------------------------

export async function savePlanFixture(farmId: string, body: PlanRequest, signal?: AbortSignal): Promise<{ plan_id: string }> {
  await delay(250, signal);
  const db = load();
  const farm = db.farms[farmId];
  const analysis = db.analyses[body.analysis_id];
  if (!farm || !analysis) fail(404, "NOT_FOUND", "Farm or analysis not found.");
  if (analysis.farm_id !== farmId) fail(409, "CONTEXT_MISMATCH", "Analysis does not belong to this farm.");
  if (body.expected_input_version !== farm.input_version || analysis.input_version !== farm.input_version) {
    fail(409, "VERSION_CONFLICT", "The farm changed after this analysis. Re-run the rotation before saving.");
  }
  let source: RotationCandidate[] = analysis.candidates;
  if (body.scenario_id) {
    const sc = db.scenarios?.[body.scenario_id];
    if (!sc) fail(404, "NOT_FOUND", "Scenario not found.");
    if (sc.baseline_analysis_id !== analysis.analysis_id) fail(409, "CONTEXT_MISMATCH", "Scenario is not based on this analysis.");
    source = sc.candidates;
  }
  const candidate = source.find((c) => c.candidate_id === body.candidate_id);
  if (!candidate) fail(422, "VALIDATION_ERROR", "Candidate not found in analysis.");

  const planId = nextId(db, "plan");
  db.plans[planId] = {
    plan_id: planId,
    farm_id: farmId,
    analysis_id: body.analysis_id,
    scenario_id: body.scenario_id ?? null,
    candidate_id: body.candidate_id,
    input_version: farm.input_version,
    created_at: new Date().toISOString(),
    candidate_snapshot: candidate,
    input_snapshot: farm.profile,
    analysis_snapshot: {
      catalog_version: analysis.catalog_version,
      model_version: analysis.model_version,
      source_refs: analysis.source_refs,
      assumptions: analysis.assumptions,
      limitations: analysis.limitations,
      data_kind: analysis.data_kind,
      analysis_created_at: analysis.created_at,
    },
  };
  save(db);
  return { plan_id: planId };
}

export async function getPlanFixture(planId: string, signal?: AbortSignal): Promise<SavedPlan> {
  await delay(200, signal);
  const plan = load().plans[planId];
  if (!plan) fail(404, "NOT_FOUND", "Plan not found.");
  return plan;
}
