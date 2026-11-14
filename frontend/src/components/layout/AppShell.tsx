/**
 * AppShell — Tharuka's layout: dark sidebar, sticky top bar (menu, current farm,
 * theme, language), fixture/offline banners, and the page outlet.
 * Owner: Shehani. Design: Tharuka.
 */
import { useEffect, useRef, useState } from "react";
import { Link, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "../ui/LanguageSwitcher";
import { Icon } from "../ui/Icon";
import { Sidebar } from "./Sidebar";
import { USE_FIXTURES } from "../../api";
import { useOnlineStatus } from "../../hooks/useOnlineStatus";
import { useTheme } from "../../hooks/useTheme";
import { useAppStore } from "../../hooks/useAppStore";

export function AppShell() {
  const { t, i18n } = useTranslation();
  const online = useOnlineStatus();
  const [theme, toggleTheme] = useTheme();
  const { pathname, hash } = useLocation();
  const isHome = pathname === "/";
  const farmName = useAppStore((s) => (pathname.startsWith("/farms/") && s.farm ? s.farm.profile.name : null));
  const [menuOpen, setMenuOpen] = useState(false);
  const mainRef = useRef<HTMLElement>(null);
  const menuBtnRef = useRef<HTMLButtonElement>(null);
  const firstRender = useRef(true);

  useEffect(() => {
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  // Move focus to the new page's content after navigation (not on first load).
  useEffect(() => {
    if (firstRender.current) {
      firstRender.current = false;
      return;
    }
    // Links to a specific result (e.g. #candidate-…) manage their own focus.
    if (hash) return;
    mainRef.current?.focus({ preventScroll: false });
  }, [pathname, hash]);

  // Close the mobile drawer with Escape and return focus to the menu button.
  useEffect(() => {
    if (!menuOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setMenuOpen(false);
        menuBtnRef.current?.focus();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [menuOpen]);

  if (isHome) {
    return (
      <div className="landing-shell">
        <a className="skip-link" href="#main">{t("nav.skipToContent")}</a>
        <header className="app-header app-header--landing">
          <div className="app-header__bar">
            <Link to="/" className="app-header__brand">
              <span className="app-header__mark" aria-hidden="true">
                <svg viewBox="0 0 24 24">
                  <path d="M19.5 4.5C13.7 4.7 9.4 7 7.2 11.2c-1.5 2.8-.8 5.6 1.5 7.1 2.4 1.5 5.4.8 7.2-1.8 2.2-3.2 2.5-7.2 3.6-12Z" />
                  <path d="M5 20c2.2-5.1 5.5-8.3 10.4-10.7" />
                </svg>
              </span>
              <span>AgroSphere <b>AI</b></span>
            </Link>
            <nav className="app-header__nav" aria-label={t("nav.main")}>
              <Link to="/" className="app-header__link">{t("nav.home")}</Link>
              <Link to="/farms/new" className="app-header__link">{t("nav.newFarm")}</Link>
              <Link to="/catalog" className="app-header__link">{t("nav.catalog")}</Link>
            </nav>
            <LanguageSwitcher />
          </div>
        </header>
        {!online && (
          <div className="offline-banner" role="status">
            <strong>{t("offline.title")}</strong> {t("offline.body")}
          </div>
        )}
        {USE_FIXTURES && <div className="fixture-ribbon" role="note">{t("common.fixtureMode")}</div>}
        <main id="main" className="landing-main" ref={mainRef} tabIndex={-1} style={{ outline: "none" }}>
          <Outlet />
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        {t("nav.skipToContent")}
      </a>
      <Sidebar id="app-sidebar" open={menuOpen} onNavigate={() => setMenuOpen(false)} />
      <button
        type="button"
        className={`sidebar-backdrop${menuOpen ? " open" : ""}`}
        aria-hidden="true"
        tabIndex={-1}
        onClick={() => setMenuOpen(false)}
      />

      <div className="app-main">
        <header className="topbar">
          <button
            ref={menuBtnRef}
            type="button"
            className="icon-btn menu-btn"
            aria-controls="app-sidebar"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? t("nav.closeMenu") : t("nav.openMenu")}
            onClick={() => setMenuOpen((o) => !o)}
          >
            <Icon name={menuOpen ? "close" : "menu"} />
          </button>
          <div className="topbar-title" title={farmName ?? undefined}>
            {farmName ?? "AgroSphere AI"}
          </div>
          <button
            type="button"
            className="icon-btn"
            onClick={toggleTheme}
            aria-label={theme === "dark" ? t("nav.lightTheme") : t("nav.darkTheme")}
            title={theme === "dark" ? t("nav.lightTheme") : t("nav.darkTheme")}
          >
            <Icon name={theme === "dark" ? "sun" : "moon"} />
          </button>
          <LanguageSwitcher />
        </header>

        {!online && (
          <div className="offline-banner" role="status">
            <strong>{t("offline.title")}</strong> {t("offline.body")}
          </div>
        )}
        {USE_FIXTURES && (
          <div className="fixture-ribbon" role="note">
            {t("common.fixtureMode")}
          </div>
        )}
        <main id="main" ref={mainRef} tabIndex={-1} style={{ outline: "none" }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
