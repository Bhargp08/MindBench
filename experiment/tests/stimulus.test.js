import { describe, it, expect } from "vitest";
import { levelToContrast, gaborLuminance, LEVEL_MIN, LEVEL_MAX } from "../src/lib/contrast.js";
import { balancedIntervals } from "../src/lib/intervals.js";
import { createRng } from "../src/lib/rng.js";

describe("levelToContrast (level in dB re full contrast)", () => {
  it("converts dB to contrast", () => {
    expect(levelToContrast(0)).toBe(1);
    expect(levelToContrast(-20)).toBeCloseTo(0.1, 12);
    expect(levelToContrast(-40)).toBeCloseTo(0.01, 12);
  });

  it("exposes the clamp range [-40, 0] dB (1% to 100% contrast)", () => {
    expect(LEVEL_MIN).toBe(-40);
    expect(LEVEL_MAX).toBe(0);
  });
});

describe("gaborLuminance", () => {
  const g = { sigma: 20, cyclesPerPixel: 0.05, orientation: 0, phase: 0 };

  it("is full-range at the center for contrast 1 (luminance 0..1, mean 0.5)", () => {
    expect(gaborLuminance(0, 0, { ...g, contrast: 1 })).toBeCloseTo(1, 12);
  });

  it("is uniform mid-grey (0.5) for contrast 0", () => {
    for (const [x, y] of [[0, 0], [5, 3], [-10, 7]]) {
      expect(gaborLuminance(x, y, { ...g, contrast: 0 })).toBe(0.5);
    }
  });

  it("scales linearly with contrast", () => {
    expect(gaborLuminance(0, 0, { ...g, contrast: 0.2 })).toBeCloseTo(0.6, 12);
  });

  it("fades to mid-grey far from the center", () => {
    expect(gaborLuminance(200, 0, { ...g, contrast: 1 })).toBeCloseTo(0.5, 6);
  });

  it("stays within [0, 1]", () => {
    for (let x = -60; x <= 60; x += 7) {
      const v = gaborLuminance(x, x / 2, { ...g, contrast: 1 });
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
  });
});

describe("balancedIntervals (2-interval forced choice)", () => {
  it("puts the target in each interval equally often, deterministically", () => {
    const a = balancedIntervals(60, createRng(7));
    const b = balancedIntervals(60, createRng(7));
    expect(a).toEqual(b);
    expect(a).toHaveLength(60);
    expect(a.filter((v) => v === 1)).toHaveLength(30);
    expect(a.filter((v) => v === 2)).toHaveLength(30);
  });
});
