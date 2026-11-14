/**
 * Step model for the core-journey tracker (Tharuka's design). Owner: Shehani.
 */
export interface JourneyStep {
  key: "setup" | "overview" | "plan" | "climate" | "ai" | "save";
  to: string;
  complete: boolean;
}

/** Pure step model (tested). */
export function journeySteps(opts: {
  farmId: string;
  hasObservation: boolean;
  hasAnalysis: boolean;
  hasScenario: boolean;
  planId: string | null;
}): JourneyStep[] {
  const base = `/farms/${opts.farmId}`;
  return [
    { key: "setup", to: `${base}/edit`, complete: true },
    { key: "overview", to: base, complete: opts.hasObservation },
    { key: "plan", to: `${base}/rotations`, complete: opts.hasAnalysis },
    { key: "climate", to: `${base}/scenario`, complete: opts.hasScenario },
    { key: "ai", to: `${base}/assistant`, complete: false },
    { key: "save", to: opts.planId ? `/plans/${opts.planId}` : `${base}/rotations`, complete: !!opts.planId },
  ];
}

export function activeStepIndex(steps: JourneyStep[], pathname: string): number {
  return steps.findIndex((s) => s.to === pathname);
}
