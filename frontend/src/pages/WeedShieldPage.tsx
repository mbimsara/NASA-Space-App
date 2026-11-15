import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import { useAppStore } from "../hooks/useAppStore";
import type { HlsContext } from "../types/api";
import { SourceBadge } from "../components/ui/SourceBadge";
import { analyzeVegetationPhoto, type VegetationTriageResult } from "../utils/vegetationTriage";

export function WeedShieldPage() {
  const farm = useAppStore((state) => state.farm)!;
  const [photoUrl, setPhotoUrl] = useState<string | null>(null);
  const [result, setResult] = useState<VegetationTriageResult | null>(null);
  const [hls, setHls] = useState<HlsContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    api.getHlsVegetation(farm.id, controller.signal).then((value) => {
      if (value.input_version === farm.input_version) setHls(value);
    }).catch(() => undefined);
    return () => controller.abort();
  }, [farm.id, farm.input_version]);

  useEffect(() => () => { if (photoUrl) URL.revokeObjectURL(photoUrl); }, [photoUrl]);
  const acceptedHls = useMemo(() => hls?.observations.filter((item) => item.quality_accepted && item.ndvi != null) ?? [], [hls]);

  const selectPhoto = async (file?: File) => {
    if (!file) return;
    if (!file.type.startsWith("image/")) { setError("Choose a JPEG, PNG, HEIC, or another browser-readable image."); return; }
    setBusy(true); setError(null); setResult(null);
    if (photoUrl) URL.revokeObjectURL(photoUrl);
    setPhotoUrl(URL.createObjectURL(file));
    try { setResult(await analyzeVegetationPhoto(file)); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "The image could not be analysed in this browser."); }
    finally { setBusy(false); }
  };

  return <div className="page">
    <h1>WeedShield field-photo triage</h1>
    <p className="muted">Screen visible green cover in a field photo on this device. The photo is not uploaded or stored. This transparent heuristic is not a trained weed detector and cannot identify weed species or separate weeds from the crop.</p>
    <div className="notice notice-warn"><strong>Farmer confirmation is required.</strong> Use the result only to decide where to inspect, photograph again, or ask a local agronomist. Do not choose herbicide from this screen.</div>
    <section className="card">
      <h2 style={{ marginTop: 0 }}>1. Add a field photo</h2>
      <input aria-label="Field photo" type="file" accept="image/*" capture="environment" onChange={(event) => void selectPhoto(event.target.files?.[0])} />
      {busy && <p>Analysing image pixels locally…</p>}
      {error && <p className="field-error" role="alert">{error}</p>}
      {photoUrl && <img src={photoUrl} alt="Selected field" style={{ display: "block", marginTop: 16, maxWidth: "100%", maxHeight: 420, borderRadius: 12 }} />}
    </section>
    {result && <section className="card">
      <h2 style={{ marginTop: 0 }}>2. Vegetation-like pixel screening</h2>
      <p style={{ fontSize: "2rem", margin: "8px 0" }}><strong>{result.vegetation_cover_percent}%</strong></p>
      <p>Pixels matching the documented green-colour heuristic: {result.vegetation_pixels.toLocaleString()} / {result.valid_pixels.toLocaleString()} ({result.width} × {result.height} analysed).</p>
      <p className="muted">Method: {result.method}. Lighting, shadows, soil colour, senescent plants, camera angle, crop canopy, and residue can change the result. This is vegetation-like cover—not weed cover.</p>
      <h3>Next field checks</h3>
      <ul><li>Inspect several representative points, not one photograph.</li><li>Record whether the green pixels are crop, weed, or unknown.</li><li>Ask a qualified local adviser to confirm species and management options.</li></ul>
    </section>}
    <section className="card">
      <h2 style={{ marginTop: 0 }}>NASA HLS field-scale context (separate evidence)</h2>
      {hls ? <><p>{acceptedHls.length} quality-accepted 30 m NDVI observation(s) in the local HLS artifact.</p><SourceBadge sourceRefs={hls.source_refs} dataKind={hls.data_kind} /><ul className="muted">{hls.limitations.map((item) => <li key={item}>{item}</li>)}</ul></> : <p className="muted">No location-matched HLS artifact is available. The phone-photo triage still works locally.</p>}
      <p className="muted">HLS NDVI is not used to classify this photo and cannot identify individual weeds.</p>
    </section>
  </div>;
}
