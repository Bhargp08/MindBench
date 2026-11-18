import { describe, it, expect } from "vitest";
import pool from "../src/data/wordpool.json";
import {
  buildRecallAssignments,
  getSessionLists,
  RECALL_ASSIGNMENT_SEED,
  N_SESSIONS,
  SMOKE_TEST_SESSIONS,
  CONFIRMATORY_SESSIONS,
  PLANNED_SESSIONS,
} from "../src/lib/recallLists.js";

const flat = (assignments) => assignments.flatMap((session) => session.flatMap((list) => list));

describe("buildRecallAssignments (52 session slots x 2 lists x 20 words; the study uses 44 of them)", () => {
  const a = buildRecallAssignments({ pool: pool.words, seed: 1 });

  it("has 52 session slots of 2 lists of 20 words; the study plans 44 (42 confirmatory + 2 smoke tests)", () => {
    expect(N_SESSIONS).toBe(52);
    expect(SMOKE_TEST_SESSIONS).toBe(2);
    expect(CONFIRMATORY_SESSIONS).toBe(42);
    expect(PLANNED_SESSIONS).toBe(44);
    expect(a).toHaveLength(52);
    for (const session of a) {
      expect(session).toHaveLength(2);
      for (const list of session) expect(list).toHaveLength(20);
    }
  });

  it("never reuses a word or a list: all 2,080 words appear exactly once across the 52 slots", () => {
    const words = flat(a);
    expect(words).toHaveLength(2080);
    expect(new Set(words).size).toBe(2080);
    expect(new Set(words)).toEqual(new Set(pool.words));
  });

  it("needs only 42 sessions x 40 words = 1,680 words for the confirmatory sessions (3-44), disjoint from the smoke tests (1-2)", () => {
    const smoke = new Set(flat(a.slice(0, SMOKE_TEST_SESSIONS)));
    const confirmatory = flat(a.slice(SMOKE_TEST_SESSIONS, PLANNED_SESSIONS));
    expect(smoke.size).toBe(80);
    expect(confirmatory).toHaveLength(1680);
    expect(new Set(confirmatory).size).toBe(1680);
    for (const w of confirmatory) expect(smoke.has(w)).toBe(false);
  });

  it("leaves 320 spare words (session slots 45-52) disjoint from the 44 planned sessions", () => {
    const planned = new Set(flat(a.slice(0, PLANNED_SESSIONS)));
    const spare = flat(a.slice(PLANNED_SESSIONS));
    expect(planned.size).toBe(1760);
    expect(spare).toHaveLength(320);
    for (const w of spare) expect(planned.has(w)).toBe(false);
  });

  it("matches word length across lists: every list has 5 words of each length 5, 6, 7 and 8", () => {
    for (const session of a) {
      for (const list of session) {
        for (const n of [5, 6, 7, 8]) expect(list.filter((w) => w.length === n)).toHaveLength(5);
      }
    }
  });

  it("is deterministic for a seed and differs across seeds", () => {
    expect(buildRecallAssignments({ pool: pool.words, seed: 1 })).toEqual(a);
    expect(buildRecallAssignments({ pool: pool.words, seed: 2 })).not.toEqual(a);
  });
});

describe("buildRecallAssignments: other sizes and errors", () => {
  const small = ["alpha", "bravo", "cargo", "delta", "eagle", "flute", "grape", "hotel"];

  it("builds a small design without reuse", () => {
    const a = buildRecallAssignments({ pool: small, seed: 3, nSessions: 2, listsPerSession: 2, listLength: 2 });
    expect(a).toHaveLength(2);
    const words = flat(a);
    expect(words).toHaveLength(8);
    expect(new Set(words).size).toBe(8);
  });

  it("throws when the pool is too small to avoid reuse", () => {
    expect(() => buildRecallAssignments({ pool: small, seed: 1, nSessions: 5, listsPerSession: 2, listLength: 2 })).toThrow();
  });

  it("throws on duplicate words in the pool", () => {
    expect(() => buildRecallAssignments({ pool: ["alpha", "alpha", "bravo", "cargo"], seed: 1, nSessions: 1, listsPerSession: 2, listLength: 2 })).toThrow();
  });
});

describe("getSessionLists (study-wide fixed assignment)", () => {
  it("returns the same 2 lists of 20 words for a session on every call", () => {
    const first = getSessionLists(7);
    expect(first).toHaveLength(2);
    for (const list of first) expect(list).toHaveLength(20);
    expect(getSessionLists(7)).toEqual(first);
  });

  it("uses the fixed study seed and the shipped pool", () => {
    const expected = buildRecallAssignments({ pool: pool.words, seed: RECALL_ASSIGNMENT_SEED });
    expect(getSessionLists(1)).toEqual(expected[0]);
    expect(getSessionLists(52)).toEqual(expected[51]);
  });

  it("rejects session numbers outside 1-52 (no list reuse)", () => {
    for (const bad of [0, 53, -1, 1.5, NaN]) expect(() => getSessionLists(bad)).toThrow();
  });
});
