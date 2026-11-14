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
} from "../types/api";

const STORE_KEY = "agrosphere_fixture_db";
const SOURCE = "synthetic-fixture-v1";

interface FixtureDb {
  farms: Record<string, FarmEnvelope>;
  analyses: Record<string, RotationAnalysis>;
  plans: Record<string, SavedPlan>;
  seq: number;
}

let memoryDb: FixtureDb | null = null;

function load(): FixtureDb {
  if (memoryDb) return memoryDb;
  try {
    const raw = localStorage.getItem(STORE_KEY);
    if (raw) return (memoryDb = JSON.parse(raw) as FixtureDb);
  } catch {
    /* storage unavailable or corrupt — start fresh */
  }
  return (memoryDb = { farms: {}, analyses: {}, plans: {}, seq: 0 });
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
  memoryDb = { farms: {}, analyses: {}, plans: {}, seq: 0 };
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
// Observations (synthetic, deterministic, with deliberate gaps)
// ---------------------------------------------------------------------------

/** Rough Sri Lanka bounding box; outside it the fixture reports no coverage. */
function insideDemoRegion(lat: number, lon: number) {
  return lat >= 5.8 && lat <= 9.9 && lon >= 79.5 && lon <= 82.0;
}

function seeded(seed: number) {
  let x = seed % 2147483647 || 1;
  return () => (x = (x * 16807) % 2147483647) / 2147483647;
}

export async function getObservationsFixture(
  farmId: string,
  start: string,
  end: string,
  signal?: AbortSignal,
): Promise<ObservationSummary> {
  await delay(500, signal);
  if (start > end) fail(422, "VALIDATION_ERROR", "Start date must be on or before end date.", { start: "Must be ≤ end." });
  const farm = load().farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", `Farm ${farmId} was not found.`);

  const days = Math.round((Date.parse(end) - Date.parse(start)) / 86_400_000) + 1;
  const { latitude, longitude } = farm.profile.location;
  const covered = insideDemoRegion(latitude, longitude);
  const rand = seeded(Math.round(latitude * 1000 + longitude * 1000) + Date.parse(start) / 86_400_000);

  const series = Array.from({ length: days }, (_, i) => {
    const date = new Date(Date.parse(start) + i * 86_400_000).toISOString().slice(0, 10);
    // Every 9th day is missing to demonstrate gaps (never zero-filled).
    const missing = !covered || i % 9 === 4;
    return {
      date,
      rainfall_mm: missing ? null : Math.round(rand() * 14 * 10) / 10,
      mean_temperature_c: missing ? null : Math.round((25 + rand() * 5) * 10) / 10,
    };
  });
  const present = series.filter((p) => p.rainfall_mm !== null);
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

  return {
    observation_id: `obs-${farmId}-${start}-${end}`,
    farm_id: farmId,
    input_version: farm.input_version,
    data_kind: "synthetic",
    period: { start, end },
    retrieved_at: null,
    source_refs: [SOURCE],
    spatial_resolution: null,
    coverage: { expected_days: days, available_days: present.length },
    summary: {
      rainfall_mm: present.length ? Math.round(sum(present.map((p) => p.rainfall_mm!)) * 10) / 10 : null,
      mean_temperature_c: present.length
        ? Math.round((sum(present.map((p) => p.mean_temperature_c!)) / present.length) * 10) / 10
        : null,
    },
    limitations: [
      "Invented values for interface development; not NASA data.",
      ...(covered ? [] : ["Location is outside the fixture's demonstration region, so no values are available."]),
    ],
    time_series: series,
  };
}

// ---------------------------------------------------------------------------
// Rotations (synthetic)
// ---------------------------------------------------------------------------

interface Template {
  crops: { id: string; name: string; demand: number }[];
  values: { water: number; soil: number; climate: number };
  reasons: string[];
}

const TEMPLATES: Template[] = [
  {
    crops: [
      { id: "rice", name: "Rice", demand: 200 },
      { id: "cowpea", name: "Cowpea", demand: 110 },
      { id: "maize", name: "Maize", demand: 140 },
    ],
    values: { water: 0.78, soil: 0.9, climate: 0.8 },
    reasons: ["Includes a legume (cowpea) between cereals", "Alternates crop families each season"],
  },
  {
    crops: [
      { id: "rice", name: "Rice", demand: 200 },
      { id: "groundnut", name: "Groundnut", demand: 130 },
      { id: "vegetables", name: "Mixed vegetables", demand: 170 },
    ],
    values: { water: 0.7, soil: 0.82, climate: 0.72 },
    reasons: ["Includes a legume (groundnut)", "Vegetables add diversity"],
  },
  {
    crops: [
      { id: "maize", name: "Maize", demand: 140 },
      { id: "soybean", name: "Soybean", demand: 120 },
      { id: "rice", name: "Rice", demand: 200 },
    ],
    values: { water: 0.65, soil: 0.78, climate: 0.68 },
    reasons: ["Opens with lower-demand crops before rice"],
  },
];

const FIXTURE_RAINFALL_PER_SEASON_MM = 100;
const EFFECTIVE_RAINFALL_FRACTION = 0.8;

function weightedScore(components: ScoreComponent[]) {
  const total = components.reduce((a, c) => a + c.weight, 0);
  if (!(total > 0)) return 0;
  return Math.round((components.reduce((a, c) => a + c.weight * c.value, 0) / total) * 1000) / 1000;
}

function buildCandidate(
  t: Template,
  index: number,
  seasons: number,
  weights: RotationRequest["priority_weights"],
  irrigationPerSeason: number | null,
  rainfallFactor = 1,
): RotationCandidate {
  const steps = Array.from({ length: seasons }, (_, i) => t.crops[i % t.crops.length]);
  const demand = steps.reduce((a, c) => a + c.demand, 0);
  const rainfall = Math.round(FIXTURE_RAINFALL_PER_SEASON_MM * seasons * rainfallFactor);
  const effective = Math.round(rainfall * EFFECTIVE_RAINFALL_FRACTION);
  const irrigation = irrigationPerSeason === null ? null : irrigationPerSeason * seasons;
  const deficit = irrigation === null ? null : Math.max(0, demand - effective - irrigation);
  const unmetShare = deficit === null ? 0 : Math.min(1, deficit / demand);
  const waterValue = Math.max(0, Math.round((t.values.water - unmetShare * 0.5 - (1 - rainfallFactor) * 0.2) * 100) / 100);

  const components: ScoreComponent[] = [
    { name: "Water efficiency", weight: weights.water, value: waterValue, direction: "higher_is_better" },
    { name: "Soil health", weight: weights.soil, value: t.values.soil, direction: "higher_is_better" },
    { name: "Climate resilience", weight: weights.climate, value: t.values.climate, direction: "higher_is_better" },
  ];
  return {
    candidate_id: `cand-${index + 1}`,
    sequence: steps.map((c, i) => ({ season_index: i + 1, crop_id: c.id, crop_name: c.name })),
    score: weightedScore(components),
    score_components: components,
    water_budget: {
      period: `${seasons}-season cycle`,
      demand_mm: demand,
      rainfall_mm: rainfall,
      effective_rainfall_mm: effective,
      irrigation_supply_mm: irrigation,
      deficit_mm: deficit,
      unit: "mm",
      assumptions: [
        `Fixture rainfall of ${FIXTURE_RAINFALL_PER_SEASON_MM} mm per season${rainfallFactor !== 1 ? `, scaled by ${rainfallFactor.toFixed(2)}` : ""}`,
        `Effective rainfall = ${EFFECTIVE_RAINFALL_FRACTION * 100}% of rainfall (placeholder, pending Bhagya)`,
        irrigation === null ? "Irrigation supply unknown — deficit cannot be computed" : "Irrigation supply from farm profile",
      ],
    },
    reasons: t.reasons,
    constraint_checks: [
      { rule: "No same crop in consecutive seasons", passed: steps.every((c, i) => i === 0 || c.id !== steps[i - 1].id), note: null },
      {
        rule: "Water budget feasibility",
        passed: deficit !== null && deficit === 0,
        note: deficit === null ? "Unknown irrigation supply" : deficit === 0 ? null : `${deficit} mm deficit`,
      },
    ],
  };
}

function rank(cands: RotationCandidate[]) {
  return [...cands].sort((a, b) => b.score - a.score || a.candidate_id.localeCompare(b.candidate_id));
}

export async function createRotationFixture(
  farmId: string,
  body: RotationRequest,
  signal?: AbortSignal,
): Promise<RotationAnalysis> {
  await delay(700, signal);
  if (body.seasons < 3 || body.seasons > 5) fail(422, "VALIDATION_ERROR", "Seasons must be 3–5.", { seasons: "3–5" });
  const db = load();
  const farm = db.farms[farmId];
  if (!farm) fail(404, "NOT_FOUND", `Farm ${farmId} was not found.`);
  if (farm.input_version !== body.input_version) {
    fail(409, "VERSION_CONFLICT", "The farm changed since this request was prepared. Reload and try again.");
  }

  const excluded = new Set(farm.profile.excluded_crop_ids.map((c) => c.toLowerCase()));
  const rejected: string[] = [];
  const candidates: RotationCandidate[] = [];
  TEMPLATES.forEach((t, i) => {
    const hit = t.crops.find((c) => excluded.has(c.id));
    if (hit) rejected.push(`Plan template ${i + 1} rejected: contains excluded crop "${hit.id}".`);
    else candidates.push(buildCandidate(t, i, body.seasons, body.priority_weights, farm.profile.irrigation_supply_mm_per_season));
  });

  const analysis: RotationAnalysis = {
    analysis_id: nextId(db, "analysis"),
    farm_id: farmId,
    input_version: body.input_version,
    observation_id: body.observation_id,
    catalog_version: body.catalog_version,
    model_version: "fixture-v1",
    data_kind: "synthetic",
    created_at: new Date().toISOString(),
    candidates: rank(candidates),
    assumptions: [
      "All values are synthetic fixtures for UI development.",
      "Score = weighted mean of component values using the request's priority weights (placeholder, pending Bhagya).",
    ],
    source_refs: [SOURCE],
    limitations: [
      "Scores are illustrative only. Do not use for agronomic decisions.",
      ...rejected,
      ...(candidates.length < 3 ? [`Only ${candidates.length} feasible plan(s) after applying exclusions.`] : []),
    ],
  };
  db.analyses[analysis.analysis_id] = analysis;
  save(db);
  return analysis;
}

// ---------------------------------------------------------------------------
// Scenarios (synthetic recalculation from the baseline)
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
  const seasons = baseline.candidates[0]?.sequence.length ?? 3;
  const weights = baseline.candidates[0]
    ? Object.fromEntries(baseline.candidates[0].score_components.map((c) => [c.name, c.weight]))
    : {};
  const w = {
    water: weights["Water efficiency"] ?? 0.5,
    soil: weights["Soil health"] ?? 0.3,
    climate: weights["Climate resilience"] ?? 0.2,
  };
  const factor = 1 + rainfallChangePct / 100;

  const recalculated = rank(
    baseline.candidates.map((b) => {
      const tIndex = Number(b.candidate_id.split("-")[1]) - 1;
      return buildCandidate(TEMPLATES[tIndex], tIndex, seasons, w, farm?.profile.irrigation_supply_mm_per_season ?? null, factor);
    }),
  );

  const differences = Object.fromEntries(
    recalculated.map((s, newRank) => {
      const b = baseline.candidates.find((c) => c.candidate_id === s.candidate_id)!;
      const oldRank = baseline.candidates.indexOf(b);
      return [
        s.candidate_id,
        {
          score_change: Math.round((s.score - b.score) * 1000) / 1000,
          deficit_change_mm:
            s.water_budget.deficit_mm === null || b.water_budget.deficit_mm === null
              ? null
              : s.water_budget.deficit_mm - b.water_budget.deficit_mm,
          rank_baseline: oldRank + 1,
          rank_scenario: newRank + 1,
        },
      ];
    }),
  );

  return {
    scenario_id: nextId(db, "scenario"),
    baseline_analysis_id: analysisId,
    parameters: { rainfall_change_pct: rainfallChangePct },
    candidates: recalculated,
    baseline_differences: differences,
    limitations: [
      `Hypothetical scenario: rainfall ${rainfallChangePct > 0 ? "+" : ""}${rainfallChangePct}% relative to the baseline. Not a forecast.`,
      "Synthetic fixture recalculation; the approved water-budget model (Bhagya) will replace it.",
    ],
    data_kind: "synthetic",
    created_at: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// Assistant (synthetic, grounded in the cached analysis numbers)
// ---------------------------------------------------------------------------

export async function sendAssistantMessageFixture(body: AssistantRequest, signal?: AbortSignal): Promise<AssistantMessage> {
  await delay(600, signal);
  const db = load();
  const analysis = db.analyses[body.analysis_id];
  if (!analysis || analysis.farm_id !== body.farm_id) {
    fail(409, "CONTEXT_MISMATCH", "The selected analysis does not belong to this farm.");
  }
  const cand =
    analysis.candidates.find((c) => c.candidate_id === body.candidate_id) ?? analysis.candidates[0];
  const content = cand
    ? `[Fixture response — ${body.language}] For "${body.message}": in analysis ${analysis.analysis_id}, ` +
      `${cand.candidate_id} (${cand.sequence.map((s) => s.crop_name ?? s.crop_id).join(" → ")}) has score ` +
      `${Math.round(cand.score * 100)}; its water deficit ` +
      `${cand.water_budget.deficit_mm === null ? "is unknown because irrigation supply was not provided" : `is ${cand.water_budget.deficit_mm} mm`}. ` +
      `Real grounded explanations come from the assistant service (Akash).`
    : `[Fixture response] Analysis ${analysis.analysis_id} has no feasible plans, so there is nothing to explain yet.`;
  return {
    role: "assistant",
    content,
    source_ids: [analysis.analysis_id, ...(body.scenario_id ? [body.scenario_id] : []), SOURCE],
    limitations: ["Synthetic fixture response, not a model-generated answer."],
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
  const candidate = analysis.candidates.find((c) => c.candidate_id === body.candidate_id);
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
