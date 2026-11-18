# Status

## MB-00: Repo, decisions, CI skeleton (awaiting merge)

### Approved exception
- The R placeholder test (`analysis/r/tests/testthat/test-placeholder.R`) is skipped via `skip()` until R is installed and confirmed. Bharg approved this skip on PR #1 (Cursor review, Nov 17, 2026). Remove the skip and create `renv.lock` once R is confirmed.

### Deferred items (intentionally not in MB-00)
- `CITATION.cff` (MB-24)
- `experiment/index.html` (MB-06 / MB-12)
- `dashboard/app.py` (MB-16)
- `renv.lock` (once R is installed and confirmed)

## MB-01: Ethics, consent, data management (PR open)
- Scope change (Bharg, Nov 17, 2026): Bharg is the only participant for now.
- Written: `docs/ethics/self_pilot_policy.md`, `docs/ethics/data_management.md` (concise).
- **Deferred:** the consent form. A draft `consent_form.md` is kept for later; its lint tests are skipped with `pytest.mark.skip` ("Deferred until other participants join; Bharg approved Nov 17, 2026"). Must be finalized, approved and un-skipped before any other participant takes part.
- The "no institutional approval claims" guard stays active.
- Open placeholders: retention end date (data management); consent contact method (deferred form).
- Pending: Cursor review and Bharg's approval.
