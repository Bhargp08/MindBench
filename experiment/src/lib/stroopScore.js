const mean = (xs) => (xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : null);

/**
 * Per-session Stroop scores. trials: [{ condition: "congruent"|"incongruent"|"neutral", rt, correct }].
 * Interference = mean correct incongruent RT - mean correct congruent RT (ms), after trimming RT < minRt
 * or > maxRt (bounds kept). Accuracy interference = congruent accuracy - incongruent accuracy.
 * Accuracy is over all trials in the condition (a missing response is an error). The preregistered
 * exclusion functions live in MB-15.
 */
export function scoreStroop(trials, { minRt = 200, maxRt = 2500 } = {}) {
  const usable = (t) => t.correct === true && typeof t.rt === "number" && t.rt >= minRt && t.rt <= maxRt;
  const cond = (name) => trials.filter((t) => t.condition === name);
  const rts = (name) => cond(name).filter(usable).map((t) => t.rt);
  const acc = (name) => {
    const xs = cond(name);
    return xs.length ? xs.filter((t) => t.correct === true).length / xs.length : null;
  };
  const meanCongruentRt = mean(rts("congruent"));
  const meanIncongruentRt = mean(rts("incongruent"));
  const congruentAccuracy = acc("congruent");
  const incongruentAccuracy = acc("incongruent");
  return {
    meanCongruentRt,
    meanIncongruentRt,
    meanNeutralRt: mean(rts("neutral")),
    interference: meanCongruentRt === null || meanIncongruentRt === null ? null : meanIncongruentRt - meanCongruentRt,
    nCongruentUsed: rts("congruent").length,
    nIncongruentUsed: rts("incongruent").length,
    congruentAccuracy,
    incongruentAccuracy,
    neutralAccuracy: acc("neutral"),
    accuracyInterference:
      congruentAccuracy === null || incongruentAccuracy === null ? null : congruentAccuracy - incongruentAccuracy,
  };
}
