# Deviations

## A. Deviations from the original build spec (before preregistration)
Decided by Bharg; none of these touches a preregistered item (nothing is registered yet).

| # | Original spec | What was done instead | Date | Consequence / where recorded |
|---|---|---|---|---|
| S1 | MB-13: 10 self-pilot sessions, a think-aloud study with 2-3 friends, post-task interview and strategy survey with qualitative coding (COGS 13) | **No formal pilot.** 1-2 smoke-test sessions on the deployed site, only to confirm saving works (study sessions 1-2, `is_pilot = 1`, excluded from analysis) | Nov 18, 2026 | Instruction clarity and parameters are untested with others; practice learning is not absorbed by a pilot phase; the session-length estimate comes only from the smoke-test timing log; **no qualitative (COGS 13) component exists, so none may be claimed**. `design.md` sections 1, 5, 6, 8; `prereg_notes.md` |
| S2 | Word pool for 52 sessions x 40 words (10 pilot + 42 confirmatory) | Requirement is **42 confirmatory x 40 = 1,680 words** (1,760 with 2 smoke-test sessions). The 2,080-word pool is kept; 320 words (session slots 45-52) are spare | Nov 18, 2026 | `wordpool.md`, `recallLists.js` |
| S3 | `is_pilot` for the first 10 sessions | `is_pilot` for the first 2 sessions (default cutoff 2) | Nov 18, 2026 | `etl.md` (includes the session-counter caveat) |
| S4 | DataPipe writes raw data to OSF | Google Drive via DataPipe; OSF Registries for the prereg, Zenodo for open data (OSF Projects are being retired) | Nov 17, 2026 | `decisions.md`, `datapipe.md` |
| S5 | MB-01 consent form for every participant | Consent form deferred while Bharg is the only participant (structure lint stays active) | Nov 17, 2026 | `docs/ethics/`, STATUS |
| S6 | MB-02 literature review with expected effect sizes and sleep literature | Slimmed to a table of canonical task parameters; effect-size and sleep-literature review deferred | Nov 17, 2026 | `literature.md`, STATUS |
| S7 | 5 primary outcomes | 2 primary outcomes (2-back d', recall proportion), chosen from Lim & Dinges (2010) Table 2; the rest secondary/exploratory | Nov 17, 2026 | `design.md` section 4, `power.md` |
| S8 | Plain mirrored Latin square; contrast keys 1/2 and Y/N | Zigzag-based balanced square with an AM/PM-balanced session map; F/J keys for every two-choice response; practice blocks added | Nov 18, 2026 | `battery.md` |

## B. Deviations from the preregistration (fill in after registration)
Template: date | preregistered item | what changed | why | effect on analysis | decided by. Log each change the day it happens (MB-17); summarize in the write-up (MB-22).

| Date | Preregistered item | Change | Reason | Effect on analysis | Decided by |
|---|---|---|---|---|---|
| | | | | | |
