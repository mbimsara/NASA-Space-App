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
  available_days: number;
}

export interface ObservationSummary {
  observation_id: string;
  farm_id: string;
  input_version: number;
  data_kind: DataKind;
  period: { start: string; end: string };
  retrieved_at: string | null;
  source_refs: string[];
  spatial_resolution: string | null;
  coverage: ObservationCoverage;
  /** Rainfall in mm, temperature in °C. Unknown variables are null — never zero. */
  summary: { rainfall_mm: number | null; mean_temperature_c: number | null };
  limitations: string[];
  /** Time-series data points (to be agreed with Matheesha) */
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

export interface ScoreComponent {
  name: string;
  weight: number;
  value: number;
  direction: "higher_is_better" | "lower_is_better";
}

export interface WaterBudget {
  period: string;
  demand_mm: number | null;
  rainfall_mm: number | null;
  effective_rainfall_mm: number | null;
  irrigation_supply_mm: number | null;
  deficit_mm: number | null;
  unit: "mm";
  assumptions: string[];
}

export interface ConstraintCheck {
  rule: string;
  passed: boolean;
  note: string | null;
}

export interface RotationCandidate {
  candidate_id: string;
  sequence: SequenceStep[];
  score: number;
  score_components: ScoreComponent[];
  water_budget: WaterBudget;
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

