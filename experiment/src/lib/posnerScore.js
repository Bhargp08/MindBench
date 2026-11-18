const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);

/**
 * Per-session Posner scores. trials: [{ valid, rt, correct }].
 * Validity effect = mean correct invalid RT - mean correct valid RT (ms), after trimming RT < minRt
 * or > maxRt (the bounds themselves are kept). Accuracy is over all trials in the condition
 * (a missing response counts as an error). The preregistered exclusion functions live in MB-15.
 */
export function scorePosner(trials, { minRt = 200, maxRt = 2500 } = {}) {
  const usable = (t) => t.correct === true && typeof t.rt === "number" && t.rt >= minRt && t.rt <= maxRt;
  const valid = trials.filter((t) => t.valid);
  const invalid = trials.filter((t) => !t.valid);
  const validRts = valid.filter(usable).map((t) => t.rt);
  const invalidRts = invalid.filter(usable).map((t) => t.rt);
  const meanValidRt = mean(validRts);
  const meanInvalidRt = mean(invalidRts);
  const acc = (xs) => (xs.length ? xs.filter((t) => t.correct === true).length / xs.length : null);
  return {
    meanValidRt,
    meanInvalidRt,
    validityEffect: meanValidRt === null || meanInvalidRt === null ? null : meanInvalidRt - meanValidRt,
    nValidUsed: validRts.length,
    nInvalidUsed: invalidRts.length,
    validAccuracy: acc(valid),
    invalidAccuracy: acc(invalid),
  };
}
