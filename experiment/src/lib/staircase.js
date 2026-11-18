import { LEVEL_MAX, LEVEL_MIN, levelToContrast } from "./contrast.js";

/** Mean of the last `lastN` reversal levels, or null if there are fewer than `lastN`. */
export function thresholdFromReversals(reversals, lastN = 6) {
  if (reversals.length < lastN) return null;
  const tail = reversals.slice(-lastN);
  return tail.reduce((a, b) => a + b, 0) / tail.length;
}

/**
 * Transformed up-down staircase (Levitt 1971). Higher level = more contrast = easier.
 * 1-up/N-down: N correct in a row lowers the level; one error raises it.
 * 1-up/2-down converges to 70.7% correct, 1-up/3-down to 79.4%.
 * Reversal: a move in the opposite direction to the previous move; the recorded level is the
 * level at which the response was given. The step is `stepInitial` until `stepChangeAfter`
 * reversals have occurred (the move causing that reversal still uses the initial step),
 * then `stepFinal`.
 */
export function createStaircase({
  start = -10,
  min = LEVEL_MIN,
  max = LEVEL_MAX,
  down = 2,
  stepInitial = 3,
  stepFinal = 1.5,
  stepChangeAfter = 2,
  stopReversals = 10,
  maxTrials = 60,
} = {}) {
  if (down !== 2 && down !== 3) throw new Error("down must be 2 or 3");
  let level = Math.min(max, Math.max(min, start));
  let run = 0;
  let lastDir = 0;
  const reversals = [];
  const history = [];

  return {
    get level() {
      return level;
    },
    get reversals() {
      return reversals;
    },
    get history() {
      return history;
    },
    get trialCount() {
      return history.length;
    },
    get done() {
      return reversals.length >= stopReversals || history.length >= maxTrials;
    },
    threshold(lastN = 6) {
      return thresholdFromReversals(reversals, lastN);
    },
    respond(correct) {
      history.push({ trial: history.length + 1, level, contrast: levelToContrast(level), correct: !!correct });
      let dir = 0;
      if (correct) {
        run += 1;
        if (run >= down) {
          dir = -1;
          run = 0;
        }
      } else {
        run = 0;
        dir = 1;
      }
      if (dir === 0) return;
      if (lastDir !== 0 && dir !== lastDir) reversals.push(level);
      const step = reversals.length - (lastDir !== 0 && dir !== lastDir ? 1 : 0) < stepChangeAfter ? stepInitial : stepFinal;
      level = Math.min(max, Math.max(min, level + dir * step));
      lastDir = dir;
    },
  };
}
