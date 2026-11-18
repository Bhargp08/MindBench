# Preregistration notes (input for MB-05)

Statements the preregistration should make, and things it must not claim. Not itself a preregistration.

## Pilot and smoke tests
- **No formal pilot study was run.** The original plan (10 self-pilot sessions, a think-aloud study with friends, interviews) was dropped (`deviations.md` S1).
- Bharg may run 1-2 smoke-test sessions on the deployed site only to confirm that data saving works. They are study sessions 1-2, flagged `is_pilot = 1` in the database, and **excluded from all analyses**. They did not inform any design decision, except possibly the session-length estimate, which is not part of any hypothesis.
- Confirmatory data are study sessions 3-44 (42 sessions over 21 days, AM and PM).
- The design (tasks, parameters, instructions, practice blocks) was **not tested with other people**.

## Must not be claimed
- Institutional review or oversight of any kind (none exists).
- A pilot-informed design, qualitative (think-aloud or interview) findings, or COGS 13-style coding.
- That task parameters come from the literature: only the staircase rule is verified; the rest are documented design choices (`literature.md`, `design.md` section 3).
- Effect sizes from natural sleep variation: the cited evidence (Lim & Dinges 2010) is from 24-48 h total sleep deprivation.
- Word-frequency matching of the recall lists (only length-matched).

## Things the preregistration should state
- Primary outcomes: P1 2-back d' (log-linear correction on every dataset) and P2 recall proportion; Holm over these 2; everything else exploratory.
- Practice rows (`practice = 1`) and smoke-test sessions are excluded; AR(1)/day-grouping model for the shared AM/PM nightly sleep (`power.md`).
- Because there is no pilot phase, early confirmatory sessions include the steepest practice-related change; session number (linear and log) is a covariate.
- Any protocol change after registration is a logged deviation (`deviations.md`, part B).

## Scoring interpretations to state (from `scoring.md`)
- 2-back responses count only within 2,000 ms of letter onset; P1 uses positions 3-60 (58 scored trials), lures count as non-targets.
- The Stroop 60% accuracy check uses all scored congruent trials before RT trimming; RT outcomes use trimmed, correct trials only.
- "Incomplete" means fewer scored trials than the design count (or no threshold/summary row, or no questionnaire).
- A stopped session normally appears as a missing session (a skipped partial upload), not as an excluded one; the stopping rule counts completed sessions.
