import { beforeEach, describe, expect, it } from "vitest";
import { clearPendingFarmEdit, pendingFarmEdit, queueFarmEdit } from "./offlineFarmQueue";
import type { FarmProfile } from "../types/api";

const profile = { schema_version: "0.1", data_kind: "farmer_input", name: "Farm" } as unknown as FarmProfile;

describe("offline farm edit queue", () => {
  beforeEach(() => localStorage.clear());
  it("keeps only the newest snapshot for each farm and preserves its base version", () => {
    queueFarmEdit({ farmId: "f1", expectedInputVersion: 2, profile, queuedAt: "2026-01-01T00:00:00Z" });
    queueFarmEdit({ farmId: "f1", expectedInputVersion: 2, profile: { ...profile, name: "Updated" }, queuedAt: "2026-01-02T00:00:00Z" });
    expect(pendingFarmEdit("f1")?.profile.name).toBe("Updated");
    expect(pendingFarmEdit("f1")?.expectedInputVersion).toBe(2);
  });
  it("clears only the selected farm", () => {
    queueFarmEdit({ farmId: "f1", expectedInputVersion: 1, profile, queuedAt: "2026-01-01T00:00:00Z" });
    queueFarmEdit({ farmId: "f2", expectedInputVersion: 1, profile, queuedAt: "2026-01-01T00:00:00Z" });
    clearPendingFarmEdit("f1");
    expect(pendingFarmEdit("f1")).toBeNull(); expect(pendingFarmEdit("f2")).not.toBeNull();
  });
});
