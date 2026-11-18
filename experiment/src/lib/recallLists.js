import pool from "../data/wordpool.json";
import { createRng, shuffle } from "./rng.js";

export const N_SESSIONS = 52; // 10 pilot + 42 confirmatory
export const PILOT_SESSIONS = 10;
export const LISTS_PER_SESSION = 2;
export const LIST_LENGTH = 20;
export const RECALL_ASSIGNMENT_SEED = 20261117; // fixed for the whole study so every device gets the same lists

/**
 * Assign words to lists with no reuse: every word appears at most once across all sessions (all 2,080 pool words
 * are used exactly once in the full design). Lists are balanced on word length (equal counts per length, within 1),
 * and the words inside each list are shuffled for presentation. Returns lists grouped by session.
 */
export function buildRecallAssignments({
  pool: words,
  seed = 1,
  nSessions = N_SESSIONS,
  listsPerSession = LISTS_PER_SESSION,
  listLength = LIST_LENGTH,
} = {}) {
  if (new Set(words).size !== words.length) throw new Error("Word pool contains duplicate words");
  const nLists = nSessions * listsPerSession;
  const need = nLists * listLength;
  if (words.length < need) throw new Error(`Pool has ${words.length} words but ${need} are needed without reuse`);

  const rng = createRng(seed);
  const lengths = [...new Set(words.map((w) => w.length))].sort((a, b) => a - b);
  const buckets = lengths.map((n) => shuffle(words.filter((w) => w.length === n), rng));

  // Select `need` words taking from the length buckets in turn, so lengths stay balanced.
  const chosen = lengths.map(() => []);
  for (let taken = 0, b = 0; taken < need; b = (b + 1) % buckets.length) {
    const w = buckets[b].pop();
    if (w !== undefined) {
      chosen[b].push(w);
      taken += 1;
    }
  }

  // Deal each length bucket round-robin over the lists, continuing the pointer across buckets.
  const lists = Array.from({ length: nLists }, () => []);
  let p = 0;
  for (const bucket of chosen) for (const w of bucket) lists[p++ % nLists].push(w);
  lists.forEach((l) => shuffle(l, rng));

  return Array.from({ length: nSessions }, (_, s) => lists.slice(s * listsPerSession, (s + 1) * listsPerSession));
}

let cached = null;

/** The two lists for a study session number (1-52). Throws outside that range, since lists would have to be reused. */
export function getSessionLists(sessionNumber) {
  if (!Number.isInteger(sessionNumber) || sessionNumber < 1 || sessionNumber > N_SESSIONS) {
    throw new Error(`Session ${sessionNumber} is outside 1-${N_SESSIONS}; no unused word lists remain`);
  }
  cached ??= buildRecallAssignments({ pool: pool.words, seed: RECALL_ASSIGNMENT_SEED });
  return cached[sessionNumber - 1];
}
