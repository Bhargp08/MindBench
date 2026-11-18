import { describe, it, expect } from "vitest";
import { scoreRecall, serialPositionCurve, sessionRecallProportion } from "../src/lib/recallScore.js";

// A small pool that includes both "apple" and "apply" (edit distance 1), plus unrelated words.
const POOL = ["apple", "apply", "chair", "table", "plane", "plans", "tree", "house", "river", "cloud", "stone"];
const LIST = ["apple", "chair", "plane", "tree", "river"];

const score = (recallText, listWords = LIST) => scoreRecall({ listWords, recallText, pool: POOL });

describe("scoreRecall: matching rules", () => {
  it('counts "Apple " (case, surrounding whitespace), "aple" (one typo) and "APPLE" as correct for "apple"', () => {
    for (const r of ["Apple ", "aple", "APPLE"]) {
      const s = score(r);
      expect(s.recalled).toEqual([true, false, false, false, false]);
      expect(s.nCorrect).toBe(1);
    }
  });

  it('counts "apply" as incorrect when "apply" is itself a pool word, even though it is one edit from "apple"', () => {
    const s = score("apply");
    expect(s.nCorrect).toBe(0);
    expect(s.recalled).toEqual([false, false, false, false, false]);
    expect(s.intrusions).toEqual(["apply"]);
  });

  it("splits the recall text on whitespace, commas, semicolons and newlines", () => {
    const s = score("apple, chair;plane\nriver   tree");
    expect(s.nCorrect).toBe(5);
    expect(s.proportion).toBe(1);
  });

  it("reports recalled flags by list position", () => {
    expect(score("river apple").recalled).toEqual([true, false, false, false, true]);
  });

  it("allows one typo only for list words of 5+ letters", () => {
    expect(score("tre").nCorrect).toBe(0); // 'tree' has 4 letters: no tolerance
    expect(score("chaor").recalled[1]).toBe(true); // 'chair', one substitution
    expect(score("chiar").recalled[1]).toBe(false); // two edits
  });

  it("credits each list word at most once", () => {
    const s = score("apple apple aple");
    expect(s.nCorrect).toBe(1);
    expect(s.repeats).toBe(2);
    expect(s.intrusions).toEqual([]);
  });

  it("treats other pool words and unknown words as intrusions", () => {
    const s = score("table xyzzy apple");
    expect(s.nCorrect).toBe(1);
    expect(s.intrusions.sort()).toEqual(["table", "xyzzy"]);
  });

  it("resolves a typo that is one edit from two list words deterministically (alphabetical first), crediting only one", () => {
    // 'planx' is one edit from both 'plane' and 'plans'
    const list = ["plans", "plane", "chair", "tree", "river"];
    const a = scoreRecall({ listWords: list, recallText: "planx", pool: POOL });
    expect(a.nCorrect).toBe(1);
    expect(a.recalled).toEqual([false, true, false, false, false]); // 'plane' < 'plans'
    const b = scoreRecall({ listWords: [...list].reverse(), recallText: "planx", pool: POOL });
    expect(b.nCorrect).toBe(1);
    expect(b.recalled[list.length - 1 - 1]).toBe(true); // still 'plane'
  });

  it("returns the recall proportion over the list length", () => {
    expect(score("apple chair").proportion).toBe(2 / 5);
    expect(score("").proportion).toBe(0);
  });
});

describe("serialPositionCurve", () => {
  it("gives the exact proportion recalled at each position across lists (hand-made example)", () => {
    const lists = [
      [true, true, false, false, true],
      [true, false, true, false, true],
      [true, true, false, false, true],
    ];
    expect(serialPositionCurve(lists)).toEqual([1, 2 / 3, 1 / 3, 0, 1]);
  });

  it("works for a single list and rejects ragged or empty input", () => {
    expect(serialPositionCurve([[true, false, true]])).toEqual([1, 0, 1]);
    expect(() => serialPositionCurve([[true, false], [true]])).toThrow();
    expect(() => serialPositionCurve([])).toThrow();
  });
});

describe("sessionRecallProportion (P2: correct words / 40)", () => {
  it("pools the lists of a session", () => {
    expect(sessionRecallProportion([{ nCorrect: 12, listLength: 20 }, { nCorrect: 8, listLength: 20 }])).toBe(0.5);
  });

  it("rejects an empty session", () => {
    expect(() => sessionRecallProportion([])).toThrow();
  });
});
