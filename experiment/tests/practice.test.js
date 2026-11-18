import { describe, it, expect } from "vitest";
import pool from "../src/data/wordpool.json";
import { PRACTICE, FEEDBACK_MS, feedbackFor, tagTrialData } from "../src/lib/practice.js";
import { buildPosnerTrials } from "../src/lib/posner.js";
import { buildStroopTrials } from "../src/lib/stroop.js";
import { buildNBackSequence } from "../src/lib/nback.js";
import { LEVEL_MIN, LEVEL_MAX } from "../src/lib/contrast.js";

describe("practice block sizes (short, with feedback)", () => {
  it("contrast: 6 forced-choice trials at a fixed easy level within the staircase range", () => {
    expect(PRACTICE.contrast.trials).toBe(6);
    expect(PRACTICE.contrast.levelDb).toBeGreaterThanOrEqual(LEVEL_MIN);
    expect(PRACTICE.contrast.levelDb).toBeLessThanOrEqual(LEVEL_MAX);
    expect(PRACTICE.contrast.levelDb).toBeGreaterThanOrEqual(-10); // clearly visible
  });

  it("posner: 8 trials (6 valid, 2 invalid) that the real generator can build", () => {
    const t = buildPosnerTrials({ seed: 1, ...PRACTICE.posner });
    expect(t).toHaveLength(8);
    expect(t.filter((x) => !x.valid)).toHaveLength(2);
  });

  it("stroop: 8 trials (4 congruent, 4 incongruent)", () => {
    const t = buildStroopTrials({ seed: 1, ...PRACTICE.stroop });
    expect(t).toHaveLength(8);
    expect(t.filter((x) => x.condition === "congruent")).toHaveLength(4);
  });

  it("nback: 12 trials with 3 targets and 2 lures, buildable for every seed tried", () => {
    for (let seed = 1; seed <= 100; seed++) {
      const s = buildNBackSequence({ seed, ...PRACTICE.nback });
      expect(s).toHaveLength(12);
      expect(s.filter((x) => x.isTarget)).toHaveLength(3);
    }
  });

  it("recall: 4 practice words that are not in the study word pool (so no study word is spent on practice)", () => {
    expect(PRACTICE.recall.words).toHaveLength(4);
    expect(new Set(PRACTICE.recall.words).size).toBe(4);
    const poolSet = new Set(pool.words);
    for (const w of PRACTICE.recall.words) {
      expect(w).toMatch(/^[a-z]{5,8}$/);
      expect(poolSet.has(w)).toBe(false);
    }
    expect(PRACTICE.recall.recallMs).toBeLessThan(90000);
  });
});

describe("feedbackFor", () => {
  it("says Correct / Incorrect for forced-choice trials", () => {
    expect(feedbackFor({ correct: true, responded: true })).toMatchObject({ kind: "correct", text: "Correct" });
    expect(feedbackFor({ correct: false, responded: true })).toMatchObject({ kind: "incorrect", text: "Incorrect" });
  });

  it("flags a missing response as too slow", () => {
    const f = feedbackFor({ correct: false, responded: false });
    expect(f.kind).toBe("timeout");
    expect(f.text.toLowerCase()).toContain("slow");
  });

  it("go/no-go (2-back): explains misses and false alarms", () => {
    expect(feedbackFor({ correct: false, responded: false, goNoGo: true }).text.toLowerCase()).toContain("missed");
    expect(feedbackFor({ correct: false, responded: true, goNoGo: true }).text.toLowerCase()).toContain("not a match");
    expect(feedbackFor({ correct: true, responded: false, goNoGo: true }).kind).toBe("correct");
  });

  it("is shown briefly", () => {
    expect(FEEDBACK_MS).toBeGreaterThanOrEqual(400);
    expect(FEEDBACK_MS).toBeLessThanOrEqual(1000);
  });
});

describe("tagTrialData", () => {
  it("marks practice trials so analysis can exclude them (default is not practice)", () => {
    expect(tagTrialData({ task: "posner" }, { practice: true })).toEqual({ task: "posner", practice: true });
    expect(tagTrialData({ task: "posner" })).toEqual({ task: "posner", practice: false });
  });
});
