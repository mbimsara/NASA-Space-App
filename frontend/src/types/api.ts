/**
 * Shared API type definitions.
 * These match the contracts published in docs/API_CONTRACTS.md.
 * Owner: Shehani. Source-of-truth for all contract shapes used by the frontend.
 */

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

export type DataKind = "observed" | "modeled" | "synthetic" | "mixed" | "satellite_retrieval";
export type Language = "en" | "si" | "ta";
export type ReviewStatus = "draft" | "approved";

// ---------------------------------------------------------------------------
// Farm profile (matches data/schemas/farm.schema.json v0.1)
// ---------------------------------------------------------------------------

export interface Location {
  latitude: number;   // WGS84 −90..90
  longitude: number;  // WGS84 −180..180
}

export interface CropHistoryEntry {
  crop_id: string;
  planted_on: string;        // ISO date YYYY-MM-DD
  harvested_on: string | null;
}

export interface SoilTestEntry {
  metric: string;
  value: number;
  unit: string;
  sampled_on: string;        // ISO date YYYY-MM-DD
}

export interface PriorityWeights {
  water: number;
  soil: number;
  climate: number;
}

export interface FarmProfile {
  schema_version: "0.1";
  data_kind: "synthetic" | "farmer_input";
  name: string;
  location: Location;
  area_ha: number;
  irrigation_supply_mm_per_season: number | null;
  crop_history: CropHistoryEntry[];
  soil_tests: SoilTestEntry[];
  priority_weights: PriorityWeights;
  excluded_crop_ids: string[];
}

export interface FarmEnvelope {
  id: string;
  input_version: number;
  profile: FarmProfile;
}

// ---------------------------------------------------------------------------
// Observations (matches API_CONTRACTS.md observation summary shape)
// ---------------------------------------------------------------------------

export interface SourceRef {
  id: string;
  label: string;
}

export interface ObservationCoverage {
  expected_days: number;
  /** Days with BOTH variables present. */
  available_days: number;
  temperature_valid_days?: number;
  precipitation_valid_days?: number;
}

/** Matheesha's normalized daily record (served by Dulanjaya's /observations). */
export interface DailyObservation {
  date: string;
  temperature_c: number | null;
  precipitation_mm_per_day: number | null;
  temperature_max_c?: number | null;
  temperature_min_c?: number | null;
}

export interface ObservationSummary {
  observation_id: string;
  farm_id: string;
  input_version: number;
  data_kind: DataKind;
  period: { start: string; end: string };
  retrieved_at: string | null;
  source_refs: string[];
  /** Provider resolution metadata (object from the live API); null when unknown. */
  spatial_resolution: Record<string, unknown> | string | null;
  coverage: ObservationCoverage;
  /** Rainfall in mm, temperature in °C. Unknown variables are null — never zero.
   *  rainfall_mm aliases rainfall_total_mm (null when any rainfall day is missing). */
  summary: {
    rainfall_mm: number | null;
    rainfall_total_mm?: number | null;
    rainfall_available_days_mm?: number | null;
    mean_temperature_c: number | null;
  };
  limitations: string[];
  /** Live API: Matheesha's normalized daily records. */
  daily?: DailyObservation[];
  provider?: string;
  source_url?: string | null;
  documentation_url?: string;
  units?: Record<string, string>;
  missing_data?: Record<string, string[]>;
  time_standard?: string;
  /** Legacy fixture shape, kept only as a fallback. */
  time_series?: TimeSeriesPoint[];
}

export interface TimeSeriesPoint {
  date: string;
  rainfall_mm: number | null;
  mean_temperature_c: number | null;
}

export interface SmapPass {
  pass: "AM" | "PM";
  accepted: boolean;
  soil_moisture_m3_m3: number | null;
  rejection_reason: string | null;
  acquisition_time_utc_raw?: string | null;
  retrieval_quality_flag?: number | null;
  distance_km?: number | null;
}

export interface SoilMoistureContext {
  schema_version: "0.1";
  kind: "smap_surface_soil_moisture_series";
  data_kind: "satellite_retrieval" | "synthetic";
  farm_id: string;
  input_version: number;
  product: "SPL3SMP_E";
  version: "006";
  units: "m3/m3";
  requested_point: Location;
  farm_distance_km: number;
  period: { start: string; end: string };
  max_distance_km: number;
  coverage: { expected_days: number; supplied_granule_days: number; accepted_AM: number; accepted_PM: number };
  daily: { date: string; granule_supplied: boolean; AM: SmapPass; PM: SmapPass }[];
  source_refs: string[];
  limitations: string[];
}

