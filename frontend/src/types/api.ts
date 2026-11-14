/**
 * Shared API type definitions.
 * These match the contracts published in docs/API_CONTRACTS.md.
 * Owner: Shehani. Source-of-truth for all contract shapes used by the frontend.
 */

// ---------------------------------------------------------------------------
// Primitives
// ---------------------------------------------------------------------------

export type DataKind = "observed" | "modeled" | "synthetic" | "mixed";
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
  crop_id?: string;
  demand_low_mm: number | null;
  demand_nominal_mm?: number | null;
  demand_high_mm: number | null;
  baseline_rainfall_mm: number | null;
  scenario_rainfall_mm: number | null;
  irrigation_mm: number | null;
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
}

export interface RotationAnalysis {
  analysis_id: string;
  farm_id: string;
  input_version: number;
  observation_id: string | null;
  catalog_version: string;
  model_version: string;
  data_kind: DataKind;
  created_at: string;
  candidates: RotationCandidate[];  // empty array is valid when no feasible plans
  /** Why no (or fewer) feasible sequences exist, e.g. "No approved crop is eligible for season 'yala'." */
  reasons?: string[];
  assumptions: string[];
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
}

// ---------------------------------------------------------------------------
// Assistant
// ---------------------------------------------------------------------------

export interface AssistantMessage {
  role: "user" | "assistant";
  content: string;
  source_ids: string[];
  limitations: string[];
  /** Optional extra metadata from Akash's service; the UI only relies on the four fields above. */
  status?: string;
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

