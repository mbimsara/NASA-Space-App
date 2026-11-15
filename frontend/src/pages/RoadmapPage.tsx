/** Capability status: working tools first, then genuinely blocked research items. */
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAppStore } from "../hooks/useAppStore";

export function RoadmapPage() {
  const { t } = useTranslation();
  const farmId = useAppStore((state) => state.selectedFarmId);
  const latestPlan = useAppStore((state) => state.recentPlans.find((plan) => plan.farmId === state.selectedFarmId));
  const available = farmId ? [
    { title: "NASA observations", detail: "POWER weather with optional SMAP, GPM and HLS context.", to: `/farms/${farmId}` },
    { title: "Soil health evidence", detail: "Local soil tests plus quality-screened SMAP and HLS context.", to: `/farms/${farmId}/soil-health` },
    { title: "Climate twins", detail: "Same-period comparison of registered farms using NASA POWER snapshots.", to: `/farms/${farmId}/climate-twins` },
    { title: "WeedShield field-photo triage", detail: "On-device vegetation-like pixel screening with farmer confirmation and separate NASA HLS context; no unsupported species claim.", to: `/farms/${farmId}/weed-shield` },
    { title: "Rotation, water and recovery workflow", detail: "Standard, SoilRevive, drought-recovery and flood-recovery screening with reviewed crop evidence and rainfall-stress scenarios.", to: `/farms/${farmId}/rotations` },
    { title: "Grounded AI review", detail: "Answers tied to the selected farm, analysis, scenario and candidate.", to: `/farms/${farmId}/assistant` },
    { title: "English voice and read-aloud", detail: "Browser speech input for the reviewed English assistant and browser read-aloud for answers.", to: `/farms/${farmId}/assistant` },
    ...(latestPlan ? [{ title: "Calendar reminders", detail: "Opt-in browser reminders while AgroSphere is open, plus reliable .ics calendar export.", to: `/plans/${latestPlan.id}` }] : []),
  ] : [];
  return (
    <div className="page">
      <h1>{t("roadmap.title")}</h1>
      <p className="muted">{t("roadmap.intro")}</p>
      <h2>{t("roadmap.availableTitle")}</h2>
      {available.length ? <div className="feature-grid">
        {available.map((item) => <article className="card" key={item.title}>
          <h3 style={{ marginTop: 0 }}>{item.title} <span className="badge-offline">Available</span></h3>
          <p>{item.detail}</p><Link className="btn" to={item.to}>Open tool</Link>
        </article>)}
      </div> : <div className="card"><p>Select or create a farm to open the available farm tools.</p><Link className="btn btn-primary" to="/farms/new">Create farm</Link></div>}
    </div>
  );
}
