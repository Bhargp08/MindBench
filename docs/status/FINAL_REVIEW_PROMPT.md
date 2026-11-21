# Prompt for the final whole-repo review (MB-25)

Paste into Cursor. This follows section 8 of `MINDBENCH_CURSOR_REVIEW_SPEC.md`.

```
You are the independent reviewer for the MindBench repo, doing the FINAL whole-repo review before v1.0. Claude wrote the repo; you review it. You never merge, never tag, and do not tag v1.0 or push release artifacts.
Inputs: MINDBENCH_CLAUDE_SPEC.md (build spec, source of truth), MINDBENCH_CURSOR_REVIEW_SPEC.md section 8, docs/status/STATUS.md, docs/status/RELEASE_CHECKLIST.md, docs/status/SELF_AUDIT.md (Claude's own pre-check; do not rely on it, verify independently).

Do the following, in order:
1. Re-check every unit's acceptance criteria (MB-00 to MB-24) with evidence (file:line, test name or output). Note units skipped or deferred on purpose (MB-13, MB-17, MB-18) and whether the spec's acceptance for the whole project is still met.
2. Run all tests, including the slow ones: npm test in experiment/, uv run pytest in etl/, dashboard/ and analysis/python/ (about 13 minutes), Rscript testthat in analysis/r/. Report pass/fail counts and CI status on main.
3. Reproduce the analyses from data_public/ (use a simulated release: `uv run python -m mindbench.public_data simulate`, then `check`, `reproduce`) and confirm nothing reads the private database.
4. Trace every number in docs/writeup/paper.md to a script output or a registered design constant; run scripts/build_paper.py and confirm paper.md equals its output.
5. Check the preregistration vs the results table vs docs/design/deviations.md for consistency (every H/P/S id covered, confirmatory decisions from the frequentist result only, deviations parts A and B).
6. Re-run the ethics checks repo-wide: no IRB or ethics-approval claims, consent form status, no real participant data, de-identification rules and consent rule in the export.
7. Check dependencies and pins (docs/VERSIONS.md vs pyproject, package.json, lock files).
8. Check git history for secrets (e.g. git log -p --all | grep -iE "token|secret|api[_-]?key") and for real data.
9. Classify findings with the severity rubric (Critical to Nit). Write docs/status/FINAL_REVIEW.md with findings ranked Critical first and a numbered fix list. Bharg approves which fixes Claude makes. Mark anything the spec makes ambiguous as "Needs Bharg decision" and quote both sources.
```
