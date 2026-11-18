import { describe, it, expect } from "vitest";
import { createStaircase, thresholdFromReversals } from "../src/lib/staircase.js";
import { createRng } from "../src/lib/rng.js";

const run = (stair, seq) => {
  for (const ch of seq) stair.respond(ch === "C");
  return stair;
};

describe("createStaircase: 1-up/2-down reversal counting (hand-made sequence)", () => {
  // start -10 dB, step 3 until the 2nd reversal then 1.5, level range [-40, 0]
  //  CC -> -13 (down)   CC -> -16 (down)   I -> up: reversal #1 at -16, level -13
  //  I  -> -10 (up)     CC -> down: reversal #2 at -10, step 3, level -13
  //  CC -> -14.5 (step now 1.5)             I -> up: reversal #3 at -14.5, level -13
  const seq = "CCCCIICCCCI";

  it("counts reversals and records the level at each reversal", () => {
    const s = run(createStaircase({}), seq);
    expect(s.reversals).toEqual([-16, -10, -14.5]);
    expect(s.level).toBe(-13);
    expect(s.trialCount).toBe(11);
  });

  it("logs level, contrast and correctness for every trial", () => {
    const s = run(createStaircase({}), "CCI");
    expect(s.history).toHaveLength(3);
    expect(s.history[0]).toMatchObject({ trial: 1, level: -10, correct: true });
    expect(s.history[0].contrast).toBeCloseTo(10 ** (-10 / 20), 10);
    expect(s.history[2]).toMatchObject({ trial: 3, level: -13, correct: false });
  });

  it("does not count the first move as a reversal; a lone correct response does not move the level", () => {
    const s = run(createStaircase({}), "C");
    expect(s.level).toBe(-10);
    expect(s.reversals).toEqual([]);
    run(s, "I");
    expect(s.level).toBe(-7);
    expect(s.reversals).toEqual([]);
  });

  it("an incorrect response resets the run of correct responses", () => {
    const s = run(createStaircase({}), "CICC"); // C, I(up), C, C -> only the last two count
    expect(s.level).toBe(-10 + 3 - 3);
  });
});

describe("createStaircase: rules, clamping, stopping", () => {
  it("1-up/3-down needs three correct in a row to step down", () => {
    const s = run(createStaircase({ down: 3 }), "CC");
    expect(s.level).toBe(-10);
    run(s, "C");
    expect(s.level).toBe(-13);
  });

  it("clamps the level to [min, max]", () => {
    const top = run(createStaircase({ start: 0, max: 0 }), "II");
    expect(top.level).toBe(0);
    const bottom = run(createStaircase({ start: -40, min: -40 }), "CCCC");
    expect(bottom.level).toBe(-40);
  });

  it("is done after the stop number of reversals (default 10)", () => {
    const s = createStaircase({});
    expect(s.done).toBe(false);
    let guard = 0;
    while (!s.done && guard++ < 1000) {
      // alternate CC, I to force a reversal about every 2 moves
      s.respond(true);
      if (!s.done) s.respond(true);
      if (!s.done) s.respond(false);
    }
    expect(s.reversals.length).toBeGreaterThanOrEqual(10);
    expect(s.done).toBe(true);
  });

  it("is done at the trial cap (default 60) even without enough reversals", () => {
    const s = createStaircase({});
    for (let i = 0; i < 60; i++) s.respond(true); // all correct: no reversals
    expect(s.trialCount).toBe(60);
    expect(s.done).toBe(true);
  });
});

describe("thresholdFromReversals", () => {
  it("is the mean of the last 6 reversals", () => {
    expect(thresholdFromReversals([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])).toBe(7.5);
  });

  it("returns null when there are fewer reversals than needed", () => {
    expect(thresholdFromReversals([1, 2, 3, 4, 5])).toBeNull();
  });

  it("supports a different window size", () => {
    expect(thresholdFromReversals([2, 4, 6, 8], 2)).toBe(7);
  });

  it("is exposed on the staircase", () => {
    const s = createStaircase({ stopReversals: 3 });
    run(s, "CCCCIICCCCI");
    expect(s.threshold(3)).toBeCloseTo((-16 - 10 - 14.5) / 3, 10);
  });
});

describe("convergence with a simulated observer (logistic psychometric function)", () => {
  // 2AFC observer: P(correct) = 0.5 + 0.5 * logistic((level + 20) / 2)
  const P = (level) => 0.5 + 0.5 / (1 + Math.exp(-(level + 20) / 2));

  const estimate = (down, seed) => {
    const rng = createRng(seed);
    const s = createStaircase({
      down,
      start: -10,
      stepInitial: 1,
      stepFinal: 1,
      stopReversals: Infinity,
      maxTrials: 2000,
    });
    while (!s.done) s.respond(rng() < P(s.level));
    const late = s.reversals.slice(10); // drop the initial approach
    return P(late.reduce((a, b) => a + b, 0) / late.length);
  };
  const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
  const SEEDS = [1, 2, 3, 4, 5].map((k) => k * 7919);

  // Single 2,000-trial runs vary by about +/-0.03 by chance, so the test averages 5 seeds.
  it("1-up/2-down converges to P(correct) = 0.7071 +/- 0.03", () => {
    expect(Math.abs(mean(SEEDS.map((sd) => estimate(2, sd))) - 0.7071)).toBeLessThan(0.03);
  });

  it("1-up/3-down converges to P(correct) = 0.7937 +/- 0.03", () => {
    expect(Math.abs(mean(SEEDS.map((sd) => estimate(3, sd))) - 0.7937)).toBeLessThan(0.03);
  });
});
