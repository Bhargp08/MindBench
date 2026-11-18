import { describe, it, expect } from "vitest";
import { scorePosner } from "../src/lib/posnerScore.js";

const t = (valid, rt, correct = true) => ({ valid, rt, correct });

describe("scorePosner", () => {
  it("validity effect = mean invalid RT - mean valid RT (350 vs 390 gives exactly 40 ms)", () => {
    const trials = [
      t(true, 340), t(true, 350), t(true, 360),
      t(false, 380), t(false, 390), t(false, 400),
    ];
    const s = scorePosner(trials);
    expect(s.meanValidRt).toBe(350);
    expect(s.meanInvalidRt).toBe(390);
    expect(s.validityEffect).toBe(40);
  });

  it("uses correct trials only and trims RT < 200 or > 2500 (boundary values 200 and 2500 are kept)", () => {
    const trials = [
      t(true, 200), t(true, 100), t(true, 300, false), t(true, 400),
      t(false, 2500), t(false, 2501), t(false, 500),
    ];
    const s = scorePosner(trials);
    expect(s.meanValidRt).toBe(300); // 200 and 400 only
    expect(s.meanInvalidRt).toBe(1500); // 2500 and 500 only
    expect(s.validityEffect).toBe(1200);
    expect(s.nValidUsed).toBe(2);
    expect(s.nInvalidUsed).toBe(2);
  });

  it("reports accuracy per condition over all trials, counting missing responses as errors", () => {
    const trials = [
      t(true, 300), t(true, 320), t(true, 340), t(true, null, false),
      t(false, 400), t(false, 420, false),
    ];
    const s = scorePosner(trials);
    expect(s.validAccuracy).toBe(0.75);
    expect(s.invalidAccuracy).toBe(0.5);
  });

  it("returns a null validity effect when a condition has no usable trials", () => {
    const s = scorePosner([t(true, 300), t(false, 100)]);
    expect(s.meanInvalidRt).toBeNull();
    expect(s.validityEffect).toBeNull();
  });

  it("allows custom trim bounds", () => {
    const s = scorePosner([t(true, 150), t(true, 250), t(false, 350)], { minRt: 100, maxRt: 300 });
    expect(s.meanValidRt).toBe(200);
    expect(s.meanInvalidRt).toBeNull();
  });
});
