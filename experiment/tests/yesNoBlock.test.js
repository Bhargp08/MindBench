import { describe, it, expect } from "vitest";
import { buildYesNoBlock, countYesNo } from "../src/lib/yesNoBlock.js";

describe("buildYesNoBlock (fixed-contrast SDT block)", () => {
  it("defaults to 60 trials: exactly 30 signal and 30 noise", () => {
    const block = buildYesNoBlock({ seed: 1 });
    expect(block).toHaveLength(60);
    expect(block.filter((t) => t.isSignal)).toHaveLength(30);
    expect(block.filter((t) => !t.isSignal)).toHaveLength(30);
  });

  it("supports other sizes and numbers each trial", () => {
    const block = buildYesNoBlock({ nSignal: 10, nNoise: 20, seed: 3 });
    expect(block).toHaveLength(30);
    expect(block.filter((t) => t.isSignal)).toHaveLength(10);
    expect(block.map((t) => t.trial)).toEqual(Array.from({ length: 30 }, (_, i) => i + 1));
  });

  it("is deterministic for a seed and differs across seeds", () => {
    const order = (seed) => buildYesNoBlock({ seed }).map((t) => t.isSignal).join("");
    expect(order(5)).toBe(order(5));
    expect(order(5)).not.toBe(order(6));
  });
});

describe("countYesNo", () => {
  it("counts hits, misses, false alarms and correct rejections exactly", () => {
    const trials = [
      { isSignal: true, respondedYes: true },
      { isSignal: true, respondedYes: true },
      { isSignal: true, respondedYes: false },
      { isSignal: false, respondedYes: true },
      { isSignal: false, respondedYes: false },
      { isSignal: false, respondedYes: false },
      { isSignal: false, respondedYes: false },
    ];
    expect(countYesNo(trials)).toEqual({
      hits: 2,
      misses: 1,
      falseAlarms: 1,
      correctRejections: 3,
      nSignal: 3,
      nNoise: 4,
    });
  });
});
