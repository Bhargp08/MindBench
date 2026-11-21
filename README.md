# MindBench

## What it is
MindBench is a preregistered online experiment battery for attention, perception and memory. One person (the author, Bharg Patel) does a short browser session twice a day for 21 days, and the question is whether naturally varying sleep, or time of day, changes performance. The two primary outcomes are 2-back working-memory d' and free-recall proportion; everything else is labelled exploratory. The analysis is preregistered (frequentist mixed model, Bayesian regression, drift-diffusion models, test-retest reliability).

This is a personal, preregistered self-experiment (N = 1 main participant). No institutional review board review has been obtained, and no institutional approval is claimed. **No data have been collected yet and there are no results**; the paper in `docs/writeup/` shows every result as pending. With 42 sessions the study can reliably detect only large within-person effects (`docs/design/power.md`).

## Live demo
[PENDING: live site URL] — the GitHub Pages deploy is switched off until the author approves it. Until then, run the battery locally (below).

## How to run
Needs Node 22 and [uv](https://docs.astral.sh/uv/). Each folder is its own project.

```bash
cd experiment && npm ci && npm run dev      # the battery in your browser (Vite dev server)
cd experiment && npm test                   # experiment tests
cd etl && uv run pytest                     # loader / validation / docs-lint tests
cd analysis/python && uv run pytest         # scoring, models, write-up tests (about 12 minutes: PyMC and PyDDM fits)
cd dashboard && uv run pytest               # dashboard tests
cd dashboard && uv run streamlit run app.py # monitoring dashboard (set MINDBENCH_DASHBOARD_PUBLIC=1 for the public aggregate view)
```

Participant data goes through DataPipe to a private Google Drive and is loaded with `cd etl && uv run python -m mindbench_etl load` into a gitignored `data/` folder. The repository and its tests contain simulated data only.

## How to reproduce
Everything below runs from the de-identified release in `data_public/` (or from a simulated one) and never touches the private database:

```bash
cd analysis/python
uv run python -m mindbench.public_data simulate --out /tmp/mindbench_sim     # a clearly labelled SIMULATED release
uv run python -m mindbench.public_data check --dir /tmp/mindbench_sim        # the de-identification check
uv run python -m mindbench.public_data reproduce --dir /tmp/mindbench_sim    # counts and descriptive checks from the release
uv run python scripts/build_paper.py                                         # rebuild docs/writeup/paper.md (refuses untraced numbers)
```

`data_public/` is empty until the author releases real data. Only the descriptive manipulation checks are recomputed from the release here; the confirmatory models are specified in `docs/design/prereg_draft.md` and are run after collection. See `docs/release/open_data.md`.

## Data
Raw data stay private (sleep and sleepiness are health-related). The public release is de-identified: participant codes are replaced by pseudonyms (P01, P02, ...), free text (typed recall words, notes, device strings) is dropped, bed and wake times and browser details are dropped, and the start time is reduced to the study day plus AM/PM (nothing finer than the date). The author's own data is released; a friend's data is released only if they ticked the open-data consent box. A script checks every file before release. The release goes to Zenodo under CC-BY-4.0: [PENDING: Zenodo DOI]. Details: `docs/ethics/data_management.md`, `docs/release/open_data.md`.

## Use of AI tools
An AI coding assistant wrote most of the code, tests and design documents in this repository, working from a written specification and with every unit reviewed by a second AI review tool; the commit history and `docs/status/STATUS.md` show the units. The author made the design decisions, wrote the preregistration choices, and merged every change. The AI tools did not collect or see any participant data. [BHARG: reword in your own voice]

## License
Code: MIT (`LICENSE`). Released data: CC-BY-4.0 (at release time). The free-recall words are selected from the EFF Large Wordlist by Joseph Bonneau / Electronic Frontier Foundation (https://www.eff.org/deeplinks/2016/07/new-wordlists-random-passphrases), used under EFF's CC BY policy; see `docs/design/wordpool.md`.

## How to cite
See `CITATION.cff` (GitHub shows a "Cite this repository" button). The DOI will be added after the Zenodo release.

## Status
Build progress is in `docs/status/STATUS.md`. The preregistration is not yet submitted.
