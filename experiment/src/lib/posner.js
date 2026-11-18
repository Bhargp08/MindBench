import { createRng, shuffle } from "./rng.js";

/**
 * Posner cueing trial list. Design (docs/design/design.md): 120 trials = 96 valid + 24 invalid,
 * target side balanced (60/60), fixation jittered 500-1000 ms. The seed fixes the order.
 * Counts are exact; for odd counts the extra left/right trials are offset so the overall
 * side imbalance never exceeds 1.
 */
export function buildPosnerTrials({ seed = 1, nValid = 96, nInvalid = 24 } = {}) {
  const rng = createRng(seed);
  const validLeft = Math.ceil(nValid / 2);
  const invalidLeft = nValid % 2 === 1 ? Math.floor(nInvalid / 2) : Math.ceil(nInvalid / 2);
  const cells = [];
  for (let i = 0; i < nValid; i++) cells.push({ valid: true, targetSide: i < validLeft ? "left" : "right" });
  for (let i = 0; i < nInvalid; i++) cells.push({ valid: false, targetSide: i < invalidLeft ? "left" : "right" });
  shuffle(cells, rng);
  return cells.map((c, i) => ({
    trial: i + 1,
    valid: c.valid,
    targetSide: c.targetSide,
    cueDirection: c.valid ? c.targetSide : c.targetSide === "left" ? "right" : "left",
    fixationMs: 500 + Math.floor(rng() * 501),
  }));
}

const KEY_SIDE = { f: "left", j: "right" };

/** F = target on the left, J = target on the right. Anything else, or no response, is incorrect. */
export function isCorrectResponse(targetSide, key) {
  if (typeof key !== "string") return false;
  return KEY_SIDE[key.toLowerCase()] === targetSide;
}
