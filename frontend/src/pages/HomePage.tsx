/** Official AgroSphere landing page: Tharuka's design with Shehani's data flow. */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useAppStore } from "../hooks/useAppStore";
import { ErrorMessage } from "../components/ui/ErrorMessage";
import { listCachedPlanIds } from "../utils/offlineCache";
import "./HomePage.css";

export function HomePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const recentFarms = useAppStore((s) => s.recentFarms);
  const recentPlans = useAppStore((s) => s.recentPlans);
  const setFarm = useAppStore((s) => s.setFarm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [offlinePlanIds] = useState(() => new Set(listCachedPlanIds()));

  const loadDemo = async () => {
    setBusy(true);
    setError(null);
    try {
      const env = await api.createDemoFarm();
      setFarm(env);
      navigate(`/farms/${env.id}`);
    } catch (err) {
      setError(err);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="landing-page">
      <section className="landing-hero" aria-labelledby="landing-title">
        <img src="/images/agrosphere-hero.webp" alt="" className="landing-hero__image" fetchPriority="high" />
        <div className="landing-hero__content">
          <p className="landing-eyebrow">{t("landing.eyebrow")}</p>
          <h1 id="landing-title">
            {t("landing.title")}<br />
            <em>{t("landing.titleAccent")}</em>
          </h1>
          <p className="landing-hero__description">{t("landing.description")}</p>
          <div className="landing-actions">
            <Link to="/farms/new" className="landing-button landing-button--primary">
              {t("landing.explore")} <span aria-hidden="true">↗</span>
            </Link>
            <button type="button" className="landing-button landing-button--outline" onClick={loadDemo} disabled={busy}>
              {busy ? t("common.loading") : t("home.loadDemo")}
            </button>
          </div>
          <a className="landing-how-link" href="#how-it-works">
            {t("landing.how")} <span aria-hidden="true">↓</span>
          </a>
          <p className="landing-hero__credit">{t("landing.challenge")}</p>
        </div>
        <aside className="landing-field-note">
          <span className="landing-eyebrow">{t("landing.fieldNote")}</span>
          <strong>{t("landing.fieldTitle")}</strong>
          <p>{t("landing.fieldDescription")}</p>
          <div className="landing-crop-sequence" aria-hidden="true">
            <span>01</span><i /><span>02</span><i /><span>03</span>
          </div>
          <small>{t("landing.fieldFooter")}</small>
        </aside>
      </section>

      <div className="landing-source-strip">
        <span>{t("landing.sourceLabel")}</span>
        <strong>NASA POWER</strong>
        <strong>SMAP</strong>
        <span>{t("landing.sourceNote")}</span>
      </div>

      <div className="landing-content">
        <ErrorMessage error={error} onRetry={loadDemo} />
        <section id="how-it-works" className="landing-platform" aria-labelledby="platform-title">
          <p className="landing-kicker">{t("landing.platformKicker")}</p>
          <h2 id="platform-title">{t("landing.platformTitle")}</h2>
          <p className="landing-lead">{t("home.journey")}</p>
          <div className="landing-feature-grid">
            {(["observe", "plan", "understand"] as const).map((key, index) => (
              <article className="landing-feature" key={key}>
                <span className="landing-feature__number">0{index + 1}</span>
                <h3>{t(`landing.${key}Title`)}</h3>
                <p>{t(`landing.${key}Description`)}</p>
              </article>
            ))}
          </div>
          <p className="landing-status">{t("landing.status")}</p>
        </section>

        <section className="landing-workspace" aria-labelledby="workspace-title">
          <div className="landing-workspace__heading">
            <div>
              <p className="landing-kicker">{t("landing.workspaceKicker")}</p>
              <h2 id="workspace-title">{t("landing.workspaceTitle")}</h2>
            </div>
            <Link to="/farms/new" className="btn btn-primary">+ {t("nav.newFarm")}</Link>
          </div>
          <div className="landing-workspace__grid">
            <div>
              <h2>{t("home.recentFarms")}</h2>
              {recentFarms.length === 0 ? (
                <p className="muted">{t("home.noFarms")}</p>
              ) : (
                <ul className="card" style={{ listStyle: "none", paddingLeft: 16 }}>
                  {recentFarms.map((farm) => (
                    <li key={farm.id} style={{ padding: "6px 0" }}>
                      <Link to={`/farms/${farm.id}`}>{farm.name}</Link>
                      <span className="muted"> ({farm.id})</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
            <div>
              <h2>{t("home.recentPlans")}</h2>
              {recentPlans.length === 0 ? (
                <p className="muted">{t("home.noPlans")}</p>
              ) : (
                <ul className="card" style={{ listStyle: "none", paddingLeft: 16 }}>
                  {recentPlans.map((plan) => (
                    <li key={plan.id} style={{ padding: "6px 0" }}>
                      <Link to={`/plans/${plan.id}`}>{plan.name}</Link>
                      <span className="muted"> ({plan.id})</span>
                      {offlinePlanIds.has(plan.id) && (
                        <span className="badge-offline" style={{ marginLeft: 8 }}>
                          {t("offline.availableBadge")}
                        </span>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </section>
        <footer className="landing-footer">
          <strong>AgroSphere AI</strong>
          <span>{t("landing.footer")}</span>
          <Link to="/catalog">{t("nav.catalog")} <span aria-hidden="true">↗</span></Link>
        </footer>
      </div>
    </div>
  );
}
