/**
 * LoadingSpinner — simple loading state component.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";

interface Props {
  label?: string;
}

export function LoadingSpinner({ label }: Props) {
  const { t } = useTranslation();
  return (
    <div role="status" aria-label={label ?? t("common.loading")} style={{ padding: 24, textAlign: "center", color: "var(--text-muted)" }}>
      <span aria-hidden="true" style={{ fontSize: 24 }}>⏳</span>
      <div style={{ marginTop: 8, fontSize: 14 }}>{label ?? t("common.loading")}</div>
    </div>
  );
}

