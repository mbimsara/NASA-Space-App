/**
 * AppShell — Tharuka's layout: dark sidebar, sticky top bar (menu, current farm,
 * theme, language), fixture/offline banners, and the page outlet.
 * Owner: Shehani. Design: Tharuka.
 */
import { useEffect, useRef, useState } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "../ui/LanguageSwitcher";
import { Icon } from "../ui/Icon";
import { Sidebar } from "./Sidebar";
import { USE_FIXTURES } from "../../api";
import { useOnlineStatus } from "../../hooks/useOnlineStatus";
import { useTheme } from "../../hooks/useTheme";
import { useAppStore } from "../../hooks/useAppStore";
import "./AppShell.css";

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
      <div>
        <a className="skip-link" href="#main">{t("nav.skipToContent")}</a>
        {!online && (
          <div className="offline-banner" role="status">
            <strong>{t("offline.title")}</strong> {t("offline.body")}
          </div>
        )}
        <main id="main" className="landing-main" ref={mainRef} tabIndex={-1} style={{ outline: "none" }}>
          <Outlet />
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell" data-theme={theme}>
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
          <div className="search">
            <Icon name="overview" />
            <input
              type="search"
              aria-label={t("nav.search")}
              placeholder={t("nav.search")}
            />
          </div>
          <div className="top-actions">
            <a href="https://www.spaceappschallenge.org/" target="_blank" rel="noopener noreferrer" className="spaceapps-topbar-badge" title="Built for NASA Space Apps Challenge 2026">
              <img src="/images/nasa-space-apps-logo.png" alt="NASA Space Apps Challenge" className="spaceapps-topbar-logo" />
              <span className="spaceapps-topbar-text">Built for <strong>NASA Space Apps 2026</strong></span>
              <span className="spaceapps-topbar-ext"><Icon name="external" /></span>
            </a>
            <span className="data-state"><i /> {USE_FIXTURES ? t("nav.modeFixtures") : t("nav.modeLive")}</span>
            {farmName && <span className="topbar-title" title={farmName}>{farmName}</span>}
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
          </div>
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
        <main id="main" className="workspace" ref={mainRef} tabIndex={-1} style={{ outline: "none" }}>
          <Outlet />
        </main>
      </div>
    </div>
  );
}
