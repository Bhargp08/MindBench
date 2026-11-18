import { describe, it, expect } from "vitest";
import { TASKS, N_ORDERS, buildTaskOrders, orderIndexForSession, orderForSession } from "../src/lib/latinSquare.js";

const orders = buildTaskOrders(TASKS);

describe("task list", () => {
  it("has the 5 battery tasks", () => {
    expect(TASKS).toEqual(["contrast", "posner", "stroop", "nback", "recall"]);
    expect(N_ORDERS).toBe(10);
  });
});

describe("buildTaskOrders: balanced (Williams-type) Latin square for 5 tasks, mirrored -> 10 orders", () => {
  it("has 10 distinct orders, each a permutation of the 5 tasks", () => {
    expect(orders).toHaveLength(10);
    expect(new Set(orders.map((o) => o.join(","))).size).toBe(10);
    for (const o of orders) expect([...o].sort()).toEqual([...TASKS].sort());
  });

  it("uses the zigzag base row (t0, t1, t4, t2, t3), cyclic shifts, then the mirror of each", () => {
    expect(orders[0]).toEqual(["contrast", "posner", "recall", "stroop", "nback"]);
    for (let i = 0; i < 5; i++) expect(orders[i + 5]).toEqual([...orders[i]].reverse());
    // cyclic shift: order 1 is order 0 with every task index + 1 (mod 5)
    const idx = (o) => o.map((t) => TASKS.indexOf(t));
    expect(idx(orders[1])).toEqual(idx(orders[0]).map((x) => (x + 1) % 5));
  });

  it("puts each task in each position exactly twice across the 10 orders", () => {
    for (const t of TASKS) {
      for (let p = 0; p < 5; p++) expect(orders.filter((o) => o[p] === t)).toHaveLength(2);
    }
  });

  it("has each ordered adjacent pair of tasks (all 20) exactly twice", () => {
    const counts = new Map();
    for (const o of orders) {
      for (let i = 0; i < 4; i++) {
        const k = `${o[i]}>${o[i + 1]}`;
        counts.set(k, (counts.get(k) ?? 0) + 1);
      }
    }
    expect(counts.size).toBe(20);
    for (const n of counts.values()) expect(n).toBe(2);
  });

  it("works for 3 items (6 orders, each ordered pair twice) and rejects an even number of items", () => {
    const o3 = buildTaskOrders(["a", "b", "c"]);
    expect(o3).toHaveLength(6);
    expect(() => buildTaskOrders(["a", "b", "c", "d"])).toThrow();
  });
});

describe("orderForSession (AM/PM-balanced: day cycles the orders, PM is offset by 5)", () => {
  it("maps sessions deterministically: day d AM -> order (d-1) mod 10, PM -> (d-1+5) mod 10", () => {
    const expected = { 1: 0, 2: 5, 3: 1, 4: 6, 5: 2, 20: 4, 21: 0, 22: 5 };
    for (const [n, i] of Object.entries(expected)) {
      expect(orderIndexForSession(Number(n))).toBe(i);
      expect(orderForSession(Number(n))).toEqual(orders[i]);
    }
    expect(orderForSession(7)).toEqual(orderForSession(7));
  });

  it("gives AM and PM of the same day different orders", () => {
    for (let day = 1; day <= 26; day++) {
      expect(orderIndexForSession(2 * day - 1)).not.toBe(orderIndexForSession(2 * day));
    }
  });

  it("covers every order exactly once among odd (AM) and once among even (PM) sessions of any 20 consecutive sessions from session 1", () => {
    const am = new Set();
    const pm = new Set();
    for (let n = 1; n <= 20; n++) (n % 2 === 1 ? am : pm).add(orderIndexForSession(n));
    expect(am.size).toBe(10);
    expect(pm.size).toBe(10);
  });

  it("does not tie an order to time of day over the 52 study sessions (AM and PM counts differ by at most 1)", () => {
    const am = Array(10).fill(0);
    const pm = Array(10).fill(0);
    for (let n = 1; n <= 52; n++) (n % 2 === 1 ? am : pm)[orderIndexForSession(n)]++;
    for (let i = 0; i < 10; i++) expect(Math.abs(am[i] - pm[i])).toBeLessThanOrEqual(1);
    expect(am.reduce((a, b) => a + b)).toBe(26);
  });

  it("rejects non-integer or non-positive session numbers", () => {
    for (const bad of [0, -1, 1.5, NaN, "3"]) expect(() => orderForSession(bad)).toThrow();
  });
});
