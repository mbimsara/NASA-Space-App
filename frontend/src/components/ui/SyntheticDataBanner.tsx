/**
 * SyntheticDataBanner — persistent visible badge for synthetic/fixture data.
 * Required on any screen that shows data_kind === "synthetic" or "mixed".
 * Owner: Shehani. Never relabel synthetic data as real NASA data.
 */
import { useTranslation } from "react-i18next";
import type { DataKind } from "../../types/api";

interface Props {
  dataKind: DataKind;
  limitations?: string[];
}

export function SyntheticDataBanner({ dataKind, limitations }: Props) {
  const { t } = useTranslation();

  if (dataKind === "observed") return null;

  const isSynthetic = dataKind === "synthetic";

  return (
    <div
      role="status"
      aria-label={isSynthetic ? t("observations.syntheticBadge") : `Data kind: ${dataKind}`}
      style={{
        background: isSynthetic ? "#fff3cd" : "#cff4fc",
        border: `2px solid ${isSynthetic ? "#ffc107" : "#0dcaf0"}`,
        borderRadius: 6,
        padding: "10px 16px",
        marginBottom: 12,
        fontSize: 14,
        fontWeight: 600,
        color: "#333",
      }}
    >
      {isSynthetic ? t("observations.syntheticBadge") : `Data kind: ${dataKind}`}
      {limitations && limitations.length > 0 && (
        <ul style={{ marginTop: 6, fontWeight: 400, fontSize: 13 }}>
          {limitations.map((l, i) => <li key={i}>{l}</li>)}
        </ul>
      )}
    </div>
  );
}

