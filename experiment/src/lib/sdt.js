// Signal detection helpers. Values are cross-checked against scipy and the Python SDT tests (MB-15).

function erfSeries(x) {
  // erf(x) = 2/sqrt(pi) * sum (-1)^n x^(2n+1) / (n! (2n+1)), accurate for |x| < ~3
  let term = x;
  let sum = x;
  for (let n = 1; n < 80; n++) {
    term *= (-x * x) / n;
    sum += term / (2 * n + 1);
  }
  return (2 / Math.sqrt(Math.PI)) * sum;
}

function erfcPositive(x) {
  if (x < 2.5) return 1 - erfSeries(x);
  // continued fraction for larger x: erfc(x) = exp(-x^2)/sqrt(pi) / (x + (1/2)/(x + 1/(x + (3/2)/(x + ...))))
  let t = x;
  for (let k = 80; k >= 1; k--) t = x + k / 2 / t;
  return Math.exp(-x * x) / Math.sqrt(Math.PI) / t;
}

/** Standard normal CDF. */
export function pnorm(z) {
  const x = Math.abs(z) / Math.SQRT2;
  const tail = 0.5 * erfcPositive(x); // P(Z > |z|)
  return z >= 0 ? 1 - tail : tail;
}

/** Inverse standard normal CDF (bisection on pnorm; p must be in (0, 1)). */
export function qnorm(p) {
  if (!(p > 0 && p < 1)) throw new RangeError(`qnorm needs 0 < p < 1, got ${p}`);
  let lo = -40;
  let hi = 40;
  for (let i = 0; i < 200; i++) {
    const mid = (lo + hi) / 2;
    if (pnorm(mid) < p) lo = mid;
    else hi = mid;
  }
  return (lo + hi) / 2;
}

/** d' = z(H) - z(FA); criterion c = -(z(H) + z(FA)) / 2. Rates must be strictly between 0 and 1. */
export function dPrimeFromRates(hitRate, falseAlarmRate) {
  const zh = qnorm(hitRate);
  const zf = qnorm(falseAlarmRate);
  return { dPrime: zh - zf, criterion: -(zh + zf) / 2 };
}

/**
 * d' from counts. Default correction is log-linear (Hautus 1995), applied to every dataset:
 * H = (hits + 0.5) / (nSignal + 1), FA = (falseAlarms + 0.5) / (nNoise + 1), so rates of 0 or 1 stay finite.
 * correction "none" uses the raw rates and throws RangeError if either is exactly 0 or 1.
 */
export function dPrimeFromCounts({ hits, nSignal, falseAlarms, nNoise }, { correction = "loglinear" } = {}) {
  if (!(nSignal > 0) || !(nNoise > 0)) throw new RangeError("nSignal and nNoise must be positive");
  if (hits < 0 || hits > nSignal || falseAlarms < 0 || falseAlarms > nNoise) {
    throw new RangeError("counts must satisfy 0 <= hits <= nSignal and 0 <= falseAlarms <= nNoise");
  }
  let hitRate;
  let falseAlarmRate;
  if (correction === "loglinear") {
    hitRate = (hits + 0.5) / (nSignal + 1);
    falseAlarmRate = (falseAlarms + 0.5) / (nNoise + 1);
  } else if (correction === "none") {
    hitRate = hits / nSignal;
    falseAlarmRate = falseAlarms / nNoise;
  } else {
    throw new Error(`unknown correction "${correction}"`);
  }
  return { hitRate, falseAlarmRate, ...dPrimeFromRates(hitRate, falseAlarmRate) };
}
