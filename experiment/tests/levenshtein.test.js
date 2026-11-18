import { describe, it, expect } from "vitest";
import { levenshtein } from "../src/lib/levenshtein.js";

describe("levenshtein", () => {
  it("computes edit distance", () => {
    expect(levenshtein("same", "same")).toBe(0);
    expect(levenshtein("apple", "aple")).toBe(1);
    expect(levenshtein("apple", "apply")).toBe(1);
    expect(levenshtein("kitten", "sitting")).toBe(3);
    expect(levenshtein("", "abc")).toBe(3);
    expect(levenshtein("abc", "")).toBe(3);
  });

  it("is symmetric", () => {
    for (const [a, b] of [["chair", "chiar"], ["table", "tabel"], ["a", "bcd"]]) {
      expect(levenshtein(a, b)).toBe(levenshtein(b, a));
    }
  });
});
