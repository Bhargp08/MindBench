import { createRng, shuffle } from "./rng.js";

export const STROOP_COLORS = ["red", "green", "blue", "yellow"];
export const STROOP_KEYS = { red: "d", green: "f", blue: "j", yellow: "k" };
export const STROOP_HEX = { red: "#d62728", green: "#2ca02c", blue: "#1f77b4", yellow: "#e6b800" };
export const NEUTRAL_WORD = "XXXX";

/** n ink colors, each used floor(n/4) times, with the remainder spread over colors in a seeded order. */
function balancedInks(n, rng) {
  const base = Math.floor(n / STROOP_COLORS.length);
  const inks = STROOP_COLORS.flatMap((c) => Array(base).fill(c));
  const extra = shuffle([...STROOP_COLORS], rng).slice(0, n - inks.length);
  return [...inks, ...extra];
}

const samePair = (a, b) => a.word === b.word && a.ink === b.ink;

function conflictsAt(items, k) {
  return (k > 0 && samePair(items[k], items[k - 1])) || (k < items.length - 1 && samePair(items[k], items[k + 1]));
}

/** Remove immediate repeats of the same word/ink pair by swapping with a later item. Returns true if clean. */
function repairRepeats(items) {
  for (let i = 1; i < items.length; i++) {
    if (!samePair(items[i], items[i - 1])) continue;
    let fixed = false;
    for (let j = i + 1; j < items.length && !fixed; j++) {
      [items[i], items[j]] = [items[j], items[i]];
      if (!conflictsAt(items, i) && !conflictsAt(items, j)) fixed = true;
      else [items[i], items[j]] = [items[j], items[i]];
    }
    if (!fixed) return false;
  }
  return items.every((_, k) => k === 0 || !samePair(items[k], items[k - 1]));
}

/**
 * Stroop trial list. Design default (docs/design/design.md): 60 congruent + 60 incongruent, no neutral.
 * Neutral trials (word "XXXX") are supported but off by default. Ink colors are balanced within each
 * condition (within 1 when the count does not divide by 4); incongruent words are spread evenly
 * over the other three colors; no word/ink pair repeats on consecutive trials. The seed fixes the order.
 */
export function buildStroopTrials({ seed = 1, nCongruent = 60, nIncongruent = 60, nNeutral = 0 } = {}) {
  const rng = createRng(seed);
  const cells = [];
  for (const ink of balancedInks(nCongruent, rng)) cells.push({ condition: "congruent", word: ink, ink });
  const incInks = balancedInks(nIncongruent, rng);
  for (const ink of STROOP_COLORS) {
    const others = STROOP_COLORS.filter((c) => c !== ink);
    const start = Math.floor(rng() * 3);
    let k = 0;
    for (const x of incInks) {
      if (x !== ink) continue;
      cells.push({ condition: "incongruent", word: others[(start + k++) % 3], ink });
    }
  }
  for (const ink of balancedInks(nNeutral, rng)) cells.push({ condition: "neutral", word: NEUTRAL_WORD, ink });

  let items = null;
  for (let attempt = 0; attempt < 200; attempt++) {
    const candidate = shuffle([...cells], rng);
    if (repairRepeats(candidate)) {
      items = candidate;
      break;
    }
  }
  if (!items) {
    throw new Error("Could not build a Stroop sequence without consecutive word/ink repeats");
  }
  return items.map((c, i) => ({ trial: i + 1, ...c }));
}

/** Respond to the ink color: D red, F green, J blue, K yellow. Anything else (or no response) is incorrect. */
export function isCorrectStroopResponse(ink, key) {
  return typeof key === "string" && STROOP_KEYS[ink] === key.toLowerCase();
}
