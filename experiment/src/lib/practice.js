export const FEEDBACK_MS = 600;

/** Practice block settings (short, with feedback). Recall words are not in the study word pool. */
export const PRACTICE = {
  contrast: { trials: 6, levelDb: -6 },
  posner: { nValid: 6, nInvalid: 2 },
  stroop: { nCongruent: 4, nIncongruent: 4 },
  nback: { nTrials: 12, nTargets: 3, nLureOne: 1, nLureThree: 1 },
  recall: { words: ["window", "pencil", "bridge", "candle"], recallMs: 25000 },
};

/** Feedback text for one practice trial. goNoGo is for the 2-back (no response can be correct). */
export function feedbackFor({ correct, responded, goNoGo = false }) {
  if (correct) return { kind: "correct", text: "Correct" };
  if (goNoGo) {
    return responded
      ? { kind: "incorrect", text: "Incorrect: that was not a match" }
      : { kind: "incorrect", text: "Missed: that was a match" };
  }
  if (!responded) return { kind: "timeout", text: "Too slow, please respond faster" };
  return { kind: "incorrect", text: "Incorrect" };
}

/** Mark trial data as practice (or not) so analysis can exclude practice trials. */
export function tagTrialData(data, { practice = false } = {}) {
  return { ...data, practice: !!practice };
}
