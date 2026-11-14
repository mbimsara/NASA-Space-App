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
            🌾 AgroSphere AI
          </Link>
          <Link to="/catalog" className="app-header__link">
            {t("nav.catalog")}
          </Link>
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
