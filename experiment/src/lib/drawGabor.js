import { gaborLuminance } from "./contrast.js";

export const GABOR = { size: 300, sigma: 35, cyclesPerPixel: 0.04, orientation: 0, phase: 0 };

/** Draw a Gabor patch (or mid-grey when contrast is 0) on a canvas. Rendering only; logic is in contrast.js. */
export function drawGabor(canvas, contrast, g = GABOR) {
  const ctx = canvas.getContext("2d");
  const { width, height } = canvas;
  if (contrast <= 0) {
    ctx.fillStyle = "rgb(128,128,128)";
    ctx.fillRect(0, 0, width, height);
    return;
  }
  const img = ctx.createImageData(width, height);
  for (let py = 0; py < height; py++) {
    for (let px = 0; px < width; px++) {
      const v = Math.round(255 * gaborLuminance(px - width / 2, py - height / 2, { ...g, contrast }));
      const i = (py * width + px) * 4;
      img.data[i] = img.data[i + 1] = img.data[i + 2] = v;
      img.data[i + 3] = 255;
    }
  }
  ctx.putImageData(img, 0, 0);
}
