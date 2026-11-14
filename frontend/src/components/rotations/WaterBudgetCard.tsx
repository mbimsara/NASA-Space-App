/**
 * WaterBudgetCard — displays the water budget for a rotation candidate.
 * Shows deficit with a visual indicator. Unknown values are null, never 0.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import type { WaterBudget } from "../../types/api";

interface Props {
  budget: WaterBudget;
}

function mmOrUnknown(value: number | null, t: (k: string) => string): string {
  return value === null ? t("common.unknown") : `${value} mm`;
}

export function WaterBudgetCard({ budget }: Props) {
  const { t } = useTranslation();
  const isDeficit = budget.deficit_mm !== null && budget.deficit_mm > 0;

  return (
    <div style={{ background: "#f0f7ff", border: "1px solid #cce0ff", borderRadius: 8, padding: 16, marginTop: 12 }}>
      <h4 style={{ margin: "0 0 10px", fontSize: 14, color: "#0066cc" }}>{t("rotation.waterBudget")}</h4>
      <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
        <tbody>
          {[
            [t("rotation.demand"), mmOrUnknown(budget.demand_mm, t)],
            [t("rotation.rainfall"), mmOrUnknown(budget.rainfall_mm, t)],
            [t("rotation.effectiveRainfall"), mmOrUnknown(budget.effective_rainfall_mm, t)],
            [t("rotation.irrigation"), mmOrUnknown(budget.irrigation_supply_mm, t)],
          ].map(([label, val]) => (
            <tr key={label}>
              <td style={{ padding: "3px 0", color: "#555", width: "55%" }}>{label}</td>
              <td style={{ fontWeight: 600 }}>{val}</td>
            </tr>
          ))}
          <tr>
            <td style={{ padding: "3px 0", color: "#555" }}>{t("rotation.deficit")}</td>
            <td style={{ fontWeight: 700, color: isDeficit ? "#c0392b" : "#27ae60" }}>
              {mmOrUnknown(budget.deficit_mm, t)}
              {isDeficit && " ⚠"}
            </td>
          </tr>
        </tbody>
      </table>
      {budget.assumptions.length > 0 && (
        <details style={{ marginTop: 8, fontSize: 12 }}>
          <summary style={{ cursor: "pointer", color: "#555" }}>{t("common.assumptions")}</summary>
          <ul style={{ margin: "4px 0 0 16px" }}>
            {budget.assumptions.map((a, i) => <li key={i}>{a}</li>)}
          </ul>
        </details>
      )}
    </div>
  );
}

