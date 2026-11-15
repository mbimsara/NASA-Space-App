import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { useAppStore } from "../hooks/useAppStore";
import type { HlsContext, SoilMoistureContext } from "../types/api";

export function SoilHealthPage() {
  const farm = useAppStore((state) => state.farm)!;
  const [smap, setSmap] = useState<SoilMoistureContext | null>(null);
  const [hls, setHls] = useState<HlsContext | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<unknown>(null);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true); setError(null); setSmap(null); setHls(null);
    Promise.allSettled([
      api.getSoilMoisture(farm.id, controller.signal),
      api.getHlsVegetation(farm.id, controller.signal),
    ]).then(([soil, vegetation]) => {
      if (soil.status === "fulfilled" && soil.value.input_version === farm.input_version) setSmap(soil.value);
      if (vegetation.status === "fulfilled" && vegetation.value.input_version === farm.input_version) setHls(vegetation.value);
      const unexpected = [soil, vegetation].find((result) => result.status === "rejected" && !(result.reason && typeof result.reason === "object" && "status" in result.reason && result.reason.status === 404));
      if (unexpected?.status === "rejected") setError(unexpected.reason);
    }).finally(() => setLoading(false));
    return () => controller.abort();
  }, [farm.id, farm.input_version]);

  const moisture = useMemo(() => {
    const values = smap?.daily.flatMap((day) => [day.AM, day.PM])
      .filter((pass) => pass.accepted && pass.soil_moisture_m3_m3 != null)
      .map((pass) => pass.soil_moisture_m3_m3!) ?? [];
    return values.length ? values.reduce((sum, value) => sum + value, 0) / values.length : null;
  }, [smap]);
  const ndvi = hls?.observations.filter((item) => item.quality_accepted && item.ndvi != null).map((item) => item.ndvi!) ?? [];
  const meanNdvi = ndvi.length ? ndvi.reduce((sum, value) => sum + value, 0) / ndvi.length : null;

  return <div className="page">
    <h1>Soil and recovery evidence</h1>
    <p className="muted">A transparent view of farmer-entered soil tests and regional NASA context. It does not convert satellite surface moisture or greenness into nutrients, pH, root-zone water, or a soil-health score.</p>
    {loading && <LoadingSpinner />}
    {error != null && <ErrorMessage error={error} />}

    <section className="card">
      <h2 style={{ marginTop: 0 }}>Local soil measurements</h2>
      {farm.profile.soil_tests.length ? <div className="table-scroll"><table className="data"><thead><tr><th>Metric</th><th>Value</th><th>Sample date</th></tr></thead><tbody>
        {farm.profile.soil_tests.map((test, index) => <tr key={`${test.metric}-${index}`}><td>{test.metric}</td><td>{test.value} {test.unit}</td><td>{test.sampled_on}</td></tr>)}
      </tbody></table></div> : <p className="notice notice-warn">No field soil tests are recorded. Add laboratory or farmer measurements before making nutrient, pH, organic-matter, or amendment decisions.</p>}
      <Link className="btn" to={`/farms/${farm.id}/edit`}>Add or update soil tests</Link>
    </section>

    <section className="card">
      <h2 style={{ marginTop: 0 }}>SMAP regional surface moisture</h2>
      {smap ? <><p className="notice notice-info">Mean of {smap.coverage.accepted_AM + smap.coverage.accepted_PM} quality-accepted AM/PM retrievals: <strong>{moisture == null ? "Unknown" : `${moisture.toFixed(3)} ${smap.units}`}</strong></p>
        <SourceBadge sourceRefs={smap.source_refs} dataKind={smap.data_kind} /><ul className="muted">{smap.limitations.map((item) => <li key={item}>{item}</li>)}</ul></>
        : !loading && <p className="muted">No verified SMAP artifact covers this farm. Nothing has been estimated or filled.</p>}
    </section>

    <section className="card">
      <h2 style={{ marginTop: 0 }}>HLS vegetation-cover context</h2>
      {hls ? <><p className="notice notice-info">Accepted NDVI observations: <strong>{hls.coverage.accepted_observations}</strong> / {hls.coverage.supplied_observations}; mean accepted NDVI: <strong>{meanNdvi == null ? "Unknown" : meanNdvi.toFixed(3)}</strong></p>
        <SourceBadge sourceRefs={hls.source_refs} retrievedAt={hls.retrieved_at} dataKind={hls.data_kind} /><ul className="muted">{hls.limitations.map((item) => <li key={item}>{item}</li>)}</ul></>
        : !loading && <p className="muted">No quality-screened HLS artifact covers this farm. NDVI is not being inferred from another location.</p>}
    </section>

    <section className="card">
      <h2 style={{ marginTop: 0 }}>Recovery planning</h2>
      <p>Use the rotation comparison to evaluate crop diversity and water-demand ranges, then test rainfall stress in the scenario tool. Satellite context cannot prescribe fertilizer, diagnose compaction, or guarantee recovery.</p>
      <div className="row"><Link className="btn btn-primary" to={`/farms/${farm.id}/rotations`}>Compare rotations</Link><Link className="btn" to={`/farms/${farm.id}/scenario`}>Test rainfall stress</Link></div>
    </section>
  </div>;
}
