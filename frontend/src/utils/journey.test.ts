import { describe, expect, it } from "vitest";
import { activeStepIndex, journeySteps } from "./journey";

const base = { farmId: "f1", hasObservation: false, hasAnalysis: false, hasScenario: false, planId: null };

describe("journey steps", () => {
  it("only marks steps complete when the farm has that result", () => {
    const s = journeySteps(base);
    expect(s.map((x) => [x.key, x.complete])).toEqual([
      ["setup", true],
      ["overview", false],
      ["plan", false],
      ["climate", false],
      ["ai", false],
      ["save", false],
    ]);
    const done = journeySteps({ ...base, hasObservation: true, hasAnalysis: true, hasScenario: true, planId: "p9" });
    expect(done.filter((x) => x.complete).map((x) => x.key)).toEqual(["setup", "overview", "plan", "climate", "save"]);
    expect(done[5].to).toBe("/plans/p9");
  });

  it("finds the active step from the URL", () => {
    const s = journeySteps(base);
    expect(activeStepIndex(s, "/farms/f1")).toBe(1);
    expect(activeStepIndex(s, "/farms/f1/scenario")).toBe(3);
    expect(activeStepIndex(s, "/farms/f1/finance")).toBe(-1);
  });
});
