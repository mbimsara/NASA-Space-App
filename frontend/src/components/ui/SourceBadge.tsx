/**
 * SourceBadge — dataset provenance: sources, kind, provider, resolution, retrieval date, links.
 * Required on every observation, analysis result, and modeled estimate.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import { formatResolution } from "../../utils/observations";
import type { ObservationSummary } from "../../types/api";

interface Props {
  sourceRefs: string[];
  retrievedAt?: string | null;
  spatialResolution?: ObservationSummary["spatial_resolution"];
  dataKind?: string;
  provider?: string;
  sourceUrl?: string | null;
  documentationUrl?: string;
}

export function SourceBadge({ sourceRefs, retrievedAt, spatialResolution, dataKind, provider, sourceUrl, documentationUrl }: Props) {
  const { t } = useTranslation();
  const resolution = spatialResolution === undefined ? undefined : formatResolution(spatialResolution);

  return (
    <div
      style={{
        fontSize: 12,
        color: "var(--text-muted)",
        background: "var(--surface-alt)",
        border: "1px solid var(--border)",
        borderRadius: 4,
        padding: "6px 10px",
        marginTop: 8,
      }}
    >
      <strong>{t("common.source")}:</strong> {sourceRefs.length > 0 ? sourceRefs.join(", ") : t("common.unknown")}
      {provider && (
        <>
          {" "}
          · <strong>{t("observations.provider")}:</strong> {provider}
        </>
      )}
      {dataKind && (
        <>
          {" "}
          · <strong>{t("observations.kind")}:</strong> {dataKind}
        </>
      )}
      {resolution !== undefined && (
        <>
          {" "}
          · <strong>{t("observations.resolution")}:</strong> {resolution ?? t("observations.resolutionUnknown")}
        </>
      )}
      {retrievedAt !== undefined && (
        <>
          {" "}
          · <strong>{t("observations.retrievedAt")}:</strong> {retrievedAt ?? t("observations.unknownRetrieval")}
        </>
      )}
      {sourceUrl && (
        <>
          {" "}
          ·{" "}
          <a href={sourceUrl} target="_blank" rel="noreferrer">
            {t("observations.sourceLink")}
          </a>
        </>
      )}
      {documentationUrl && (
        <>
          {" "}
          ·{" "}
          <a href={documentationUrl} target="_blank" rel="noreferrer">
            {t("observations.docsLink")}
          </a>
        </>
      )}
    </div>
  );
}
