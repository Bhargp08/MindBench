import { levenshtein } from "./levenshtein.js";

const normalize = (s) => String(s).toLowerCase().trim();
const clean = (s) => normalize(s).replace(/^[^a-z]+|[^a-z]+$/g, "");

/**
 * Score one free-recall list.
 * - Responses are split on whitespace, commas and semicolons, lowercased, and stripped of surrounding punctuation.
 * - An exact match to a list word is correct.
 * - A response that is itself a pool word but not a list word is an intrusion, even if it is one edit from a list
 *   word (so "apply" is wrong when "apple" was shown and "apply" is in the pool).
 * - Otherwise one typo (Levenshtein <= 1) is accepted for list words of 5+ letters; if a response is within one
 *   edit of several list words, the closest wins and ties go to the alphabetically first word.
 * - Each list word is credited at most once; extra responses that match an already credited word are `repeats`.
 * Returns { recalled: boolean[] (by list position), nCorrect, proportion, intrusions, repeats }.
 */
export function scoreRecall({ listWords, recallText, pool }) {
  const list = listWords.map(normalize);
  const poolSet = new Set(pool.map(normalize));
  const recalled = new Array(list.length).fill(false);
  const intrusions = [];
  let repeats = 0;

  const tokens = String(recallText ?? "")
    .split(/[\s,;]+/)
    .map(clean)
    .filter(Boolean);

  const credit = (idx) => {
    if (recalled[idx]) repeats += 1;
    else recalled[idx] = true;
  };
  const intrude = (t) => {
    if (!intrusions.includes(t)) intrusions.push(t);
  };

  const rest = [];
  for (const t of tokens) {
    const idx = list.indexOf(t);
    if (idx >= 0) credit(idx);
    else rest.push(t);
  }
  for (const t of rest) {
    if (poolSet.has(t)) {
      intrude(t);
      continue;
    }
    let best = null;
    list.forEach((w, idx) => {
      if (w.length < 5) return;
      const d = levenshtein(t, w);
      if (d > 1) return;
      if (best === null || d < best.d || (d === best.d && w < list[best.idx])) best = { idx, d };
    });
    if (best) credit(best.idx);
    else intrude(t);
  }

  const nCorrect = recalled.filter(Boolean).length;
  return { recalled, nCorrect, proportion: list.length ? nCorrect / list.length : 0, intrusions, repeats };
}

/** Proportion recalled at each serial position across lists. flagLists: boolean[][] of equal length. */
export function serialPositionCurve(flagLists) {
  if (!flagLists.length) throw new Error("serialPositionCurve needs at least one list");
  const n = flagLists[0].length;
  if (flagLists.some((l) => l.length !== n)) throw new Error("all lists must have the same length");
  return Array.from({ length: n }, (_, p) => flagLists.filter((l) => l[p]).length / flagLists.length);
}

/** P2: correct words over total words across the lists of a session. results: [{ nCorrect, listLength }]. */
export function sessionRecallProportion(results) {
  if (!results.length) throw new Error("sessionRecallProportion needs at least one list");
  const correct = results.reduce((a, r) => a + r.nCorrect, 0);
  const total = results.reduce((a, r) => a + r.listLength, 0);
  return correct / total;
}
