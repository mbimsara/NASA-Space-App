/**
 * AppShell — header, language switcher, fixture ribbon and page outlet.
 * Owner: Shehani. Visual design pending Tharuka's component handoff.
 */
import { useEffect } from "react";
import { Link, Outlet } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { LanguageSwitcher } from "../ui/LanguageSwitcher";
import { USE_FIXTURES } from "../../api";

export function AppShell() {
  const { t, i18n } = useTranslation();

  useEffect(() => {
    document.documentElement.lang = i18n.language;
  }, [i18n.language]);

  return (
    <>
      <a className="skip-link" href="#main">
        {t("nav.skipToContent")}
      </a>
      <header className="app-header">
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
          <nav className="app-header__nav" aria-label={t("nav.home")}>
            <Link to="/" className="app-header__link">{t("nav.home")}</Link>
            <Link to="/farms/new" className="app-header__link">{t("nav.newFarm")}</Link>
            <Link to="/catalog" className="app-header__link">{t("nav.catalog")}</Link>
          </nav>
          <LanguageSwitcher />
        </div>
      </header>
      {USE_FIXTURES && (
        <div className="fixture-ribbon" role="note">
          {t("common.fixtureMode")}
        </div>
      )}
      <main id="main" tabIndex={-1}>
        <Outlet />
      </main>
    </>
  );
}
