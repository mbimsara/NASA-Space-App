/**
 * ObservationsPage — farm overview: observation summary, chart, coverage,
 * provenance, missing-data state, and the next step (compare rotations).
 * Owner: Shehani. Time-series field names to be confirmed with Matheesha.
 */
import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { isAbortError } from "../api/requestGuard";
import { useAppStore } from "../hooks/useAppStore";
import { useLatestRequest } from "../hooks/useLatestRequest";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { SyntheticDataBanner } from "../components/ui/SyntheticDataBanner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { MissingDataPlaceholder } from "../components/ui/MissingDataPlaceholder";
import { ObservationChart } from "../components/observations/ObservationChart";
import { todayIso } from "../utils/validation";
import type { ObservationSummary } from "../types/api";

function monthAgo() {
  const d = new Date();
  d.setMonth(d.getMonth() - 1);
  return todayIso(d);
}

export function ObservationsPage() {
  const { t } = useTranslation();
  const farm = useAppStore((s) => s.farm)!;
  const guard = useLatestRequest();

  const [start, setStart] = useState(monthAgo);
  const [end, setEnd] = useState(() => todayIso());
  const [obs, setObs] = useState<ObservationSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const rangeInvalid = !start || !end || start > end;

  const fetchObs = useCallback(
    (from: string, to: string) => {
      const ticket = guard.next();
      setLoading(true);
      setError(null);
      api
        .getObservations(farm.id, from, to, ticket.signal)
        .then((res) => {
          // Never display a response for another farm.
          if (ticket.isCurrent() && res.farm_id === farm.id) setObs(res);
        })
        .catch((err) => {
          if (ticket.isCurrent() && !isAbortError(err)) setError(err);
        })
        .finally(() => {
          if (ticket.isCurrent()) setLoading(false);
        });
    },
    [farm.id, guard],
  );

  useEffect(() => {
    setObs(null);
    fetchObs(monthAgo(), todayIso());
  }, [fetchObs]);

  const s = obs?.summary;

  return (
    <div className="page">
      <h1>{t("observations.title")}</h1>

      <form
        className="card row"
        onSubmit={(e) => {
          e.preventDefault();
          if (!rangeInvalid) fetchObs(start, end);
        }}
      >
        <div className="field">
          <label htmlFor="obs-start">{t("observations.startDate")}</label>
          <input id="obs-start" type="date" value={start} max={end} onChange={(e) => setStart(e.target.value)} />
        </div>
        <div className="field">
          <label htmlFor="obs-end">{t("observations.endDate")}</label>
          <input
            id="obs-end"
            type="date"
            value={end}
            min={start}
            max={todayIso()}
            onChange={(e) => setEnd(e.target.value)}
          />
        </div>
        <button type="submit" className="btn btn-secondary" disabled={loading || rangeInvalid}>
          {loading ? t("common.loading") : t("observations.load")}
        </button>
        {rangeInvalid && (
          <span className="field-error" role="alert">
            {t("observations.rangeInvalid")}
          </span>
        )}
      </form>

      {loading && <LoadingSpinner />}
      {!loading && error != null && <ErrorMessage error={error} onRetry={() => fetchObs(start, end)} />}

      {!loading && obs && (
        <>
          <SyntheticDataBanner dataKind={obs.data_kind} limitations={obs.limitations} />

          <div className="card">
            <div className="row" style={{ alignItems: "stretch" }}>
              <div className="notice notice-info" style={{ minWidth: 160, margin: 0 }}>
                <div className="muted">{t("observations.rainfallTotal")}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  {s?.rainfall_mm != null ? `${s.rainfall_mm} mm` : t("common.unknown")}
                </div>
              </div>
              <div className="notice notice-warn" style={{ minWidth: 160, margin: 0 }}>
                <div className="muted">{t("observations.temperatureMean")}</div>
                <div style={{ fontSize: 22, fontWeight: 700 }}>
                  {s?.mean_temperature_c != null ? `${s.mean_temperature_c} °C` : t("common.unknown")}
                </div>
              </div>
            </div>
            <p className="muted">
              {obs.period.start} → {obs.period.end} · {t("observations.coverage")}:{" "}
              {t("observations.coverageText", {
                available: obs.coverage.available_days,
                expected: obs.coverage.expected_days,
              })}
            </p>
            {obs.coverage.available_days === 0 ? (
              <MissingDataPlaceholder reason={obs.limitations.join(" ")} />
            ) : (
              <>
                {obs.coverage.available_days < obs.coverage.expected_days && (
                  <p className="muted">{t("observations.gapsNote")}</p>
                )}
                <ObservationChart timeSeries={obs.time_series} hasData />
              </>
            )}
            <SourceBadge
              sourceRefs={obs.source_refs}
              retrievedAt={obs.retrieved_at}
              spatialResolution={obs.spatial_resolution}
              dataKind={obs.data_kind}
            />
          </div>
        </>
      )}

      <Link to={`/farms/${farm.id}/rotations`} className="btn btn-primary">
        {t("observations.nextStep")} →
      </Link>
    </div>
  );
}
