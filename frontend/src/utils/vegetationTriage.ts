export interface VegetationTriageResult {
  width: number;
  height: number;
  valid_pixels: number;
  vegetation_pixels: number;
  vegetation_cover_percent: number;
  method: "transparent-green-pixel-heuristic-0.1";
}

/**
 * Transparent phone-photo triage, not a trained classifier. A pixel is counted
 * as vegetation-like when green clearly exceeds red/blue and has useful colour
 * contrast. This cannot distinguish crop, weed, residue, shadow, or species.
 */
export function vegetationCoverFromRgba(data: Uint8ClampedArray, width: number, height: number): VegetationTriageResult {
  if (width <= 0 || height <= 0 || data.length !== width * height * 4) throw new Error("Invalid RGBA image buffer.");
  let valid = 0;
  let green = 0;
  for (let index = 0; index < data.length; index += 4) {
    const [r, g, b, alpha] = [data[index], data[index + 1], data[index + 2], data[index + 3]];
    if (alpha < 128) continue;
    valid += 1;
    const contrast = Math.max(r, g, b) - Math.min(r, g, b);
    if (g >= 40 && contrast >= 20 && g > r * 1.08 && g > b * 1.08) green += 1;
  }
  return {
    width,
    height,
    valid_pixels: valid,
    vegetation_pixels: green,
    vegetation_cover_percent: valid ? Math.round((green / valid) * 1000) / 10 : 0,
    method: "transparent-green-pixel-heuristic-0.1",
  };
}

export async function analyzeVegetationPhoto(file: File): Promise<VegetationTriageResult> {
  const bitmap = await createImageBitmap(file);
  try {
    const scale = Math.min(1, 900 / Math.max(bitmap.width, bitmap.height));
    const width = Math.max(1, Math.round(bitmap.width * scale));
    const height = Math.max(1, Math.round(bitmap.height * scale));
    const canvas = document.createElement("canvas");
    canvas.width = width;
    canvas.height = height;
    const context = canvas.getContext("2d", { willReadFrequently: true });
    if (!context) throw new Error("This browser cannot read the selected image.");
    context.drawImage(bitmap, 0, 0, width, height);
    return vegetationCoverFromRgba(context.getImageData(0, 0, width, height).data, width, height);
  } finally {
    bitmap.close();
  }
}
