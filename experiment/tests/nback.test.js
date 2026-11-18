import { describe, it, expect } from "vitest";
import { buildNBackSequence, scoreNBack, CONSONANTS } from "../src/lib/nback.js";

// Independent classification from the letters alone (2-back task).
function classify(letters, i) {
  // i is 0-based; positions 1 and 2 (i = 0, 1) are never targets or lures
  if (i < 2) return "start";
  if (letters[i] === letters[i - 2]) return "target";
  if (letters[i] === letters[i - 1]) return "lure1";
  if (i >= 3 && letters[i] === letters[i - 3]) return "lure3";
  return "nontarget";
}
const countType = (seq, type) => seq.filter((t) => t.type === type).length;

describe("buildNBackSequence: design defaults (60 trials, 18 targets = 30%, 3 one-back + 3 three-back lures)", () => {
  const seq = buildNBackSequence({ seed: 1 });
  const letters = seq.map((t) => t.letter);

  it("has 60 numbered trials with exact type counts", () => {
    expect(seq).toHaveLength(60);
    expect(seq.map((t) => t.trial)).toEqual(Array.from({ length: 60 }, (_, i) => i + 1));
    expect(countType(seq, "target")).toBe(18);
    expect(countType(seq, "lure1")).toBe(3);
    expect(countType(seq, "lure3")).toBe(3);
    expect(countType(seq, "start")).toBe(2);
    expect(countType(seq, "nontarget")).toBe(34);
  });

  it("has no target or lure in positions 1-2, and position 2 differs from position 1", () => {
    expect(seq[0].type).toBe("start");
    expect(seq[1].type).toBe("start");
    expect(letters[1]).not.toBe(letters[0]);
  });

  it("labels agree with the letters: classification from the letter sequence alone gives the same types", () => {
    seq.forEach((t, i) => expect(t.type).toBe(classify(letters, i)));
  });

  it("uses consonants only", () => {
    expect(CONSONANTS).not.toMatch(/[AEIOU]/);
    for (const l of letters) expect(CONSONANTS).toContain(l);
  });

  it("is fixed by the seed and differs across seeds", () => {
    expect(buildNBackSequence({ seed: 1 })).toEqual(seq);
    expect(buildNBackSequence({ seed: 2 })).not.toEqual(seq);
  });

  it("keeps exact counts and clean labels across 200 seeds", () => {
    for (let seed = 1; seed <= 200; seed++) {
      const s = buildNBackSequence({ seed });
      const ls = s.map((t) => t.letter);
      expect(countType(s, "target")).toBe(18);
      expect(countType(s, "lure1")).toBe(3);
      expect(countType(s, "lure3")).toBe(3);
      s.forEach((t, i) => expect(t.type).toBe(classify(ls, i)));
    }
  });
});

describe("buildNBackSequence: other sizes", () => {
  it("100 trials at 30% targets gives exactly 30 targets with 5 + 5 lures", () => {
    const s = buildNBackSequence({ seed: 3, nTrials: 100, nTargets: 30, nLureOne: 5, nLureThree: 5 });
    const ls = s.map((t) => t.letter);
    expect(s).toHaveLength(100);
    expect(countType(s, "target")).toBe(30);
    expect(countType(s, "lure1")).toBe(5);
    expect(countType(s, "lure3")).toBe(5);
    s.forEach((t, i) => expect(t.type).toBe(classify(ls, i)));
  });

  it("throws when the requested targets and lures do not fit after position 2", () => {
    expect(() => buildNBackSequence({ seed: 1, nTrials: 20, nTargets: 15, nLureOne: 3, nLureThree: 3 })).toThrow();
  });
});

describe("scoreNBack (positions 1-2 are not scored; lure responses are false alarms)", () => {
  // 18 targets, 40 scored non-targets (positions 3-60 = 58 trials). 15 hits, 6 false alarms (2 of them on lures).
  const mk = (position, type, responded) => ({ position, type, responded });
  const trials = [mk(1, "start", true), mk(2, "start", true)];
  let pos = 3;
  for (let i = 0; i < 18; i++) trials.push(mk(pos++, "target", i < 15));
  for (let i = 0; i < 2; i++) trials.push(mk(pos++, "lure1", true));
  for (let i = 0; i < 2; i++) trials.push(mk(pos++, "lure3", i === 0 ? true : false));
  for (let i = 0; i < 36; i++) trials.push(mk(pos++, "nontarget", i < 3));

  it("counts hits, misses, false alarms and correct rejections, ignoring positions 1-2", () => {
    const s = scoreNBack(trials);
    expect(s.nTargets).toBe(18);
    expect(s.nNonTargets).toBe(40);
    expect(s.hits).toBe(15);
    expect(s.misses).toBe(3);
    expect(s.falseAlarms).toBe(6); // 2 one-back lures + 1 three-back lure + 3 other
    expect(s.correctRejections).toBe(34);
    expect(s.lureFalseAlarms).toBe(3);
  });

  it("matches the hand-worked d' with the log-linear correction (15/18 hits, 6/40 false alarms)", () => {
    const s = scoreNBack(trials);
    expect(s.dPrime).toBeCloseTo(1.899925, 5);
    expect(s.criterion).toBeCloseTo(0.050528, 5);
  });

  it("handles a perfect session without infinite d'", () => {
    const perfect = trials.map((t) => ({ ...t, responded: t.type === "target" }));
    const s = scoreNBack(perfect);
    expect(s.hits).toBe(18);
    expect(s.falseAlarms).toBe(0);
    expect(s.dPrime).toBeCloseTo(4.188857, 5); // scipy: H = 18.5/19, FA = 0.5/41
    expect(Number.isFinite(s.dPrime)).toBe(true);
  });
});
