import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import { api } from "../api";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { LoadingSpinner } from "../components/ui/LoadingSpinner";
import { SourceBadge } from "../components/ui/SourceBadge";
import { useAppStore } from "../hooks/useAppStore";
import type { ClimateTwinsResult } from "../types/api";

export function ClimateTwinPage() {
  const farm = useAppStore((state) => state.farm)!;
  const latest = useAppStore((state) => state.latestObservation);
  const [result, setResult] = useState<ClimateTwinsResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const observationId = latest?.farmId === farm.id && latest.inputVersion === farm.input_version ? latest.observationId : null;

  useEffect(() => {
    // The selected farm/observation is the result-context boundary.
    // oxlint-disable-next-line react/set-state-in-effect
    setResult(null); setError(null);
  }, [farm.id, farm.input_version, observationId]);

  if (!observationId) return <div className="page"><h1>Historical climate twins</h1><div className="card"><p>Load a complete NASA POWER observation for this farm first.</p><Link className="btn btn-primary" to={`/farms/${farm.id}`}>Open NASA observations</Link></div></div>;

  return <div className="page">
    <h1>Historical climate twins</h1>
    <p className="muted">Compare this farm with other registered farms that have complete NASA POWER snapshots for the identical dates. Similarity covers rainfall and mean temperature—not soils, pests, markets, or future suitability.</p>
    <button className="btn btn-primary" disabled={loading} onClick={() => {
      setLoading(true); setError(null);
      api.getClimateTwins(farm.id, observationId).then(setResult).catch(setError).finally(() => setLoading(false));
    }}>{loading ? "Comparing…" : "Find climate twins"}</button>
    {loading && <LoadingSpinner />}{error != null && <ErrorMessage error={error} />}
    {result && <section className="card" style={{ marginTop: 16 }}>
      <SourceBadge sourceRefs={result.source_refs} dataKind="modeled" />
      {result.twins.length ? <div className="table-scroll"><table className="data"><thead><tr><th>Farm</th><th>Location</th><th>Similarity</th><th>Δ temperature</th><th>Δ rainfall</th></tr></thead><tbody>
        {result.twins.map((item) => <tr key={item.observation_id}><td>{item.farm_id}</td><td>{item.requested_location.latitude.toFixed(3)}, {item.requested_location.longitude.toFixed(3)}</td><td>{item.similarity_score.toFixed(1)}%</td><td>{item.temperature_difference_c.toFixed(1)} °C</td><td>{item.rainfall_difference_mm.toFixed(1)} mm</td></tr>)}
      </tbody></table></div> : <p className="notice notice-info">No other eligible same-period farm snapshots exist yet. Register another farm and load the same observation dates to compare it.</p>}
      <h3>Limitations</h3><ul className="muted">{result.limitations.map((item) => <li key={item}>{item}</li>)}</ul>
    </section>}
  </div>;
}
