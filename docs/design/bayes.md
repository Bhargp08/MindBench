# Bayesian regression (MB-20)

Code: `analysis/python/mindbench/bayes.py`. Tests: `analysis/python/tests/test_bayes.py` (written failing first; **simulated data only**, the module never reads the database).

## Model (prereg D5, matching the D3 model)
Per primary outcome (z-scored across included sessions), sessions ordered by calendar slot (slot = 2*(day-1)+PM+1):
`y = b0 + b_sleep*sleep_c + b_k*k_z + b_lnk*lnk_z + b_pm*pm_z + u_day + e`, `e` AR(1) over slots. `sleep_c` = hours slept centered at the mean; `k` (= session number minus 2), `ln k` and PM are standardized.

| Parameter | Prior |
|---|---|
| b0 | N(0, 1) |
| b_sleep | N(0, 0.5) per hour |
| b_k, b_lnk, b_pm | N(0, 1) per SD |
| day SD (sigma_u) | HalfNormal(0.5) |
| residual marginal SD (sigma) | HalfNormal(1) |
| AR(1) phi | N(0, 0.5) truncated to (-1, 1) |

(The priors for b_k, b_lnk, b_pm, the day SD, and the standardized predictors changed from the first D5 wording at Bharg's instruction, Nov 20, 2026; `prereg_draft.md` D5 was updated to match.)

## Likelihood and LOO/WAIC
The joint distribution is the D3 model with the **day intercept integrated out**: covariance `sigma_u^2 * (same day) + sigma^2 * phi^|slot distance|`, so missed sessions leave gaps. It is evaluated as **one-step-ahead predictive densities** p(y_t | earlier sessions) from the Cholesky factor; they multiply to the joint density (checked in a test against explicit conditional-Gaussian formulas) and are the pointwise terms for PSIS-LOO (ArviZ) and WAIC (computed in `bayes.waic_from_loglik`; ArviZ 1.x has no `waic`). With dependent observations both are **approximate, not true leave-one-out**; Pareto-k counts (good <= .5, ok <= .7, bad <= 1, very bad > 1) are reported by `loo_report`.

**Design note.** The first version kept explicit day effects in the model and used pointwise log-likelihood conditional on them. LOO then could not see the sleep term (sleep is a day-level predictor and the free day effects absorb it): with a large simulated effect the LOO difference was 0.7 against a standard error of 1.9. Integrating the day intercept out fixed this (difference 18 against 5.4 for a 1.2 SD/hour effect) and also removed divergences on small data.

## Checks (simulated, 21 days x 2 sessions unless noted)
- **Recovery:** 20 simulations, 90% intervals: pooled coverage 0.925 (b0 .95, b_sleep .85, b_k 1.0, b_lnk 1.0, b_pm .80, sigma_u .90, sigma .90, phi 1.0); the test requires pooled >= 0.80 and every parameter >= 0.60.
- **Diagnostics** on 10-day data: R-hat < 1.01, no divergences, ESS > 100 in the test (the preregistered criterion for real fits is ESS > 400).
- **LOO** prefers the model with sleep for a large effect (difference > 2 SE) and does not clearly prefer it when the true effect is zero.
- Prior scales are checked by prior-predictive sampling.

## Limits
- Sampling is sequential (`cores=1`), 2-4 chains; the recovery test takes a few minutes.
- Only the primary-outcome models are built here. The hierarchical trial-level models in the spec (log-RT, accuracy) are not part of prereg D5 and are not implemented; participants are not a level (one participant).
- Not run on real data (after collection, MB-22).
