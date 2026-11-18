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

## MB-02: Canonical task parameters (PR open, slimmed scope)
- Scope change (Bharg, Nov 17, 2026): one table of canonical task parameters (`docs/design/literature.csv` + `literature.md`), each row with one source and a verified/[UNVERIFIED] flag.
- **Deferred stretch work (not scheduled):** the expected-effect-size review and the sleep-deprivation literature section (including natural-vs-total sleep loss effect sizes, Lim & Dinges, Ratcliff & Van Dongen, KSS and the remaining spec reference list). Power analysis (MB-04) currently relies on the spec's simulation values.
- Only the staircase rule is verified. All other rows are [UNVERIFIED]; verify against primary papers or set as explicit design choices in MB-03.
