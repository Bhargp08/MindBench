# Public data export and reproduction (MB-24)

Code: `analysis/python/mindbench/public_data.py` (`python -m mindbench.public_data {export,check,simulate,reproduce}`). Tests: `analysis/python/tests/test_public_data.py` (written failing first; simulated data only). Rules and steps for the release: `docs/release/open_data.md`.

## Design
- **`export_public`**: private SQLite -> `sessions.csv`, `trials.csv`, `participants.csv`, `codebook.md`. Pseudonyms P01.. (researcher first, then others in code order); date + AM/PM instead of a start time (prereg D2/D1, same rule as the dashboard); exclusion rule codes instead of text; scores from `scoring.score_session`; scored trials of stroop/posner/nback/yesno only, with a fixed condition vocabulary and no response strings. The consent rule: owner codes are released, anyone else only when `consent[code] is True`. The export runs `check_public_dir` on its own output and removes the files if it fails.
- **`check_public_dir`**: exact file list, exact column list per file, a validator per column (pseudonym pattern, calendar date, AM/PM, 0/1 flags, closed vocabularies for exclusion codes, task, condition and role), plus a scan of every cell for known participant codes (case-insensitive), code-shaped tokens (8 capitals/digits), clock times and date-times. Also scans file names and `.md` files for known codes.
- **`reproduce`**: reads only the release (the check runs first and a failing folder is refused). Recomputes counts and the two descriptive manipulation checks (MC:S1 Stroop interference, MC:S2 Posner validity effect) as day-level means with a 95% t interval, and returns them in the shape `synthesis.build_results_table` takes; the paper builder then traces them like any other number. Not recomputed here: H1/H2 (needs MB-18, R), DDM, Bayes, reliability. They stay pending.
- **`simulate_public`**: a fully simulated release in the real format (codebook says SIMULATED), used by tests and the README.

## Decisions to know about
- Trials are released without response strings and without RT-trimming flags; analysts re-apply the preregistered trimming (200-2,500 ms) themselves. Recall words and per-list data are not released at trial level (only per-session recall counts).
- Bed/wake times, device, time zone and screen details are dropped, not coarsened.
- Sessions without a start time are left out of the release (no study day), and counted in the export report.
- The check enforces rules, not re-identification risk; see `open_data.md`.

## Not done
No real data exported; no Zenodo upload (Bharg's step); `check --db` against a real database has only been tried on simulated ones; DDM and reliability inputs (trial-level) are in the release format but not re-run from it in this unit.
