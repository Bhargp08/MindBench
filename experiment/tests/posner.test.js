import { describe, it, expect } from "vitest";
import { buildPosnerTrials, isCorrectResponse } from "../src/lib/posner.js";

const count = (xs, f) => xs.filter(f).length;

describe("buildPosnerTrials (80/20 validity, design defaults)", () => {
  const trials = buildPosnerTrials({ seed: 1 });

  it("has 120 numbered trials: exactly 96 valid and 24 invalid", () => {
    expect(trials).toHaveLength(120);
    expect(trials.map((t) => t.trial)).toEqual(Array.from({ length: 120 }, (_, i) => i + 1));
    expect(count(trials, (t) => t.valid)).toBe(96);
    expect(count(trials, (t) => !t.valid)).toBe(24);
  });

  it("balances target side 60/60 overall and within each validity condition", () => {
    expect(count(trials, (t) => t.targetSide === "left")).toBe(60);
    expect(count(trials, (t) => t.targetSide === "right")).toBe(60);
    expect(count(trials, (t) => t.valid && t.targetSide === "left")).toBe(48);
    expect(count(trials, (t) => !t.valid && t.targetSide === "left")).toBe(12);
  });

  it("points the cue at the target when valid and away from it when invalid", () => {
    for (const t of trials) {
      const opposite = t.targetSide === "left" ? "right" : "left";
      expect(t.cueDirection).toBe(t.valid ? t.targetSide : opposite);
    }
  });

  it("uses integer fixation durations from 500 to 1000 ms", () => {
    for (const t of trials) {
      expect(Number.isInteger(t.fixationMs)).toBe(true);
      expect(t.fixationMs).toBeGreaterThanOrEqual(500);
      expect(t.fixationMs).toBeLessThanOrEqual(1000);
    }
  });

  it("is fixed by the seed and differs across seeds", () => {
    expect(buildPosnerTrials({ seed: 1 })).toEqual(trials);
    expect(buildPosnerTrials({ seed: 2 })).not.toEqual(trials);
  });
});

describe("buildPosnerTrials: other sizes", () => {
  it("200 trials at 80% validity: exactly 160 valid and 40 invalid, sides within 1", () => {
    const t = buildPosnerTrials({ seed: 9, nValid: 160, nInvalid: 40 });
    expect(t).toHaveLength(200);
    expect(count(t, (x) => x.valid)).toBe(160);
    expect(count(t, (x) => !x.valid)).toBe(40);
    const left = count(t, (x) => x.targetSide === "left");
    expect(Math.abs(left - (200 - left))).toBeLessThanOrEqual(1);
  });

  it("keeps sides within 1 for odd counts", () => {
    const t = buildPosnerTrials({ seed: 4, nValid: 7, nInvalid: 3 });
    const left = count(t, (x) => x.targetSide === "left");
    expect(Math.abs(left - (10 - left))).toBeLessThanOrEqual(1);
    expect(count(t, (x) => x.valid)).toBe(7);
  });
});

describe("isCorrectResponse (F = left, J = right)", () => {
  it("maps keys to sides, ignoring case", () => {
    expect(isCorrectResponse("left", "f")).toBe(true);
    expect(isCorrectResponse("left", "F")).toBe(true);
    expect(isCorrectResponse("right", "j")).toBe(true);
    expect(isCorrectResponse("left", "j")).toBe(false);
    expect(isCorrectResponse("right", "f")).toBe(false);
  });

  it("treats no response or other keys as incorrect", () => {
    expect(isCorrectResponse("left", null)).toBe(false);
    expect(isCorrectResponse("left", "x")).toBe(false);
  });
});
