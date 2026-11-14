import { describe, expect, it } from "vitest";
import demoFarm from "../../../data/fixtures/farm.synthetic.json";
import { farmFormSchema, fieldErrors, isIsoDate, normalizeWeights, serverFieldErrors, type FarmFormValues } from "./validation";

const valid = (): FarmFormValues => {
  const { schema_version: _v, data_kind: _k, ...rest } = demoFarm as typeof demoFarm & { schema_version: string };
  return structuredClone(rest) as FarmFormValues;
};

const errorsOf = (v: unknown) => {
  const r = farmFormSchema.safeParse(v);
  return r.success ? {} : fieldErrors(r.error);
};

describe("farmFormSchema", () => {
  it("accepts the shared synthetic demo farm (unknown irrigation/soil)", () => {
    expect(farmFormSchema.safeParse(valid()).success).toBe(true);
  });

  it("requires a name and positive area", () => {
    const e = errorsOf({ ...valid(), name: " ", area_ha: 0 });
    expect(e.name).toBeDefined();
    expect(e.area_ha).toMatch(/greater than zero/);
    expect(errorsOf({ ...valid(), area_ha: Number.NaN }).area_ha).toBeDefined();
  });

  it("validates coordinate ranges", () => {
    const e = errorsOf({ ...valid(), location: { latitude: 91, longitude: -181 } });
    expect(e["location.latitude"]).toBeDefined();
    expect(e["location.longitude"]).toBeDefined();
  });

  it("enforces harvest on/after planting and no future planting", () => {
    const e = errorsOf({
      ...valid(),
      crop_history: [
        { crop_id: "rice", planted_on: "2025-05-01", harvested_on: "2025-04-01" },
        { crop_id: "rice", planted_on: "2999-01-01", harvested_on: null },
      ],
    });
    expect(e["crop_history.0.harvested_on"]).toMatch(/on or after/);
    expect(e["crop_history.1.planted_on"]).toMatch(/future/);
  });

  it("distinguishes unknown (null), rainfed (0) and an amount chosen but not entered (NaN)", () => {
    expect(farmFormSchema.parse({ ...valid(), irrigation_supply_mm_per_season: 0 }).irrigation_supply_mm_per_season).toBe(0);
    expect(errorsOf({ ...valid(), irrigation_supply_mm_per_season: Number.NaN }).irrigation_supply_mm_per_season).toMatch(
      /Rainfed or Unknown/,
    );
  });

  it("keeps unknown irrigation as null and rejects negatives", () => {
    expect(farmFormSchema.parse({ ...valid(), irrigation_supply_mm_per_season: null }).irrigation_supply_mm_per_season).toBeNull();
    expect(errorsOf({ ...valid(), irrigation_supply_mm_per_season: -5 }).irrigation_supply_mm_per_season).toBeDefined();
  });

  it("requires explicit units and values on soil tests", () => {
    const e = errorsOf({ ...valid(), soil_tests: [{ metric: "pH", value: Number.NaN, unit: "", sampled_on: "2025-01-01" }] });
    expect(e["soil_tests.0.unit"]).toBeDefined();
    expect(e["soil_tests.0.value"]).toBeDefined();
  });

  it("requires a positive weight total", () => {
    expect(errorsOf({ ...valid(), priority_weights: { water: 0, soil: 0, climate: 0 } }).priority_weights).toBeDefined();
  });
});

describe("helpers", () => {
  it("isIsoDate rejects impossible dates", () => {
    expect(isIsoDate("2025-02-28")).toBe(true);
    expect(isIsoDate("2025-02-30")).toBe(false);
    expect(isIsoDate("28/02/2025")).toBe(false);
  });

  it("normalizeWeights sums to 1", () => {
    const w = normalizeWeights({ water: 2, soil: 1, climate: 1 });
    expect(w).toEqual({ water: 0.5, soil: 0.25, climate: 0.25 });
  });
});

describe("serverFieldErrors (backend 422 → form fields)", () => {
  it("maps Dulanjaya's dotted locations, with or without the PATCH profile prefix", () => {
    expect(
      serverFieldErrors({ area_ha: "Must be > 0", "profile.location.latitude": "Out of range", "body.name": "Required" }),
    ).toEqual({ area_ha: "Must be > 0", "location.latitude": "Out of range", name: "Required" });
  });
});

