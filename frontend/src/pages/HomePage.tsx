/**
 * HomePage — start a new farm, load the synthetic demo farm, or reopen recent farms/plans.
 * Owner: Shehani.
 */
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
    <div className="page">
      <h1>{t("home.title")}</h1>
      <p className="muted">{t("home.journey")}</p>

      <ErrorMessage error={error} onRetry={loadDemo} />

      <div className="row" style={{ marginBottom: 24 }}>
        <Link to="/farms/new" className="btn btn-primary">
          + {t("nav.newFarm")}
        </Link>
        <button type="button" className="btn" onClick={loadDemo} disabled={busy}>
          {busy ? t("common.loading") : t("home.loadDemo")}
        </button>
      </div>

      <h2>{t("home.recentFarms")}</h2>
      {recentFarms.length === 0 ? (
        <p className="muted">{t("home.noFarms")}</p>
      ) : (
        <ul className="card" style={{ listStyle: "none", paddingLeft: 16 }}>
          {recentFarms.map((f) => (
            <li key={f.id} style={{ padding: "6px 0" }}>
              <Link to={`/farms/${f.id}`}>{f.name}</Link> <span className="muted">({f.id})</span>
            </li>
          ))}
        </ul>
      )}

      <h2>{t("home.recentPlans")}</h2>
      {recentPlans.length === 0 ? (
        <p className="muted">{t("home.noPlans")}</p>
      ) : (
        <ul className="card" style={{ listStyle: "none", paddingLeft: 16 }}>
          {recentPlans.map((p) => (
            <li key={p.id} style={{ padding: "6px 0" }}>
              <Link to={`/plans/${p.id}`}>{p.name}</Link> <span className="muted">({p.id})</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