export interface GpmContext {
  schema_version: "0.1";
  kind: "gpm_imerg_daily_series";
  data_kind: "satellite_retrieval" | "synthetic";
  farm_id: string;
  input_version: number;
  product: "GPM_3IMERGDF";
  version: "07";
  units: "mm/day";
  requested_point: Location;
  farm_distance_km: number;
  period: { start: string; end: string };
  spatial_resolution_degrees: number;
  coverage: { expected_days: number; valid_days: number };
  daily: { date: string; precipitation_mm: number | null }[];
  source_refs: string[];
  retrieved_at: string | null;
  limitations: string[];
}

export interface HlsContext {
  schema_version: "0.1";
  kind: "hls_vegetation_series";
  data_kind: "satellite_retrieval" | "synthetic";
  farm_id: string;
  input_version: number;
  products: ("HLSL30" | "HLSS30")[];
  version: "2.0";
  index: "NDVI";
  requested_point: Location;
  farm_distance_km: number;
  spatial_resolution_m: number;
  period: { start: string; end: string };
  coverage: { supplied_observations: number; accepted_observations: number };
  observations: { date: string; product: "HLSL30" | "HLSS30"; ndvi: number | null; cloud_percent: number; quality_accepted: boolean; rejection_reason: string | null }[];
  source_refs: string[];
  retrieved_at: string | null;
  limitations: string[];
}

export interface ClimateTwinsResult {
  schema_version: "0.1";
  kind: "historical_climate_twins";
  farm_id: string;
  observation_id: string;
  period: { start: string; end: string };
  twins: { farm_id: string; observation_id: string; input_version: number; requested_location: Location;
    mean_temperature_c: number; rainfall_total_mm: number; temperature_difference_c: number;
    rainfall_difference_mm: number; similarity_score: number }[];
  excluded: { observation_id: string | null; reason: string }[];
  source_refs: string[];
  assumptions: string[];
  limitations: string[];
}

export interface SeasonFeedback {
  schema_version: "0.1";
  feedback_id: string;
  plan_id: string;
  data_kind: "farmer_input";
  season_index: number;
  planted_on: string | null;
  harvested_on: string | null;
  actual_crop_id: string | null;
  yield_value: number | null;
  yield_unit: "kg" | "kg/ha" | "t" | "t/ha" | null;
  notes: string;
  created_at: string;
  limitations: string[];
}

export type SeasonFeedbackRequest = Pick<SeasonFeedback, "season_index" | "planted_on" | "harvested_on" | "actual_crop_id" | "yield_value" | "yield_unit" | "notes">;

// ---------------------------------------------------------------------------
// Rotation analysis
// ---------------------------------------------------------------------------

export interface SequenceStep {
  season_index: number;
  crop_id: string;
  crop_name?: string;
}

/** rotation-score-0.1 (docs/ROTATION_SCORING_SPEC.md, Bhagya). */
export type ScoreComponentName = "water_sufficiency" | "crop_diversity" | "scenario_resilience" | (string & {});

export interface ScoreComponent {
  name: ScoreComponentName;
  /** Farmer priority mapped to this component (water / soil / climate). */
  requested_weight: number;
  /** After renormalization; 0 when the component is unavailable. */
  effective_weight: number;
  /** 0–100; null when not computable (missing input or no scenario) — never shown as 0. */
  value: number | null;
  direction: "higher_is_better" | "lower_is_better";
}

export interface WaterBudget {
  period: string;
  demand_mm: number | null;
  rainfall_mm: number | null;
  rainfall_total_mm?: number | null;
  effective_rainfall_mm: number | null;
  irrigation_supply_mm: number | null;
  deficit_mm: number | null;
  unit: "mm";
  assumptions: string[];
}

/**
 * Range-based water screening (Bhagya's WaterBudgetRange, zerokali20 commit 454b4c1).
 * balance = available − demand: negative means a shortfall. Unknown values are null.
 */
export interface WaterBudgetRange {
  /** Per season/crop record (rotation-score-0.1). */
  season_index?: number;
  /** maha / yala / inter-season, when supplied. */
  season_label?: string;
  crop_id?: string;
  demand_low_mm: number | null;
  demand_nominal_mm?: number | null;
  demand_high_mm: number | null;
  baseline_rainfall_mm: number | null;
  scenario_rainfall_mm: number | null;
  irrigation_mm: number | null;
  /** Baseline (no scenario) available water and coverage, kept separate from the scenario values. */
  baseline_available_water_mm?: number | null;
  baseline_coverage_low_percent?: number | null;
  baseline_coverage_high_percent?: number | null;
  /** Scenario (or baseline when no scenario) available water. */
  available_water_mm: number | null;
  /** available − high demand */
  balance_low_mm: number | null;
  /** available − low demand */
  balance_high_mm: number | null;
  coverage_low_percent: number | null;
  coverage_high_percent: number | null;
  demand_basis: string | null;
  model_version: string | null;
  source_url?: string | null;
  assumptions: string[];
  limitations?: string[];
}

