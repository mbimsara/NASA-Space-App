/**
 * CatalogPage — validation status of data/catalogs/crops.json.
 * Surfaces schema problems before the engine or UI consumes catalog data.
 * Owner: Shehani. Scientific content and approval: Tharuka (research) and Bhagya.
 */
import { useTranslation } from "react-i18next";
import { loadedCatalog } from "../catalog";
import { localizeToolMessage } from "../i18n/toolMessages";
import { Icon } from "../components/ui/Icon";
import "./CatalogPage.css";

export function CatalogPage() {
  const { t } = useTranslation();
  const { ok, issues, notes, catalog } = loadedCatalog;

  return (
    <div className="page catalog-page">
      <h1>{t("catalog.title")}</h1>
      <p className="muted">{t("catalog.intro")}</p>

      <div className={`notice ${ok ? "notice-ok" : "notice-warn"}`} role="status">
        <strong>{ok ? t("catalog.valid") : t("catalog.invalid", { count: issues.length })}</strong>
        {catalog && (
          <div>
            {t("catalog.summary", {
              version: catalog.catalog_version,
              status: t(`catalog.status.${catalog.status}`, { defaultValue: catalog.status }),
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
            <li key={i}>{localizeToolMessage(n, t)}</li>
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
                  <td>{localizeToolMessage(iss.message, t)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {catalog && catalog.crops.length > 0 && (
        <div className="card catalog-table-card">
          <div className="catalog-table-scroll" role="region" aria-label={t("nav.catalog")} tabIndex={0}>
          <table className="data catalog-table" aria-label={t("nav.catalog")}>
            <colgroup><col className="catalog-col-id" /><col className="catalog-col-name" /><col className="catalog-col-family" /><col className="catalog-col-seasons" /><col className="catalog-col-water" /><col className="catalog-col-review" /><col className="catalog-col-source" /></colgroup>
            <thead>
              <tr>
                <th scope="col">{t("catalog.identifier")}</th>
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
                  <th scope="row" className="catalog-crop-name">{c.name}</th>
                  <td className="catalog-family">{c.family ?? t("common.unknown")}</td>
                  <td><div className="catalog-seasons">{c.season_labels.map((season) => <span className="catalog-season" key={season}>{t(`rotation.seasonLabel.${season}`, { defaultValue: season })}</span>)}{c.season_labels.length === 0 && "—"}</div></td>
                  <td className="catalog-water">{c.water_demand_mm_per_cycle === null ? <span className="muted">{t("common.unknown")}</span> : <><strong>{c.water_demand_mm_per_cycle.toLocaleString()}</strong> <span>mm</span></>}</td>
                  <td><span className={`catalog-review catalog-review--${c.review_status}`}><i aria-hidden="true" />{t(`catalog.status.${c.review_status}`, { defaultValue: c.review_status })}</span></td>
                  <td>
                    {c.sources.map((s, i) => (
                      <div className="catalog-source" key={i}>
                        <a href={s.url} target="_blank" rel="noopener noreferrer">
                          {new URL(s.url).host.replace(/^www\./, "")}<Icon name="external" />
                        </a>
                        <time dateTime={s.accessed_on}>{s.accessed_on}</time>
                      </div>
                    ))}
                    {c.sources.length === 0 && <span className="muted">{t("common.unknown")}</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
        </div>
      )}
    </div>
  );
}
