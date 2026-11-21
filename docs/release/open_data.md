# Open data release (MB-24)

Code: `analysis/python/mindbench/public_data.py`. Tests: `analysis/python/tests/test_public_data.py`. **Simulated data only so far; nothing here has touched real participant data.**

## What the release contains
`data_public/` holds exactly `sessions.csv`, `trials.csv`, `participants.csv` and `codebook.md` (the data dictionary, written by the export). Nothing else may be in the folder.

## De-identification rules (enforced by the check and by the export)
- **Participant code:** replaced by a pseudonym (P01, P02, ...; the researcher first). Real participant codes, or anything shaped like one, are rejected in any cell and any file name. The code-to-pseudonym map is written to a private file (`data/pid_map.json`, gitignored) and is never released.
- **Free text:** none. Typed recall words and manual exclusion notes are never exported; trial rows carry only a fixed vocabulary (`congruent`, `valid`, `target`, ...). A column or value outside the vocabulary fails the check.
- **Timestamps finer than the date:** the start time becomes the study day (`date`, YYYY-MM-DD; a start between midnight and 4 am belongs to the previous day, prereg D2) and `period` (AM or PM, prereg D1/D9). Clock times and date-times anywhere in a cell are rejected. Bed and wake times are dropped.
- **Device and browser:** user agent, screen size, device string, time zone and source file names are dropped.
- **Health data:** hours slept, sleepiness (KSS) and caffeine are released only for the researcher's own data and for friends who consented to open data.

## Consent rule
The researcher's own data (`--owner`) is released. Anyone else is released only if the private consent file maps their code to a literal `true`. `"yes"`, `1`, `"true"`, `null` or a missing entry all mean "not released". Omitted participants are counted in the export report, never named.

## Steps (all run locally; nothing is uploaded by the code)
```bash
cd analysis/python
uv run python -m mindbench.public_data export --db ../../data/mindbench.sqlite --out /path/outside/repo/data_public --owner <your code> [--consent ../../data/consent.json]
uv run python -m mindbench.public_data check --dir /path/outside/repo/data_public --db ../../data/mindbench.sqlite
uv run python -m mindbench.public_data reproduce --dir /path/outside/repo/data_public
```
`check --db` also searches every cell for the real participant codes in the private database. The export runs the same check on its own output and deletes the files if it fails.

## Before upload (Bharg's steps)
1. Review the files by eye (open `sessions.csv`; look for anything that could identify a person, including very rare dates or values). The check cannot judge re-identification risk beyond its rules.
2. Run `mindbench.public_data check --db` once more on the exact folder to upload.
3. Bharg uploads to Zenodo under CC-BY-4.0 and links the DOI from the OSF registration and `CITATION.cff` / README. This is an external action; the code never uploads.
4. Do not commit real data to the repository unless you want it public there too; if you do, the test `test_the_committed_data_public_folder_is_empty_or_passes_the_check` will check it.

## What `reproduce` does
Reads only the release (it never opens the private database): counts of sessions, included sessions and days, and the two descriptive manipulation checks (Stroop interference, Posner validity effect) as day-level means with a 95% t interval, written into the MB-22 synthesis table. Confirmatory and other analyses stay pending there. The paper builder accepts these results and refuses to write the paper if any number is not traced.

## Limits
The check enforces rules, not judgement: it cannot tell whether a combination of dates and sleep values could identify someone. For the researcher's own data that is the researcher's choice; for friends it is covered by the consent form's open-data box (the consent form is still a deferred draft; finalise it before any friend takes part).
