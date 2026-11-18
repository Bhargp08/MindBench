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

## MB-06: Battery scaffold (PR open)
- Implemented and tested (24 JS tests): config loader, participant codes, questionnaire validator, mock saver, session metadata, info-screen text. Plus a jsPsych 8.4.0 shell (fullscreen, info screen, participant code, questionnaire, finish) built with Vite 5.4.21.
- Verified by hand in the browser (mock mode): one session produced one JSON file with every field.
- DataPipe: the right package is the **extension** `@jspsych/extension-pipe` 0.2.0, not the plugin (see `docs/design/datapipe.md`). Production saver not yet written (needs its own failing tests and Bharg's approval).
- Not in this unit: tasks (MB-07-MB-11), refresh-rate measurement (timing log in MB-12), DataPipe dashboard setup (Bharg).

## MB-06b: Production saver (stacked on MB-06, PR open)
- `experiment/src/lib/pipeExtension.js` (DataPipe extension adapter) + production branch of `createSaver`; shell wired for production mode and a `?simulate` flag. 32 JS tests pass.
- Verified in browser with a fake ID and `?simulate` only; no real upload tested.
- Do not merge before PR #7 (MB-06).

## MB-07: Contrast staircase + SDT block (PR open)
- Pure logic (tested): seeded RNG, 1-up/2-down and 1-up/3-down staircase (dB units, range [-40, 0], start -10, step 3 then 1.5 dB after the 2nd reversal, stop at 10 reversals or 60 trials, threshold = mean of last 6 reversals), Gabor luminance, balanced 2IFC intervals, 60-trial yes/no block (30 signal / 30 noise) with hit/FA counts. 60 JS tests pass.
- Canvas shell (`src/tasks/contrast.js`, `src/lib/drawGabor.js`): 2IFC staircase then yes/no block at the session threshold; logs level, contrast, target interval, response and correctness per trial.
- Verified in a browser (mock mode, scripted responder): full session ran without errors; 38 staircase trials, 60 yes/no trials (30/30), per-trial fields logged, Gabor rendering checked visually.
- Design choices recorded: if fewer than 6 reversals occur (trial cap), the final level is used as the threshold and `usedFallback` is logged. d' and c are computed in MB-15.
- Observation for MB-15/ETL: a guessing observer pins the staircase at the 0 dB ceiling (reversals recorded at the clamp). Add a data-quality flag for thresholds at the ceiling or floor.
- Not verified: physical stimulus size and timing accuracy on real displays (Gabor size is in pixels; viewing distance is unspecified); no practice block yet (MB-12).
- Keeping the consent-form lint active (structure only) per Bharg, Nov 17, 2026.

## MB-08: Posner cueing (merged)
- Tested pure logic: seeded trial generator (120 trials = 96 valid + 24 invalid, sides 60/60 overall and 48/48 + 12/12 by validity, cue direction, fixation 500-1000 ms), response mapping (F = left, J = right), scoring (validity effect = mean invalid - mean valid correct RT, trimming RT < 200 or > 2500 with boundary values kept, accuracy per condition). 74 JS tests pass.
- Shell (`src/tasks/posner.js`) wired into the battery after the contrast block: placeholder boxes, arrow cue 100 ms + 200 ms gap (SOA 300 ms), target until response or 2,500 ms.
- Design choice added to `design.md`: respond to the target side with F/J (the design only said "target until response").
- Verified in a browser harness (10 trials, 8 valid + 2 invalid, scripted responder): correct logging (SOA, validity, side, cue, response, RT), no errors; display checked visually. The full 120-trial block and real RT timing were not run.
- Hypothesis handling follows design.md: the validity effect (S2) is secondary/exploratory and two-sided; MB-15 owns the preregistered exclusion functions.
- Cursor fix before merge: intro text no longer says the arrow is “usually right” (misread as side); clarified to “usually points to where the dot will appear.”
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).
