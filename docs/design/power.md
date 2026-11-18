# Power Analysis (MB-04)

Code: `analysis/python/mindbench/power.py`. Tests: `analysis/python/tests/test_power.py`. Figures and numbers: `figures/power_curves.png`, `power_results.json` (made by `analysis/python/scripts/power_report.py`, seed 20261117, 1,000 simulations per point, so about +/-0.015 sampling error).

## Model
DV = r * sleep + noise. Sleep ~ N(0, 1); noise is unit-variance AR(1) with phi = 0.3; r is the within-person correlation. **AM and PM sessions of a day share the same night's sleep** (as in the design), so the predictor is autocorrelated too. The analysis uses a one-step Cochrane-Orcutt AR(1) correction. "Effective power" below includes the AR(1) correction and Holm over the 5 primary outcomes (all sharing the sleep predictor, independent errors).

## Spec-verified checks (tests)
Analytic paired t: d_z = 0.5 needs n = 34 (0.808); d_z = 0.3 needs n = 90 (0.804); 21 AM/PM pairs at d_z = 0.65 give 0.809. Simulated i.i.d. correlation test: n = 40, r = .43 gives about 0.80; n = 28 gives about 0.65; n = 40, r = .30 gives about 0.48.

## Findings that differ from, or add to, the spec
1. **AR(1) errors alone do not inflate type-I error** when sleep is independent across sessions (about 0.050). Inflation appears because AM and PM share the same sleep value: uncorrected type-I is about 0.083 at n = 40, phi = 0.3. The AR(1) correction brings it to about 0.061 (slightly liberal). This still motivates the AR model in MB-18, but the reason is the shared nightly sleep.
2. Holm and the AR/shared-sleep results are **calibrated by simulation, not from the spec**.

## Power at the planned 42 sessions (r = 0.43, the spec's 80% target)
| Sessions | i.i.d., no correction | AR(1) + shared sleep | + Holm over 5 outcomes |
|---|---|---|---|
| 28 | 0.64 | 0.57 | 0.45 |
| 40 | 0.83 | 0.75 | 0.62 |
| **42 (planned)** | about 0.84 | about 0.77 | **about 0.66** |
| 48 | 0.86 | 0.79 | 0.73 |
| 60 | 0.95 | 0.90 | 0.85 |

For a smaller effect (r = 0.30) effective power at 42 sessions is only about 0.26 to 0.28 (Holm, AR(1)). Effect size detectable at 80% effective power with 42 sessions (Holm, AR(1), shared sleep): **r of about 0.49** (power 0.70 at r = .45, 0.83 at r = .50, 0.91 at r = .55).

**AM vs PM (H2):** 21 paired days at d_z = 0.65 give 0.81 for one test but **0.56 at alpha = .01** (Bonferroni bound for 5 outcomes; Holm is slightly better). Reaching 80% at alpha = .01 needs 32 pairs (about 32 days) at d_z = 0.65.

## Session-count decision (for Bharg's approval)
**Keep 42 sessions (21 days x 2)**, as in `design.md`. Reasoning: 2-3 weeks is the stated burden; 60 sessions (30 days) would reach about 0.85 effective power for r = .43 but adds 9 days of daily sessions; 42 gives honest 80% power only for large within-person effects (r of about 0.5 or more, d_z of about 0.65 for AM/PM at an uncorrected alpha).

**Honest framing:** at 42 sessions the study can reliably detect only large effects once multiplicity and autocorrelation are accounted for; a null result is likely and is an acceptable outcome. Natural sleep variation probably produces smaller effects than lab sleep deprivation (not reviewed in MB-02, deferred). Options if more power is wanted: more days (up to 30), or fewer primary outcomes (a smaller Holm family).

## Limits
Assumes a linear within-person effect, constant phi, independent outcomes, and normal errors. Real outcomes are likely correlated, which would make Holm less costly than shown. Not simulated: practice effects (modeled via session number in MB-18) and missing sessions.
