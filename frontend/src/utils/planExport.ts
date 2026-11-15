import type { SavedPlan } from "../types/api";

export function planReportJson(plan: SavedPlan): string {
  return JSON.stringify({
    schema_version: "0.1",
    kind: "agrosphere_saved_plan_report",
    exported_at: new Date().toISOString(),
    plan,
    limitations: [
      "This report preserves the saved snapshot; it is not a guarantee of crop performance.",
      "NASA gridded observations are not on-farm measurements, and hypothetical scenarios are not forecasts.",
    ],
  }, null, 2);
}

export function downloadPlanReport(plan: SavedPlan) {
  const url = URL.createObjectURL(new Blob([planReportJson(plan)], { type: "application/json" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `agrosphere-plan-${plan.plan_id}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
