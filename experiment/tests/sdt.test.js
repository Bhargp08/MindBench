import { describe, it, expect } from "vitest";
import { qnorm, dPrimeFromRates, dPrimeFromCounts } from "../src/lib/sdt.js";

describe("qnorm (inverse standard normal CDF)", () => {
  it("matches known quantiles", () => {
    expect(qnorm(0.5)).toBeCloseTo(0, 12);
    expect(qnorm(0.975)).toBeCloseTo(1.959963984540054, 8);
    expect(qnorm(0.8)).toBeCloseTo(0.8416212335729143, 8);
    expect(qnorm(0.001)).toBeCloseTo(-3.090232306167813, 8);
  });

  it("is antisymmetric", () => {
    for (const p of [0.01, 0.2, 0.37, 0.49]) expect(qnorm(p)).toBeCloseTo(-qnorm(1 - p), 10);
  });

  it("rejects probabilities of 0 or 1 and values outside (0, 1)", () => {
    for (const p of [0, 1, -0.1, 1.2, NaN]) expect(() => qnorm(p)).toThrow(RangeError);
  });
});

describe("dPrimeFromRates (no correction; values shared with the Python SDT tests in MB-15)", () => {
  it("H = .80, FA = .20 gives d' 1.6832 and c 0", () => {
    const r = dPrimeFromRates(0.8, 0.2);
    expect(r.dPrime).toBeCloseTo(1.6832, 4);
    expect(r.criterion).toBeCloseTo(0, 10);
  });

  it("H = .90, FA = .30 gives d' 1.8060 and c -0.3786", () => {
    const r = dPrimeFromRates(0.9, 0.3);
    expect(r.dPrime).toBeCloseTo(1.806, 4);
    expect(r.criterion).toBeCloseTo(-0.3786, 4);
  });

  it("rejects rates of exactly 0 or 1", () => {
    expect(() => dPrimeFromRates(1, 0.2)).toThrow(RangeError);
    expect(() => dPrimeFromRates(0.8, 0)).toThrow(RangeError);
  });
});

describe("dPrimeFromCounts (log-linear correction, Hautus 1995: H = (hits+0.5)/(nSignal+1), FA = (fa+0.5)/(nNoise+1))", () => {
  // Expected values computed independently with scipy.stats.norm.ppf.
  it("hand-worked example: 15 hits of 18 targets, 6 false alarms of 40 non-targets", () => {
    // H = 15.5/19 = 0.815789, FA = 6.5/41 = 0.158537, d' = z(H) - z(FA) = 1.899925, c = 0.050528
    const r = dPrimeFromCounts({ hits: 15, nSignal: 18, falseAlarms: 6, nNoise: 40 });
    expect(r.hitRate).toBeCloseTo(0.815789, 6);
    expect(r.falseAlarmRate).toBeCloseTo(0.158537, 6);
    expect(r.dPrime).toBeCloseTo(1.899925, 5);
    expect(r.criterion).toBeCloseTo(0.050528, 5);
  });

  it("perfect performance (hit rate 1, false-alarm rate 0) stays finite: 18/18 and 0/40", () => {
    const r = dPrimeFromCounts({ hits: 18, nSignal: 18, falseAlarms: 0, nNoise: 40 });
    expect(r.hitRate).toBeCloseTo(0.973684, 6);
    expect(r.falseAlarmRate).toBeCloseTo(0.012195, 6);
    expect(r.dPrime).toBeCloseTo(4.188857, 5);
    expect(Number.isFinite(r.criterion)).toBe(true);
  });

  it("worst performance (hit rate 0, false-alarm rate 1) stays finite: 0/18 and 40/40", () => {
    const r = dPrimeFromCounts({ hits: 0, nSignal: 18, falseAlarms: 40, nNoise: 40 });
    expect(r.dPrime).toBeCloseTo(-4.188857, 5);
  });

  it("chance performance gives d' 0: 9/18 and 20/40", () => {
    expect(dPrimeFromCounts({ hits: 9, nSignal: 18, falseAlarms: 20, nNoise: 40 }).dPrime).toBeCloseTo(0, 10);
  });

  it("spec example: 50/50 hits and 0/50 false alarms gives H .99020, FA .00980, d' 4.6675", () => {
    const r = dPrimeFromCounts({ hits: 50, nSignal: 50, falseAlarms: 0, nNoise: 50 });
    expect(r.hitRate).toBeCloseTo(0.990196, 6);
    expect(r.falseAlarmRate).toBeCloseTo(0.009804, 6);
    expect(r.dPrime).toBeCloseTo(4.6675, 4);
  });

  it('correction "none" works for interior rates but refuses extreme ones', () => {
    const ok = dPrimeFromCounts({ hits: 16, nSignal: 20, falseAlarms: 4, nNoise: 20 }, { correction: "none" });
    expect(ok.dPrime).toBeCloseTo(1.6832, 4); // H = .8, FA = .2
    expect(() => dPrimeFromCounts({ hits: 20, nSignal: 20, falseAlarms: 4, nNoise: 20 }, { correction: "none" })).toThrow(RangeError);
    expect(() => dPrimeFromCounts({ hits: 10, nSignal: 20, falseAlarms: 0, nNoise: 20 }, { correction: "none" })).toThrow(RangeError);
  });

  it("rejects impossible counts and empty denominators", () => {
    expect(() => dPrimeFromCounts({ hits: 19, nSignal: 18, falseAlarms: 0, nNoise: 40 })).toThrow(RangeError);
    expect(() => dPrimeFromCounts({ hits: 0, nSignal: 0, falseAlarms: 0, nNoise: 40 })).toThrow(RangeError);
    expect(() => dPrimeFromCounts({ hits: -1, nSignal: 18, falseAlarms: 0, nNoise: 40 })).toThrow(RangeError);
  });
});
