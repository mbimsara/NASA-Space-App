/**
 * SeasonWaterTable — per season/crop water screening (rotation-score-0.1).
 * One row per season: crop, demand low–high, baseline/scenario rainfall, irrigation,
 * coverage range (uncapped), balance range; plus basis, model version, assumptions, limitations.
 * Unknown values show "Unknown", never 0.
 * Owner: Shehani. Water model: Bhagya.
 */
import { useTranslation } from "react-i18next";
import type { SequenceStep, WaterBudgetRange } from "../../types/api";
import { fmtMm, fmtRange, isKnown } from "../../utils/format";

interface Props {
  ranges: WaterBudgetRange[];
  sequence: SequenceStep[];
}

export function SeasonWaterTable({ ranges, sequence }: Props) {
  const { t } = useTranslation();
  const u = t("common.unknown");
  if (ranges.length === 0) {
    return <p className="muted" style={{ fontSize: 12 }}>{t("rotation.noSeasonWater")}</p>;
  }

  // Show "baseline → scenario" only when a scenario actually changed the value.
  const hasScenario = ranges.some(
    (r) => isKnown(r.baseline_rainfall_mm) && isKnown(r.scenario_rainfall_mm) && r.baseline_rainfall_mm !== r.scenario_rainfall_mm,
  );
  const pair = (b: string, s: string) => (hasScenario && b !== s ? `${b} → ${s}` : s);

  const cropName = (r: WaterBudgetRange, i: number) => {
    const step = sequence.find((s) => s.season_index === r.season_index) ?? sequence[i];
    return step?.crop_name ?? r.crop_id ?? step?.crop_id ?? u;
  };
  const uniq = (xs: (string | null | undefined)[]) => [...new Set(xs.filter((x): x is string => !!x))];
  const notes = uniq(ranges.flatMap((r) => [...r.assumptions, ...(r.limitations ?? [])]));
  const bases = uniq(ranges.map((r) => r.demand_basis));
  const models = uniq(ranges.map((r) => r.model_version));
  const links = uniq(ranges.map((r) => r.source_url ?? null));

  return (
    <div className="notice notice-info" style={{ marginTop: 12, padding: 12 }}>
      <h4 style={{ margin: "0 0 4px", fontSize: 14 }}>{t("rotation.seasonWaterTitle")}</h4>
      <p className="muted" style={{ fontSize: 12, margin: "0 0 8px" }}>
        {t("rotation.waterWording")}
      </p>
      <div className="table-scroll">
        <table className="data" style={{ fontSize: 12, minWidth: 560 }}>
          <thead>
            <tr>
              <th scope="col">{t("rotation.season")}</th>
              <th scope="col">{t("rotation.demandRange")}</th>
              <th scope="col">{hasScenario ? t("rotation.rainfallBaselineScenario") : t("rotation.rainfallTotal")}</th>
              <th scope="col">{t("rotation.irrigation")}</th>
              <th scope="col">{hasScenario ? t("rotation.availableBaselineScenario") : t("rotation.availableWater")}</th>
              <th scope="col">{hasScenario ? t("rotation.coverageBaselineScenario") : t("rotation.coverageRange")}</th>
              <th scope="col">{hasScenario ? t("rotation.balanceScenario") : t("rotation.balanceRange")}</th>
            </tr>
          </thead>
          <tbody>
            {ranges.map((r, i) => {
              const short = isKnown(r.balance_low_mm) && r.balance_low_mm < 0;
              return (
                <tr key={`${r.season_index ?? i}-${r.crop_id ?? ""}`}>
                  <th scope="row" style={{ fontWeight: 400, background: "transparent" }}>
                    {r.season_index ?? i + 1}.{" "}
                    {r.season_label && <span className="muted">{t(`rotation.seasonLabel.${r.season_label}`, { defaultValue: r.season_label })} · </span>}
                    <strong>{cropName(r, i)}</strong>
                  </th>
                  <td>{fmtRange(r.demand_low_mm, r.demand_high_mm, u, "mm")}</td>
                  <td>{pair(fmtMm(r.baseline_rainfall_mm, u), fmtMm(r.scenario_rainfall_mm, u))}</td>
                  <td>{fmtMm(r.irrigation_mm, u)}</td>
                  <td>
                    {pair(
                      fmtMm(r.baseline_available_water_mm ?? (hasScenario ? null : r.available_water_mm), u),
                      fmtMm(r.available_water_mm, u),
                    )}
                  </td>
                  <td>
                    {pair(
                      fmtRange(
                        r.baseline_coverage_low_percent ?? (hasScenario ? null : r.coverage_low_percent),
                        r.baseline_coverage_high_percent ?? (hasScenario ? null : r.coverage_high_percent),
                        u,
                        "%",
                      ),
                      fmtRange(r.coverage_low_percent, r.coverage_high_percent, u, "%"),
                    )}
                  </td>
                  <td style={{ color: short ? "var(--red-700)" : undefined, fontWeight: short ? 600 : undefined }}>
                    {fmtRange(r.balance_low_mm, r.balance_high_mm, u, "mm", true)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <p className="muted" style={{ fontSize: 12, margin: "6px 0 0" }}>
        {t("rotation.balanceHelp")} · {t("rotation.demandBasis")}: {bases.join(", ") || u} · {t("plan.modelVersion")}:{" "}
        {models.join(", ") || u}
        {links.map((l, i) => (
          <span key={l}>
            {" · "}
            <a href={l} target="_blank" rel="noreferrer">
              {t("common.source")} {links.length > 1 ? i + 1 : ""}
            </a>
          </span>
        ))}
      </p>
      {notes.length > 0 && (
        <details style={{ marginTop: 6, fontSize: 12 }}>
          <summary style={{ cursor: "pointer" }}>{t("rotation.rangeAssumptions")}</summary>
          <ul style={{ margin: "4px 0 0 16px" }}>
            {notes.map((a, i) => (
              <li key={i}>{a}</li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}
