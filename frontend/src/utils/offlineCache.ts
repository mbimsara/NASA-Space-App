/**
 * Offline viewing cache for saved plans (IMPLEMENTATION_PLAN: "offline viewing of
 * saved results can precede offline editing"). Read-only: nothing here is ever
 * written back to the server, so no sync/conflict policy is needed yet.
 * Owner: Shehani. Offline editing waits for Dulanjaya's sync contract.
 */
import type { FarmEnvelope, SavedPlan } from "../types/api";
import { PLAN_CACHE_KEY } from "../api/config";

const KEY = PLAN_CACHE_KEY;
export const MAX_CACHED_PLANS = 10;

export interface CachedPlan {
  plan: SavedPlan;
  farm: FarmEnvelope | null;
  /** When this device last stored the copy (ISO timestamp). */
  cachedAt: string;
}

function readAll(): Record<string, CachedPlan> {
  try {
    const raw = localStorage.getItem(KEY);
    const parsed = raw ? JSON.parse(raw) : {};
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function writeAll(all: Record<string, CachedPlan>) {
  try {
    localStorage.setItem(KEY, JSON.stringify(all));
  } catch {
    /* storage full or unavailable — offline copy is a convenience, not a guarantee */
  }
}

export function cachePlan(plan: SavedPlan, farm: FarmEnvelope | null, now: Date = new Date()): CachedPlan {
  const all = readAll();
  const entry: CachedPlan = { plan, farm, cachedAt: now.toISOString() };
  all[plan.plan_id] = entry;
  // Keep only the most recently cached plans.
  const keep = Object.values(all)
    .sort((a, b) => b.cachedAt.localeCompare(a.cachedAt))
    .slice(0, MAX_CACHED_PLANS);
  writeAll(Object.fromEntries(keep.map((e) => [e.plan.plan_id, e])));
  return entry;
}

export function getCachedPlan(planId: string): CachedPlan | null {
  return readAll()[planId] ?? null;
}

export function listCachedPlanIds(): string[] {
  return Object.keys(readAll());
}

export function clearOfflineCache() {
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
}
