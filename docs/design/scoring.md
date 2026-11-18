# Scoring, exclusions and SDT (MB-15)

Code: `analysis/python/mindbench/{sdt,exclusions,scoring,data}.py`. Tests: `analysis/python/tests/` (synthetic data only; fixtures come from `etl/tests/fixtures`).

Data flow: browser raw rows -> Drive -> ETL (`etl.md`) -> SQLite -> `load_sessions` -> rules -> `score_session` / `score_database`. `apply_exclusions(conn)` writes the automatic reasons into `sessions.excluded_reason` (prefix `auto: `; a reason without that prefix was entered by hand and is never overwritten).

## Where d' comes from (P1 and S4)
The browser logs only raw responses (`type`, `position`, `responded` for the 2-back; `isSignal`, `respondedYes` for yes/no). **No d' is stored in the data.** P1 and S4 are computed only in `mindbench/sdt.py` (Hautus 1995 log-linear correction on every dataset: H = (hits + 0.5)/(n_signal + 1), FA = (false alarms + 0.5)/(n_noise + 1); d' = z(H) - z(FA); c = -(z(H) + z(FA))/2).

`experiment/src/lib/sdt.js` (used by the browser-side `scoreNBack`, which the shell does not call) is a separate JavaScript implementation of the same formula. `tests/test_sdt_crosslang.py` runs both on a grid of counts and requires agreement to 1e-7, so they cannot drift apart. Spec values: H .80 / FA .20 -> d' 1.6832, c 0; H .90 / FA .30 -> 1.8060, -0.3786; 50/50 hits and 0/50 false alarms -> 4.6675.

## Rules (design.md section 5, one function each; each docstring quotes the rule and a test checks it)
| Rule | Function | Boundary tested |
|---|---|---|
| 1 RT trimming (Stroop, Posner) | `rule1_trim_rt` | 200 and 2,500 kept; 199.999 and 2,500.001 dropped |
| 2 correct trials only (S1, S2) | `rule2_correct_trials_only` | errors and missing responses dropped |
| 3 session exclusion | `rule3_session_exclusion` | Stroop congruent accuracy exactly 60% kept (integer arithmetic), 59/100 excluded; one trial short = incomplete |
| 4 smoke-test sessions | `rule4_smoke_test_session` | `is_pilot` 1 excluded; 0 or NULL kept |
| 5 missing sleep log (H1 only) | `rule5_missing_sleep_log`, `h1_eligible` | 0 hours is present; None is missing |
| 6 stopped session = incomplete | `rule6_stopped_session` | no timing row, or unfinished tasks |

Practice rows (`practice = 1`) and untagged rows (fixation, cues) are never scored: this is a precondition from `battery.md`/`etl.md`, not one of the six rules.

## Interpretations the rule text leaves open (preregistration-relevant; state them in the prereg)
An independent review of the rule code (Nov 18, 2026) found no blockers; items 1-2 below were changed after it.
1. **RT trimming (rule 1) applies to RT outcomes. The rule 3 accuracy check is made on all scored congruent trials before trimming**, so anticipations (under 200 ms) count as trials and as errors if wrong. (An earlier version dropped them first, which let key-mashing under 200 ms dodge the check.) Fast correct responses count as correct. Trials with no response have no RT, are not trimmed, and count as errors. Stroop accuracy measures in the scores use the same untrimmed trials.
2. **2-back response window: a response counts only if its RT is 2,000 ms or less from letter onset** (design.md section 3: "response window 2,000 ms from onset"). The trial lasts 2,500 ms and the browser records later presses, so the window is enforced in scoring (`NBACK_RESPONSE_WINDOW_MS`). A press at 2,001-2,500 ms is a miss (on a target) or a correct rejection (on a non-target).
3. **"Incomplete" (rule 3) means a task is present only if all its scored trials are present** at the design counts (Posner 120, Stroop 120, 2-back 60, yes/no 60, 2 recall lists plus the summary row; contrast also needs the staircase's threshold row), not merely that some rows exist. Fewer is incomplete; **more is not an exclusion** but appears in `data_warnings`. The counts are the defaults in `EXPECTED_SCORED` and are tested at full size.
4. **A stopped session (rule 6)** is one with no final `timing` row or with unfinished tasks listed in it. **In practice a stopped session usually never reaches the database**: DataPipe leaves abandoned runs as `.partial.json` files, which the ETL skips. Stopped sessions therefore show up as **missing sessions (gaps in the session numbers, and skipped partial files), not as excluded ones**; the preregistration should say so, and the dashboard/collection report (MB-16, MB-17) should list them, because the stopping rule counts completed sessions.
5. **Sleep log missing (rule 5)** means no questionnaire or `hours_slept` NULL; 0 hours is a valid log. This **cannot currently occur through the ETL**: a file without a sleep log is rejected as invalid (so that session would drop out of all analyses, not only H1). The browser form requires the answer, so the case is latent; the rule stays as a safeguard.
6. **P2 uses the browser-computed per-list `nCorrect`**, with a consistency check (`P2_consistent`, and `data_warnings`) against the recalled flags and the summary row. The raw `recallText` is stored, so recall can be re-scored in Python if ever needed.
7. **Yes/no trials with no response are coded "no"**; the count is reported as `S4_n_no_response`, and `S3_used_fallback` marks sessions where the staircase hit its trial cap before 6 reversals. Report both with S4.
8. **Smoke-test flag (rule 4)** comes from the browser's session counter (see `etl.md`); check `SELECT session_number, is_pilot FROM sessions` before analysis.

## Scores per session
P1 `P1_dprime`/`P1_criterion` (positions 1-2 not scored, lures are non-targets, 2,000 ms window; lure false alarms reported as `P1_lure_false_alarms`); P2 `P2_recall_proportion` (correct words / 40); S1 Stroop interference (plus accuracy interference); S2 Posner validity effect; S3 contrast threshold (dB, contrast, `used_fallback`); S4 yes/no d' and c; recall serial-position curve; covariates (sleep hours, KSS, caffeine, session number, timestamp); `P2_consistent`, `S4_n_no_response` and `warnings` (`data_warnings`). Missing measures are `None`, never 0.

## Not done here
Counting of the preregistered analyses (MB-18 to MB-21); CSV export for R (MB-18 will define its table); the 2-back and recall "classic effect" checks.
