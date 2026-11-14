/**
 * MissingDataPlaceholder — shown when observation data is null/unavailable.
 * Never substitutes zero for a null value.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";

interface Props {
  reason?: string;
  variable?: string;
}

export function MissingDataPlaceholder({ reason, variable }: Props) {
  const { t } = useTranslation();
  return (
    <div
      role="status"
      aria-label={`${variable ? variable + ": " : ""}${t("observations.missingData")}`}
      style={{
        background: "var(--error-bg)",
        border: "1px solid var(--error-border)",
        borderRadius: 6,
        padding: "10px 14px",
        fontSize: 13,
        color: "var(--error-text)",
      }}
    >
      {variable && <strong>{variable}: </strong>}
      {t("observations.missingData")}
      {reason && (
        <div style={{ marginTop: 4, fontSize: 12 }}>
          {t("observations.missingDataReason", { reason })}
        </div>
      )}
    </div>
  );
}

