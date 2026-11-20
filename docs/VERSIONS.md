# Pinned versions

| Component | Version | Status |
|---|---|---|
| Node | 22 (LTS; `.nvmrc`, CI) | pinned |
| jsPsych | 8.4.0 | pinned in `experiment/package.json` |
| vitest | 2.1.9 | pinned |
| Python (etl) | >=3.11 via uv | pinned in `etl/pyproject.toml` |
| pytest | 8.3.4 | pinned |
| R | via renv (lockfile created once R is confirmed) | pending |
| numpy, scipy (analysis core) | see row below (MB-20) | `analysis/python/pyproject.toml` |
| matplotlib | 3.11.2 | pinned (MB-04; analysis/python/pyproject.toml) |
| Vite | 5.4.21 (experiment build) | pinned (MB-06) |
| jsPsych plugins | html-button-response 2.1.0, survey-html-form 2.1.0, fullscreen 2.1.0 | pinned (MB-06) |
| jsPsych canvas-keyboard-response, html-keyboard-response | 2.1.0, 2.2.0 | pinned (MB-07) |
| EFF Large Wordlist | sha256 addd3553... (see wordpool.json) | source of the recall word pool (MB-11) |
| google-auth, jsonschema, requests | 2.62.2, 4.26.0, 2.34.2 | pinned in etl/pyproject.toml (MB-14) |
| Streamlit (dashboard) | 1.67.0 (pandas comes with it) | pinned in dashboard/pyproject.toml (MB-16) |
| @jspsych/extension-pipe | 0.2.0 | verified on npm, not yet installed |
| PyMC | 6.4.0 | pinned in the `bayes` dependency group of analysis/python/pyproject.toml (MB-20); requires Python 3.12-3.14 |
| ArviZ | 1.3.0 | pinned (MB-20); `az.waic` no longer exists in 1.x, WAIC is computed in `bayes.py` |
| Python (analysis/python, dashboard) | 3.13 (`.python-version`; `requires-python >=3.12,<3.15`) | raised from 3.11: PyMC 6 and scipy 1.18 need 3.12+; the dashboard depends on the analysis package (MB-20) |
| numpy, scipy, numba, llvmlite (analysis/python) | numpy >=2.0,<2.4 (2.3.5 locked); scipy >=1.18 (1.18.1); numba <0.63 (0.62.1); llvmlite <0.46 (0.45.1) | PyMC 6 needs scipy >=1.18; newer llvmlite has no Intel-Mac wheel, and numba 0.62 supports numpy up to 2.3 (MB-20) |
| PyDDM | 0.9.0 | installed in the `bayes` uv group (MB-21); API checked against 0.9.0: bound `B` is the half-width, `OverlayUniformMixture` takes `umixturecoef`, fit value via `fitted.fitresult.value()` |

Registry versions were checked Nov 17, 2026 (per spec). Follow the docs for the pinned version, not older tutorials.
