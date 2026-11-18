# MindBench Design Document (MB-03)

Status: approved after Cursor review (Nov 17, 2026); Bharg merge authorized. Nothing here is registered yet. Parameters marked **[design choice]** are decisions made here because no canonical value exists in the literature (see `literature.csv`, mostly `[UNVERIFIED]`); they are not claims about the literature.

## 1. Design
- Intensive within-person (N = 1) longitudinal design; main participant: Bharg. No other participants for now.
- **Confirmatory phase:** 21 calendar days, 2 sessions/day (AM, PM) = **42 sessions**. Preceded by **10 pilot sessions** (MB-13) that are flagged `is_pilot` and excluded from all confirmatory analysis.
- **Sleep is observed, never manipulated** (natural night-to-night variation).
- **Timing windows [design choice]:** AM session starts 07:00-11:00 local time and at least 30 min after waking; PM session starts 17:00-21:00. Actual start time is logged.
- **Same device and browser** for every session where possible; both are logged.
- **Task order:** balanced Latin square across the 5 tasks (10 orders, square plus mirror; construction confirmed in MB-12). Session N maps to a fixed order; the order is logged.
- **Session length:** about 25-35 min **(estimate; timed in MB-13)**.

## 2. Predictors and covariates
- **Sleep:** hours slept the previous night, self-logged in the questionnaire before the session (continuous). The PM session of a day uses the same night's value as the AM session.
- **Time of day:** AM vs PM.
- **Covariates:** sleepiness (KSS, 1-9 [scale details to verify in the questionnaire build]), session number, caffeine (yes/no).

## 3. Tasks: explicit design choices
All values below are **[design choice]** unless noted. They are chosen to fit the session budget and to keep every proportion exactly generatable (tests in MB-07 to MB-12).

| Task | Parameters |
|---|---|
| **Contrast staircase** (2-interval forced choice) | Gabor patch, 200 ms per interval. Transformed 1-up/2-down (converges to 70.7%; verified, Levitt 1971). Step 3 dB until the 2nd reversal, then 1.5 dB. Stop after 10 reversals or 60 trials (cap). Threshold = mean of the last 6 reversals. Level clamped to [min, max] set in MB-07. |
| **SDT block** (yes/no) | 60 trials (30 signal, 30 noise) at the session's staircase threshold contrast. d' and criterion c with the log-linear correction (Hautus 1995). |
| **Posner cueing** | Central arrow cue; **80% valid / 20% invalid** (design choice; matches the commonly reported ratio, secondary source only). 120 trials = 96 valid + 24 invalid, left/right balanced 60/60. No neutral or catch trials. Fixation 500-1000 ms jitter, **SOA 300 ms** (cue onset to target onset: arrow 100 ms, then 200 ms blank), target until response or 2,500 ms. **Response [design choice, added in MB-08]:** a filled dot appears in a left or right placeholder box; press F for left, J for right (so errors are possible and "correct trials only" is meaningful). |
| **Stroop** | 4 colors (red, green, blue, yellow), keys D F J K. 120 trials = 60 congruent + 60 incongruent (no neutral); each color 15 times per condition. No immediate repeat of the same word/color pair. Stimulus until response or 2,500 ms; ITI 500 ms. **Keys [design choice, added in MB-09]:** respond to the ink color, D red, F green, J blue, K yellow. Neutral trials ("XXXX") are supported by the code but off by default, matching this no-neutral design. |
| **2-back** | Consonant letters, 60 trials, **30% targets = exactly 18** (design choice; spec default), plus 6 lures (3 one-back, 3 three-back). No targets or lures in positions 1-2. Letter 500 ms, response window 2,000 ms from onset, trial length 2,500 ms. **Response and scoring [design choices, added in MB-10]:** go/no-go, SPACE for a match and nothing otherwise; positions 1-2 are not scored, so a session scores 58 trials (18 targets, 40 non-targets including the 6 lures); lure responses are false alarms. **d' uses the log-linear correction on every dataset** (Hautus 1995: H = (hits + 0.5)/(targets + 1), FA = (false alarms + 0.5)/(non-targets + 1)), so hit or false-alarm rates of 0 or 1 stay finite. |
| **Free recall** | 2 lists/session of 20 words each, **2 s per word** (Murdock 1962 used 2 s for lists up to 20; the exact setup is secondary-source only). No distractor (keeps recency), 90 s typed recall per list. No list reuse: the pool needs at least 2,080 unique words for 42 confirmatory + 10 pilot sessions (52 × 40); the source and license are confirmed in MB-11. Matching: case/whitespace-normalized, Levenshtein <= 1 for words of 5+ letters; ties resolved deterministically. |

Each task has a short instruction screen and a practice block with feedback (MB-12).

## 4. Hypotheses and outcomes
**Primary outcomes (2; preregistered; the only members of the Holm family):**
| ID | Outcome (per session) | Definition |
|---|---|---|
| P1 | 2-back d' | z(H) - z(FA) with log-linear correction (higher = better) |
| P2 | Recall proportion | Correct words / 40 (higher = better; serial-position curve is secondary) |

