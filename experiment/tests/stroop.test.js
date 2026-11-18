import { describe, it, expect } from "vitest";
import { buildStroopTrials, isCorrectStroopResponse, STROOP_COLORS, STROOP_KEYS, NEUTRAL_WORD } from "../src/lib/stroop.js";

const count = (xs, f) => xs.filter(f).length;
const by = (xs, cond) => xs.filter((t) => t.condition === cond);

describe("constants", () => {
  it("has 4 colors and the keys D F J K", () => {
    expect(STROOP_COLORS).toEqual(["red", "green", "blue", "yellow"]);
    expect(STROOP_KEYS).toEqual({ red: "d", green: "f", blue: "j", yellow: "k" });
  });
});

describe("buildStroopTrials: design default (60 congruent + 60 incongruent, no neutral)", () => {
  const trials = buildStroopTrials({ seed: 1 });

  it("has 120 numbered trials with exact condition counts", () => {
    expect(trials).toHaveLength(120);
    expect(trials.map((t) => t.trial)).toEqual(Array.from({ length: 120 }, (_, i) => i + 1));
    expect(by(trials, "congruent")).toHaveLength(60);
    expect(by(trials, "incongruent")).toHaveLength(60);
    expect(by(trials, "neutral")).toHaveLength(0);
  });

  it("congruent trials have word = ink; incongruent trials have word != ink", () => {
    for (const t of by(trials, "congruent")) expect(t.word).toBe(t.ink);
    for (const t of by(trials, "incongruent")) expect(t.word).not.toBe(t.ink);
  });

  it("uses each ink color exactly 15 times per condition (30 overall)", () => {
    for (const cond of ["congruent", "incongruent"]) {
      for (const c of STROOP_COLORS) {
        expect(count(by(trials, cond), (t) => t.ink === c)).toBe(15);
      }
    }
  });

  it("uses each of the 12 incongruent word/ink pairs exactly 5 times", () => {
    const pairs = new Map();
    for (const t of by(trials, "incongruent")) {
      const k = `${t.word}|${t.ink}`;
      pairs.set(k, (pairs.get(k) ?? 0) + 1);
    }
    expect(pairs.size).toBe(12);
    for (const n of pairs.values()) expect(n).toBe(5);
  });

  it("has no immediate repeat of the same word/ink pair across 1,000 seeds", () => {
    for (let seed = 1; seed <= 1000; seed++) {
      const ts = buildStroopTrials({ seed });
      for (let i = 1; i < ts.length; i++) {
        const same = ts[i].word === ts[i - 1].word && ts[i].ink === ts[i - 1].ink;
        expect(same).toBe(false);
      }
    }
  });

  it("is fixed by the seed and differs across seeds", () => {
    expect(buildStroopTrials({ seed: 1 })).toEqual(trials);
    expect(buildStroopTrials({ seed: 2 })).not.toEqual(trials);
  });
});

describe("buildStroopTrials: with neutral trials and uneven sizes", () => {
  it("builds 40 congruent + 40 incongruent + 40 neutral with exact counts and balanced ink", () => {
    const t = buildStroopTrials({ seed: 5, nCongruent: 40, nIncongruent: 40, nNeutral: 40 });
    expect(t).toHaveLength(120);
    expect(by(t, "neutral")).toHaveLength(40);
    for (const n of by(t, "neutral")) expect(n.word).toBe(NEUTRAL_WORD);
    for (const cond of ["congruent", "incongruent", "neutral"]) {
      for (const c of STROOP_COLORS) expect(count(by(t, cond), (x) => x.ink === c)).toBe(10);
    }
  });

  it("keeps each ink color within 1 of equal in a condition when counts do not divide by 4", () => {
    const t = buildStroopTrials({ seed: 3, nCongruent: 10, nIncongruent: 14, nNeutral: 0 });
    for (const cond of ["congruent", "incongruent"]) {
      const counts = STROOP_COLORS.map((c) => count(by(t, cond), (x) => x.ink === c));
      expect(Math.max(...counts) - Math.min(...counts)).toBeLessThanOrEqual(1);
    }
    expect(by(t, "congruent")).toHaveLength(10);
    expect(by(t, "incongruent")).toHaveLength(14);
  });

  it("still has no immediate pair repeats with neutral trials", () => {
    for (let seed = 1; seed <= 200; seed++) {
      const ts = buildStroopTrials({ seed, nCongruent: 40, nIncongruent: 40, nNeutral: 40 });
      for (let i = 1; i < ts.length; i++) {
        expect(ts[i].word === ts[i - 1].word && ts[i].ink === ts[i - 1].ink).toBe(false);
      }
    }
  });
});

describe("isCorrectStroopResponse (respond to the ink color: D red, F green, J blue, K yellow)", () => {
  it("maps keys to ink colors, ignoring case", () => {
    expect(isCorrectStroopResponse("red", "d")).toBe(true);
    expect(isCorrectStroopResponse("green", "F")).toBe(true);
    expect(isCorrectStroopResponse("blue", "j")).toBe(true);
    expect(isCorrectStroopResponse("yellow", "k")).toBe(true);
    expect(isCorrectStroopResponse("red", "f")).toBe(false);
  });

  it("treats no response or other keys as incorrect", () => {
    expect(isCorrectStroopResponse("red", null)).toBe(false);
    expect(isCorrectStroopResponse("red", "x")).toBe(false);
  });
});
