import { createRng, shuffle } from "./rng.js";
import { dPrimeFromCounts } from "./sdt.js";

export const CONSONANTS = "BCDFGHJKLMNPQRSTVWXZ";

/** Type of the letter at 0-based index i, from the letter sequence alone (2-back task). */
export function classifyNBack(letters, i) {
  if (i < 2) return "start"; // positions 1-2 are never targets or lures
  if (letters[i] === letters[i - 2]) return "target";
  if (letters[i] === letters[i - 1]) return "lure1"; // 1-back match
  if (i >= 3 && letters[i] === letters[i - 3]) return "lure3"; // 3-back match
  return "nontarget";
}

/**
 * 2-back letter sequence. Design defaults (docs/design/design.md): 60 trials, 18 targets (30%), 3 one-back
 * and 3 three-back lures, none in positions 1-2, consonants only. Counts are exact and every label agrees
 * with the letters (no accidental matches). The seed fixes the sequence.
 */
export function buildNBackSequence({ seed = 1, nTrials = 60, nTargets = 18, nLureOne = 3, nLureThree = 3 } = {}) {
  const slots = [];
  for (let i = 2; i < nTrials; i++) slots.push(i);
  if (nTargets + nLureOne + nLureThree > slots.length) {
    throw new Error("Too many targets and lures for the sequence length (none allowed in positions 1-2)");
  }
  const rng = createRng(seed);
  const pick = (pool) => pool[Math.floor(rng() * pool.length)];

  for (let attempt = 0; attempt < 1000; attempt++) {
    const order = shuffle([...slots], rng);
    const lure3 = order.filter((i) => i >= 3).slice(0, nLureThree);
    const rest = order.filter((i) => !lure3.includes(i));
    const wanted = new Array(nTrials).fill("nontarget");
    wanted[0] = wanted[1] = "start";
    lure3.forEach((i) => (wanted[i] = "lure3"));
    rest.slice(0, nTargets).forEach((i) => (wanted[i] = "target"));
    rest.slice(nTargets, nTargets + nLureOne).forEach((i) => (wanted[i] = "lure1"));
    if (lure3.length < nLureThree) continue;

    const letters = [];
    let ok = true;
    for (let i = 0; i < nTrials && ok; i++) {
      const recent = [letters[i - 1], letters[i - 2], letters[i - 3]];
      let letter;
      if (wanted[i] === "target") letter = letters[i - 2];
      else if (wanted[i] === "lure1") letter = letters[i - 1];
      else if (wanted[i] === "lure3") letter = letters[i - 3];
      else letter = pick([...CONSONANTS].filter((c) => !recent.includes(c)));
      letters.push(letter);
      if (classifyNBack(letters, i) !== wanted[i]) ok = false;
    }
    if (ok) return letters.map((letter, i) => ({ trial: i + 1, letter, type: wanted[i], isTarget: wanted[i] === "target" }));
  }
  throw new Error("Could not build a 2-back sequence with the requested counts");
}

/**
 * Score a 2-back session. trials: [{ position (1-based), type, responded }]. Positions 1-2 are not scored.
 * Lures count as non-targets (a response to a lure is a false alarm). d' and c use the log-linear correction.
 */
export function scoreNBack(trials) {
  const scored = trials.filter((t) => t.position >= 3);
  const targets = scored.filter((t) => t.type === "target");
  const nonTargets = scored.filter((t) => t.type !== "target");
  const hits = targets.filter((t) => t.responded).length;
  const falseAlarms = nonTargets.filter((t) => t.responded).length;
  const sdt = dPrimeFromCounts({ hits, nSignal: targets.length, falseAlarms, nNoise: nonTargets.length });
  return {
    nTargets: targets.length,
    nNonTargets: nonTargets.length,
    hits,
    misses: targets.length - hits,
    falseAlarms,
    correctRejections: nonTargets.length - falseAlarms,
    lureFalseAlarms: nonTargets.filter((t) => t.responded && (t.type === "lure1" || t.type === "lure3")).length,
    hitRate: sdt.hitRate,
    falseAlarmRate: sdt.falseAlarmRate,
    dPrime: sdt.dPrime,
    criterion: sdt.criterion,
  };
}
