export const TASKS = ["contrast", "posner", "stroop", "nback", "recall"];
export const N_ORDERS = 10;

/**
 * Balanced task orders for an odd number n of items: the Williams-type zigzag row (0, 1, n-1, 2, n-2, ...)
 * cyclically shifted n times, plus the mirror (reverse) of each, giving 2n orders. Every item appears in every
 * position exactly twice and every ordered adjacent pair appears exactly twice. (A plain cyclic square plus its
 * mirror is NOT balanced: it covers only half of the ordered pairs.)
 */
export function buildTaskOrders(items = TASKS) {
  const n = items.length;
  if (n < 3 || n % 2 === 0) throw new Error("buildTaskOrders needs an odd number of items (3 or more)");
  const zigzag = [0];
  let lo = 1;
  let hi = n - 1;
  while (zigzag.length < n) zigzag.push(zigzag.length % 2 === 1 ? lo++ : hi--);
  const cyclic = Array.from({ length: n }, (_, r) => zigzag.map((x) => items[(x + r) % n]));
  return [...cyclic, ...cyclic.map((o) => [...o].reverse())];
}

/**
 * Index (0-9) of the task order for a study session number (1-based). Sessions alternate AM/PM within a day: the
 * AM order is (day - 1) mod 10 and the PM order is offset by 5, so over any 10 days every order occurs once in
 * the AM and once in the PM (an order is never tied to time of day) and the two sessions of a day differ.
 * This follows the session schedule, not the clock; actual time of day is logged separately.
 */
export function orderIndexForSession(sessionNumber) {
  if (!Number.isInteger(sessionNumber) || sessionNumber < 1) throw new Error(`Invalid session number: ${sessionNumber}`);
  const day = Math.ceil(sessionNumber / 2);
  const slot = (sessionNumber - 1) % 2;
  return (day - 1 + (N_ORDERS / 2) * slot) % N_ORDERS;
}

let cached = null;

export function orderForSession(sessionNumber) {
  const idx = orderIndexForSession(sessionNumber);
  cached ??= buildTaskOrders(TASKS);
  return cached[idx];
}
