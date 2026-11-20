# Test-retest and split-half reliability (MB-19)

Code: `analysis/python/mindbench/reliability.py`. Tests: `analysis/python/tests/test_reliability.py` (written failing first; simulated data only, no real outcomes are read by this module or its tests).

## Definition (preregistration D6)
- **Primary:** ICC(3,1), consistency, **days as targets and the AM and PM sessions as the two measurements**, computed on the **residuals from `y ~ k + ln(k)`** (`k` = study session number minus 2, so the first confirmatory session is k = 1; the model is fitted by least squares on all included sessions). The **raw ICC** (no residualizing) is reported next to it, and so is **ICC(2,1)** (absolute agreement) for both.
- Only days with both an AM and a PM session are used (`n_days` is reported). Two sessions in one day and slot are an error here: keep only the first (prereg rule) before calling.
- **Intervals:** (1) F-based (Shrout & Fleiss 1979 for ICC(1,1) and ICC(3,1); McGraw & Wong 1996 with Satterthwaite df for ICC(2,1)); (2) **bootstrap over days**, 10,000 resamples by default, percentile, fixed seed. The F intervals assume independent days; the AM and PM sessions of a day share the night's sleep and the day component, so this ICC mixes within-day consistency with stability, and the bootstrap is reported alongside (as the draft says).
- **Split-half (within session):** odd vs even trials scored by a caller-supplied function, Pearson r across sessions, **Spearman-Brown** `2r/(1+r)`, Fisher-z intervals (endpoints transformed with Spearman-Brown). Sessions with a missing half score are dropped and counted.
- **Interpretation:** Koo & Li (2016) bands (.5 / .75 / .9) via `interpret()`; **[UNVERIFIED]**: the thresholds have not been checked against the paper (Koo & Li apply them to the 95% CI, the helper labels the point estimate). Exploratory only.

## Checks
- Shrout & Fleiss 6 x 4 example: ICC(1,1) 0.1657, ICC(2,1) 0.2898, ICC(3,1) 0.7148; Spearman-Brown r = 0.5 gives 0.6667. F interval values are checked against reference values from common ICC software (tolerance .01).
- Simulation: the ICC(3,1) of two measurements with day SD = noise SD averages 0.50; F-interval coverage is near 95%; a shared practice trend with no true day effect inflates the raw ICC but not the residual ICC.

## Notes
- This is day-to-day consistency within one person, not between-person reliability; no hypothesis is tested with it (exploratory, outside the Holm family).
- Wiring to real scored data is MB-22 (analysis after data collection); no data pipeline is added here.
