/**
 * Typed API client for AgroSphere AI.
 * Owner: Shehani (@shehani419)
 *
 * Uses axios with AbortController-based stale-response guards.
 * All requests return typed results or throw ApiClientError.
 * Provider credentials are NEVER stored here — backend handles them.
 */

import axios from "axios";
import { configuration } from "./config";
import demoFarmProfile from "../../../data/fixtures/farm.synthetic.json";
import type { AxiosError, AxiosRequestConfig } from "axios";
import type {
  FarmEnvelope,
  FarmProfile,
  ObservationSummary,
  RotationAnalysis,
  ScenarioResult,
  AssistantMessage,
  AssistantRequest,
  SavedPlan,
  ApiError,
  SoilMoistureContext,
} from "../types/api";

// ---------------------------------------------------------------------------
// Base client
// ---------------------------------------------------------------------------

const BASE_URL = configuration.apiBaseUrl;

const http = axios.create({
  baseURL: BASE_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30_000,
});

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code: string;
  public readonly fields: Record<string, string> | undefined;

  constructor(status: number, envelope: ApiError) {
    super(envelope.error.message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = envelope.error.code;
    this.fields = envelope.error.fields;
  }
}

function handleAxiosError(err: unknown): never {
  if (axios.isAxiosError(err)) {
    const axErr = err as AxiosError<ApiError>;
    if (axErr.code === "ERR_CANCELED") {
      throw new DOMException("Request cancelled", "AbortError");
    }
    if (axErr.response) {
      const data = axErr.response.data;
      const envelope: ApiError =
        data && typeof data === "object" && data.error && typeof data.error.code === "string" && typeof data.error.message === "string"
          ? data
          : { error: { code: axErr.response.status >= 500 ? "UNAVAILABLE" : "HTTP_ERROR", message: axErr.message } };
      throw new ApiClientError(axErr.response.status, envelope);
    }
    // No response: backend unreachable, DNS, CORS or timeout.
    throw new ApiClientError(0, { error: { code: "network", message: "Network error — check your connection and retry." } });
  }
  throw err;
}

async function request<T>(config: AxiosRequestConfig, signal?: AbortSignal): Promise<T> {
  try {
    const res = await http.request<T>({ ...config, signal });
    return res.data;
  } catch (err) {
    handleAxiosError(err);
  }
}

// ---------------------------------------------------------------------------
// Farm endpoints
// ---------------------------------------------------------------------------

/** POST /farms — create a new farm, returns farm envelope with server-allocated ID */
export async function createFarm(profile: Omit<FarmProfile, "schema_version">, signal?: AbortSignal): Promise<FarmEnvelope> {
  return request<FarmEnvelope>({
    method: "POST",
    url: "/farms",
    data: { ...profile, schema_version: "0.1" },
  }, signal);
}

/** GET /farms/:id */
export async function getFarm(farmId: string, signal?: AbortSignal): Promise<FarmEnvelope> {
  return request<FarmEnvelope>({ method: "GET", url: `/farms/${farmId}` }, signal);
}

/** PATCH /farms/:id — full profile replacement; pass expected_input_version for optimistic locking */
export async function updateFarm(
  farmId: string,
  expectedInputVersion: number,
  profile: Omit<FarmProfile, "schema_version">,
  signal?: AbortSignal
): Promise<FarmEnvelope> {
  return request<FarmEnvelope>({
    method: "PATCH",
    url: `/farms/${farmId}`,
    data: {
      expected_input_version: expectedInputVersion,
      profile: { ...profile, schema_version: "0.1" },
    },
  }, signal);
}

// ---------------------------------------------------------------------------
// Observation endpoints
// ---------------------------------------------------------------------------

/** GET /farms/:id/observations?start=YYYY-MM-DD&end=YYYY-MM-DD */
export async function getObservations(
  farmId: string,
  start: string,
  end: string,
  signal?: AbortSignal
): Promise<ObservationSummary> {
  return request<ObservationSummary>({
    method: "GET",
    url: `/farms/${farmId}/observations`,
    params: { start, end },
  }, signal);
}

/** GET /farms/:id/soil-moisture — quality-filtered regional SMAP context when available. */
export async function getSoilMoisture(farmId: string, signal?: AbortSignal): Promise<SoilMoistureContext> {
  return request<SoilMoistureContext>({ method: "GET", url: `/farms/${farmId}/soil-moisture` }, signal);
}

// ---------------------------------------------------------------------------
// Rotation endpoints
// ---------------------------------------------------------------------------

export type SeasonLabel = "maha" | "yala" | "inter-season";
export const SEASON_LABELS: SeasonLabel[] = ["maha", "yala", "inter-season"];

export interface RotationRequest {
  input_version: number;
  /** Required by the live API (422 when null); the UI blocks generation without it. */
  observation_id: string | null;
  seasons: number; // 3–5
  /** Ordered season identity, one per season; the API does not infer a calendar from a count. */
  season_labels?: SeasonLabel[];
  catalog_version: string;
  priority_weights: { water: number; soil: number; climate: number };
  /**
   * Season-specific rainfall: "calendar" lets the server pick one historical season
   * per planned season; a list gives explicit chronological dates. Omit to keep water unknown.
   */
  season_periods?: "calendar" | { start: string; end: string }[];
}

/** POST /farms/:id/rotations — returns immutable rotation analysis */
export async function createRotation(
  farmId: string,
  body: RotationRequest,
  signal?: AbortSignal
): Promise<RotationAnalysis> {
  return request<RotationAnalysis>({ method: "POST", url: `/farms/${farmId}/rotations`, data: body }, signal);
}

// ---------------------------------------------------------------------------
// Scenario endpoints
// ---------------------------------------------------------------------------

/** POST /analyses/:id/scenarios — rainfall_change_pct is −100..100 */
export async function createScenario(
  analysisId: string,
  rainfallChangePct: number,
  signal?: AbortSignal
): Promise<ScenarioResult> {
  return request<ScenarioResult>({
    method: "POST",
    url: `/analyses/${analysisId}/scenarios`,
    data: { rainfall_change_pct: rainfallChangePct },
  }, signal);
}

// ---------------------------------------------------------------------------
// Assistant endpoint
// ---------------------------------------------------------------------------

/** POST /assistant/messages */
export async function sendAssistantMessage(
  body: AssistantRequest,
  signal?: AbortSignal
): Promise<AssistantMessage> {
  return request<AssistantMessage>({ method: "POST", url: "/assistant/messages", data: body }, signal);
}

// ---------------------------------------------------------------------------
// Plan endpoints
// ---------------------------------------------------------------------------

export interface PlanRequest {
  analysis_id: string;
  scenario_id?: string;
  candidate_id: string;
  expected_input_version: number;
}

/** POST /farms/:id/plans — save selected plan */
export async function savePlan(
  farmId: string,
  body: PlanRequest,
  signal?: AbortSignal
): Promise<{ plan_id: string }> {
  return request<{ plan_id: string }>({ method: "POST", url: `/farms/${farmId}/plans`, data: body }, signal);
}

/** GET /plans/:id — reload a saved plan with its original analysis snapshot */
/** Create the documented synthetic demo farm (data/fixtures/farm.synthetic.json). */
export async function createDemoFarm(signal?: AbortSignal): Promise<FarmEnvelope> {
  return createFarm(demoFarmProfile as Omit<FarmProfile, "schema_version">, signal);
}

export async function getPlan(planId: string, signal?: AbortSignal): Promise<SavedPlan> {
  return request<SavedPlan>({ method: "GET", url: `/plans/${planId}` }, signal);
}

