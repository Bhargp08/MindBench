import { createRng, shuffle } from "./rng.js";

/** Fixed-contrast yes/no block: exactly nSignal signal and nNoise noise trials, shuffled by seed. */
export function buildYesNoBlock({ nSignal = 30, nNoise = 30, seed = 1 } = {}) {
  const flags = [...Array(nSignal).fill(true), ...Array(nNoise).fill(false)];
  shuffle(flags, createRng(seed));
  return flags.map((isSignal, i) => ({ trial: i + 1, isSignal }));
}

/** Hit/miss/false-alarm/correct-rejection counts. d' and c are computed in MB-15. */
export function countYesNo(trials) {
  const c = { hits: 0, misses: 0, falseAlarms: 0, correctRejections: 0, nSignal: 0, nNoise: 0 };
  for (const t of trials) {
    if (t.isSignal) {
      c.nSignal++;
      if (t.respondedYes) c.hits++;
      else c.misses++;
    } else {
      c.nNoise++;
      if (t.respondedYes) c.falseAlarms++;
      else c.correctRejections++;
    }
  }
  return c;
}
