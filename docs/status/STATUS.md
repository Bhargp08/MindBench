# Status

## MB-00: Repo, decisions, CI skeleton (merged)

### Approved exception
- The R placeholder test (`analysis/r/tests/testthat/test-placeholder.R`) is skipped via `skip()` until R is installed and confirmed. Bharg approved this skip on PR #1 (Cursor review, Nov 17, 2026). Remove the skip and create `renv.lock` once R is confirmed.

### Deferred items (intentionally not in MB-00)
- `CITATION.cff` (MB-24)
- `experiment/index.html` (MB-06 / MB-12)
- `dashboard/app.py` (MB-16)
- `renv.lock` (once R is installed and confirmed)

## MB-01: Ethics, consent, data management (merged)
- Scope change (Bharg, Nov 17, 2026): Bharg is the only participant for now.
- Written and approved: `docs/ethics/self_pilot_policy.md`, `docs/ethics/data_management.md`.
- Consent form: draft kept in `docs/ethics/consent_form.md` for later use; structure lint tests are active. Must be finalized (contact method filled in) before any other participant takes part. Bharg approved deferring *use* of the form while he is the only participant (Nov 17, 2026).
- The "no institutional approval claims" guard stays active.
- Retention set (Bharg, Nov 17, 2026): raw data until Dec 31, 2028 or 2 years after write-up publication, whichever is later, then deleted; open data on Zenodo kept indefinitely.
- Open placeholder: consent contact method (deferred form).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).

## MB-02: Canonical task parameters (merged, slimmed scope)
- Scope change (Bharg, Nov 17, 2026): one table of canonical task parameters (`docs/design/literature.csv` + `literature.md`), each row with one source and a verified/[UNVERIFIED] flag.
- **Deferred stretch work (not scheduled):** the expected-effect-size review and the sleep-deprivation literature section (including natural-vs-total sleep loss effect sizes, Lim & Dinges, Ratcliff & Van Dongen, KSS and the remaining spec reference list). Power analysis (MB-04) currently relies on the spec's simulation values.
- Only the staircase rule is verified. All other rows are [UNVERIFIED]; verify against primary papers or set as explicit design choices in MB-03.
- Follow-up: total-deprivation vs natural-variation caveat added to `literature.md` (PR mb/MB-02-caveat).

## MB-03: Design document (merged)
- `docs/design/design.md`: hypotheses H1-H3, explicit design choices for every unverified parameter (Posner 80/20, 2-back 30% targets, trial counts, timings), exclusion rules, analysis summary, stopping and deviation rules.
- Built with Sonnet; spec recommends Opus for MB-03. No code or tests (doc unit).
- Cursor fix before merge: free-recall word-pool requirement corrected to 2,080 (52 sessions × 40 words).
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).
- **Superseded by MB-04:** original draft had 5 primary outcomes (P1–P5) with Holm over 5; confirmatory primaries are now P1 (2-back d') and P2 (recall), per Bharg's MB-04 decision.

## MB-04: Power analysis (merged)
- `analysis/python/mindbench/power.py` + tests, `docs/design/power.md`, figure and numbers via `scripts/power_report.py`.
- **Decisions (Bharg, Nov 17, 2026):** keep 42 sessions; reduce primary outcomes to 2 (P1 2-back d', P2 recall proportion), chosen from the verified Lim & Dinges (2010) Table 2; Stroop, Posner, contrast threshold and others are secondary/exploratory, outside the Holm family.
- Effective power at 42 sessions, r = .43 (AR(1) + shared nightly sleep + Holm over 2): about 0.74. 80% effective power needs r of about 0.46. A null result is likely and acceptable.
- Carry to MB-18: AR(1) errors alone do not inflate type-I; the shared AM/PM nightly sleep does (0.083 uncorrected). Model AR(1) errors and day grouping.
- Design doc updated to match (primary/secondary outcomes, H1/H2/H3, Holm family of 2).
- Cursor fix before merge: Holm comparison test uses n_sims=2000 (spec minimum); VERSIONS.md lists exact numpy/scipy/matplotlib pins; MB-03 STATUS notes 5→2 primary supersession.
- Approved by Bharg and merged after Cursor review (Nov 17, 2026).
