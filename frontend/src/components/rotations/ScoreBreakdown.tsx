/**
 * ScoreBreakdown — shows score components, weights and direction.
 * Explicitly labels scores as NOT yield predictions.
 * Owner: Shehani. Score formula requires Bhagya's approval.
 */
import { useTranslation } from "react-i18next";
import type { ScoreComponent } from "../../types/api";

interface Props {
  score: number;
  components: ScoreComponent[];
}

export function ScoreBreakdown({ score, components }: Props) {
  const { t } = useTranslation();

  return (
    <div style={{ marginTop: 12 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 8 }}>
        <div style={{ fontSize: 18, fontWeight: 700, color: "#2c7a2c" }}>
          {t("rotation.score")}: {(score * 100).toFixed(0)}
        </div>
        <div style={{ fontSize: 11, color: "#888", fontStyle: "italic" }}>
          {t("rotation.scoreNote")}
        </div>
      </div>
      <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
        <thead>
          <tr style={{ background: "#f0f0f0" }}>
            <th style={{ textAlign: "left", padding: "4px 6px" }}>Component</th>
            <th style={{ padding: "4px 6px" }}>Weight</th>
            <th style={{ padding: "4px 6px" }}>Value</th>
            <th style={{ padding: "4px 6px" }}>Direction</th>
          </tr>
        </thead>
        <tbody>
          {components.map((c) => (
            <tr key={c.name} style={{ borderTop: "1px solid #eee" }}>
              <td style={{ padding: "4px 6px" }}>{c.name}</td>
              <td style={{ padding: "4px 6px", textAlign: "center" }}>{(c.weight * 100).toFixed(0)}%</td>
              <td style={{ padding: "4px 6px", textAlign: "center", fontWeight: 600 }}>
                {(c.value * 100).toFixed(0)}
              </td>
              <td style={{ padding: "4px 6px", textAlign: "center", fontSize: 11, color: "#555" }}>
                {c.direction === "higher_is_better" ? "↑ higher" : "↓ lower"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

