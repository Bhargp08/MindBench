# Status

## MB-00: Repo, decisions, CI skeleton (merged)

### Approved exception
- The R placeholder test (`analysis/r/tests/testthat/test-placeholder.R`) is skipped via `skip()` until R is installed and confirmed. Bharg approved this skip on PR #1 (Cursor review, Nov 17, 2026). Remove the skip and create `renv.lock` once R is confirmed.

### Deferred items (intentionally not in MB-00)
- `CITATION.cff` (MB-24)
- `experiment/index.html` (MB-06 / MB-12)
- `dashboard/app.py` (MB-16)
- `renv.lock` (once R is installed and confirmed)

## MB-01: Ethics, consent, data management (merged)
- Scope change (Bharg, Nov 17, 2026): Bharg is the only participant for now.
- Written and approved: `docs/ethics/self_pilot_policy.md`, `docs/ethics/data_management.md`.
- Consent form: draft kept in `docs/ethics/consent_form.md` for later use; structure lint tests are active. Must be finalized (contact method filled in) before any other participant takes part. Bharg approved deferring *use* of the form while he is the only participant (Nov 17, 2026).
- The "no institutional approval claims" guard stays active.
- Retention set (Bharg, Nov 17, 2026): raw data until Dec 31, 2028 or 2 years after write-up publication, whichever is later, then deleted; open data on Zenodo kept indefinitely.
- Open placeholder: consent contact method (deferred form).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-02: Canonical task parameters (merged, slimmed scope)
- Scope change (Bharg, Nov 17, 2026): one table of canonical task parameters (`docs/design/literature.csv` + `literature.md`), each row with one source and a verified/[UNVERIFIED] flag.
- **Deferred stretch work (not scheduled):** the expected-effect-size review and the sleep-deprivation literature section (including natural-vs-total sleep loss effect sizes, Lim & Dinges, Ratcliff & Van Dongen, KSS and the remaining spec reference list). Power analysis (MB-04) currently relies on the spec's simulation values.
- Only the staircase rule is verified. All other rows are [UNVERIFIED]; verify against primary papers or set as explicit design choices in MB-03.
- Follow-up: total-deprivation vs natural-variation caveat added to `literature.md` (PR mb/MB-02-caveat).

