# Synthesis and deviations (MB-22)

Code: `analysis/python/mindbench/synthesis.py`. Tests: `analysis/python/tests/test_synthesis.py` (written failing first; no data, nothing invented).

## What it does
- **One results table covering every preregistered analysis.** `ANALYSES` lists 15 rows: H1 and H2 for each primary outcome (P1, P2; the four confirmatory rows), H3 for Stroop and Posner (DDM), S1-S5, the manipulation checks, and reliability. Each row names the prereg section it comes from (`anchor`), and a test checks that text exists in `prereg_draft.md`. A second test is the spec's consistency check: every H, P and S ID used in the prereg appears in the table (`missing_prereg_ids`).
- **Sources per row:** frequentist (MB-18), Bayesian (MB-20), DDM (MB-21), reliability (MB-19). `build_results_table(results)` fills in what exists; everything else says `pending`. Unknown IDs, unplanned sources and conclusions outside the fixed vocabulary (supported / not supported / cannot tell / descriptive / pending) are rejected.
- **Decision rules follow the prereg:** a confirmatory decision comes from the frequentist result only (a Bayesian-only result leaves it `pending`). Frequentist inputs are expected to carry Holm-adjusted inference separately within H1 (P1, P2) and within H2 (P1, P2); this module does not re-run Holm. A significant negative H1 effect is "not supported (wrong direction)"; H2 is two-sided; every other row is labelled exploratory or descriptive.
- **Convergence column:** `converge` / `diverge` by effect direction across the planned sources, `incomplete` while any is pending, `single source` otherwise. It is a reading aid, not a test.
- **Deviations:** `parse_deviations` reads `deviations.md` (part A before registration, part B after) and rejects an incomplete part B row; `render_deviations_section` writes the "Deviations from preregistration" text for the write-up, saying "no deviations" only when part B is empty, and always listing the part A build-plan changes.

## Not done
- **MB-18 (frequentist analysis, needs R) does not exist yet,** so no row can be filled for H1, H2, S or the manipulation checks. This unit does not run any analysis; it fixes how results will be assembled.
- No results, no real data. Writing results into the table, separating exploratory analyses in the write-up, and finalizing `deviations.md` happen after collection; part B stays empty until the registration exists.
