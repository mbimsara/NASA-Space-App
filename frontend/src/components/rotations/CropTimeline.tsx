/**
 * CropTimeline — visual seasonal timeline for a rotation candidate.
 * Shows each season's crop as a colored segment.
 * Owner: Shehani.
 */
import type { SequenceStep } from "../../types/api";

// Deterministic color per crop family/id
const CROP_COLORS: Record<string, string> = {
  rice: "#4CAF50",
  cowpea: "#8BC34A",
  maize: "#FFC107",
  groundnut: "#FF9800",
  soybean: "#9C27B0",
  vegetables: "#00BCD4",
  default: "#607D8B",
};

function colorFor(cropId: string): string {
  return CROP_COLORS[cropId] ?? CROP_COLORS.default;
}

interface Props {
  sequence: SequenceStep[];
}

export function CropTimeline({ sequence }: Props) {
  if (sequence.length === 0) return null;

  return (
    <div
      role="img"
      aria-label={`Crop rotation: ${sequence.map((s) => s.crop_name ?? s.crop_id).join(" → ")}`}
      style={{ display: "flex", gap: 4, margin: "10px 0" }}
    >
      {sequence.map((step) => (
        <div
          key={step.season_index}
          style={{
            flex: 1,
            background: colorFor(step.crop_id),
            borderRadius: 6,
            padding: "10px 6px",
            textAlign: "center",
            color: "#fff",
            fontWeight: 600,
            fontSize: 13,
            minWidth: 70,
          }}
        >
          <div style={{ fontSize: 11, opacity: 0.85 }}>Season {step.season_index}</div>
          {step.crop_name ?? step.crop_id}
        </div>
      ))}
    </div>
  );
}

