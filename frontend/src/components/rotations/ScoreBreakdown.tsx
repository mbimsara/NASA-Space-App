/**
 * ScoreBreakdown — rotation-score-0.1 components (docs/ROTATION_SCORING_SPEC.md, Bhagya).
 * Shows requested and effective weights, 0–100 values, and the approved wording.
 * Unknown values show "Unknown", never 0. Not a yield prediction.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import type { ScoreComponent } from "../../types/api";
import { fmtScore, fmtWeight, isKnown } from "../../utils/format";

interface Props {
  score: number | null;
  components: ScoreComponent[];
}

const KNOWN = ["water_sufficiency", "crop_diversity", "scenario_resilience"];

export function ScoreBreakdown({ score, components }: Props) {
  const { t } = useTranslation();
  const u = t("common.unknown");
  const label = (name: string) => (KNOWN.includes(name) ? t(`rotation.comp.${name}`) : name);
  const unavailable = components.filter((c) => !isKnown(c.value));
  const renormalized = components.some(
    (c) => isKnown(c.requested_weight) && isKnown(c.effective_weight) && Math.abs(c.requested_weight - c.effective_weight) > 1e-6,
  );

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginBottom: 4, flexWrap: "wrap" }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: "var(--green-700)" }}>
          {t("rotation.score")}: {fmtScore(score, u)}
          {isKnown(score) && <span className="muted" style={{ fontSize: 12, fontWeight: 400 }}> / 100</span>}
        </div>
      </div>
      <p className="muted" style={{ fontSize: 12, margin: "0 0 8px", fontStyle: "italic" }}>
        {t("rotation.scoreNote")}
      </p>
      <div className="table-scroll">
        <table className="data" style={{ fontSize: 12 }}>
          <thead>
            <tr>
              <th scope="col">{t("rotation.component")}</th>
              <th scope="col">{t("rotation.value")}</th>
              <th scope="col">{t("rotation.requestedWeight")}</th>
              <th scope="col">{t("rotation.effectiveWeight")}</th>
            </tr>
          </thead>
          <tbody>
            {components.map((c) => (
              <tr key={c.name}>
                <th scope="row" style={{ fontWeight: 400, background: "transparent" }}>
                  {label(c.name)}{" "}
                  <span className="muted">({c.direction === "higher_is_better" ? `↑ ${t("rotation.higher")}` : `↓ ${t("rotation.lower")}`})</span>
                </th>
                <td style={{ fontWeight: 600 }}>{fmtScore(c.value, u)}</td>
                <td>{fmtWeight(c.requested_weight, u)}</td>
                <td>{fmtWeight(c.effective_weight, u)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {unavailable.length > 0 && (
        <p className="muted" style={{ fontSize: 12, margin: "6px 0 0" }}>
          {t("rotation.missingComponents", { names: unavailable.map((c) => label(c.name)).join(", ") })}
          {renormalized && ` ${t("rotation.renormalized")}`}
        </p>
      )}
      <details style={{ marginTop: 6, fontSize: 12 }}>
        <summary style={{ cursor: "pointer" }}>{t("rotation.aboutComponents")}</summary>
        <ul style={{ margin: "4px 0 0 16px" }}>
          {components
            .filter((c) => KNOWN.includes(c.name))
            .map((c) => (
              <li key={c.name}>{t(`rotation.compHelp.${c.name}`)}</li>
            ))}
          <li>{t("rotation.smallDifferences")}</li>
        </ul>
      </details>
    </div>
  );
}
