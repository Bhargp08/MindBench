# MindBench Preregistration (OSF Registries): DRAFT, not submitted

**Status:** draft for Bharg to review and submit himself. **Nothing has been submitted anywhere.** Written Nov 18, 2026. Source documents: `design.md`, `power.md`, `scoring.md`, `battery.md`, `etl.md`, `wordpool.md`, `deviations.md`, `prereg_notes.md`. Everything under the six numbered sections below (Study Information to Other) is written to be pasted into the form; the two sections before and after are for you and are not part of the registration.

---

## Before you submit (for Bharg; not part of the registration)

**1. Order of events (please choose; this changes one answer).**
- Deploy the site (needs your approval), run the 1-2 **smoke-test** sessions to confirm saving works, **then register, then start confirmatory collection** (register before the first confirmatory session, session 3). The smoke-test sessions are real data that exist before registration. Keep them unanalyzed: check only that files arrived and rows loaded (counts), **do not run the scoring code on them or look at performance values**, and answer "Existing data" as in section 3 below (Option A). This draft uses Option A only (decision D8).
- If you would rather register before any data exist, tell me and I will rewrite the Existing data answer; the draft does not carry two versions.
- Either way the smoke-test sessions must be study sessions 1-2 (same browser profile as the study, so the session counter continues at 3; see `etl.md`).

**2. Freeze the documents the registration cites.** After this PR is merged, create a tag and note its commit hash (these are your actions; I have not created a tag or pushed anything):
```bash
git checkout main && git pull
git tag -a prereg-v1 -m "Frozen documents cited by the OSF registration"
git push origin prereg-v1
git rev-parse prereg-v1^{commit}      # full commit hash to paste below
```
Paste it where the draft says **[FREEZE COMMIT: full hash of tag prereg-v1]** (section 6). Files at their last-changed commits when this was written: `design.md` be31a9e, `power.md` d2e545c, `scoring.md` be31a9e, `prereg_notes.md` be31a9e. If you already created `prereg-v1` from an earlier version of this draft, re-tag it after this PR is merged (delete the old tag, create it again on the merge commit) so that the tag contains this version; a hash from the old tag would not match. After the tag, a change to any of these is a deviation.

