import { describe, expect, it } from "vitest";
import repoCatalog from "../../../data/catalogs/crops.json";
import { validateCatalog } from "./validateCatalog";

const crop = (over: Record<string, unknown> = {}) => ({
  id: "cowpea",
  name: "Cowpea",
  family: "Fabaceae",
  season_labels: ["Yala"],
  water_demand_mm_per_cycle: 300,
  sources: [{ url: "https://example.org/cowpea", accessed_on: "2026-01-10", notes: "Test entry" }],
  review_status: "approved",
  ...over,
});

const catalog = (crops: unknown[], over: Record<string, unknown> = {}) => ({
  schema_version: "0.1",
  catalog_version: "test-1",
  status: "research_pending",
  region: "Test region",
  crops,
  ...over,
});

const paths = (r: ReturnType<typeof validateCatalog>) => r.issues.map((i) => i.path);

describe("validateCatalog", () => {
  it("accepts the repository catalog and notes that it is empty", () => {
    const r = validateCatalog(repoCatalog);
    expect(r.ok).toBe(true);
    expect(r.notes.join(" ")).toMatch(/empty/);
    expect(r.approvedCrops).toHaveLength(0);
  });

  it("accepts a well-formed approved crop", () => {
    const r = validateCatalog(catalog([crop()], { status: "reviewed" }));
    expect(r.ok).toBe(true);
    expect(r.approvedCrops.map((c) => c.id)).toEqual(["cowpea"]);
  });

  it("flags missing identifiers", () => {
    const { id: _omit, ...noId } = crop();
    expect(paths(validateCatalog(catalog([noId])))).toContain("$.crops[0].id");
    expect(paths(validateCatalog(catalog([crop({ id: "  " })])))).toContain("$.crops[0].id");
  });

  it("flags duplicate IDs", () => {
    const r = validateCatalog(catalog([crop(), crop()]));
    expect(r.ok).toBe(false);
    expect(r.issues[0].message).toMatch(/Duplicate crop ID/);
  });

  it("flags invalid water units/values but allows null (unknown)", () => {
    expect(validateCatalog(catalog([crop({ water_demand_mm_per_cycle: 0 })])).ok).toBe(false);
    expect(validateCatalog(catalog([crop({ water_demand_mm_per_cycle: "300mm" })])).ok).toBe(false);
    const r = validateCatalog(catalog([crop({ water_demand_mm_per_cycle: null })]));
    expect(r.ok).toBe(true);
    expect(r.notes.join(" ")).toMatch(/unknown water demand/);
  });

  it("flags malformed sources", () => {
    const bad = crop({ sources: [{ url: "ftp://x", accessed_on: "10/01/2026", notes: "" }] });
    const p = paths(validateCatalog(catalog([bad])));
    expect(p).toEqual(
      expect.arrayContaining(["$.crops[0].sources[0].url", "$.crops[0].sources[0].accessed_on", "$.crops[0].sources[0].notes"]),
    );
  });

  it("requires sources, seasons and family for approved crops", () => {
    const r = validateCatalog(catalog([crop({ sources: [], season_labels: [], family: null })]));
    expect(paths(r)).toEqual(
      expect.arrayContaining(["$.crops[0].sources", "$.crops[0].season_labels", "$.crops[0].family"]),
    );
  });

  it("allows unknown family on draft crops", () => {
    const r = validateCatalog(catalog([crop({ review_status: "draft", family: null })]));
    expect(r.ok).toBe(true);
    expect(r.approvedCrops).toHaveLength(0);
  });

  it("requires a reviewed catalog to contain only approved crops", () => {
    expect(validateCatalog(catalog([], { status: "reviewed" })).ok).toBe(false);
    expect(validateCatalog(catalog([crop({ review_status: "draft" })], { status: "reviewed" })).ok).toBe(false);
  });

  it("rejects unexpected fields and wrong schema version", () => {
    const p = paths(validateCatalog(catalog([crop({ yield: 5 })], { schema_version: "0.2" })));
    expect(p).toEqual(expect.arrayContaining(["$.schema_version", "$.crops[0].yield"]));
  });

  it("rejects non-object input", () => {
    expect(validateCatalog(null).ok).toBe(false);
    expect(validateCatalog(catalog("x" as unknown as unknown[])).ok).toBe(false);
  });
});