**Why these two (decision by Bharg, Nov 17, 2026; evidence in `power.md`):** among the battery's outcomes they have the strongest prior evidence of sensitivity to sleep loss in the Lim & Dinges (2010) meta-analysis of 24-48 h total sleep deprivation (working-memory accuracy g = -0.555; short-term memory recall g = -0.383, with directly matching n-back and verbal recall studies). That evidence is from total sleep deprivation; effects of natural sleep variation are probably smaller.

**Secondary / exploratory (outside the Holm family; no multiplicity correction; labeled exploratory in all reports):**
| ID | Outcome | Definition |
|---|---|---|
| S1 | Stroop interference | Mean correct incongruent RT minus mean correct congruent RT (ms), after trimming |
| S2 | Posner validity effect | Mean correct invalid RT minus mean correct valid RT (ms), after trimming |
| S3 | Contrast threshold | Mean of last 6 reversals (lower = better) |
| S4 | SDT d' and criterion c | Yes/no block, log-linear corrected |
| S5 | Other | Stroop accuracy interference, mean RT per task, recall serial-position curve, DDM parameters (H3), sleepiness effects |

- **H1 (sleep, directional, confirmatory):** more prior-night sleep predicts better performance: higher P1 and higher P2. Directional predictions for the secondary outcomes (lower S1 interference, lower S3 threshold; S2 two-sided, no reliable direction **[UNVERIFIED]**) are exploratory.
- **H2 (time of day, two-sided, confirmatory):** AM and PM differ on P1 and P2 (no direction assumed: time-of-day effects are task-dependent). Tested with paired AM/PM comparisons within day. The same comparison on S1-S3 is exploratory.
- **H3 (mechanism, Stroop and Posner; exploratory, outside the Holm family):** if sleep or time of day has an effect on RT performance (S1, S2), it acts on drift rate v, boundary separation a, both, or neither. Expectation that less sleep lowers drift rate is **[UNVERIFIED]**. "Cannot tell" is an acceptable answer.
- **Classic-effect checks (manipulation checks, not hypotheses):** Stroop interference > 0, Posner validity effect > 0, a U-shaped serial-position curve.

## 5. Exclusion and data rules (code exactly as written, MB-15)
1. **Trial RT trimming:** drop Stroop and Posner trials with RT < 200 ms or > 2,500 ms (RT exactly 200 or 2,500 is kept). Design choice: the upper bound equals the response deadline.
2. **Error trials:** RT outcomes (S1, S2) use correct trials only.
3. **Session exclusion:** exclude the whole session if Stroop congruent accuracy < 60% (exactly 60% is kept), or if the session is incomplete (any of the 5 tasks or the questionnaire missing).
4. **Pilot data:** the first 10 sessions (`is_pilot = 1`) are never in confirmatory analyses.
5. **Missing data:** no imputation. Sessions missing the sleep log are dropped from H1 analyses only. Missing sessions are not made up, except the extension rule in section 7.
6. **Stop rule:** a stopped session (see `self_pilot_policy.md`) counts as incomplete.

## 6. Analysis plan (summary; details in MB-18 to MB-21)
- **H1:** per outcome (P1, P2 confirmatory; S-outcomes exploratory), regression of the outcome on sleep hours, session number (linear plus log term) and time of day, with AR(1) or HAC errors; the PM and AM of a day are not independent, so day is a grouping term. Report estimates with 95% intervals, plus a Bayesian version (MB-20).
- **H2:** paired AM/PM difference per day (paired t, bootstrap CI with at least 10,000 resamples).
- **H3:** DDM fits per condition (PyDDM) with competing drift/boundary/both/neither models, compared by BIC; posterior-predictive checks on RT quantiles.
- **Practice effects:** modeled explicitly via session number, preregistered.
- **Multiple comparisons:** Holm correction across the 2 primary outcomes (P1, P2) within each of H1 and H2 (alpha = .05). Secondary outcomes are reported without correction and labeled exploratory. Effective power under this family is in `power.md` (about 0.74 at r = 0.43, 42 sessions, with AR(1) and shared nightly sleep).
- **Inference criteria:** a frequentist effect is "supported" if its Holm-adjusted p < .05 and the direction matches; null results are reported as such, with intervals.

## 7. Stopping rule and deviations
- **Stopping rule:** collection stops after 21 calendar days of confirmatory sessions (42 scheduled). Missed sessions may be recovered by extending up to 7 extra days, stopping at 42 completed sessions at the latest. No peeking at hypothesis tests during collection (the dashboard shows data quality only).
- **Deviations:** any change after registration is logged in `docs/design/deviations.md` with date, reason and effect, and is reported in the write-up. Changes to a preregistered decision need Bharg's decision first.

## 8. Open items
- Per-parameter literature checks (Posner 80/20, Murdock details, n-back target rate) remain `[UNVERIFIED]`; they are design choices, not citations.
- Stimulus ranges for the staircase, the word-pool source, and the Latin-square construction are settled in MB-07, MB-11 and MB-12.
- Built with Sonnet (spec recommends Opus). Cursor consistency review completed Nov 17, 2026 (DVs ↔ hypotheses ↔ analyses); Opus self-review still optional.
