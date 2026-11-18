import { describe, it, expect } from "vitest";
import { estimateRefreshRate, nominalRefreshRate, measureRefreshRate, createTimingLog } from "../src/lib/timingLog.js";

const frames = (hz, n = 61, jitter = () => 0) => Array.from({ length: n }, (_, i) => (i * 1000) / hz + jitter(i));

describe("estimateRefreshRate (from requestAnimationFrame timestamps)", () => {
  it("recovers 60, 120 and 144 Hz", () => {
    for (const hz of [60, 120, 144]) {
      const r = estimateRefreshRate(frames(hz));
      expect(r.hz).toBeCloseTo(hz, 3);
      expect(r.medianFrameMs).toBeCloseTo(1000 / hz, 4);
      expect(r.sdMs).toBeCloseTo(0, 6);
      expect(r.nDroppedFrames).toBe(0);
    }
  });

  it("tolerates timestamp jitter (about +/-0.3 ms)", () => {
    const r = estimateRefreshRate(frames(60, 61, (i) => 0.3 * Math.sin(i * 1.7)));
    expect(Math.abs(r.hz - 60)).toBeLessThan(0.7);
    expect(r.sdMs).toBeLessThan(1);
  });

  it("ignores dropped frames in the rate and counts them", () => {
    const ts = [0];
    for (let i = 1; i <= 60; i++) ts.push(ts[i - 1] + (i % 20 === 0 ? 2 : 1) * (1000 / 60));
    const r = estimateRefreshRate(ts);
    expect(r.hz).toBeCloseTo(60, 3);
    expect(r.nDroppedFrames).toBe(3);
  });

  it("returns null with fewer than 10 timestamps", () => {
    expect(estimateRefreshRate(frames(60, 9))).toBeNull();
    expect(estimateRefreshRate([])).toBeNull();
  });
});

describe("nominalRefreshRate", () => {
  it("snaps to a common rate within 2%, otherwise null", () => {
    expect(nominalRefreshRate(59.94)).toBe(60);
    expect(nominalRefreshRate(119.88)).toBe(120);
    expect(nominalRefreshRate(143.9)).toBe(144);
    expect(nominalRefreshRate(75.2)).toBe(75);
    expect(nominalRefreshRate(70)).toBeNull();
  });
});

describe("measureRefreshRate (injectable requestAnimationFrame)", () => {
  it("collects frames and estimates the rate", async () => {
    let t = 1000;
    const raf = (cb) => {
      t += 1000 / 144;
      const stamp = t;
      setTimeout(() => cb(stamp), 0);
    };
    const r = await measureRefreshRate({ raf, nFrames: 40 });
    expect(r.hz).toBeCloseTo(144, 2);
    expect(r.nominalHz).toBe(144);
    expect(r.nFrames).toBeGreaterThanOrEqual(39);
  });
});

describe("createTimingLog (per-task durations on an injectable clock)", () => {
  const makeClock = () => {
    let t = 5000;
    return { now: () => t, advance: (ms) => (t += ms) };
  };

  it("records the duration of each finished task in order, plus the total", () => {
    const clock = makeClock();
    const log = createTimingLog({ now: clock.now });
    log.start("posner");
    clock.advance(240_000);
    log.end("posner");
    clock.advance(5_000); // gap between tasks is not counted
    log.start("stroop");
    clock.advance(150_000);
    log.end("stroop");
    expect(log.toJSON()).toEqual({
      tasks: { posner: { ms: 240_000 }, stroop: { ms: 150_000 } },
      totalTaskMs: 390_000,
      unfinished: [],
    });
  });

  it("lists tasks that were started but not finished", () => {
    const clock = makeClock();
    const log = createTimingLog({ now: clock.now });
    log.start("nback");
    expect(log.toJSON().unfinished).toEqual(["nback"]);
    expect(log.toJSON().tasks).toEqual({});
  });

  it("rejects ending an unstarted task and starting a task twice", () => {
    const log = createTimingLog({ now: () => 0 });
    expect(() => log.end("posner")).toThrow();
    log.start("posner");
    expect(() => log.start("posner")).toThrow();
  });
});
