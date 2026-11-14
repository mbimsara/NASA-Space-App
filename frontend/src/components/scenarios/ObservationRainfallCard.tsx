/**
 * ObservationRainfallCard — the original NASA observation total next to the
 * uniformly scaled scenario total (live API `observation_rainfall`).
 * The stored observation is never changed; unknown totals show "Unknown".
 */
import { useTranslation } from "react-i18next";
import type { ScenarioResult } from "../../types/api";
import { fmtMm, fmtSignedMm } from "../../utils/format";

interface Props {
  rain: NonNullable<ScenarioResult["observation_rainfall"]>;
}

export function ObservationRainfallCard({ rain }: Props) {
  const { t } = useTranslation();
  const u = t("common.unknown");
  return (
    <div className="card">
      <h2 style={{ marginTop: 0, fontSize: "1.05rem" }}>{t("scenario.observationRainfall")}</h2>
      <p className="muted" style={{ fontSize: 12 }}>
        {t("scenario.observationPeriod", {
          start: rain.period_start,
          end: rain.period_end,
          valid: rain.valid_days,
          expected: rain.expected_days,
        })}
      </p>
      <table className="data">
        <tbody>
          <tr>
            <th scope="row">{t("scenario.baseline")}</th>
            <td>{fmtMm(rain.baseline_rainfall_mm, u)}</td>
          </tr>
          <tr>
            <th scope="row">{t("scenario.scenario")}</th>
            <td>{fmtMm(rain.scenario_rainfall_mm, u)}</td>
          </tr>
          <tr>
            <th scope="row">{t("scenario.difference")}</th>
            <td>{fmtSignedMm(rain.difference_mm, u)}</td>
          </tr>
        </tbody>
      </table>
      <p className="muted" style={{ fontSize: 12 }}>
        {t("scenario.observationUnchanged")}
      </p>
    </div>
  );
}
