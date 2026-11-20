"""MB-23 figures. Reads docs/design/power_mixed_results.json (made by power_mixed_report.py); writes docs/writeup/figures/."""
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[3]
res = json.loads((ROOT / "docs" / "design" / "power_mixed_results.json").read_text())
out = ROOT / "docs" / "writeup" / "figures"
out.mkdir(parents=True, exist_ok=True)

fig, ax = plt.subplots(figsize=(6, 4))
for label, key, style in (("30% day component (planning)", "day_share_0.30", "-"), ("no day component", "day_share_0.00", "--")):
    pts = sorted((float(k[1:]), v["power_holm_both"]) for k, v in res["scenarios"][key].items() if "power_holm_both" in v)
    ax.plot([p[0] for p in pts], [p[1] for p in pts], style, marker="o", label=label)
ax.axhline(0.8, color="grey", lw=1)
ax.set_xlabel("within-person correlation r")
ax.set_ylabel("power (Holm, both primary outcomes true)")
ax.set_ylim(0, 1)
ax.legend()
fig.tight_layout()
fig.savefig(out / "power_mixed.png", dpi=150)
