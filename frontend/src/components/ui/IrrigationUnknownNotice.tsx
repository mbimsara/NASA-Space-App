/**
 * IrrigationUnknownNotice — explains why water results are "Unknown" when the
 * farm's irrigation is unknown (null), and links to fix it. Unknown is not zero:
 * rainfed farms should choose "Rainfed — no irrigation" instead.
 * Owner: Shehani. Rule: Bhagya (ROTATION_SCORING_SPEC.md, API_CONTRACTS.md).
 */
import { Link } from "react-router-dom";
import { useTranslation } from "react-i18next";

export function IrrigationUnknownNotice({ farmId, irrigation }: { farmId: string; irrigation: number | null }) {
  const { t } = useTranslation();
  if (irrigation !== null) return null;
  return (
    <div className="notice notice-warn" role="note">
      <strong>{t("irrigationNotice.title")}</strong> {t("irrigationNotice.body")}{" "}
      <Link to={`/farms/${farmId}/edit`}>{t("irrigationNotice.action")}</Link>
    </div>
  );
}
