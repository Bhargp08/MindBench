"""Paper assembly (MB-23). The paper is built from docs/writeup/paper_template.md.

Every number that is not a registered design constant must come from a {{placeholder}} filled by a script output
(power_mixed_results.json, the synthesis table, deviations.md). `untraced_numbers` finds any that do not; the tests
require none. With no results the paper says so and makes no claims. Reads no database or data file.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from . import synthesis

ROOT = Path(__file__).resolve().parents[3]
START, END, SEP = "⟦", "⟧", "|"

# Design constants that may be typed into the prose. Each appears in the preregistration (a test checks).
ALLOWED_CONSTANTS = ("21", "42", "44", "2,000", "10,000", ".05")

REFERENCES = {
    "limdinges2010": {"cite": "(Lim & Dinges, 2010)", "verified": True,
                      "text": "Lim, J., & Dinges, D. F. (2010). A meta-analysis of the impact of short-term sleep deprivation on cognitive variables. Psychological Bulletin, 136(3), 375-389."},
    "levitt1971": {"cite": "(Levitt, 1971)", "verified": False,
                   "text": "Levitt, H. (1971). Transformed up-down methods in psychoacoustics. Journal of the Acoustical Society of America, 49(2B), 467-477."},
    "posner1980": {"cite": "(Posner, 1980)", "verified": True,
                   "text": "Posner, M. I. (1980). Orienting of attention. Quarterly Journal of Experimental Psychology, 32(1), 3-25."},
    "murdock1962": {"cite": "(Murdock, 1962)", "verified": True,
                    "text": "Murdock, B. B. (1962). The serial position effect of free recall. Journal of Experimental Psychology, 64(5), 482-488."},
    "shrout1979": {"cite": "(Shrout & Fleiss, 1979)", "verified": False,
                   "text": "Shrout, P. E., & Fleiss, J. L. (1979). Intraclass correlations: Uses in assessing rater reliability. Psychological Bulletin, 86(2), 420-428."},
    "wagenmakers2007": {"cite": "(Wagenmakers et al., 2007)", "verified": False,
                        "text": "Wagenmakers, E.-J., van der Maas, H. L. J., & Grasman, R. P. P. P. (2007). An EZ-diffusion model for response time and accuracy. Psychonomic Bulletin & Review, 14(1), 3-22."},
}

FIGURES = [{"id": "power", "script": "analysis/python/scripts/writeup_figures.py", "image": "figures/power_mixed.png"}]


# ------------------------------------------------------------------------------------------------ placeholders
def placeholders(template: str) -> set[str]:
    return set(re.findall(r"\{\{([\w.]+)\}\}", template))


def render(template: str, values: dict, mark: bool = False, pending_ok: bool = False) -> str:
    def sub(m):
        key = m.group(1)
        if key in values:
            return f"{START}{key}{SEP}{values[key]}{END}" if mark else str(values[key])
        if pending_ok:
            return f"[PENDING: {key}]"
        raise KeyError(key)

    return re.sub(r"\{\{([\w.]+)\}\}", sub, template)


def strip_marks(text: str) -> str:
    return re.sub(rf"{START}[\w.]+\{SEP}(.*?){END}", r"\1", text, flags=re.DOTALL)


# ------------------------------------------------------------------------------------------------ number tracing
_NUMBER = re.compile(r"(?<![\w.])(\d{1,3}(?:,\d{3})+|\d+\.\d+|\.\d+|\d{2,})(?![\w])")
_LABELS = re.compile(r"\b[A-Z]{1,3}\d\b|MB-\d+|\d+-back|\d-up/\d-down|ICC\(\d,\d\)|AR\(\d\)|\bd'|\b[A-Z]{2,}:S\d\b")


def untraced_numbers(text: str) -> list[str]:
    """Numbers in prose that come neither from a filled placeholder nor from the registered design constants.
    Not checked: the references block, single digits, hypothesis/outcome labels (H1, S3, ...), citation strings."""
    text = re.sub(f"{START}.*?{END}", " ", text, flags=re.DOTALL)
    text = re.split(r"^## References", text, flags=re.MULTILINE)[0]
    for r in REFERENCES.values():
        text = text.replace(r["cite"], " ")
    text = _LABELS.sub(" ", text)
    return [n for n in _NUMBER.findall(text) if n not in ALLOWED_CONSTANTS]


# ------------------------------------------------------------------------------------------------ content
def render_references() -> str:
    lines = []
    for r in sorted(REFERENCES.values(), key=lambda r: r["text"]):
        lines.append(f"- {r['text']}" + ("" if r["verified"] else " [bibliographic details not verified]"))
    return "\n".join(lines)


def collect_values(results: dict, registration_url: str | None = None) -> dict:
    """Everything the template may reference, each from a script output: the mixed-model power simulation, the synthesis
    table built from `results` (analysis id -> source -> result), deviations.md."""
    power = json.loads((ROOT / "docs" / "design" / "power_mixed_results.json").read_text())
    head = power["headline"]
    r_keys = sorted(float(m.group(1)) for k in head if (m := re.match(r"r([\d.]+)_holm_both$", k)))
    rows = synthesis.build_results_table(results)
    done = [r for r in rows if r["status"] != "not yet run"]
    deviations = synthesis.parse_deviations((ROOT / "docs" / "design" / "deviations.md").read_text(encoding="utf-8"))
    return {
        "power.r_high": f"{r_keys[-1]:.2f}", "power.r_low": f"{r_keys[0]:.2f}",
        "power.holm_r43": f"{head['r0.43_holm_both']:.2f}", "power.holm_r30": f"{head['r0.30_holm_both']:.2f}",
        "power.detectable_r": f"{head['detectable_r_80']:.2f}", "power.sims": f"{power['meta']['n_sims']:,}",
        "power.day_share": f"{float(head['planning_scenario'].rsplit('_', 1)[1]):.0%}",
        "status.note": ("No data have been analysed yet: every result below is pending." if not done
                        else "Results are partly complete; rows marked pending have not been run."),
        "table.confirmatory": synthesis.render_markdown([r for r in rows if r["tier"] == "confirmatory"], title=False, level=4),
        "table.exploratory": synthesis.render_markdown([r for r in rows if r["tier"] != "confirmatory"], title=False, level=4),
        "section.deviations": synthesis.render_deviations_section(deviations).split("\n", 2)[2],
        "registration.url": registration_url or "[PENDING: registration.url]",
        "references": render_references(),
    }


def build_paper(template: str, values: dict, mark: bool = False) -> str:
    text = render(template, values, mark=mark, pending_ok=True)
    return re.sub(r"\[@([\w-]+)\]", lambda m: REFERENCES[m.group(1)]["cite"], text)
