/**
 * SeasonInputsCard — the dated historical rainfall period behind each planned season
 * (live API `season_inputs`). One period and one total per season; unknown totals
 * (incomplete coverage) show "Unknown", never a partial sum.
 */
import { useTranslation } from "react-i18next";
import type { SeasonInput } from "../../types/api";
import { fmtMm } from "../../utils/format";

interface Props {
  inputs: SeasonInput[];
}

export function SeasonInputsCard({ inputs }: Props) {
  const { t } = useTranslation();
  const u = t("common.unknown");
  return (
    <div className="card">
      <h2 style={{ marginTop: 0, fontSize: "1.05rem" }}>{t("rotation.seasonInputsTitle")}</h2>
      <p className="muted" style={{ fontSize: 12 }}>
        {t("rotation.seasonInputsHelp")}
      </p>
      <div className="table-scroll">
        <table className="data">
          <thead>
            <tr>
              <th scope="col">{t("rotation.seasonColumn")}</th>
              <th scope="col">{t("rotation.seasonPeriod")}</th>
              <th scope="col">{t("rotation.seasonRainfall")}</th>
              <th scope="col">{t("rotation.seasonCoverage")}</th>
            </tr>
          </thead>
          <tbody>
            {inputs.map((s) => (
              <tr key={s.season_index}>
                <th scope="row" style={{ fontWeight: 400 }}>
                  {s.season_index}. {t(`rotation.seasonLabel.${s.season_label}`)}
                </th>
                <td>
                  {s.period_start} → {s.period_end}
                  <div className="muted" style={{ fontSize: 12 }}>
                    {t(`rotation.seasonPeriodSource.${s.period_source}`)}
                  </div>
                </td>
                <td>{fmtMm(s.rainfall_total_mm, u)}</td>
                <td>
                  {s.rainfall_valid_days}/{s.expected_days}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
