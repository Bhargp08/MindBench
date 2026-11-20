# Monitoring dashboard and nightly ETL (MB-16)

Code: `dashboard/` (`app.py`, `mindbench_dashboard/{metrics,config,nightly}.py`, tests in `dashboard/tests/`). Streamlit 1.67.0.

## What it is for
**Preregistered monitoring only**: whether sessions are being completed, and whether the data are clean. The preregistration says no hypothesis tests are run during collection, so the dashboard shows **completion and data quality only**.

## What it shows
- **Completion:** confirmatory sessions completed out of 42, remaining, smoke tests run, excluded sessions (by reason), the day of the 21 scheduled days, and the preregistered **stopping rule** status (stop at 42 completed sessions, or after the 21 days plus up to 7 extension days, or when session slot 52 is reached). A completed session is one whose battery finished, even if a rule excludes it later.
- **Session-number gaps:** numbers from 3 up to the highest seen that have no loaded session, each with a reason: a file failed validation, only a **partial upload** exists, or no file at all. Slots 1-2 (smoke tests) are optional and never count as gaps. The stopping rule counts completed sessions, and a stopped session normally never reaches the database, so it appears here as **missing, not excluded**.
- **Skipped partial uploads:** the `*.partial.json` files DataPipe leaves for abandoned sessions (the ETL skips them), plus files that failed validation (from the last nightly report).
- **Data quality:** per session: battery finished, tasks complete (counts against the design counts, not values), start time against the planned windows (07:00-11:00 AM, 17:00-21:00 PM, from the logged local time; AM = before 12:00), total task minutes, refresh-rate plausibility, and a **Stroop flag** (congruent-trial accuracy against the preregistered 60% exclusion limit: shown as ok or below limit, never as a value). Trends by session: task durations, share of trials with no response (timeouts), responses faster than 200 ms.
- **Sleep log** (local mode only): hours slept per session. This is the predictor, not an outcome.

## What it never shows
No outcome values: not the primary outcomes (2-back d', recall proportion), not the secondary ones (Stroop interference, Posner validity effect, contrast threshold, yes/no d'), not hit or false-alarm counts, recall scores or serial-position curves, and no hypothesis tests, p-values or model fits. Three tests enforce this:
1. **No outcome-like field names** anywhere in the data the dashboard builds.
2. **Invariance:** two databases that differ only in performance on the 2-back, recall, yes/no, threshold, Posner and incongruent-Stroop data produce byte-identical dashboard data.
3. **No scoring code:** the dashboard sources never import the outcome-scoring or d' modules (checked by a source scan).

It reads sessions through the ETL loader and the exclusion rules only. The one performance-derived item is the Stroop exclusion flag, which is a preregistered data-quality rule.

## Public mode
`MINDBENCH_DASHBOARD_PUBLIC=1` (only 1, true or yes turn it on) shows aggregates only: counts of sessions, completion by task, gap and partial-upload counts, stopping status. It drops participant codes, file names (they contain the code), free text, user agent, time zone, time of day, the sleep log and any timestamp finer than a date. Tests scan the public data for the participant code, file names, device strings and recall words. Host it publicly only if you want even these counts public; the default is local.

## Nightly ETL
`python -m mindbench_dashboard.nightly` (run from `dashboard/` with `uv run`): (1) download new files from Google Drive if credentials are set in the environment (otherwise it reports "skipped" and still loads what is in `data/raw`; any download error is reported and never stops the load), (2) validate and load every file into `data/mindbench.sqlite` (idempotent; a bad file never blocks the others), (3) write the automatic exclusion reasons into `sessions.excluded_reason` (`auto: ...`; manual notes are never overwritten), (4) write `data/etl_report.json` (what loaded, what failed and why, partial uploads skipped, download status), which the dashboard reads. Exit code 1 if any file failed. `--no-download` loads local files only.

**Scheduling is not installed by this repo.** Templates are in `dashboard/schedule/` (`nightly.sh`, `crontab.example`, `com.mindbench.nightly.plist.template` for macOS launchd, `windows-task.ps1.template` for Windows Task Scheduler). Credentials stay in environment variables or an env file outside the repo; CI never runs this against real data (it uses synthetic fixtures).

## Running it
```bash
uv run --project dashboard python -m mindbench_dashboard.nightly --no-download    # load files already in data/raw
uv run --project dashboard streamlit run dashboard/app.py                          # local dashboard
MINDBENCH_DASHBOARD_PUBLIC=1 uv run --project dashboard streamlit run dashboard/app.py   # public (aggregates only) view
```
Paths default to `data/mindbench.sqlite`, `data/raw`, `data/etl_report.json` (all gitignored); override with `MINDBENCH_DB`, `MINDBENCH_RAW`, `MINDBENCH_REPORT`.

## Notes and limits
- Time of day and day follow the preregistration (D1/D2/D9), in `metrics._day_and_slot`: AM = 04:00 to before 12:00, PM = 12:00 onward, from the logged local start time and never from odd/even session numbers; a start from 00:00 up to 04:00 belongs to the previous calendar day as its PM session (outside the planned windows); a second session in the same day and slot is flagged `duplicate_slot` (only the first is analysed). The day number of the schedule uses this day.
- Gaps are computed from loaded sessions and skipped partial files. A session whose file never reached Drive cannot be told apart from one that was never started ("no file").
- Not tested live against real data or a real Drive folder. The visual layout was checked in a browser against a synthetic database only.
