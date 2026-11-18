const median = (xs) => {
  const s = [...xs].sort((a, b) => a - b);
  const m = s.length >> 1;
  return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2;
};
const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;

/**
 * Refresh rate from requestAnimationFrame timestamps (ms). Frames more than 1.5x the median interval are counted
 * as dropped and left out of the rate. Returns null with fewer than 10 timestamps.
 */
export function estimateRefreshRate(timestamps) {
  if (!Array.isArray(timestamps) || timestamps.length < 10) return null;
  const deltas = timestamps.slice(1).map((t, i) => t - timestamps[i]);
  const med = median(deltas);
  const kept = deltas.filter((d) => d <= 1.5 * med && d >= 0.5 * med);
  const m = mean(kept);
  const sd = Math.sqrt(mean(kept.map((d) => (d - m) ** 2)));
  return {
    hz: 1000 / m,
    medianFrameMs: med,
    sdMs: sd,
    nDroppedFrames: deltas.filter((d) => d > 1.5 * med).length,
    nFrames: timestamps.length,
    plausible: 1000 / m >= 20 && 1000 / m <= 500, // false for throttled or background tabs
  };
}

const COMMON_RATES = [30, 50, 60, 75, 90, 100, 120, 144, 165, 240];

/** Snap a measured rate to a common display rate if within 2%, else null. */
export function nominalRefreshRate(hz) {
  const hit = COMMON_RATES.find((r) => Math.abs(hz - r) / r <= 0.02);
  return hit ?? null;
}

/**
 * Measure the display refresh rate over `nFrames` animation frames. `raf` is injectable for tests. Resolves after
 * `timeoutMs` with whatever frames arrived (null if fewer than 10), so a throttled or background tab cannot hang it.
 */
export function measureRefreshRate({ raf = globalThis.requestAnimationFrame?.bind(globalThis), nFrames = 60, timeoutMs = 4000 } = {}) {
  if (typeof raf !== "function") return Promise.resolve(null);
  return new Promise((resolve) => {
    const stamps = [];
    let settled = false;
    const finish = () => {
      if (settled) return;
      settled = true;
      const est = estimateRefreshRate(stamps);
      resolve(est && { ...est, nominalHz: nominalRefreshRate(est.hz) });
    };
    const timer = setTimeout(finish, timeoutMs);
    const tick = (t) => {
      if (settled) return;
      stamps.push(t);
      if (stamps.length >= nFrames) {
        clearTimeout(timer);
        finish();
      } else raf(tick);
    };
    raf(tick);
  });
}

/** Per-task durations on an injectable clock (default performance.now). */
export function createTimingLog({ now = () => performance.now() } = {}) {
  const open = new Map();
  const tasks = {};
  return {
    start(task) {
      if (open.has(task)) throw new Error(`Task "${task}" already started`);
      open.set(task, now());
    },
    end(task) {
      if (!open.has(task)) throw new Error(`Task "${task}" was not started`);
      tasks[task] = { ms: now() - open.get(task) };
      open.delete(task);
    },
    toJSON() {
      return {
        tasks: { ...tasks },
        totalTaskMs: Object.values(tasks).reduce((a, t) => a + t.ms, 0),
        unfinished: [...open.keys()],
      };
    },
  };
}
