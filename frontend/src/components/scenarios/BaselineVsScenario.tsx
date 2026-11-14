/**
 * BaselineVsScenario — per-candidate comparison of baseline and hypothetical scenario.
 * Matches candidates by ID (not by position) so re-ranking is visible.
 * Always labelled "Hypothetical scenario" — never presented as a forecast.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import type { RotationAnalysis, ScenarioResult } from "../../types/api";

interface Props {
  baseline: RotationAnalysis;
  scenario: ScenarioResult;
}

const signed = (n: number) => `${n > 0 ? "+" : ""}${n}`;

export function BaselineVsScenario({ baseline, scenario }: Props) {
  const { t } = useTranslation();
  const pct = scenario.parameters.rainfall_change_pct;
  const mm = (v: number | null) => (v === null ? t("common.unknown") : `${v} mm`);

  return (
    <div className="card">
      <div className="notice notice-warn" role="status" style={{ fontWeight: 600 }}>
        {t("scenario.hypotheticalLabel")} — {t("scenario.rainfallChange")} {signed(pct)}%
      </div>

      {baseline.candidates.length === 0 ? (
        <p className="muted">{t("rotation.noCandidates")}</p>
      ) : (
        <div className="table-scroll">
          <table className="data">
            <thead>
              <tr>
                <th scope="col">{t("scenario.plan")}</th>
                <th scope="col">{t("scenario.rank")}</th>
                <th scope="col">{t("rotation.score")}</th>
                <th scope="col">{t("rotation.effectiveRainfall")}</th>
                <th scope="col">{t("rotation.deficit")}</th>
              </tr>
            </thead>
            <tbody>
              {baseline.candidates.map((b, i) => {
                const sIdx = scenario.candidates.findIndex((c) => c.candidate_id === b.candidate_id);
                const s = sIdx >= 0 ? scenario.candidates[sIdx] : null;
                const crops = b.sequence.map((x) => x.crop_name ?? x.crop_id).join(" → ");
                const scoreDelta = s ? Math.round((s.score - b.score) * 100) : null;
                const deficitDelta =
                  s && s.water_budget.deficit_mm !== null && b.water_budget.deficit_mm !== null
                    ? s.water_budget.deficit_mm - b.water_budget.deficit_mm
                    : null;
                return (
                  <tr key={b.candidate_id}>
                    <th scope="row" style={{ fontWeight: 400 }}>
                      <strong>{b.candidate_id}</strong>
                      <div className="muted">{crops}</div>
                    </th>
                    <td>
                      {i + 1} → {s ? sIdx + 1 : t("common.notAvailable")}
                    </td>
                    <td>
                      {Math.round(b.score * 100)} → {s ? Math.round(s.score * 100) : t("common.notAvailable")}
                      {scoreDelta !== null && <span className="muted"> ({signed(scoreDelta)})</span>}
                    </td>
                    <td>
                      {mm(b.water_budget.effective_rainfall_mm)} → {s ? mm(s.water_budget.effective_rainfall_mm) : "—"}
                    </td>
                    <td>
                      {mm(b.water_budget.deficit_mm)} → {s ? mm(s.water_budget.deficit_mm) : "—"}
                      {deficitDelta !== null && (
                        <span style={{ color: deficitDelta > 0 ? "var(--red-700)" : "var(--green-700)" }}>
                          {" "}
                          ({signed(deficitDelta)} mm)
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      <p className="muted">{t("scenario.sameBaseline", { id: scenario.baseline_analysis_id })}</p>
      {scenario.limitations.length > 0 && (
        <div className="muted">
          <strong>{t("common.limitations")}:</strong>
          <ul style={{ marginTop: 4 }}>
            {scenario.limitations.map((l, i) => (
              <li key={i}>{l}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
