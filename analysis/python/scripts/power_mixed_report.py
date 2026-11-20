"""Re-simulate H1 type-I error and power for the preregistered primary model (MB-05b).

Run from analysis/python:  uv run python scripts/power_mixed_report.py
Writes docs/design/power_mixed_results.json. Scenarios: r in {0, .30, .35, .40, .43, .45, .50, .55}, with and
without a 30% shared-day component in the noise, 21 days x 2 sessions, AR(1) phi = 0.3, 2,000 simulations each.
A secondary run with the GLS AR(1) fit (no day intercept) on the same data is recorded for comparison.
"""
import json
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np

from mindbench import mixed_power as mp

OUT = Path(__file__).resolve().parents[3] / "docs" / "design" / "power_mixed_results.json"
N_SIMS = 2000
CHUNKS = 16
R_GRID = [0.0, 0.30, 0.35, 0.40, 0.43, 0.45, 0.50, 0.55]
SHARES = [0.0, 0.30]
GLS_R = [0.0, 0.30, 0.43]
BASE_SEED = 20261118


def key_r(r):
    return f"r{r:.2f}"


def key_share(s):
    return f"day_share_{s:.2f}"


def job(args):
    model, share, r, seed, n = args
    return (model, share, r), mp.scenario_counts(r, share, n, seed, model=model)


def main():
    jobs, ss = [], np.random.SeedSequence(BASE_SEED)
    seeds = iter(ss.spawn(len(SHARES) * (len(R_GRID) + len(GLS_R)) * CHUNKS))
    for model, rs in (("mixed", R_GRID), ("gls_ar1", GLS_R)):
        for share in SHARES:
            for r in rs:
                for _ in range(CHUNKS):
                    jobs.append((model, share, r, int(next(seeds).generate_state(1)[0]), N_SIMS // CHUNKS))
    totals = {}
    with Pool(processes=min(14, len(jobs))) as pool:
        for k, c in pool.imap_unordered(job, jobs):
            t = totals.setdefault(k, {})
            for name, v in c.items():
                t[name] = t.get(name, 0) + v
    res = {"meta": {
        "n_sims": N_SIMS, "n_days": 21, "phi": 0.3, "base_seed": BASE_SEED,
        "model": "linear mixed model: random intercept for day + AR(1) over calendar slots (slot = 2*(day-1)+PM+1), REML, "
                 "b1 tested with t on df = included days - 5; covariates: sleep (centered), k, ln k, PM",
        "dgp": "sleep drawn per day (AM and PM share it); y = r*sleep + sqrt(1-r^2)*e, e unit variance = sqrt(share)*day component "
               "+ sqrt(1-share)*AR(1) noise (phi 0.3); two sessions per day, 21 days, no missing sessions; outcomes have independent noise",
        "definitions": {
            "type1_single": "two-sided rejection (p < .05) of a null outcome, pooled over two null outcomes",
            "type1_fwer_holm": "any Holm rejection (two-sided) among two null outcomes",
            "power_single": "p < .05 and b1 > 0 (uncorrected), pooled over two true outcomes",
            "power_holm_both": "Holm-adjusted p < .05 and b1 > 0, both outcomes true (mean over the two)",
            "power_holm_one": "Holm-adjusted p < .05 and b1 > 0 for the true outcome when the other outcome is null"},
    }, "scenarios": {}, "gls_ar1_comparison": {}}
    for (model, share, r), c in totals.items():
        target = res["scenarios"] if model == "mixed" else res["gls_ar1_comparison"]
        target.setdefault(key_share(share), {})[key_r(r)] = mp.counts_to_rates(c, r)

    plan = res["scenarios"][key_share(0.30)]
    xs = [r for r in R_GRID if r > 0]
    ys = [plan[key_r(r)]["power_holm_both"] for r in xs]
    detect = None
    for (x0, y0), (x1, y1) in zip(zip(xs, ys), zip(xs[1:], ys[1:])):
        if y0 < 0.80 <= y1:
            detect = x0 + (0.80 - y0) * (x1 - x0) / (y1 - y0)
            break
    res["headline"] = {
        "planning_scenario": key_share(0.30),
        "r0.43_holm_both": plan["r0.43"]["power_holm_both"],
        "r0.30_holm_both": plan["r0.30"]["power_holm_both"],
        "detectable_r_80": round(detect, 2) if detect else None,
        "note": "planning scenario = 30% shared-day component; detectable r by linear interpolation of Holm-both power on the r grid",
    }
    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(json.dumps(res["headline"], indent=1))
    for share, d in res["scenarios"].items():
        print(share, {k: {m: round(v, 3) for m, v in x.items() if isinstance(v, float)} for k, x in d.items()})
    print("GLS comparison", json.dumps({s: {k: {m: round(v, 3) for m, v in x.items() if isinstance(v, float)} for k, x in d.items()} for s, d in res["gls_ar1_comparison"].items()}))


if __name__ == "__main__":
    sys.exit(main())
