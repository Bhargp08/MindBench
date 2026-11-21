# Self-audit before the final review (MB-25)

**Claude's own pre-check, Nov 21, 2026. This is not the independent review**: that is Cursor's (`FINAL_REVIEW.md`), and Bharg approves any fixes. Produced by `analysis/python/mindbench/release_audit.py` (read-only; `uv run python -m mindbench.release_audit` from `analysis/python`; tested by `tests/test_release_audit.py`, written failing first).

## Result of the run
```text
[PASS] secrets in history
    none found
[PASS] private data tracked
    none found
[PASS] commit messages
    no attribution lines; 26 commit(s) carry the review tool's own trailer
[FAIL] pins
    analysis/python/pyproject.toml: scipy>=1.18 has no exact pin or upper bound
[INFO] open placeholders
    PENDING: 7
    BHARG: 1
    UNVERIFIED: 30
    FREEZE: 2
[PASS] paper traced
    every number traced; paper.md matches the builder
[PASS] preregistration coverage
    every H/P/S id has a results row
[PASS] release files
    present
```

## What it means
- **Secrets in history: none found** across every branch, including deleted lines. The patterns cover key blocks and well-known token shapes, not every possible secret; Cursor's keyword grep is a second, different check.
- **Private data tracked: none.** No sqlite/db/.env/raw session/partial/consent/pid-map files; `data_public/` holds only `.gitkeep`.
- **Commit messages:** no attribution lines in commits written by Claude. 26 commits carry `Co-authored-by: Cursor`, added by the review tool to its own commits (not rewritten); one squash-merge commit names Bharg himself.
- **Pins: one finding (Minor).** `analysis/python/pyproject.toml` has `scipy>=1.18` with no upper bound; the lock file pins 1.18.1, so builds are reproducible, but the declared range is open. Proposed fix: `scipy>=1.18,<2` and `uv lock`. **Not changed**; it needs Bharg's approval as part of the fix list.
- **Open placeholders** (`[PENDING`, `[BHARG`, unverified markers, freeze-commit slot) are all intentional and listed in `RELEASE_CHECKLIST.md` as Bharg's steps: live-site URL, Zenodo DOI, registration URL, AI-tools wording, freeze commit, unverified references and literature parameters (30 lines, mostly `literature.csv`/`literature.md`).
- **Paper traced, preregistration coverage, release files:** pass.

## Not covered by this audit
Whole-repo logic review, acceptance criteria per unit, the R tests (R not installed), CI status on GitHub, whether every number in docs outside the paper is right, and re-identification risk of any future release. Also not covered: MB-18 (R frequentist analysis) does not exist, so no confirmatory result can be produced yet.

## Small fix made in this unit
`STATUS.md` listed MB-16 as "PR open"; it was merged as PR #21. Heading corrected.
