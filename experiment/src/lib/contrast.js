/** Stimulus level is in dB relative to full (100%) contrast: contrast = 10^(dB/20). */
export const LEVEL_MIN = -40; // 1% contrast
export const LEVEL_MAX = 0; // 100% contrast

export function levelToContrast(levelDb) {
  return 10 ** (levelDb / 20);
}

/**
 * Gabor luminance (0..1, mean 0.5) at pixel offset (x, y) from the patch center.
 * contrast 0..1 scales the sinusoid amplitude; sigma is the Gaussian envelope SD in pixels.
 */
export function gaborLuminance(x, y, { contrast, sigma, cyclesPerPixel, orientation = 0, phase = 0 }) {
  const envelope = Math.exp(-(x * x + y * y) / (2 * sigma * sigma));
  const u = x * Math.cos(orientation) + y * Math.sin(orientation);
  return 0.5 + 0.5 * contrast * envelope * Math.cos(2 * Math.PI * cyclesPerPixel * u + phase);
}
