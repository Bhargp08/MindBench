# Drift-diffusion models (MB-21)

Code: `analysis/python/mindbench/ddm.py`. Tests: `analysis/python/tests/test_ddm.py`. Prereg: D7 (exploratory, H3). **Simulated data only so far**; nothing here has touched real participant data.

## Question (H3)
Does sleep (below vs above the median hours slept) or time of day (AM vs PM) change **drift rate** (`v`) or **boundary separation** (`a`) in the speeded tasks? The answer may be "cannot tell", and that is a reported result.

## Tasks and data
Stroop and Posner only (the 2-back is not speeded in the DDM sense and is left out; this follows prereg D7). Correct and error RTs go together. Responses are coded **correct vs error** (accuracy coding; the Stroop task has four response keys, so there is no natural upper/lower response). The condition that drives drift is congruency (Stroop) or cue validity (Posner). Inputs are scored, already-filtered trials: RT in ms, a 0/1 correct flag, the condition, the session group. The module converts ms to seconds and rejects RTs outside (0.1 s, 2.0 s]; the 2,000 ms cut is the prereg rule and the exclusions live in `exclusions.py`, not here.

## Session groups
- **Sleep:** below vs above the median `hours_slept` over the included sessions. Sessions exactly at the median are left out of the sleep comparison (prereg D7).
- **Time of day:** AM vs PM from the logged start time (D2/D9).
Each comparison is fitted separately for each task.

## Models (all fitted by PyDDM 0.9.0, maximum likelihood)
Common to every model: unbiased start (`x0 = 0`), noise `sigma = 1`, drift per condition `v_c` (two values), non-decision time `t0` shared across conditions **and** session groups, and a **fixed 2% uniform-mixture contaminant** (`OverlayUniformMixture`, `umixturecoef = 0.02`) so a single stray RT cannot give an infinite likelihood. The 2% is a modelling choice, not estimated.

| Model | Drift | Boundary |
|---|---|---|
| `null` | `v_c` | `a` |
| `drift` | `v_c + dv * group` | `a` |
| `boundary` | `v_c` | `a + da * group` |
| `both` | `v_c + dv * group` | `a + da * group` |

PyDDM's `B` is the **half-width** (bounds at ±B), checked numerically: `v = 1, B = 1` gives P(upper) = 0.88076 and mean decision time 0.7613 s against the analytic 0.88080 and 0.76159 s. We report `a = 2B`.

Solver: `dx = dt = 0.01 s`, `T_dur = 3 s`, differential evolution.

## Comparison
BIC per model (PyDDM `LossBIC`). The model with the lowest BIC is the best; if the runner-up is within **2 BIC units** the verdict is **"cannot tell"** (prereg). Verdicts: `neither` (null best), `drift`, `boundary`, `both`, `cannot tell`.

**Identifiability rule (prereg D7).** If error trials are under **5%** of the pooled trials of the task in either session group, boundary separation is **not identifiable** for that task: only `null` and `drift` are compared, and the boundary result is reported as not identifiable, not as a null effect.

## Checks
- **EZ-diffusion** (Wagenmakers et al., 2007; s = 0.1) per condition and group from accuracy, RT mean and variance of correct trials. A sanity check only, not an inference. Pc of exactly 0, 0.5 or 1 gets the standard edge correction (Pc = 1 - 1/(2n), and so on); the function says when it did.
- **Predictive checks:** RT quantiles (.1, .3, .5, .7, .9) for correct and error responses, observed vs predicted by the fitted model, for every condition x group cell. Cells with fewer than 5 trials of a response type have no observed quantiles and are marked, not filled.
- **Tests with simulated data:** analytic P and MDT, the EZ worked example, parameter recovery (500 trials x 2 conditions, 10 seeds, within 10% on average), and a drift-only effect picked by BIC in at least 8 of 10 simulations.

## Limits
Single pooled fit per task, not hierarchical: trials from different sessions are treated as exchangeable within a cell, which ignores between-session variability and makes BIC differences optimistic. The prereg allows the hierarchical Bayesian alternative only if chosen before registration; it was not, so this stays the pooled fit and the write-up says so. No across-trial variability in drift, start point or `t0` (so slow errors are not well captured). Exploratory.
