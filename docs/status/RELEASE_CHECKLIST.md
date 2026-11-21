# Release checklist (MB-25)

State on Nov 21, 2026. **No tag has been made and nothing has been published.** The whole-repo review is Cursor's (`docs/status/FINAL_REVIEW.md`, not yet written); the paste-ready prompt is `FINAL_REVIEW_PROMPT.md`. Claude's own pre-review check is `SELF_AUDIT.md`.

## Acceptance (MB-25): all unchecked until the review is done
- [ ] No open Critical or Major findings in `FINAL_REVIEW.md`
- [ ] CI green on `main` (JS, Python matrix, R)
- [ ] This checklist complete
- [ ] Fixes Bharg approved from the review's numbered fix list are merged

## Built and merged (Claude)
MB-00 to MB-12, MB-14, MB-15, MB-16, MB-19 to MB-24 (plus MB-05, MB-05b, MB-06b). Detail: `STATUS.md`.

## Not built, and why
- **MB-13 self-pilot and think-aloud:** skipped by decision (deviation S1, `deviations.md`); smoke tests only; no qualitative component is claimed.
- **MB-17 data collection:** Bharg's, 21 days of sessions. No data exist yet.
- **MB-18 frequentist analysis (R):** needs R (not installed); the R test folder has pending (skipped) tests. The confirmatory H1/H2 rows in the synthesis table stay pending until it exists. This is a gap in the acceptance of the whole project, not only a to-do.

## Bharg only (external actions; Claude does none of these)
- [ ] Review the prereg draft, especially D5 (Bayesian priors) and D10 wording; check the **unverified references** (Levitt 1971, Shrout & Fleiss 1979, Wagenmakers et al. 2007) and the Koo & Li thresholds
- [ ] Finalise the consent form before any friend takes part (it is a deferred draft)
- [ ] Submit the OSF registration; paste the registration URL and the freeze commit hash; **re-tag** `prereg-v1` if the tag exists from before the D3 to D9 changes
- [ ] Approve and run the GitHub Pages deploy (workflow is off); set up DataPipe and the private Drive; run the smoke tests
- [ ] Collect data (21 days), then run MB-18 when R exists, then the analyses on real scored data and write the Results prose
- [ ] Export, review and check the release (`docs/release/open_data.md`), upload to Zenodo (CC-BY-4.0), add the DOI and release date to `CITATION.cff` and README
- [ ] Reword the README and paper AI-tools paragraphs in your own voice
- [ ] Install pandoc and LaTeX for the PDF (not installed here)
- [ ] Record the demo video and screenshots (`docs/release/`)
- [ ] Tag v1.0 (Bharg only, after the review is clean)

## Standing rules, checked by `SELF_AUDIT.md`
No secrets in history; no real data tracked; no attribution lines in commits written by Claude; every PR reviewed by Cursor and merged by Bharg.
