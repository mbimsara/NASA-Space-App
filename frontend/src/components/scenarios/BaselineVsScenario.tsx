/**
 * BaselineVsScenario — per-plan comparison of baseline and hypothetical scenario
 * (rotation-score-0.1). Matches plans by candidate_id so re-ranking is visible.
 * Always labelled "Hypothetical scenario" — never presented as a forecast.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import type { RotationAnalysis, RotationCandidate, ScenarioResult } from "../../types/api";
import { asSeasonRanges, fmtScore, fmtSignedMm, isKnown } from "../../utils/format";

interface Props {
  baseline: RotationAnalysis;
  scenario: ScenarioResult;
}

const signed = (n: number) => `${n > 0 ? "+" : ""}${n}`;

const comp = (c: RotationCandidate | null, name: string) =>
  c?.score_components.find((x) => x.name === name)?.value ?? null;

/** Lowest conservative season balance (available − high demand); null if any season is unknown. */
function worstBalance(c: RotationCandidate | null): number | null {
  if (!c) return null;
  const vals = asSeasonRanges(c.water_budget_range).map((r) => r.balance_low_mm);
  if (vals.length === 0 || vals.some((v) => !isKnown(v))) return null;
  return Math.min(...(vals as number[]));
}

export function BaselineVsScenario({ baseline, scenario }: Props) {
  const { t } = useTranslation();
  const pct = scenario.parameters.rainfall_change_pct;
  const u = t("common.unknown");
  const na = t("common.notAvailable");

  return (
    <div className="card">
      <div className="notice notice-warn" role="status" style={{ fontWeight: 600 }}>
        {t("scenario.hypotheticalLabel")} — {t("scenario.rainfallChange")} {signed(pct)}%
      </div>
      <p className="muted" style={{ fontSize: 12 }}>
        {t("rotation.compHelp.scenario_resilience")}
      </p>

      {baseline.candidates.length === 0 ? (
        <p className="muted">{t("rotation.noCandidates")}</p>
      ) : (
        <div className="table-scroll">
          <table className="data" style={{ minWidth: 560 }}>
            <thead>
              <tr>
                <th scope="col">{t("scenario.plan")}</th>
                <th scope="col">{t("scenario.rank")}</th>
                <th scope="col">{t("rotation.score")}</th>
                <th scope="col">{t("rotation.comp.water_sufficiency")}</th>
                <th scope="col">{t("rotation.comp.scenario_resilience")}</th>
                <th scope="col">{t("scenario.worstBalance")}</th>
              </tr>
            </thead>
            <tbody>
              {baseline.candidates.map((b, i) => {
                const sIdx = scenario.candidates.findIndex((c) => c.candidate_id === b.candidate_id);
                const s = sIdx >= 0 ? scenario.candidates[sIdx] : null;
                const crops = b.sequence.map((x) => x.crop_name ?? x.crop_id).join(" → ");
                const delta = s && isKnown(s.score) && isKnown(b.score) ? Math.round((s.score - b.score) * 10) / 10 : null;
                const wb = worstBalance(b);
                const ws = worstBalance(s);
                return (
                  <tr key={b.candidate_id}>
                    <th scope="row" style={{ fontWeight: 400 }}>
                      <strong>{b.candidate_id}</strong>
                      <div className="muted">{crops}</div>
                    </th>
                    <td>
                      {i + 1} → {s ? sIdx + 1 : na}
                    </td>
                    <td>
                      {fmtScore(b.score, u)} → {s ? fmtScore(s.score, u) : na}
                      {delta !== null && <span className="muted"> ({signed(delta)})</span>}
                    </td>
                    <td>{fmtScore(comp(b, "water_sufficiency"), u)}</td>
                    <td>{s ? fmtScore(comp(s, "scenario_resilience"), u) : na}</td>
                    <td>
                      {fmtSignedMm(wb, u)} → {s ? fmtSignedMm(ws, u) : na}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {scenario.candidates.some((c) => !isKnown(comp(c, "scenario_resilience"))) && (
        <div className="notice notice-warn" role="note">
          {t("scenario.impactUnknown")}
        </div>
      )}
      <p className="muted">{t("scenario.sameBaseline", { id: scenario.baseline_analysis_id })}</p>
      <p className="muted" style={{ fontSize: 12 }}>
        {t("rotation.smallDifferences")}
      </p>
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