## MB-03: Design document (merged)
- `docs/design/design.md`: hypotheses H1-H3, explicit design choices for every unverified parameter (Posner 80/20, 2-back 30% targets, trial counts, timings), exclusion rules, analysis summary, stopping and deviation rules.
- Built with Sonnet; spec recommends Opus for MB-03. No code or tests (doc unit).
- Cursor fix before merge: free-recall word-pool requirement corrected to 2,080 (52 sessions × 40 words).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).
- **Superseded by MB-04:** original draft had 5 primary outcomes (P1–P5) with Holm over 5; confirmatory primaries are now P1 (2-back d') and P2 (recall), per Bharg's MB-04 decision.

## MB-04: Power analysis (merged)
- `analysis/python/mindbench/power.py` + tests, `docs/design/power.md`, figure and numbers via `scripts/power_report.py`.
- **Decisions (Bharg, Nov 17, 2026):** keep 42 sessions; reduce primary outcomes to 2 (P1 2-back d', P2 recall proportion), chosen from the verified Lim & Dinges (2010) Table 2; Stroop, Posner, contrast threshold and others are secondary/exploratory, outside the Holm family.
- Effective power at 42 sessions, r = .43 (AR(1) + shared nightly sleep + Holm over 2): about 0.74. 80% effective power needs r of about 0.46. A null result is likely and acceptable.
- Carry to MB-18: AR(1) errors alone do not inflate type-I; the shared AM/PM nightly sleep does (0.083 uncorrected). Model AR(1) errors and day grouping.
- Design doc updated to match (primary/secondary outcomes, H1/H2/H3, Holm family of 2).
- Cursor fix before merge: Holm comparison test uses n_sims=2000 (spec minimum); VERSIONS.md lists exact numpy/scipy/matplotlib pins; MB-03 STATUS notes 5→2 primary supersession.
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-06: Battery scaffold (merged)
- Implemented and tested (24 JS tests): config loader, participant codes, questionnaire validator, mock saver, session metadata, info-screen text. Plus a jsPsych 8.4.0 shell (fullscreen, info screen, participant code, questionnaire, finish) built with Vite 5.4.21.
- Verified by hand in the browser (mock mode): one session produced one JSON file with every field.
- DataPipe: the right package is the **extension** `@jspsych/extension-pipe` 0.2.0, not the plugin (see `docs/design/datapipe.md`).
- Not in this unit originally: tasks (MB-07–MB-11), refresh-rate measurement (timing log in MB-12), DataPipe dashboard setup (Bharg).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-06b: Production saver (merged)
- `experiment/src/lib/pipeExtension.js` (DataPipe extension adapter) + production branch of `createSaver`; shell wired for production mode and a `?simulate` flag. 32 JS tests pass.
- Verified in browser with a fake ID and `?simulate` only; no real upload tested (needs Bharg's DataPipe experiment ID).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026; reopened as PR #9 after stacked #8 closed).

## MB-07: Contrast staircase + SDT block (merged)
- Pure logic (tested): seeded RNG, 1-up/2-down and 1-up/3-down staircase (dB units, range [-40, 0], start -10, step 3 then 1.5 dB after the 2nd reversal, stop at 10 reversals or 60 trials, threshold = mean of last 6 reversals), Gabor luminance, balanced 2IFC intervals, 60-trial yes/no block (30 signal / 30 noise) with hit/FA counts. 60 JS tests pass.
- Canvas shell (`src/tasks/contrast.js`, `src/lib/drawGabor.js`): 2IFC staircase then yes/no block at the session threshold; logs level, contrast, target interval, response and correctness per trial.
- Verified in a browser (mock mode, scripted responder): full session ran without errors; 38 staircase trials, 60 yes/no trials (30/30), per-trial fields logged, Gabor rendering checked visually.
- Design choices recorded: if fewer than 6 reversals occur (trial cap), the final level is used as the threshold and `usedFallback` is logged. d' and c are computed in MB-15.
- Observation for MB-15/ETL: a guessing observer pins the staircase at the 0 dB ceiling (reversals recorded at the clamp). Add a data-quality flag for thresholds at the ceiling or floor.
- Not verified: physical stimulus size and timing accuracy on real displays (Gabor size is in pixels; viewing distance is unspecified); no practice block yet (MB-12).
- Keeping the consent-form lint active (structure only) per Bharg, Nov 17, 2026.
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-08: Posner cueing (merged)
- Tested pure logic: seeded trial generator (120 trials = 96 valid + 24 invalid, sides 60/60 overall and 48/48 + 12/12 by validity, cue direction, fixation 500-1000 ms), response mapping (F = left, J = right), scoring (validity effect = mean invalid - mean valid correct RT, trimming RT < 200 or > 2500 with boundary values kept, accuracy per condition). 74 JS tests pass.
- Shell (`src/tasks/posner.js`) wired into the battery after the contrast block: placeholder boxes, arrow cue 100 ms + 200 ms gap (SOA 300 ms), target until response or 2,500 ms.
- Design choice added to `design.md`: respond to the target side with F/J (the design only said "target until response").
- Verified in a browser harness (10 trials, 8 valid + 2 invalid, scripted responder): correct logging (SOA, validity, side, cue, response, RT), no errors; display checked visually. The full 120-trial block and real RT timing were not run.
- Hypothesis handling follows design.md: the validity effect (S2) is secondary/exploratory and two-sided; MB-15 owns the preregistered exclusion functions.
- Cursor fix before merge: intro text no longer says the arrow is “usually right” (misread as side); clarified to “usually points to where the dot will appear.”
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-09: Stroop (merged)
- Tested pure logic: seeded trial generator (default 60 congruent + 60 incongruent; each ink 15x per condition; each of 12 incongruent pairs exactly 5x; no consecutive word/ink repeats across 1,000 seeds; optional neutral "XXXX" trials, off by default), key mapping (D red, F green, J blue, K yellow), scoring (interference = mean correct incongruent - congruent RT, trim 200/2500 with bounds kept; accuracy interference; neutral RT/accuracy when present). 92 JS tests pass.
- Shell (`src/tasks/stroop.js`) wired into the battery after Posner: ITI 500 ms, stimulus until response or 2,500 ms.
- Design choices added to `design.md`: key-to-color mapping; neutral trials supported but off by default (design says no neutral; Bharg's message listed neutral, so asked for proportions if wanted).
- Verified in a browser harness (8 trials, scripted responder, 4 congruent + 4 incongruent): correct logging, condition/word/ink consistent, no errors; ink colors checked visually. Full 120-trial block and real timing not run.
- Stroop interference is S1 (secondary/exploratory).
- Cursor fix before merge: `buildStroopTrials` throws if it cannot eliminate consecutive word/ink repeats (previously could return a dirty sequence after 200 failed repairs).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-10: 2-back working memory (merged)
- Tested pure logic: normal quantile and d'/criterion (`lib/sdt.js`, log-linear correction by default, throws on extreme rates when uncorrected), seeded 2-back generator (60 trials = 18 targets + 3 one-back + 3 three-back lures + 34 others + 2 start; none in positions 1-2; labels verified against the letters over 200 seeds), and session scoring (positions 1-2 not scored, lures count as false alarms). 116 JS tests pass.
- d' tests use values computed independently with scipy, including a hand-worked example (15/18 hits, 6/40 false alarms: H 0.815789, FA 0.158537, d' 1.899925, c 0.050528) and extreme cases (18/18 and 0/40: d' 4.188857). The same values as the MB-15 Python tests (1.6832, 1.8060, 4.6675) pass in JS. Cursor recompute matched scipy to ≥5 decimals.
- Shell (`src/tasks/nback.js`) wired into the battery after Stroop: letter 500 ms, fixed 2,500 ms trial, SPACE for a match.
- Design choices added to `design.md`: go/no-go response, 58 scored trials, log-linear correction on every dataset. P1 is 2-back d' (primary, Holm family of 2).
- Verified in a browser harness (14 trials, scripted responder): labels and responses correct, no errors. Full 60-trial block and real timing not run.
- MB-15 should reuse these formulas in Python (`sdt.py`) and add cross-language tests.
- Cursor fix before merge: STATUS marked MB-06 / MB-06b / MB-07 as merged (were stale “PR open”).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-11: Free recall (merged)
- 2,080-word pool built from the EFF Large Wordlist (`src/data/wordpool.json`, script `scripts/build-wordpool.mjs`, source sha256 recorded): 520 words each of length 5-8, no two words within one edit. Licence recorded in `docs/design/wordpool.md`: CC BY per EFF's site policy, **not confirmed per file** (policy text/badge disagree on version; list page has no licence line; article cites third-party Ghent data). Attribution in the JSON and README.
- Tested logic: scorer ("Apple ", "aple", "APPLE" correct; "apply" incorrect when it is a pool word; typo tolerance only for 5+ letter words; deterministic ties; no double credit), exact serial-position proportions, session proportion (P2), and a fixed study-wide assignment with **no list reuse across all 52 sessions including the 10 pilot sessions** (every pool word used exactly once; lists length-matched). 147 JS tests pass.
- Shell (`src/tasks/recall.js`) wired into the battery: 2 lists of 20 words at 2 s per word, no distractor, 90 s typed recall with an "I'm done" button; logs per-list score, intrusions and a session summary (`recall_summary`).
- Verified in a browser harness (2 lists of 6 words, scripted typing): words shown in order, typo and punctuation handled, intrusions flagged, summary 6/12 = 0.5. Real study lists load for sessions 1 and 52 and session 53 is refused. Full 20-word/90 s timing not run.
- Limitations: word frequency is not controlled (design asked for it); the pool had a keyword check only for sensitive words and contains a few brand/unusual words.
- Cursor review (Nov 18, 2026): acceptance criteria met; TDD order preserved (no test weakening vs 105051e); local JS 147/147; serial-position hand example recomputed as [1, 2/3, 1/3, 0, 1]; 52×2×20 no-reuse assignment verified via tests.
- Approved by Bharg and merged after Cursor review (Nov 18, 2026).
