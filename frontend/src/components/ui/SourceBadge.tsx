/**
 * SourceBadge — reusable component showing dataset provenance metadata.
 * Required on every observation, analysis result, and modeled estimate.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";

interface Props {
  sourceRefs: string[];
  retrievedAt?: string | null;
  spatialResolution?: string | null;
  dataKind?: string;
}

export function SourceBadge({ sourceRefs, retrievedAt, spatialResolution, dataKind }: Props) {
  const { t } = useTranslation();

  return (
    <div
      style={{
        fontSize: 12,
        color: "#555",
        background: "#f8f9fa",
        border: "1px solid #dee2e6",
        borderRadius: 4,
        padding: "6px 10px",
        marginTop: 8,
      }}
    >
      <strong>{t("common.source")}:</strong>{" "}
      {sourceRefs.length > 0 ? sourceRefs.join(", ") : t("common.unknown")}
      {dataKind && <> · <strong>Kind:</strong> {dataKind}</>}
      {spatialResolution && <> · <strong>{t("observations.resolution")}:</strong> {spatialResolution}</>}
      {retrievedAt !== undefined && (
        <> · <strong>{t("observations.retrievedAt")}:</strong>{" "}
          {retrievedAt ?? t("observations.unknownRetrieval")}</>
      )}
    </div>
  );
}

