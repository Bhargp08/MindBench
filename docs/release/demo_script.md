# Two-minute demo video script (MB-24)

Everything shown is the local build, simulated data and the dashboard in public mode. No real participant data, no participant codes, no sleep values. The live site link is a placeholder until the deploy is approved, so the battery is shown from the local dev server. Target length 2:00; narrate in plain words, no claims about results (there are none).

| Time | On screen | Narration |
|---|---|---|
| [00:00-00:12] | Title card, repository page | "MindBench is a preregistered one-person experiment: does natural variation in sleep, or time of day, change attention, memory and perception?" |
| [00:12-00:35] | Local battery: contrast task, Stroop, 2-back, recall, 3 seconds each (simulated session, practice screens visible) | "Five short tasks in the browser, about half an hour, twice a day for three weeks. The words in the recall task are picked from a public word list." |
| [00:35-00:55] | `docs/design/prereg_draft.md`, the hypotheses and the power paragraph | "Two primary outcomes, 2-back d' and recall, are fixed in advance. With 42 sessions the study can only detect large effects, and the write-up says so." |
| [00:55-01:20] | Dashboard in public mode, simulated database | "During collection the dashboard shows completion and data quality only. It never shows outcomes, so nobody, including me, peeks at the results." |
| [01:20-01:45] | Terminal: `public_data simulate`, then `check`; then a file edited to include a time of day and `check` failing; then `reproduce` | "Before data is released a check rejects participant codes, free text and any timestamp finer than the date. Anything that passes can be re-analysed from the public files." |
| [01:45-02:00] | Paper with every result marked pending; README | "There are no results yet: every number in the paper is traced to a script, and the unfilled ones say pending. Code is MIT, data will be CC-BY. Thanks for watching." |

## Recording notes
- Record at the simulated-data state only; use the screenshot plan (`screenshot_plan.md`) for stills.
- Hide the terminal prompt path if it shows a username; hide any browser bookmarks.
- Do not show `data/`, `.env`, the DataPipe or Google Drive pages, or the private pseudonym map.
