/**
 * RoadmapPage — planned capabilities, visibly labelled as not yet implemented
 * (IMPLEMENTATION_PLAN: "Keep these visibly identified as planned capabilities
 * until implemented"), each with the dependency it is waiting for.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";

const ITEMS = [
  { key: "offlineEdit", owner: "Dulanjaya, Shehani" },
  { key: "reminders", owner: "Dulanjaya, Shehani" },
  { key: "soilModes", owner: "Bhagya, Tharuka, Shehani" },
  { key: "weed", owner: "Akash, Shehani" },
  { key: "voice", owner: "Akash, Shehani, Tharuka" },
] as const;

export function RoadmapPage() {
  const { t } = useTranslation();
  return (
    <div className="page">
      <h1>{t("roadmap.title")}</h1>
      <p className="muted">{t("roadmap.intro")}</p>
      <ul style={{ listStyle: "none", padding: 0 }}>
        {ITEMS.map((it) => (
          <li key={it.key} className="card">
            <h2 style={{ margin: "0 0 4px", fontSize: "1.05rem" }}>
              {t(`roadmap.items.${it.key}.title`)} <span className="badge-planned">{t("common.roadmapFeature")}</span>
            </h2>
            <p style={{ margin: "0 0 4px" }}>{t(`roadmap.items.${it.key}.what`)}</p>
            <p className="muted" style={{ margin: 0, fontSize: "0.85rem" }}>
              <strong>{t("roadmap.waitingFor")}:</strong> {t(`roadmap.items.${it.key}.why`)} · <strong>{t("roadmap.owners")}:</strong>{" "}
              {it.owner}
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
