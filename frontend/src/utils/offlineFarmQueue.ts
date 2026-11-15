import type { FarmProfile } from "../types/api";

export interface PendingFarmEdit {
  farmId: string;
  expectedInputVersion: number;
  profile: FarmProfile;
  queuedAt: string;
}

const KEY = "agrosphere_pending_farm_edits_v1";

function read(): Record<string, PendingFarmEdit> {
  try {
    const value = JSON.parse(localStorage.getItem(KEY) ?? "{}");
    return value && typeof value === "object" && !Array.isArray(value) ? value : {};
  } catch { return {}; }
}

function write(value: Record<string, PendingFarmEdit>) {
  localStorage.setItem(KEY, JSON.stringify(value));
}

export function pendingFarmEdit(farmId: string): PendingFarmEdit | null {
  return read()[farmId] ?? null;
}

export function queueFarmEdit(edit: PendingFarmEdit) {
  const queued = read();
  // One current snapshot per farm avoids replaying several edits against the
  // same expected version. The newest local edit replaces the older draft.
  queued[edit.farmId] = edit;
  write(queued);
}

export function clearPendingFarmEdit(farmId: string) {
  const queued = read();
  delete queued[farmId];
  write(queued);
}