export interface ConstraintCheck {
  rule: string;
  passed: boolean;
  note: string | null;
}

export interface RotationCandidate {
  candidate_id: string;
  sequence: SequenceStep[];
  /** 0–100 heuristic comparison score; null when not computable — never displayed as 0. */
  score: number | null;
  score_components: ScoreComponent[];
  /** Optional plan aggregate; must not replace the per-season records. */
  water_budget: WaterBudget;
  /** Per season/crop records (an older single object is also accepted by the UI). */
  water_budget_range?: WaterBudgetRange[] | WaterBudgetRange | null;
  reasons: string[];
  constraint_checks: ConstraintCheck[];
  planning_evidence?: {
    mode: "standard" | "soil_revive" | "drought_recovery" | "flood_recovery";
    legume_seasons: number;
    unique_crop_families: number;
    mean_crop_water_demand_mm: number | null;
    source_refs: string[];
    interpretation: string[];
    local_checks_required: string[];
  };
}

export interface RotationAnalysis {
  analysis_id: string;
  farm_id: string;
  input_version: number;
  observation_id: string | null;
  catalog_version: string;
  model_version: string;
  planning_mode?: "standard" | "soil_revive" | "drought_recovery" | "flood_recovery";
  data_kind: DataKind;
  created_at: string;
  candidates: RotationCandidate[];  // empty array is valid when no feasible plans
  /** Why no (or fewer) feasible sequences exist, e.g. "No approved crop is eligible for season 'yala'." */
  reasons?: string[];
  assumptions: string[];
  source_refs: string[];
  limitations: string[];
  /** Live API: one dated historical rainfall input per planned season (empty when not requested). */
  season_inputs?: SeasonInput[];
}

export interface SeasonInput {
  season_index: number;
  season_label: string;
  period_start: string;
  period_end: string;
  period_source: "season_calendar" | "request";
  observation_id: string;
  data_kind: DataKind;
  expected_days: number;
  rainfall_valid_days: number;
  /** null when the period has missing rainfall days — never a partial sum. */
  rainfall_total_mm: number | null;
  source_refs: string[];
  limitations: string[];
}

// ---------------------------------------------------------------------------
// Scenario result
// ---------------------------------------------------------------------------

export interface ScenarioResult {
  scenario_id: string;
  baseline_analysis_id: string;
  parameters: { rainfall_change_pct: number };
  candidates: RotationCandidate[];
  baseline_differences: Record<string, unknown>;
  limitations: string[];
  /** Scenarios are always hypothetical; fixtures report "synthetic". */
  data_kind: DataKind;
  created_at?: string;
  /** Live API only: whole observation period, original NASA rainfall vs the scaled scenario (null = incomplete). */
  observation_rainfall?: {
    period_start: string;
    period_end: string;
    expected_days: number;
    valid_days: number;
    baseline_rainfall_mm: number | null;
    scenario_rainfall_mm: number | null;
    difference_mm: number | null;
  };
  /** Live API only: true when the farm profile changed after the baseline analysis. */
  baseline_outdated?: boolean;
  assumptions?: string[];
  source_refs?: string[];
}

// ---------------------------------------------------------------------------
// Assistant
// ---------------------------------------------------------------------------

export interface AssistantMessage {
  role: "user" | "assistant";
  content: string;
  source_ids: string[];
  limitations: string[];
  /** Optional extras from Akash's respond(); the UI only requires the four fields above. */
  status?: "answered" | "insufficient_context" | "unsupported_question" | (string & {});
  assumptions?: string[];
  language?: string;
}

export interface AssistantRequest {
  farm_id: string;
  analysis_id: string;
  scenario_id?: string;
  candidate_id?: string;
  language: Language;
  message: string;
}

// ---------------------------------------------------------------------------
// Saved plan
// ---------------------------------------------------------------------------

export interface SavedPlan {
  plan_id: string;
  farm_id: string;
  analysis_id: string;
  scenario_id: string | null;
  candidate_id: string;
  input_version: number;
  created_at: string;
  candidate_snapshot: RotationCandidate;
  /** Farm profile exactly as analysed (stored by the server with the plan). */
  input_snapshot?: FarmProfile;
  analysis_snapshot: Pick<RotationAnalysis, "catalog_version" | "model_version" | "source_refs" | "assumptions" | "limitations"> & {
    data_kind?: DataKind;
    analysis_created_at?: string;
  };
}

// ---------------------------------------------------------------------------
// API error envelope
// ---------------------------------------------------------------------------

export interface ApiError {
  error: {
    code: string;
    message: string;
    fields?: Record<string, string>;
  };
}

