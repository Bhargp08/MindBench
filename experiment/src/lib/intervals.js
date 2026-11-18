import { shuffle } from "./rng.js";

/** Target interval (1 or 2) for each 2IFC trial, balanced and shuffled deterministically. */
export function balancedIntervals(n, rng) {
  const out = Array.from({ length: n }, (_, i) => (i % 2 === 0 ? 1 : 2));
  return shuffle(out, rng);
}
