/**
 * CropTimeline — seasonal timeline for a rotation candidate.
 * Text colour is chosen from the background luminance so every block meets
 * WCAG AA contrast; unknown crop IDs get a stable colour from a small palette.
 * Owner: Shehani.
 */
import { useTranslation } from "react-i18next";
import type { SequenceStep } from "../../types/api";
import { colorFor, textColorFor } from "../../utils/cropColors";

export function CropTimeline({ sequence }: { sequence: SequenceStep[] }) {
  const { t } = useTranslation();
  if (sequence.length === 0) return null;
  const names = sequence.map((s) => s.crop_name ?? s.crop_id).join(" → ");

  return (
    <div role="img" aria-label={t("rotation.timelineLabel", { crops: names })} style={{ display: "flex", gap: 4, margin: "10px 0", flexWrap: "wrap" }}>
      {sequence.map((step) => {
        const bg = colorFor(step.crop_id);
        return (
          <div
            key={step.season_index}
            style={{
              flex: "1 1 70px",
              background: bg,
              color: textColorFor(bg),
              borderRadius: 6,
              padding: "10px 6px",
              textAlign: "center",
              fontWeight: 600,
              fontSize: 13,
            }}
          >
            <div style={{ fontSize: 11 }}>{t("rotation.seasonN", { n: step.season_index })}</div>
            {step.crop_name ?? step.crop_id}
          </div>
        );
      })}
    </div>
  );
}
