import { describe, expect, it } from "vitest";
import { vegetationCoverFromRgba } from "./vegetationTriage";

describe("vegetation photo triage", () => {
  it("counts transparent-green heuristic pixels and reports its method", () => {
    const pixels = new Uint8ClampedArray([
      20, 100, 20, 255,
      100, 100, 100, 255,
      70, 60, 20, 255,
      0, 200, 0, 0,
    ]);
    const result = vegetationCoverFromRgba(pixels, 2, 2);
    expect(result.valid_pixels).toBe(3);
    expect(result.vegetation_pixels).toBe(1);
    expect(result.vegetation_cover_percent).toBe(33.3);
    expect(result.method).toBe("transparent-green-pixel-heuristic-0.1");
  });

  it("rejects buffers that do not match the dimensions", () => {
    expect(() => vegetationCoverFromRgba(new Uint8ClampedArray(3), 1, 1)).toThrow(/Invalid RGBA/);
  });
});
