"""Generate MB-04 power figures and numbers. Run: uv run python scripts/power_report.py"""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mindbench import power

OUT = Path(__file__).resolve().parents[3] / "docs" / "design"
FIG = OUT / "figures"
SEED = 20261117
NS = list(range(20, 61, 4))
KW = dict(phi=0.3, paired_sleep=True, method="ar1")

results = {"ns": NS, "curves": {}, "detectable": {}}
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
for ax, r in zip(axes, (0.43, 0.30)):
    iid = power.power_curve(NS, r=r, n_sims=1000, seed=SEED)
    ar = power.power_curve(NS, r=r, n_sims=1000, seed=SEED, **KW)
    holm = power.power_curve(NS, r=r, n_sims=1000, seed=SEED, holm_m=5, **KW)
    results["curves"][str(r)] = {"iid_uncorrected": iid, "ar1_shared_sleep": ar, "ar1_shared_sleep_holm5": holm}
    for label, c in (("i.i.d., no correction", iid), ("AR(1) + shared sleep", ar), ("AR(1) + shared sleep + Holm (5 outcomes)", holm)):
        ax.plot([n for n, _ in c], [p for _, p in c], marker="o", ms=3, label=label)
    ax.axhline(0.8, color="gray", ls="--", lw=1)
    ax.axvline(42, color="gray", ls=":", lw=1)
    ax.set_title(f"within-person r = {r}")
    ax.set_xlabel("sessions")
axes[0].set_ylabel("power")
axes[0].legend(fontsize=7, loc="lower right")
fig.tight_layout()
fig.savefig(FIG / "power_curves.png", dpi=150)

# Detectable r at 42 sessions (80% power), Holm over 5 true outcomes, AR(1) + shared sleep
for r in (0.40, 0.45, 0.50, 0.55, 0.60):
    results["detectable"][str(r)] = power.simulate_holm_power(
        n=42, r=r, m=5, n_true=5, n_sims=1000, seed=SEED, **KW
    )

# AM/PM paired analytic (days = pairs)
results["paired"] = {str(n): power.paired_t_power(0.65, n) for n in (14, 18, 21, 28)}
results["paired_dz_for_80_at_21"] = 0.65
(OUT / "power_results.json").write_text(json.dumps(results, indent=1))
print(json.dumps(results["detectable"]), json.dumps(results["paired"]))
for r, d in results["curves"].items():
    for k, c in d.items():
        print(r, k, [(n, round(p, 2)) for n, p in c if n in (28, 40, 44, 48, 60)])
