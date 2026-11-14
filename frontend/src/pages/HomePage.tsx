/** Official AgroSphere landing page: Tharuka's design with Shehani's data flow. */
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { api } from "../api";
import { useAppStore } from "../hooks/useAppStore";
import { ErrorMessage } from "../components/ui/ErrorMessage";

export function HomePage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const recentFarms = useAppStore((s) => s.recentFarms);
  const recentPlans = useAppStore((s) => s.recentPlans);
  const setFarm = useAppStore((s) => s.setFarm);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);

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
    <div className="home-page">
      <section className="home-hero">
        <div className="home-hero__image" aria-hidden="true" />
        <div className="home-hero__shade" aria-hidden="true" />
        <div className="home-hero__content">
          <span className="eyebrow">{t("home.eyebrow")}</span>
          <h1>{t("home.title")}</h1>
          <p>{t("home.heroDescription")}</p>
          <div className="home-hero__actions">
            <Link to="/farms/new" className="btn btn-primary btn-large">
              {t("home.startPlanning")} <span aria-hidden="true">→</span>
            </Link>
            <button type="button" className="btn btn-glass btn-large" onClick={loadDemo} disabled={busy}>
              {busy ? t("common.loading") : t("home.loadDemo")}
            </button>
          </div>
          <p className="home-hero__journey">{t("home.journey")}</p>
        </div>
      </section>

      <div className="home-content">
        <ErrorMessage error={error} onRetry={loadDemo} />

        <section className="home-feature-grid" aria-label={t("home.capabilities")}>
          <article className="home-feature card">
            <span className="home-feature__number">01</span>
            <h2>{t("home.featureObserve")}</h2>
            <p>{t("home.featureObserveText")}</p>
          </article>
          <article className="home-feature card">
            <span className="home-feature__number">02</span>
            <h2>{t("home.featureRotate")}</h2>
            <p>{t("home.featureRotateText")}</p>
          </article>
          <article className="home-feature card">
            <span className="home-feature__number">03</span>
            <h2>{t("home.featureExplain")}</h2>
            <p>{t("home.featureExplainText")}</p>
          </article>
        </section>

        <section className="home-workspace">
          <div className="home-workspace__intro">
            <span className="eyebrow">{t("home.workspace")}</span>
            <h2>{t("home.continueWork")}</h2>
            <p>{t("home.workspaceText")}</p>
          </div>
          <div className="home-recents">
            <article className="card home-recent-card">
              <div className="home-recent-card__head">
                <h3>{t("home.recentFarms")}</h3>
                <Link to="/farms/new">{t("nav.newFarm")}</Link>
              </div>
              {recentFarms.length === 0 ? (
                <p className="muted">{t("home.noFarms")}</p>
              ) : (
                <ul className="home-recent-list">
                  {recentFarms.map((farm) => (
                    <li key={farm.id}>
                      <Link to={`/farms/${farm.id}`}>{farm.name}</Link>
                      <span>{farm.id}</span>
                    </li>
                  ))}
                </ul>
              )}
            </article>

            <article className="card home-recent-card">
              <div className="home-recent-card__head">
                <h3>{t("home.recentPlans")}</h3>
              </div>
              {recentPlans.length === 0 ? (
                <p className="muted">{t("home.noPlans")}</p>
              ) : (
                <ul className="home-recent-list">
                  {recentPlans.map((plan) => (
                    <li key={plan.id}>
                      <Link to={`/plans/${plan.id}`}>{plan.name}</Link>
                      <span>{plan.id}</span>
                    </li>
                  ))}
                </ul>
              )}
            </article>
          </div>
        </section>
      </div>
    </div>
  );
}
