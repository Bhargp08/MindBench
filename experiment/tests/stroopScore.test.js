import { describe, it, expect } from "vitest";
import { scoreStroop } from "../src/lib/stroopScore.js";

const t = (condition, rt, correct = true) => ({ condition, rt, correct });

describe("scoreStroop", () => {
  it("interference = mean incongruent RT - mean congruent RT (600 vs 700 gives exactly 100 ms)", () => {
    const s = scoreStroop([
      t("congruent", 590), t("congruent", 600), t("congruent", 610),
      t("incongruent", 690), t("incongruent", 700), t("incongruent", 710),
    ]);
    expect(s.meanCongruentRt).toBe(600);
    expect(s.meanIncongruentRt).toBe(700);
    expect(s.interference).toBe(100);
  });

  it("uses correct trials only and trims RT < 200 or > 2500 (bounds are kept)", () => {
    const s = scoreStroop([
      t("congruent", 200), t("congruent", 150), t("congruent", 500, false), t("congruent", 400),
      t("incongruent", 2500), t("incongruent", 2600), t("incongruent", 700),
    ]);
    expect(s.meanCongruentRt).toBe(300);
    expect(s.meanIncongruentRt).toBe(1600);
    expect(s.interference).toBe(1300);
    expect(s.nCongruentUsed).toBe(2);
    expect(s.nIncongruentUsed).toBe(2);
  });

  it("accuracy interference = congruent accuracy - incongruent accuracy (hand example)", () => {
    const s = scoreStroop([
      t("congruent", 500), t("congruent", 510), t("congruent", 520), t("congruent", 530),
      t("incongruent", 600), t("incongruent", 610), t("incongruent", 620), t("incongruent", 630, false),
    ]);
    expect(s.congruentAccuracy).toBe(1);
    expect(s.incongruentAccuracy).toBe(0.75);
    expect(s.accuracyInterference).toBe(0.25);
  });

  it("counts missing responses as errors in accuracy", () => {
    const s = scoreStroop([t("congruent", 500), t("congruent", null, false)]);
    expect(s.congruentAccuracy).toBe(0.5);
  });

  it("reports neutral mean RT and accuracy when neutral trials exist, null otherwise", () => {
    const withN = scoreStroop([t("neutral", 640), t("neutral", 660), t("congruent", 600), t("incongruent", 700)]);
    expect(withN.meanNeutralRt).toBe(650);
    expect(withN.neutralAccuracy).toBe(1);
    const noN = scoreStroop([t("congruent", 600), t("incongruent", 700)]);
    expect(noN.meanNeutralRt).toBeNull();
    expect(noN.neutralAccuracy).toBeNull();
  });

  it("returns null interference when a condition has no usable trials", () => {
    const s = scoreStroop([t("congruent", 600), t("incongruent", 100)]);
    expect(s.meanIncongruentRt).toBeNull();
    expect(s.interference).toBeNull();
  });
});
