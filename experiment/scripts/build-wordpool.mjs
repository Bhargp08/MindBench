// Builds src/data/wordpool.json from the EFF Large Wordlist.
// Usage: node scripts/build-wordpool.mjs /path/to/eff_large_wordlist.txt
// Download: https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt
import { createHash } from "node:crypto";
import { readFileSync, writeFileSync } from "node:fs";
import { createRng, shuffle } from "../src/lib/rng.js";

const SOURCE_SHA256 = "addd35536511597a02fa0a9ff1e5284677b8883b83e986e43f15a3db996b903e";
const SEED = 20261117;
const LENGTHS = [5, 6, 7, 8];
const PER_LENGTH = 520; // 2,080 words = 52 session slots x 2 lists x 20 words (the study uses 44; the rest are spare)

const path = process.argv[2];
if (!path) throw new Error("Pass the path to eff_large_wordlist.txt");
const raw = readFileSync(path);
const sha = createHash("sha256").update(raw).digest("hex");
if (sha !== SOURCE_SHA256) throw new Error(`Unexpected source file (sha256 ${sha})`);

const oneEdit = (a, b) => {
  if (a === b) return true;
  if (Math.abs(a.length - b.length) > 1) return false;
  if (a.length === b.length) {
    let d = 0;
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i] && ++d > 1) return false;
    return d === 1;
  }
  const [s, l] = a.length < b.length ? [a, b] : [b, a];
  let i = 0;
  while (i < s.length && s[i] === l[i]) i++;
  return s.slice(i) === l.slice(i + 1);
};

const candidates = raw
  .toString("utf8")
  .split("\n")
  .map((line) => line.trim().split(/\s+/)[1])
  .filter((w) => w && /^[a-z]{5,8}$/.test(w))
  .sort();

// Greedy near-duplicate removal (alphabetical): keep a word only if it is not within one edit of a kept word.
const kept = [];
for (const w of candidates) if (!kept.some((k) => oneEdit(w, k))) kept.push(w);

const rng = createRng(SEED);
const pool = [];
for (const n of LENGTHS) {
  const bucket = shuffle(kept.filter((w) => w.length === n), rng);
  if (bucket.length < PER_LENGTH) throw new Error(`Only ${bucket.length} words of length ${n}`);
  pool.push(...bucket.slice(0, PER_LENGTH));
}
pool.sort();

const out = {
  source: "EFF Large Wordlist for Passphrases (Joseph Bonneau, Electronic Frontier Foundation, 2016)",
  sourceUrl: "https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt",
  sourceSha256: SOURCE_SHA256,
  license: "CC BY (Creative Commons Attribution), per EFF's site copyright policy",
  licenseUrl: "https://www.eff.org/copyright",
  attribution:
    "Words selected from the EFF Large Wordlist by Joseph Bonneau / Electronic Frontier Foundation, https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases",
  licenseNote:
    "EFF's copyright policy licenses EFF's original site content under CC BY unless otherwise noted (its text names CC BY 4.0 while its badge links CC BY 3.0 US). The list's own page has no per-file licence statement, and EFF's article says the list draws on Ghent University word familiarity and concreteness data (third-party). Not independently confirmed per file; attribution is given. Revisit before redistributing the word list on its own.",
  selection: `Alphabetic words of 5-8 letters; greedy alphabetical removal of words within one edit of a kept word; ${PER_LENGTH} per length chosen by seeded shuffle (seed ${SEED}); stored alphabetically. Built by scripts/build-wordpool.mjs.`,
  words: pool,
};
writeFileSync(new URL("../src/data/wordpool.json", import.meta.url), JSON.stringify(out, null, 1) + "\n");
console.log(`wrote ${pool.length} words`);
