# Free-recall word pool (MB-11)

**File:** `experiment/src/data/wordpool.json` (2,080 words, with source and licence metadata). **Built by:** `experiment/scripts/build-wordpool.mjs` from the EFF Large Wordlist (sha256 in the JSON), seed 20261117.

## Source and licence status
| | |
|---|---|
| Source | EFF Large Wordlist for Passphrases, Joseph Bonneau / Electronic Frontier Foundation, 2016. https://www.eff.org/files/2016/07/18/eff_large_wordlist.txt |
| Licence | CC BY, per EFF's copyright policy (https://www.eff.org/copyright): EFF's original site material is licensed CC BY "unless otherwise noted". |
| Attribution | "Words selected from the EFF Large Wordlist by Joseph Bonneau / Electronic Frontier Foundation." Kept in the JSON and in the README. |

**What was and was not confirmed (Nov 18, 2026):**
- Confirmed: EFF's copyright policy states a CC BY licence for original EFF material; the list is hosted on eff.org and credited to EFF.
- **Not confirmed per file:** the policy page's text names CC BY 4.0 while its badge links CC BY 3.0 US, the list's own page has no licence statement, and EFF's article says the list draws on Ghent University word familiarity and concreteness data, which is third-party. Secondary repositories label it CC BY 3.0 US.
- Practical position: reuse for this research with attribution is low-risk. Revisit before releasing the word list on its own (the open data release will include the words participants saw, with attribution).

## Selection rules
Alphabetic words of 5-8 letters (4 hyphenated or short words excluded); greedy alphabetical removal of any word within one edit of a kept word (so typo matching is never ambiguous across the pool); 520 words per length chosen by seeded shuffle; stored alphabetically. 2,080 = 52 sessions (10 pilot + 42 confirmatory) x 2 lists x 20 words, **each word used exactly once** (no list reuse).

## Lists
Fixed study-wide assignment (`recallLists.js`, seed 20261117): every list has exactly 5 words of each length 5, 6, 7, 8 (length-matched); word order inside a list is shuffled. Session N always gets the same 2 lists; sessions outside 1-52 are refused rather than reusing words.

## Scoring (`recallScore.js`)
Case and surrounding whitespace/punctuation are ignored; responses are split on whitespace, commas and semicolons. A response that is a pool word but not on the list is an intrusion, even when one edit from a list word ("apply" is wrong when "apple" was shown). Otherwise one typo (edit distance 1) is accepted for list words of 5+ letters; ties go to the alphabetically first word; each list word is credited once. P2 = correct words / 40 per session.

## Limitations
- **Word frequency is not controlled.** `design.md` asked for frequency and length matching; no frequency norms with a clear licence were used, so lists are length-matched only. Frequency differences between lists add noise but are not systematic.
- The pool mixes parts of speech and includes a few brand or unusual words (for example "kleenex"). It has had only a keyword check for sensitive words (two false positives), not a manual read.
