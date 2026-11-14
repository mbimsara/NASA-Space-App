/**
 * OutdatedAnalysisBanner — shown when selected analysis input_version ≠ current farm input_version.
 * Prevents saving an outdated result as the current selection.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";

interface Props {
  isOutdated: boolean;
  onRerun?: () => void;
}

export function OutdatedAnalysisBanner({ isOutdated, onRerun }: Props) {
  const { t } = useTranslation();
  if (!isOutdated) return null;

  return (
    <div
      role="alert"
      style={{
        background: "#fff3cd",
        border: "2px solid #ffc107",
        borderRadius: 6,
        padding: "10px 16px",
        marginBottom: 12,
        color: "#856404",
        fontSize: 14,
        display: "flex",
        alignItems: "center",
        gap: 12,
        justifyContent: "space-between",
      }}
    >
      <span>⚠ {t("rotation.outdatedBanner")}</span>
      {onRerun && (
        <button
          onClick={onRerun}
          style={{ padding: "4px 12px", cursor: "pointer", background: "#ffc107", border: "none", borderRadius: 4, fontWeight: 600 }}
        >
          {t("rotation.rerun")}
        </button>
      )}
    </div>
  );
}

