# Final whole-repo review (MB-25)

**Reviewer:** Cursor (independent). **Date:** Nov 21, 2026. **Scope:** MB-00–MB-24 on `main` after PR #28 merge. **I did not tag v1.0, merge this review as a release, or publish data.**

## Summary

The repository is **fit for a code/preregistration v1.0** in the sense that tests pass, there are no tracked secrets or private data, the paper traceability and synthesis/prereg coverage hold, and open-data rules are implemented and tested. It is **not fit to claim confirmatory H1/H2 results** until **MB-18** (frequentist R analysis) exists and real data have been run. Seven `[PENDING]` and one `[BHARG]` markers in product docs are intentional pre-release slots.

**Automated audit** (`uv run python -m mindbench.release_audit` from `analysis/python`): **all checks pass** after fix #1 (scipy upper bound, merged in PR #28).

**CI:** GitHub Actions **5/5 green** on PR #28 (including the scipy follow-up commit).

## Tests (local, `CI=1`, this review)

| Suite | Passed | Notes |
|---|---|---|
| analysis/python | 393 | ~13 min (PyMC + PyDDM) |
| etl | 130 | includes `test_release_docs`, `test_final_review_docs` |
| dashboard | 71 | |
| experiment (vitest) | 193 | |
| R testthat | skipped | placeholder `skip()` until R confirmed (MB-00 approved exception) |

**Reproduce from public data only:** `uv run python -m mindbench.public_data simulate --out /tmp/mb_sim` → `check` → `reproduce` completes; `reproduce` source has no `sqlite3` / `load_sessions` / `score_database` (`test_public_data.py::TestReproduce::test_it_never_opens_the_private_database`).

**Paper:** `build_paper.py` and `test_writeup.py` — untraced numbers empty; committed `paper.md` equals builder output.

## Findings (severity rubric)

### Critical

*None.*

### Major

1. **MB-18 frequentist analysis (R) not built.** Confirmatory H1/H2 cannot be produced; synthesis rows stay pending. Documented in `RELEASE_CHECKLIST.md` and `STATUS.md`. **Not a blocker for merging MB-25 tooling**, but **blocks “study complete” acceptance** until R is installed and MB-18 is implemented. *Evidence:* no `mindbench` frequentist/R fit module; R tests skipped in CI.

### Minor

*None open on `main` after PR #28.*

### Nit

1. **D2/D9 date logic duplicated** in `public_data.day_and_period` and `dashboard…metrics._day_and_slot` (equivalent rules; export tests cover prereg cases). Consider a shared helper later to avoid drift.

### Informational (no fix required)

- **26+ commits** with `Co-authored-by: Cursor <cursoragent@cursor.com>` (review-tool trailer); `release_audit` counts these separately — not treated as Claude attribution failures.
- **Open markers:** `[PENDING]` (7), `[BHARG: reword]` (1), `[UNVERIFIED]` / literature flags (30), freeze-commit placeholders (2) — listed in `RELEASE_CHECKLIST.md` as Bharg’s steps.
- **No qualitative pilot** (deviation S1); paper/README state this; no false claims found (`test_release_docs`, `test_writeup`).

### Needs Bharg decision

1. **What v1.0 means:** tag **code + prereg-ready toolchain** now vs wait until **MB-18 + post-collection analyses**? Checklist currently allows tooling release with MB-18 deferred; confirm that matches your intent.

## Acceptance by unit (evidence sketch)

| Unit | Status | Evidence |
|---|---|---|
| MB-00–MB-04 | Met | CI skeleton, ethics docs, power/mixed (`power_mixed_results.json`), tests in `analysis/python/tests` |
| MB-05 / 05b | Met | `prereg_draft.md`, lint `etl/tests/test_prereg_lint.py` |
| MB-06–MB-12 | Met | experiment vitest 193; tasks per STATUS |
| MB-13 | Skipped | Deviation S1; no formal pilot claimed |
| MB-14–MB-16 | Met | ETL, scoring, dashboard (public mode, D2/D9 tests) |
| MB-17 | Bharg | Data collection not started |
| **MB-18** | **Not built** | See Major #1 |
| MB-19–MB-24 | Met | reliability, bayes, ddm, synthesis, writeup, public_data, README/CITATION |
| MB-25 | Met (this review) | `release_audit.py`, this file, checklists |

Detail per unit: `docs/status/STATUS.md`.

## Ethics / data

- README and paper: **no IRB approval claimed**; self-experiment wording (`test_writeup`, `test_release_docs`).
- **No real participant data** in git; `forbidden_tracked` passes; `data_public/` only `.gitkeep`.
- Export: consent `is True` only; de-id check (codes, free text, date+AM/PM only, whole-cell epoch) — `test_public_data.py`.
- Consent form still **deferred draft** for friends (`RELEASE_CHECKLIST.md`).

## Prereg / synthesis / deviations

- `synthesis.missing_prereg_ids` empty vs `prereg_draft.md`; 15 analysis rows (`test_synthesis.py`).
- Confirmatory decisions from frequentist only in `synthesis._decision` (tests).
- `deviations.md` part A (S1–S8) parses; part B empty until registration (`test_synthesis.py::TestDeviations`).

## Dependencies

- Pins audited by `release_audit.pin_problems`; **pass** on `main` after `scipy>=1.18,<2` + lock refresh.
- `docs/VERSIONS.md` documents Python 3.12–3.14, PyMC/ArviZ/pyddm group, Intel-Mac numba pin.

## Git history (secrets)

- `release_audit.scan_history`: **none** on all branches (complemented by pattern tests with fake secrets; not a substitute for org-wide secret scanning).

## Numbered fix list

| # | Severity | Item | Status |
|---|---|---|---|
| 1 | Minor | `scipy>=1.18,<2` in `analysis/python/pyproject.toml` + `uv lock` | **Done** (PR #28, post-review commit) |
| 2 | Major | Implement MB-18 frequentist/R confirmatory pipeline when R is available | **Open** — Bharg approves scheduling |
| 3 | — | OSF submit, `prereg-v1` re-tag, Zenodo, live URL, consent finalisation, unverified references | **Bharg only** (`RELEASE_CHECKLIST.md`) |
| 4 | Nit | Optional shared D2/D9 time helper (dashboard vs `public_data`) | **Optional** — approve if wanted |

## Release verdict

- **MB-25 (audit + this review):** merge complete; **no open Critical or Minor findings** on `main`.
- **v1.0 tag:** remains **Bharg’s** after you approve fix list items and checklist; I recommend **not** tagging v1.0 as “results complete” until MB-17/18 and real analyses are done unless you explicitly want a **codebase-only** v1.0 now.