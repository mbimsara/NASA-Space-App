/**
 * WaterBudgetCard — optional plan-level aggregate. Per Bhagya's spec it never
 * replaces the per-season records (SeasonWaterTable), so it is shown collapsed.
 * Effective rainfall has no approved method: null is shown as "Not modeled".
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import type { WaterBudget } from "../../types/api";
import { fmtMm, isKnown } from "../../utils/format";

export function WaterBudgetCard({ budget }: { budget: WaterBudget }) {
  const { t } = useTranslation();
  const u = t("common.unknown");
  const isDeficit = isKnown(budget.deficit_mm) && budget.deficit_mm > 0;
  const rows: [string, string, string?][] = [
    [t("rotation.demand"), fmtMm(budget.demand_mm, u)],
    [t("rotation.rainfallTotal"), fmtMm(budget.rainfall_total_mm ?? budget.rainfall_mm, u)],
    [
      t("rotation.effectiveRainfall"),
      budget.effective_rainfall_mm === null ? t("rotation.notModeled") : fmtMm(budget.effective_rainfall_mm, u),
    ],
    [t("rotation.irrigation"), fmtMm(budget.irrigation_supply_mm, u)],
    [
      t("rotation.deficit"),
      fmtMm(budget.deficit_mm, u) + (isDeficit ? " ⚠" : ""),
      isKnown(budget.deficit_mm) ? (isDeficit ? "var(--red-700)" : "var(--green-700)") : undefined,
    ],
  ];

  return (
    <details style={{ marginTop: 8, fontSize: 13 }}>
      <summary style={{ cursor: "pointer", fontWeight: 600 }}>
        {t("rotation.planAggregate")} <span className="muted">({budget.period})</span>
      </summary>
      <table className="data" style={{ fontSize: 12, marginTop: 6 }}>
        <tbody>
          {rows.map(([label, val, color]) => (
            <tr key={label}>
              <th scope="row" style={{ fontWeight: 400, width: "55%", background: "transparent" }}>
                {label}
              </th>
              <td style={{ fontWeight: 600, color }}>{val}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {budget.assumptions.length > 0 && (
        <ul className="muted" style={{ fontSize: 12, margin: "4px 0 0 16px" }}>
          {budget.assumptions.map((a, i) => (
            <li key={i}>{a}</li>
          ))}
        </ul>
      )}
    </details>
  );
}
