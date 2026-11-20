# Write-up (MB-23)

Code: `analysis/python/mindbench/writeup.py`, `scripts/build_paper.py`, `scripts/writeup_figures.py`. Template: `docs/writeup/paper_template.md`; output: `docs/writeup/paper.md` (generated, do not edit by hand). Tests: `analysis/python/tests/test_writeup.py` (failing first).

## How "every number traces to a script output" is enforced
- The template has `{{placeholders}}`; values come from `collect_values`: the mixed-model power JSON, the synthesis table (MB-22), `deviations.md`. A missing value shows as `[PENDING: key]`, never a blank or a guess.
- `untraced_numbers` flags any number in the built text that is neither inside a filled placeholder nor a registered design constant (21, 42, 44, 2,000, 10,000, .05; a test checks each is in the prereg). Single digits, hypothesis/outcome labels (H1, S3), the references block and citation strings are not checked. `build_paper.py` refuses to write the paper if any number is untraced.
- The committed `paper.md` must equal the builder's output (a test), so it cannot drift from the template.

## State
- **No data have been analysed**, so the Results section is the pending synthesis table and says so. No claims, no invented numbers.
- The older `docs/design/figures/power_curves.png` comes from the superseded GLS model and is **not** used; the paper's power figure is made from the mixed-model JSON.
- References: only Lim & Dinges (2010), Posner (1980) and Murdock (1962) have had their bibliographic details checked in this project; the other three are flagged "[bibliographic details not verified]" in the paper and must be checked before submission.
- **PDF:** pandoc and a LaTeX engine are not installed here, so no PDF was built. `cd docs/writeup && pandoc paper.md -o paper.pdf` once they are.
- Registration link: `[PENDING: registration.url]` until Bharg registers (pass `--registration-url` to the builder).
- The AI-tools paragraph is a neutral draft; Bharg sets the final wording (as for prereg D10).

## After data
Run the analyses, write their results to a JSON file (analysis id -> source -> {conclusion, estimate, interval, direction}), then `build_paper.py --results results.json`. The Results prose beyond the tables (what the numbers mean) is written then, with each number as a placeholder.
