/**
 * CatalogPage — validation status of data/catalogs/crops.json.
 * Surfaces schema problems before the engine or UI consumes catalog data.
 * Owner: Shehani. Scientific content and approval: Tharuka (research) and Bhagya.
 */
import { useTranslation } from "react-i18next";
import { loadedCatalog } from "../catalog";

export function CatalogPage() {
  const { t } = useTranslation();
  const { ok, issues, notes, catalog } = loadedCatalog;

  return (
    <div className="page">
      <h1>{t("catalog.title")}</h1>
      <p className="muted">{t("catalog.intro")}</p>

      <div className={`notice ${ok ? "notice-ok" : "notice-warn"}`} role="status">
        <strong>{ok ? t("catalog.valid") : t("catalog.invalid", { count: issues.length })}</strong>
        {catalog && (
          <div>
            {t("catalog.summary", {
              version: catalog.catalog_version,
              status: catalog.status,
              region: catalog.region,
              count: catalog.crops.length,
              approved: loadedCatalog.approvedCrops.length,
            })}
          </div>
        )}
      </div>

      {notes.length > 0 && (
        <ul className="notice notice-info" style={{ paddingLeft: 32 }}>
          {notes.map((n, i) => (
            <li key={i}>{n}</li>
          ))}
        </ul>
      )}

      {issues.length > 0 && (
        <div className="card table-scroll">
          <table className="data">
            <thead>
              <tr>
                <th scope="col">{t("catalog.path")}</th>
                <th scope="col">{t("catalog.problem")}</th>
              </tr>
            </thead>
            <tbody>
              {issues.map((iss, i) => (
                <tr key={i}>
                  <td>
                    <code>{iss.path}</code>
                  </td>
                  <td>{iss.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {catalog && catalog.crops.length > 0 && (
        <div className="card table-scroll">
          <table className="data">
            <thead>
              <tr>
                <th scope="col">ID</th>
                <th scope="col">{t("catalog.name")}</th>
                <th scope="col">{t("catalog.family")}</th>
                <th scope="col">{t("catalog.seasons")}</th>
                <th scope="col">{t("catalog.water")}</th>
                <th scope="col">{t("catalog.review")}</th>
                <th scope="col">{t("common.source")}</th>
              </tr>
            </thead>
            <tbody>
              {catalog.crops.map((c) => (
                <tr key={c.id}>
                  <td>
                    <code>{c.id}</code>
                  </td>
                  <td>{c.name}</td>
                  <td>{c.family ?? t("common.unknown")}</td>
                  <td>{c.season_labels.join(", ") || "—"}</td>
                  <td>{c.water_demand_mm_per_cycle === null ? t("common.unknown") : `${c.water_demand_mm_per_cycle} mm`}</td>
                  <td>{c.review_status}</td>
                  <td>
                    {c.sources.map((s, i) => (
                      <div key={i}>
                        <a href={s.url} target="_blank" rel="noreferrer">
                          {new URL(s.url).host}
                        </a>{" "}
                        <span className="muted">({s.accessed_on})</span>
                      </div>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
