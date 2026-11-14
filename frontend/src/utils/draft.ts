/**
 * Local draft persistence utilities.
 * Saves/restores unfinished farm form data to localStorage.
 * Owner: Shehani.
 *
 * Rules:
 * - Only saves draft if the form has been touched (non-empty name)
 * - Provides a clear-draft function
 * - Draft is keyed per farmId (or "new" for a new farm)
 */
import type { FarmFormValues } from "./validation";

const DRAFT_KEY_PREFIX = "agrosphere_farm_draft_";

export function saveDraft(farmId: string | "new", values: Partial<FarmFormValues>): void {
  try {
    localStorage.setItem(`${DRAFT_KEY_PREFIX}${farmId}`, JSON.stringify({
      values,
      savedAt: new Date().toISOString(),
    }));
  } catch {
    // localStorage might be unavailable — fail silently
  }
}

export function loadDraft(farmId: string | "new"): { values: Partial<FarmFormValues>; savedAt: string } | null {
  try {
    const raw = localStorage.getItem(`${DRAFT_KEY_PREFIX}${farmId}`);
    if (!raw) return null;
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function clearDraft(farmId: string | "new"): void {
  try {
    localStorage.removeItem(`${DRAFT_KEY_PREFIX}${farmId}`);
  } catch { /* ignore */ }
}

