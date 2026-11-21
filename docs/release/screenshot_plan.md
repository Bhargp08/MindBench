# Dashboard and project screenshot plan (MB-24)

Rules for every image: **simulated data or public mode only**. Never show a participant code, hours slept (sleep values), time of day or any timestamp finer than a date, file names that contain a participant code, the `data/` folder, `.env`, DataPipe or Google Drive pages. Crop out the OS menu bar and any username. Light theme, 1440 px wide, saved as PNG in `docs/release/shots/` (the folder is created when the shots are taken; none exist yet).

| # | File | What it shows and how to get it |
|---|---|---|
| 1 | `dashboard_public_overview.png` | Dashboard with `MINDBENCH_DASHBOARD_PUBLIC=1` on a simulated database: completion count, stopping status, task completion |
| 2 | `dashboard_public_gaps.png` | Same mode: gap and partial-upload counts (counts only) |
| 3 | `battery_stroop.png` | A Stroop trial from the local dev server (`npm run dev`), practice screen, no questionnaire values entered |
| 4 | `battery_recall.png` | The recall screen with the word list showing (the words are from the public word pool) |
| 5 | `deid_check_fail.png` | Terminal: `public_data check` failing on a simulated folder edited to contain a clock time |
| 6 | `deid_check_pass.png` | Terminal: `public_data simulate`, `check` passing, `reproduce` output (the codebook line says SIMULATED) |
| 7 | `paper_pending_tables.png` | `docs/writeup/paper.md` Results section with every row pending |

Capture order: 1-2 need the dashboard running against a database built from the synthetic fixtures (`MINDBENCH_EXPECTED=fixture`). If a shot would need real data to look meaningful, skip it; a screenshot of empty or simulated state is the honest one.
