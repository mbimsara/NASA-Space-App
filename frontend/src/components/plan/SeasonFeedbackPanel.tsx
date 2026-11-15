import { useEffect, useState } from "react";

import { api } from "../../api";
import { ErrorMessage } from "../ui/ErrorMessage";
import type { SeasonFeedback } from "../../types/api";

export function SeasonFeedbackPanel({ planId, seasons }: { planId: string; seasons: number[] }) {
  const [items, setItems] = useState<SeasonFeedback[]>([]);
  const [season, setSeason] = useState(seasons[0] ?? 1);
  const [crop, setCrop] = useState("");
  const [planted, setPlanted] = useState("");
  const [harvested, setHarvested] = useState("");
  const [yieldValue, setYieldValue] = useState("");
  const [yieldUnit, setYieldUnit] = useState<SeasonFeedback["yield_unit"]>("kg/ha");
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    api.listPlanFeedback(planId, controller.signal).then(setItems).catch(setError);
    return () => controller.abort();
  }, [planId]);

  return <section className="card no-print" aria-labelledby="feedback-title">
    <h2 id="feedback-title" style={{ marginTop: 0 }}>Season feedback</h2>
    <p className="muted">Record what actually happened. These farmer-entered outcomes remain separate from NASA observations and do not automatically retrain the model.</p>
    {error != null && <ErrorMessage error={error} />}
    <form className="row" onSubmit={(event) => {
      event.preventDefault(); setSaving(true); setError(null);
      api.createPlanFeedback(planId, {
        season_index: season, planted_on: planted || null, harvested_on: harvested || null,
        actual_crop_id: crop.trim() || null, yield_value: yieldValue === "" ? null : Number(yieldValue),
        yield_unit: yieldValue === "" ? null : yieldUnit, notes: notes.trim(),
      }).then((item) => { setItems((prior) => [item, ...prior]); setNotes(""); setYieldValue(""); })
        .catch(setError).finally(() => setSaving(false));
    }}>
      <label className="field">Season<select value={season} onChange={(e) => setSeason(Number(e.target.value))}>{seasons.map((value) => <option key={value} value={value}>{value}</option>)}</select></label>
      <label className="field">Actual crop ID<input value={crop} maxLength={100} onChange={(e) => setCrop(e.target.value)} /></label>
      <label className="field">Planted<input type="date" value={planted} onChange={(e) => setPlanted(e.target.value)} /></label>
      <label className="field">Harvested<input type="date" value={harvested} min={planted || undefined} onChange={(e) => setHarvested(e.target.value)} /></label>
      <label className="field">Yield (optional)<input type="number" min="0" step="any" value={yieldValue} onChange={(e) => setYieldValue(e.target.value)} /></label>
      <label className="field">Yield unit<select value={yieldUnit ?? "kg/ha"} disabled={yieldValue === ""} onChange={(e) => setYieldUnit(e.target.value as SeasonFeedback["yield_unit"])}><option>kg</option><option>kg/ha</option><option>t</option><option>t/ha</option></select></label>
      <label className="field" style={{ flexBasis: "100%" }}>Notes<textarea value={notes} maxLength={2000} onChange={(e) => setNotes(e.target.value)} /></label>
      <button className="btn btn-primary" disabled={saving || seasons.length === 0}>{saving ? "Saving…" : "Save feedback"}</button>
    </form>
    {items.length > 0 && <div className="table-scroll" style={{ marginTop: 16 }}><table className="data"><thead><tr><th>Season</th><th>Crop</th><th>Dates</th><th>Yield</th><th>Notes</th></tr></thead><tbody>
      {items.map((item) => <tr key={item.feedback_id}><td>{item.season_index}</td><td>{item.actual_crop_id ?? "—"}</td><td>{item.planted_on ?? "—"} → {item.harvested_on ?? "—"}</td><td>{item.yield_value == null ? "—" : `${item.yield_value} ${item.yield_unit}`}</td><td>{item.notes || "—"}</td></tr>)}
    </tbody></table></div>}
  </section>;
}
