# Canonical task parameters (MB-02, slimmed)

Source of truth: `literature.csv` (columns: task, parameter, value, source, locator, verified).

| Task | Parameter | Value | Verified |
|---|---|---|---|
| Staircase | Rule | 1-up/2-down -> 70.7% correct; 1-up/3-down -> 79.4% (Levitt 1971) | yes |
| Staircase | Reversals, steps, timing | none canonical; MB-03 design choice | [UNVERIFIED] |
| Posner | Cue validity | 80/20 (secondary source for Posner 1980) | [UNVERIFIED] |
| Posner | SOA, trial count | none canonical; MB-03 | [UNVERIFIED] |
| Stroop | 4 colors; proportions, trial count | none canonical; MB-03 | [UNVERIFIED] |
| 2-back | Target rate | ~30% (spec default); no primary source found | [UNVERIFIED] |
| 2-back | Lures | n-1/n+1 used in the literature (Kane et al. 2007); rate unconfirmed | [UNVERIFIED] |
| Free recall | List length | 10-40 words (Murdock 1962, via secondary summaries) | [UNVERIFIED] |
| Free recall | Rate | 2 s/word (lists of 10-20), 1 s/word (lists of 20-40) | [UNVERIFIED] |

Only the staircase rule is verified (also recomputed numerically). Everything else must be flagged `[UNVERIFIED]` if used in MB-03, or checked against the primary paper first. Bibliographic details were confirmed for Murdock (1962) and Posner (1980) by search; their methods were not read in full.

## Caveat: total sleep deprivation vs natural variation

Most sleep–cognition effect sizes in the literature come from **lab total sleep deprivation** (or severe restriction), not from the modest night-to-night variation MindBench will log. Effects under natural sleep variation are expected to be much smaller, so those papers are upper bounds—not planning targets—for detectable effects. Full expected-effect-size and sleep-lit review remain deferred stretch work (see `docs/status/STATUS.md`); this caveat still applies to any sleep-related interpretation in later units.
