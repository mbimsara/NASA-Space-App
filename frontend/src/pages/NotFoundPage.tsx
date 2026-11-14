import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function NotFoundPage() {
  const { t } = useTranslation();
  return (
    <div className="page">
      <h1>{t("errors.NOT_FOUND")}</h1>
      <Link to="/">{t("nav.home")}</Link>
    </div>
  );
}