**3. Template caveat.** OSF Registries offers a standard template named "OSF Preregistration" (confirmed on OSF's help site). Its exact field labels were **not** verified from OSF's own pages (the section names below come from secondary copies of the template). Open the form at https://osf.io/prereg/, start a registration directly (no OSF Project is needed), and map the answers below to its fields. Registrations cannot be edited or deleted once submitted; withdrawal is possible but irreversible. You can submit publicly or under an embargo of up to four years (OSF help, checked Nov 18, 2026).

**4. Decisions I proposed where the design left a detail open.** Each is written into the text below as a default and marked `[DECISION Dn]`. Please confirm or change them (and ask for a statistical read of D3-D7) **before** submitting, because they cannot be changed afterwards without a logged deviation.

| # | Decision | Default in this draft |
|---|---|---|
| D1 | Time-of-day variable | By logged local start time: AM = 04:00 to before 12:00, PM = 12:00 to 23:59 or 00:00 up to 04:00 (see D2); sessions starting outside the 07:00-11:00 / 17:00-21:00 windows are kept but flagged, with a sensitivity analysis that drops them |
| D2 | "Day" and the PM sleep value | Day = local calendar date of the start, except that a session starting from 00:00 up to 04:00 belongs to the previous calendar day (and counts as its PM session); a PM session uses that day's AM-session sleep value (its own report if the AM session is missing) |
| D3 | H1 model | Linear mixed model fitted by REML: random intercept for day plus AR(1) residuals over calendar slots (slot = 2*(day-1)+PM+1, so missed sessions leave gaps); predictors sleep, session number (linear + log), PM; b1 tested with a t test on df = included days - 5; KSS and caffeine not in the primary model. The earlier GLS (AR(1) in session order) is a sensitivity analysis only |
| D4 | H2 test and interval | Paired t on days with both sessions usable; BCa bootstrap (10,000 resamples of whole days) for the interval |
| D5 | Bayesian priors and model | Same structure as the D3 model (day intercept, AR(1) over slots) on standardized outcomes; weakly informative priors listed in section 5; supplementary only |
| D6 | ICC definition | ICC(3,1) with days as targets and AM/PM as the two measurements, computed on residuals after removing practice (y ~ k + ln(k)); the raw ICC is also reported; plus split-half with Spearman-Brown |
| D7 | H3 session groups and DDM structure | Below / above the median sleep hours (sessions at the median are left out of the sleep comparison); AM vs PM; congruency (Stroop) and cue validity (Posner) always drive drift; boundary comparison reported as not identifiable when error trials are scarce |
| D8 | Existing data answer | Option A (smoke tests run before registration, unanalyzed) |
| D9 | AM/PM, "completed session" and the session-slot cap | AM/PM comes from the logged start time, not from odd/even session numbers; completed = the battery finished (final timing record), even if rule 3 later excludes it; stopped sessions use up session numbers and word lists; collection also stops when session slot 52 is reached |
| D10 | AI-assistance and conflict statements | Included in section 6; edit to your wording |

**5. Things only you can do:** submit the registration; choose public vs embargo; deploy the site; create the DataPipe experiment and the Google Drive access for the ETL; run the smoke tests.

---

## 1. Study Information

**Title.** MindBench: Does naturally varying sleep, or time of day, change attention and memory in one person? A preregistered within-person (N = 1) study with a browser battery.

**Description.** One adult (the researcher, Bharg Patel) completes a browser-based battery of five short tasks (contrast detection with a yes/no signal-detection block, Posner spatial cueing, Stroop, 2-back working memory, and serial-position free recall), twice a day (morning and evening) for 21 calendar days. He records how long he slept the night before each session. Sleep is only observed, never restricted or changed. The study asks (1) whether prior-night sleep duration and time of day change performance, and (2) whether any change in speeded tasks reflects evidence-accumulation speed (drift rate) or response caution (decision boundary). The confirmatory analyses are frequentist (a mixed model with a day effect and AR(1) errors), supplemented by Bayesian regression and drift-diffusion models.

This is a personal, preregistered self-experiment. No institutional review board review has been obtained, and no institutional oversight is claimed. **No formal pilot study was run** (see section 6). The study can support conclusions about this one person only. Because natural sleep variation is probably much smaller than the experimentally induced sleep loss in the literature, and only large within-person effects are detectable (section 3), **a null result is likely and is an acceptable outcome.**

**Hypotheses.**
- **H1 (sleep; directional; confirmatory).** More prior-night sleep predicts better performance: a **higher 2-back d' (P1)** and a **higher free-recall proportion (P2)**.
- **H2 (time of day; two-sided; confirmatory).** Morning and evening sessions differ on P1 and P2 (no direction is assumed; time-of-day effects are task-dependent).
- **H3 (mechanism; exploratory; outside the Holm family).** If sleep or time of day affects speeded performance (Stroop interference S1, Posner validity effect S2), the change acts on drift rate, on boundary separation, on both, or on neither. "Cannot tell" is an acceptable answer. The expectation that less sleep lowers drift rate is unverified.
- **Secondary / exploratory outcomes** (no multiplicity correction; labeled exploratory everywhere): S1 Stroop interference (predicted lower with more sleep), S2 Posner validity effect (two-sided), S3 contrast threshold (predicted lower with more sleep), S4 yes/no d' and criterion c (two-sided), S5 other measures (section 4). The same-day AM/PM comparison on S1-S3 is also exploratory.
- **Manipulation checks (not hypotheses).** Stroop interference > 0, Posner validity effect > 0, and a U-shaped serial-position curve (primacy and recency).

---

## 2. Design Plan

**Study type.** Observational, within-person (N = 1) intensive longitudinal study. No experimental manipulation of sleep.

**Blinding.** None. The researcher is the only participant and knows his sleep. Task order, trial order and word lists are seeded and fixed in advance in the code (below). The analysis code is written and tested on simulated data, and committed, before any confirmatory outcome is analyzed, and no hypothesis tests are run during collection (the dashboard shows data-quality information only).

**Study design.**
- 21 calendar days, 2 sessions per day (morning, evening) = **42 confirmatory sessions** (study sessions 3-44, below). Morning sessions are planned for 07:00-11:00 local time and at least 30 minutes after waking; evening sessions for 17:00-21:00. The actual start time is logged. Same device and browser for every session where possible; 57 cm viewing distance is instructed (not measured).
- **Predictors:** hours slept the previous night (self-report before each session), time of day (AM/PM). **Covariates:** session number, sleepiness (Karolinska Sleepiness Scale, 1-9, asked before each session), caffeine in the last 4 hours (yes/no).
- **Counterbalancing:** task order follows a balanced Latin square for the five tasks (10 orders: a zigzag base row cyclically shifted five times plus the mirror of each; every task appears in every position twice and every ordered adjacent pair twice). The order for session N is fixed in advance and offset by 5 for evening sessions, so an order is not tied to time of day (`battery.md`). Task order is logged.
- **Practice:** every task starts with a short practice block with feedback (contrast 6 trials, Posner 8, Stroop 8, 2-back 12, recall 1 list of 4 words). Practice data are tagged and never analyzed.

**Randomization.** Seeded pseudo-random trial orders (seed derived from participant code and session number); a fixed, study-wide assignment of 2,080 words to 52 session slots (seed 20261117), with no word reused.

---

## 3. Sampling Plan

**Existing data.** (The option wording follows secondary copies of the template; use the form's own labels.) "Registration prior to analysis of the data." One or two smoke-test sessions (study sessions 1-2, flagged `is_pilot = 1`) were collected on the deployed site only to confirm that data saving works. They are excluded from all analyses. Their files and row counts were checked; their performance values and sleep values were not examined or scored. **[DECISION D8: Option A is written here; tell me if you want to register before any data exist.]**

**Explanation of existing data.** As above. No formal pilot data exist. The design was not informed by any data from this participant or from other people.

**Data collection procedures.** Participant: the researcher only (an adult). No recruitment, payment or other participants. The experiment is a static web page (jsPsych 8.4.0) that sends each session's data through DataPipe to a private Google Drive folder; a local Python ETL validates the files and loads them into SQLite (`etl.md`). Each session has a participant code (random, no names, emails or IP addresses), a session questionnaire (hours slept last night, bed and wake times, KSS, caffeine, device), session metadata (time, time zone, browser, screen size, refresh-rate estimate) and the five tasks:

| Task | Trials and parameters (all documented design choices; only the staircase rule is taken from the literature) |
|---|---|
| Contrast detection | Two-interval forced choice with a Gabor patch (200 ms per interval), 1-up/2-down staircase (70.7% correct; step 3 dB until the 2nd reversal, then 1.5 dB), stop after 10 reversals or 60 trials, threshold = mean of the last 6 reversals. Then a yes/no block of 60 trials (30 signal, 30 noise) at that threshold. |
| Posner cueing | 120 trials: 96 valid and 24 invalid (80/20), left/right balanced; arrow cue 100 ms, SOA 300 ms; respond to the target side (F left, J right); target until response or 2,500 ms. |
| Stroop | 120 trials: 60 congruent and 60 incongruent, 4 ink colors (D red, F green, J blue, K yellow); respond to the ink color; until response or 2,500 ms. |
| 2-back | 60 consonant letters: 18 targets (30%), 6 lures (3 one-back, 3 three-back); none in positions 1-2; letter 500 ms; SPACE for a match; **responses count only within 2,000 ms of letter onset.** |
| Free recall | 2 lists of 20 words, 2 s per word, no distractor, 90 s of typed recall per list; words from a fixed 2,080-word pool (5-8 letters; each list has 5 words of each length), no word reused; typo-tolerant matching (edit distance 1 for list words of 5+ letters). Lists are length-matched, not frequency-matched. |

Session length is expected to be about 25-35 minutes (an estimate, not yet measured).

**Sample size.** One participant. **42 confirmatory sessions** (study sessions 3-44) over **21 calendar days**, two per day. **44 planned sessions** in total, counting the 1-2 smoke-test sessions (study sessions 1-2); the word pool covers 52 session slots, so 8 slots (45-52) are spare.

**Sample size rationale.** Chosen for feasibility (2-3 weeks of daily sessions), not for a target effect size; no reliable effect size for natural sleep variation is available. A simulation of the primary model (`power.md`; 2,000 simulations per scenario; REML mixed model with a day intercept and AR(1) residuals over calendar slots; sleep shared by the AM and PM sessions of a day; 30% of the residual variance shared within a day, AR(1) phi = 0.3; Holm over the 2 primary outcomes; no missed sessions) gives these effective powers at 42 sessions: within-person r = 0.43: **0.58**; r = 0.30: **0.27**; 80% effective power needs r of about **0.53**. The type-I error of one test in the same model is 0.06 (family-wise 0.06 under Holm). The earlier GLS analysis that ignored the day component would have a type-I error of about 0.10 in this scenario, which is why the day effect is in the primary model. For H2, 21 paired days at d_z = 0.65 give 0.81 for one test and 0.71 at alpha = .025 (80% at alpha = .025 would need 26 pairs). These figures come from the author's simulation, not from the literature; missed sessions and practice effects are not simulated, so real power is lower. The study can reliably detect only large within-person effects; effects of natural sleep variation are probably smaller than those from total sleep deprivation (the evidence for choosing the two primary outcomes, Lim & Dinges 2010, is from 24-48 h total deprivation).

**Stopping rule.** Confirmatory collection stops after 21 calendar days (42 scheduled sessions). Missed sessions may be recovered by extending up to 7 extra days, and collection stops at 42 completed sessions at the latest. A session is completed when its battery finished (a final timing record exists), even if a rule in the exclusion section later excludes it. A stopped session uses up its session number and word list, so collection also stops if session slot 52 is reached. No hypothesis tests are run during collection. **[DECISION D9]**

---

## 4. Variables

**Manipulated variables.** None. Sleep is observed.

**Measured variables.**
- **Predictors:** `hours slept` (self-report, 0-16, before each session); `time of day` (AM/PM; D1 below).
- **Covariates:** study session number; KSS (1-9); caffeine (yes/no).
- **Primary outcomes (per session):**
  - **P1: 2-back d'** = z(H) - z(FA), with the log-linear correction (Hautus 1995) applied to every dataset: H = (hits + 0.5)/(targets + 1), FA = (false alarms + 0.5)/(non-targets + 1). Positions 1-2 are not scored, so a session scores 58 trials (18 targets; 40 non-targets, including the 6 lures; responses to lures are false alarms). A response counts only if it comes within 2,000 ms of letter onset. Higher = better.
  - **P2: recall proportion** = correct words over the 2 scored lists / 40. Higher = better.
- **Secondary / exploratory outcomes (per session):**
  - **S1** Stroop interference: mean RT of correct incongruent trials minus mean RT of correct congruent trials (ms), after RT trimming.
  - **S2** Posner validity effect: mean correct invalid RT minus mean correct valid RT (ms), after trimming.
  - **S3** contrast threshold: mean of the last 6 staircase reversals (dB re full contrast; lower = better); sessions where the staircase hit its trial cap before 6 reversals are marked (final level used).
  - **S4** yes/no d' and criterion c at the threshold contrast (log-linear corrected); the number of trials without a response is reported (coded "no").
  - **S5** other: Stroop accuracy interference (congruent minus incongruent accuracy), mean RT per task, recall serial-position curve, drift-diffusion parameters (H3), sleepiness effects.

**Indices.** All outcome scores are computed by `analysis/python/mindbench/scoring.py` from the raw trial data; the browser stores no outcome scores except the staircase threshold and the per-list recall counts (the recall counts are cross-checked against the stored recalled flags and summary row). Missing measures are missing, never 0.

---

## 5. Analysis Plan

Software: Python (PyMC, ArviZ, PyDDM, SciPy; the primary model is fitted by `mindbench.mixed_power`) and R (tidyverse, glmmTMB, nlme, boot); exact versions are pinned in `docs/VERSIONS.md` at the frozen commit. The Python REML fit is cross-checked against R `glmmTMB` (random intercept for day, AR(1) over the slot factor) once R is available; a material disagreement is reported.

**Statistical models.**

*H1 (confirmatory).* For each primary outcome y (P1, P2), over included sessions (rules below), the linear mixed model
`y = b0 + b1*sleep + b2*k + b3*ln(k) + b4*PM + u_day + e`,
where `sleep` is hours slept (centered at its mean over included sessions), `k` = study session number minus 2 (so the first confirmatory session is k = 1), `PM` = 1 for evening sessions, `u_day` is a random intercept for day (shared by the two sessions of a day), and `e` has AR(1) autocorrelation over calendar slots: slot = 2*(day-1)+PM+1, so correlation depends on the distance in slots and missed sessions leave gaps rather than shifting later sessions. Fitted by REML (Python, `mindbench.mixed_power`; both variance components and phi estimated). The test of H1 is the two-sided t test of b1 on df = included days - 5 (a small-sample choice: with 21 days the residual df is limited by the number of days); the direction must be positive. Reported: b1 with a 95% interval. KSS and caffeine are not in the primary model (KSS lies on the causal path from sleep to performance); they are added in exploratory models. **Sensitivity analyses (not used for the decision):** the earlier GLS with AR(1) errors in session order (`nlme::gls`, corAR1), the same with continuous-time AR(1) over slots (corCAR1), and the mixed model with day-clustered robust standard errors; results are reported side by side. **[DECISION D3]**

*H2 (confirmatory).* For each primary outcome, over days on which both the AM and PM sessions are included, the difference PM - AM; a two-sided paired t test of the mean difference; 95% interval from a BCa bootstrap (10,000 resamples of whole days, fixed seed). The effect size d_z is reported. The within-day difference mixes time of day with practice; the `PM` coefficient in the H1 model is reported alongside. **[DECISION D4]**

*Time of day, day and sleep value.* Time of day is defined from the logged local start time, not from odd/even session numbers: AM = 04:00 to before 12:00, PM = 12:00 or later. A day is the local calendar date of the start, except that a session starting between 00:00 and 04:00 belongs to the previous calendar day and counts as its PM session (so a late-night session is not mistaken for the morning of the next date), and it uses that previous day's sleep value. Sessions that start outside the planned windows (07:00-11:00, 17:00-21:00) are kept, flagged, and a sensitivity analysis drops them. The PM session of a day uses that day's AM-session sleep value; if the AM session is missing, the PM session's own report is used. If two sessions fall in the same slot of one day, both are kept and flagged. **[DECISIONS D1, D2, D9]**

*Manipulation checks (not hypotheses).* Stroop interference: mean of S1 over included sessions with a 95% interval (one-sample t, and a BCa bootstrap with 10,000 resamples of whole days); same for the Posner validity effect S2. Serial position: mean proportion recalled at positions 1-3 minus positions 8-12 (primacy) and positions 18-20 minus positions 8-12 (recency), each with a 95% interval. No correction; reported descriptively.

*Secondary and exploratory outcomes.* The H1 model is run for S1-S4 and the S5 measures, and the H2 comparison for S1-S3; no correction; every result labeled exploratory. A repeated-measures ANOVA is not planned (the design is a single-person time series, not a factorial design).

*Regression diagnostics (all models).* Residual plots, influence (Cook's distance), normality and heteroscedasticity checks are reported. They never remove observations; points with Cook's D above 4/n are flagged and the model is refit without them as a sensitivity analysis.

*Bayesian regression (supplementary; not used for the confirmatory decision).* PyMC models matching the D3 model for P1 and P2 (day intercept, AR(1) over calendar slots, same predictors), on outcomes standardized (z-scored) across included sessions, with sleep in hours, centered at its mean. The AR(1) process is a latent series over all calendar slots with a one-step-ahead conditional likelihood, so missed slots carry no observation. Priors: intercept ~ N(0, 1); slopes b1-b4 ~ N(0, 0.5) per hour of sleep (per unit for the other predictors); day-intercept SD ~ HalfNormal(1); AR(1) coefficient ~ N(0, 0.5) truncated to (-1, 1); residual SD ~ HalfNormal(1). NUTS; reported: posterior mean, 95% credible interval and P(b1 > 0). Diagnostics: R-hat < 1.01, bulk and tail ESS > 400, no divergences; prior and posterior predictive checks. Model comparison with WAIC and PSIS-LOO (ArviZ; Pareto-k reported) for the model with versus without the sleep term. **[DECISION D5]**

*Drift-diffusion models (H3; exploratory).* For Stroop and Posner (correct and error RTs together), PyDDM fits. In every model the trial-level condition drives drift rate (congruency for Stroop, cue validity for Posner); the competing models then let drift rate, boundary separation, both, or neither differ between sessions (below-median vs above-median sleep; AM vs PM). They are compared by BIC (a difference under 2 is reported as "cannot tell"); starting point unbiased, non-decision time shared across conditions. Boundary separation is called not identifiable, and its comparison is not reported, when error trials are under 5% of the trials in either session group, because boundary and drift then trade off. Posterior/fit predictive checks of RT quantiles (.1, .3, .5, .7, .9) for correct and error responses; EZ-diffusion as a sanity check. Sessions exactly at the median are left out of the sleep comparison. The detailed DDM specification will be committed to `docs/design/` before the first confirmatory session; changes after that are logged deviations. **[DECISION D7]**

*Reliability (exploratory).* Test-retest: ICC(3,1) with days as targets and the AM and PM sessions as the two measurements, with 95% intervals, for each task outcome. It is computed on residuals from the practice model y ~ k + ln(k), so that learning across the study does not inflate stability, and the raw ICC (no residualizing) is reported next to it. Split-half reliability within session (odd vs even trials) with Spearman-Brown correction. Interpreted with Koo & Li (2016) thresholds (thresholds not yet verified). This describes day-to-day stability within this one person, not between-person reliability. **[DECISION D6]**

*Practice effects.* Modeled through `k` and `ln(k)` in every model. Because there was no pilot phase, the steepest early learning falls inside the confirmatory sessions; the report states how much early change the two terms absorb.

**Transformations.** None, except RT trimming (below), centering of sleep, and z-scoring of outcomes in the Bayesian models.

**Inference criteria.** Alpha = .05, two-sided tests. **Holm correction over the two primary outcomes (P1, P2), separately within H1 (on b1) and within H2.** An effect is "supported" if its Holm-adjusted p is below .05 and its direction matches the hypothesis (H1: positive). An H1 result in the wrong direction (negative b1, even if significant) is not supported, and is reported as a wrong-direction result with its interval. H2 is two-sided, so a significant difference in either direction is supported. Otherwise a hypothesis is "not supported"; null results are reported with their intervals, and no equivalence is claimed. Secondary, exploratory and Bayesian results are never used to claim support for H1 or H2. Effects are interpreted against the sensitivity figures in section 3.

**Data exclusion.** Implemented in code exactly as written (`exclusions.py`; each rule is one function with its text in the docstring):
1. **Trial RT trimming:** drop Stroop and Posner trials with RT < 200 ms or > 2,500 ms (RT exactly 200 or 2,500 is kept). Trials without a response have no RT and stay in as errors.
2. **Error trials:** RT outcomes (S1, S2) use correct trials only.
3. **Session exclusion:** exclude the whole session if Stroop congruent accuracy is below 60% (exactly 60% is kept), or if the session is incomplete (any of the 5 tasks or the questionnaire missing). **The 60% check is made on all scored congruent trials before RT trimming**, so anticipations under 200 ms count as trials (and as errors if wrong); RT trimming applies to the RT outcomes. "Incomplete" means fewer scored trials than the design count (Posner 120, Stroop 120, 2-back 60, yes/no 60, 2 recall lists plus the summary row, a threshold row for the contrast task) or a missing questionnaire. More trials than the design count is not an exclusion (it is reported as a data warning).
4. **Smoke-test data:** sessions flagged `is_pilot = 1` (the 1-2 smoke-test runs, study sessions 1-2) are never analyzed.
5. **Missing data:** no imputation. Sessions missing the sleep log are dropped from H1 analyses only. Missing sessions are not made up, except under the stopping rule.
6. **Stop rule:** a stopped session counts as incomplete. In practice an abandoned session is left by the upload service as a partial file that is not loaded, so it appears as a **missing session**, not as an excluded one; the number of such sessions is reported.

Also: practice trials (tagged) are never scored; positions 1-2 of the 2-back are not scored; 2-back responses count only within 2,000 ms of letter onset. The `is_pilot` flag follows the browser's session counter; it is checked against session numbers 1-2 before analysis.

**Missing data.** As rule 5 above. Recall scores computed in the browser are cross-checked against the stored flags and summary row; disagreements are reported.

**Exploratory analyses.** Everything labeled exploratory above, plus any analysis not described here. Exploratory results are reported separately and labeled as such.

---

## 6. Other

**Deviations from the original build plan, recorded before registration.** The project's original plan included 10 self-pilot sessions, a think-aloud study with friends and qualitative coding. **This was skipped: no formal pilot study was run** (deviation S1 in `deviations.md`). Replaced by 1-2 smoke-test sessions on the deployed site, only to confirm that saving works (study sessions 1-2, `is_pilot = 1`, excluded). Consequences: the design was not tested with other people, instruction clarity and the task parameters are untested beyond the developer's own checks, practice-related learning is not absorbed by a pilot phase, the session-length estimate rests only on the smoke-test timing, and **there is no qualitative component and none is claimed.** Other approved changes to the original plan (consent form deferred while the researcher is the only participant; literature review slimmed; two primary outcomes instead of five; data stored via DataPipe to Google Drive instead of OSF; F/J keys and practice blocks added) are listed in `deviations.md`, part A.

**Deviations after registration.** Any change to a preregistered item after registration is logged in `deviations.md` (part B) on the day it happens, with the reason and its effect on the analysis, and is reported in the write-up in a "Deviations from preregistration" section. Changes after the first confirmatory session need an explicit decision by the researcher.

**Ethics.** A personal self-experiment. No institutional review board review has been obtained, and no institutional approval or oversight is claimed. Sleep is observed, never restricted. Raw data are private; sleep and sleepiness are health-related and are released only in de-identified, consented form.

**Limitations (stated in advance).** One person: no generalization beyond him. Natural, uncontrolled sleep variation, self-reported sleep (not actigraphy). Practice effects and time-of-day confounds within day. Task parameters are documented design choices, not literature values (only the staircase rule is verified). Recall lists are length-matched but not frequency-matched. Stimulus sizes are in pixels and not physically calibrated; the viewing distance is instructed. Only large within-person effects are detectable.

**Materials, code and data.** Code, tasks, analysis scripts and design documents: https://github.com/Bhargp08/MindBench. Frozen documents cited by this registration: **[FREEZE COMMIT: full hash of tag prereg-v1]** (`design.md`, `power.md`, `scoring.md`, `prereg_notes.md`, `deviations.md`). De-identified data and the analysis outputs will be released on Zenodo under CC-BY-4.0 and linked to this registration. Raw data are kept until Dec 31, 2028 or 2 years after the write-up is published, whichever is later, then deleted; the released open data are kept indefinitely. The free-recall word pool is selected from the EFF Large Wordlist (Joseph Bonneau / EFF, https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases) under EFF's CC BY policy (licence not confirmed per file; `wordpool.md`).

**Use of AI tools and conflicts of interest.** The code, tests and design documents were written with an AI coding assistant (Claude, Anthropic) and reviewed by a second AI tool (Cursor); the researcher made the design decisions and approved every change. No funding; no conflicts of interest to declare. **[DECISION D10: edit to your own wording.]**

---

## Coverage of the planned analyses (for Cursor's check; not part of the registration)

Every analysis planned in the build units after data collection appears above:

| Unit | Planned analysis | Where it is preregistered |
|---|---|---|
| MB-15 | Scoring, six exclusion rules, d' with log-linear correction | Section 4 (variables), section 5 (data exclusion; exact text and interpretations) |
| MB-18 | Mixed model with a day effect and AR(1) over calendar slots | Section 5, H1 model (D3) and sensitivity analyses |
| MB-18 | Repeated-measures ANOVA where factorial | Section 5: explicitly **not** planned (not a factorial design) |
| MB-18 | Bootstrap CIs (at least 10,000 resamples) | Section 5, H2 and manipulation checks (BCa, whole days) |
| MB-18 | Regression diagnostics | Section 5, regression diagnostics |
| MB-18 | Classic-effect replication (Stroop > 0, Posner > 0, serial position) | Section 1 and section 5, manipulation checks |
| MB-19 | ICC per task outcome and split-half reliability | Section 5, reliability (D6) |
| MB-20 | Bayesian hierarchical/regression models, priors, diagnostics, predictive checks, WAIC and PSIS-LOO | Section 5, Bayesian regression (D5) |
| MB-21 | Drift-diffusion models, competing models, predictive checks, EZ-diffusion | Section 5, drift-diffusion models (D7) |
| MB-22 | Synthesis, deviations, exploratory labeling | Section 5 (exploratory analyses) and section 6 (deviations) |

A "hierarchical" model with participants as a level is not planned: there is one participant.
