/**
 * Sidebar — Tharuka's dark-forest navigation: brand, current-farm switcher,
 * core journey links, tools, planned features, and data-mode footer.
 * Fixed on desktop; an off-canvas drawer below 960 px.
 * Owner: Shehani. Design: Tharuka.
 */
import { NavLink, Link } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { Icon } from "../ui/Icon";
import { useAppStore } from "../../hooks/useAppStore";
import { USE_FIXTURES } from "../../api";

interface Props {
  open: boolean;
  onNavigate: () => void;
  id: string;
}

function initials(name: string): string {
  const parts = name.split(/\s+/).filter((w) => /^[\p{L}\p{N}]/u.test(w));
  return (parts[0]?.[0] ?? "F").toUpperCase() + (parts[1]?.[0] ?? "").toUpperCase();
}

export function Sidebar({ open, onNavigate, id }: Props) {
  const { t } = useTranslation();
  const farmId = useAppStore((s) => s.selectedFarmId);
  const farmName = useAppStore((s) => s.farm?.profile.name ?? s.recentFarms.find((f) => f.id === s.selectedFarmId)?.name ?? null);
  const latestPlan = useAppStore((s) => s.recentPlans.find((p) => p.farmId === s.selectedFarmId) ?? null);

  const farmLinks: [string, string, string, boolean?][] = farmId
    ? [
        [`/farms/${farmId}/edit`, "edit", t("journey.setup")],
        [`/farms/${farmId}`, "overview", t("journey.overview"), true],
        [`/farms/${farmId}/rotations`, "rotate", t("journey.plan")],
        [`/farms/${farmId}/scenario`, "climate", t("journey.climate")],
        [`/farms/${farmId}/assistant`, "chat", t("journey.ai")],
      ]
    : [];

  const link = (to: string, icon: string, label: string, end = false) => (
    <NavLink key={`${to}|${icon}|${label}`} to={to} end={end} onClick={onNavigate}>
      <Icon name={icon} />
      <span>{label}</span>
    </NavLink>
  );

  return (
    <aside id={id} className={`sidebar${open ? " open mobile-open" : ""}`} aria-label={t("nav.main")}>
      <Link to="/" className="side-brand" onClick={onNavigate}>
        <span className="brand-mark">
          <img src="/images/agrosphere-logo.png" alt="AgroSphere AI Logo" className="brand-logo-img" />
        </span>
        <span>
          AgroSphere <b>AI</b>
        </span>
      </Link>

      <Link to="/" className="farm-switch" onClick={onNavigate} aria-label={t("nav.switchFarm")}>
        <span className="farm-initials" aria-hidden="true">
          {farmName ? initials(farmName) : "+"}
        </span>
        <span>
          <b>{farmName ?? t("nav.noFarm")}</b>
          <small>{farmName ? t("nav.switchFarm") : t("nav.chooseFarm")}</small>
        </span>
      </Link>

      <nav className="side-nav" aria-label={t("nav.main")}>
        <span className="side-section">{t("nav.coreJourney")}</span>
        {link("/", "home", t("nav.home"), true)}
        {farmId ? (
          farmLinks.map(([to, icon, label, end]) => link(to, icon, label, end))
        ) : (
          <>
            {link("/farms/new", "farm", t("journey.setup"))}
            <span className="side-disabled" aria-disabled="true">
              <Icon name="rotate" />
              <span>{t("nav.needsFarm")}</span>
            </span>
          </>
        )}
        {latestPlan ? (
          link(`/plans/${latestPlan.id}`, "save", t("journey.save"))
        ) : (
          <span className="side-disabled" aria-disabled="true">
            <Icon name="save" />
            <span>{t("journey.save")}</span>
          </span>
        )}

        <span className="side-section">{t("nav.tools")}</span>
        {farmId && link(`/farms/${farmId}/rotations`, "climate", t("nav.waterBudget"))}
        <NavLink to="/roadmap#soil" onClick={onNavigate}><Icon name="farm" /><span>{t("nav.soilHealth")}</span><span className="side-tag">{t("nav.soon")}</span></NavLink>
        <NavLink to="/roadmap#weed" onClick={onNavigate}><Icon name="overview" /><span>{t("nav.weedShield")}</span><span className="side-tag">{t("nav.soon")}</span></NavLink>
        <NavLink to="/roadmap#twins" onClick={onNavigate}><Icon name="map" /><span>{t("nav.climateTwin")}</span><span className="side-tag">{t("nav.soon")}</span></NavLink>
        {latestPlan ? link(`/plans/${latestPlan.id}`, "save", t("nav.farmCalendar")) : <NavLink to="/roadmap" onClick={onNavigate}><Icon name="save" /><span>{t("nav.farmCalendar")}</span></NavLink>}
        {farmId && link(`/farms/${farmId}/finance`, "coin", t("nav.financialPlanner"))}
        {latestPlan ? link(`/plans/${latestPlan.id}`, "book", t("nav.reportsHistory")) : <NavLink to="/roadmap" onClick={onNavigate}><Icon name="book" /><span>{t("nav.reportsHistory")}</span></NavLink>}
        <NavLink to="/roadmap" onClick={onNavigate}><Icon name="overview" /><span>{t("nav.communityWater")}</span><span className="side-tag">{t("nav.soon")}</span></NavLink>
        {link("/catalog", "book", t("nav.catalog"))}
        <NavLink to="/roadmap" onClick={onNavigate}><Icon name="edit" /><span>{t("nav.settings")}</span></NavLink>

        <span className="side-section">{t("nav.planned")}</span>
        <NavLink to="/roadmap" onClick={onNavigate}>
          <Icon name="map" />
          <span>{t("nav.roadmap")}</span>
          <span className="side-tag">{t("nav.soon")}</span>
        </NavLink>
      </nav>

      <div className="side-bottom">
        <a href="https://www.spaceappschallenge.org/" target="_blank" rel="noopener noreferrer" className="spaceapps-side-card" title="Built for NASA Space Apps 2026 - Visit official challenge site">
          <div className="spaceapps-side-logo-wrap"><img src="/images/nasa-space-apps-logo.png" alt="NASA Space Apps Challenge" className="spaceapps-side-logo" /></div>
          <div className="spaceapps-side-info"><span className="spaceapps-side-tag">HACKATHON 2026</span><strong className="spaceapps-side-title">NASA Space Apps</strong><span className="spaceapps-side-link">spaceappschallenge.org <Icon name="external" /></span></div>
        </a>
        <b>{USE_FIXTURES ? t("nav.modeFixtures") : t("nav.modeLive")}</b>
        {USE_FIXTURES ? t("nav.modeFixturesHelp") : t("nav.modeLiveHelp")}
      </div>
    </aside>
  );
}
