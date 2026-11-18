import { describe, it, expect } from "vitest";
import pool from "../src/data/wordpool.json";
import { levenshtein } from "../src/lib/levenshtein.js";

describe("word pool (source, licence and structure)", () => {
  it("records its source, licence and attribution", () => {
    expect(pool.source).toMatch(/EFF/);
    expect(pool.sourceUrl).toMatch(/^https:\/\/www\.eff\.org\//);
    expect(pool.sourceSha256).toMatch(/^[0-9a-f]{64}$/);
    expect(pool.license).toMatch(/CC BY/);
    expect(pool.licenseUrl).toMatch(/^https:\/\//);
    expect(pool.attribution).toMatch(/Bonneau/);
    expect(typeof pool.licenseNote).toBe("string"); // must state what was and was not confirmed
    expect(pool.licenseNote.length).toBeGreaterThan(40);
  });

  it("has exactly 2,080 unique words (52 sessions x 2 lists x 20 words)", () => {
    expect(pool.words).toHaveLength(2080);
    expect(new Set(pool.words).size).toBe(2080);
  });

  it("uses only lowercase alphabetic words of 5-8 letters, 520 of each length", () => {
    for (const w of pool.words) expect(w).toMatch(/^[a-z]{5,8}$/);
    for (const n of [5, 6, 7, 8]) expect(pool.words.filter((w) => w.length === n)).toHaveLength(520);
  });

  it("has no two words within edit distance 1 (so typo matching is unambiguous)", () => {
    const words = pool.words;
    for (let i = 0; i < words.length; i++) {
      for (let j = i + 1; j < words.length; j++) {
        if (Math.abs(words[i].length - words[j].length) > 1) continue;
        expect(levenshtein(words[i], words[j])).toBeGreaterThan(1);
      }
    }
  });

  it("is stored in alphabetical order", () => {
    expect([...pool.words].sort()).toEqual(pool.words);
  });
});
