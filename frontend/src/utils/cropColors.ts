/**
 * Crop timeline colours with WCAG AA text contrast. Owner: Shehani.
 */
const CROP_COLORS: Record<string, string> = {
  rice: "#2e7d32",
  cowpea: "#9ccc65",
  maize: "#ffca28",
  groundnut: "#ef6c00",
  soybean: "#7b1fa2",
  vegetables: "#00838f",
};
const PALETTE = ["#1565c0", "#6d4c41", "#ad1457", "#558b2f", "#00695c", "#f9a825", "#4527a0", "#c62828"];

export function colorFor(cropId: string): string {
  if (CROP_COLORS[cropId]) return CROP_COLORS[cropId];
  let h = 0;
  for (const ch of cropId) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTE[h % PALETTE.length];
}

/** Relative luminance (WCAG). */
function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/** Black or white, whichever has the higher contrast ratio against `bg`. */
export function textColorFor(bg: string): "#000000" | "#ffffff" {
  const L = luminance(bg);
  return (L + 0.05) / 0.05 >= 1.05 / (L + 0.05) ? "#000000" : "#ffffff";
}
