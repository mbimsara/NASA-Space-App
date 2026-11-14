/**
 * CandidateCard — one rotation candidate: timeline, score breakdown, water budget,
 * reasons and constraint checks. Used by the rotation workspace and saved plan view.
 * Owner: Shehani.
 */
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import type { RotationCandidate } from "../../types/api";
import { CropTimeline } from "./CropTimeline";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { WaterBudgetCard } from "./WaterBudgetCard";
import { SeasonWaterTable } from "./SeasonWaterTable";
import { asSeasonRanges } from "../../utils/format";

interface Props {
  candidate: RotationCandidate;
  rank: number;
  selected?: boolean;
  children?: ReactNode;
}

export function CandidateCard({ candidate: cand, rank, selected = false, children }: Props) {
  const { t } = useTranslation();
  return (
    <article
      className="card"
      aria-label={t("rotation.candidate", { index: rank })}
      style={selected ? { borderColor: "var(--green-600)", borderWidth: 2, background: "var(--green-50)" } : undefined}
    >
      <h3 style={{ margin: "0 0 8px", fontSize: "1rem" }}>
        {t("rotation.candidate", { index: rank })}
        {selected && <span style={{ marginLeft: 8, fontSize: 12, color: "var(--green-700)" }}>✓ {t("rotation.selected")}</span>}
      </h3>
      <CropTimeline sequence={cand.sequence} />
      <ScoreBreakdown score={cand.score} components={cand.score_components} />
      <SeasonWaterTable ranges={asSeasonRanges(cand.water_budget_range)} sequence={cand.sequence} />
      <WaterBudgetCard budget={cand.water_budget} />

      {cand.reasons.length > 0 && (
        <details style={{ marginTop: 12, fontSize: 13 }}>
          <summary style={{ cursor: "pointer", fontWeight: 600 }}>{t("rotation.reasons")}</summary>
          <ul style={{ marginTop: 6 }}>
            {cand.reasons.map((r, j) => (
              <li key={j}>{r}</li>
            ))}
          </ul>
        </details>
      )}

      <details style={{ marginTop: 8, fontSize: 13 }}>
        <summary style={{ cursor: "pointer", fontWeight: 600 }}>{t("rotation.constraints")}</summary>
        <ul style={{ marginTop: 6, listStyle: "none", padding: 0 }}>
          {cand.constraint_checks.map((c, j) => (
            <li key={j} style={{ marginBottom: 4 }}>
              <span style={{ color: c.passed ? "var(--green-700)" : "var(--red-700)", marginRight: 6 }}>
                {c.passed ? `✓ ${t("rotation.passed")}` : `✗ ${t("rotation.failed")}`}
              </span>
              {c.rule}
              {c.note && <span className="muted"> — {c.note}</span>}
            </li>
          ))}
        </ul>
      </details>
      {children}
    </article>
  );
}
