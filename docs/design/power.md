# Power Analysis (MB-04)

Code: `analysis/python/mindbench/power.py`. Tests: `analysis/python/tests/test_power.py`. Figure and numbers: `figures/power_curves.png`, `power_results.json` (made by `analysis/python/scripts/power_report.py`; seed 20261117; 1,000 simulations per point, so sampling error is about +/-0.015 and neighboring points can be slightly non-monotone).

## Model
DV = r * sleep + noise. Sleep ~ N(0, 1); noise is unit-variance AR(1) with phi = 0.3; r is the within-person correlation. **AM and PM sessions of a day share the same night's sleep** (as in the design), so the predictor is autocorrelated too. The analysis uses a one-step Cochrane-Orcutt AR(1) correction. "Effective power" includes the AR(1) correction and Holm over the **2 primary outcomes** (P1 2-back d', P2 recall proportion), which share the sleep predictor and have independent errors.

## Primary outcomes: why these two (Bharg's decision, Nov 17, 2026)
Evidence: Lim & Dinges (2010), *Psychol. Bull.* 136(3), 375-389, Table 2 (24-48 h **total** sleep deprivation; text read from the paper, **verified**):

| Domain (outcome) | Combined g | Maps to |
|---|---|---|
| Working memory, accuracy | -0.555 | **P1 2-back d'** |
| Working memory, RT | -0.515 | |
| Complex attention, accuracy | -0.479 | Stroop, Posner (as classified in the paper) |
| Short-term memory, recall | -0.383 | **P2 free recall** |
| Complex attention, RT | -0.312 | S1/S2 are RT difference scores |
| Processing speed, RT | -0.302 | |
| Simple attention (lapses / RT) | -0.762 / -0.732 | not in this battery |

- P1 has the largest pooled effect among domains the battery measures, and the meta-analysis includes n-back studies directly (e.g. Choo et al. 2005, g = -0.660 for working memory).
- P2 has a significant pooled recall effect with directly matching verbal-recall studies (individual effects -0.582 and -0.430).
- Stroop and Posner fall under complex attention, but the pooled domain effect mixes many task types, and the study-level Stroop effects in the table are small or inconsistent (range -0.511 to +0.098), so **the interference and validity scores (differences between conditions) have weaker evidence**. The contrast threshold has no matching domain. These go to secondary/exploratory (S1-S3), outside the Holm family.

Caveats: (1) these effects are from total sleep deprivation; natural sleep variation probably gives smaller effects; (2) the g values are not used as expected effect sizes (the effect-size review is deferred stretch work); (3) the task-to-domain mapping follows the paper's classification, checked only for the studies listed above; (4) the choice is made before any data collection.

## Spec-verified checks (tests)
Analytic paired t: d_z = 0.5 needs n = 34 (0.808); d_z = 0.3 needs n = 90 (0.804); 21 AM/PM pairs at d_z = 0.65 give 0.809. Simulated i.i.d. correlation test: n = 40, r = .43 about 0.80; n = 28 about 0.65; n = 40, r = .30 about 0.48.

## Findings that differ from, or add to, the spec (kept for MB-18)
1. **AR(1) errors alone do not inflate type-I error** when sleep is independent across sessions (about 0.050). Inflation appears because AM and PM share the same sleep value: uncorrected type-I is about 0.083 at n = 40, phi = 0.3; the AR(1) correction brings it to about 0.061 (slightly liberal). This still motivates the AR model in MB-18, but the reason is the shared nightly sleep. **MB-18 must model this (AR(1) errors, and day as a grouping term).**
2. Holm and AR/shared-sleep results are **calibrated by simulation, not from the spec**.

## Power at the planned 42 sessions (direct simulation at n = 42)
| Within-person r | i.i.d., no correction | AR(1) + shared sleep | + Holm, 2 primary outcomes (both true) | Superseded: Holm over 5 |
|---|---|---|---|---|
| 0.43 | 0.81 | 0.75 | **0.74** | 0.64 |
| 0.30 | 0.48 | 0.44 | **0.39** | 0.27 |

(An earlier draft of this document quoted "about 0.84 / 0.77 / 0.66" for 42 sessions; those were rough, not direct simulations, and are replaced by the values above.)

If only one of the two primary outcomes has a true effect at r = 0.43, its power is about 0.69. Effect size detectable at 80% effective power with 42 sessions (Holm over 2, AR(1), shared sleep, both outcomes truly affected): **r of about 0.46** (0.52 at r = .35, 0.66 at .40, 0.79 at .45, 0.87 at .50, 0.94 at .55). With the old 5-outcome family it was about 0.49.

**AM vs PM (H2):** 21 paired days at d_z = 0.65 give 0.81 for one test and **0.71 at alpha = .025** (Bonferroni bound for 2 outcomes; Holm is slightly better); 80% at alpha = .025 would need 26 pairs (about 26 days).

## Session count
**Decision (Bharg, Nov 17, 2026): 42 sessions (21 days x 2).** With 2 primary outcomes, effective power at r = 0.43 is about 0.74 (60 sessions would give about 0.89).

## Honest framing
At 42 sessions the study can reliably detect only large within-person effects (r of about 0.46 or more) once autocorrelation and the 2-outcome Holm family are accounted for. Effects of natural sleep variation are probably smaller than those from total sleep deprivation, so **a null result is likely, and it is an acceptable outcome** of this study. Secondary outcomes are exploratory and underpowered; they will be reported as such.

## Limits
Assumes a linear within-person effect, constant phi, independent outcomes (real outcomes are probably correlated, which makes Holm less costly than shown), and normal errors. Not simulated: practice effects (modeled via session number in MB-18) and missing sessions.
