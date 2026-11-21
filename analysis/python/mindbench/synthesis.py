"""Synthesis (MB-22): one results table covering every preregistered analysis, and the deviations log.

This module only assembles results handed to it. It reads no database or data file and makes up no numbers: a row
with no result says "pending". Confirmatory decisions (H1, H2) come from the frequentist analysis only (prereg: Bayesian,
exploratory and DDM results are never used to claim support); everything else is labelled exploratory or descriptive.
"""
from __future__ import annotations

import re

SOURCES = ("frequentist", "bayes", "ddm", "reliability")  # MB-18, MB-20, MB-21, MB-19
CONCLUSIONS = ("supported", "not supported", "cannot tell", "descriptive", "pending")
DIRECTIONS = ("positive", "negative", "none", "unclear")


def _a(id, label, tier, sources, anchor, group):
    return {"id": id, "label": label, "tier": tier, "sources": tuple(sources), "anchor": anchor, "group": group}


# `anchor` is text that must appear in docs/design/prereg_draft.md, so each row points at a preregistered analysis.
ANALYSES = [
    _a("H1:P1", "H1 sleep -> 2-back d' (P1)", "confirmatory", ("frequentist", "bayes"), "H1 (confirmatory)", "H1"),
    _a("H1:P2", "H1 sleep -> free-recall proportion (P2)", "confirmatory", ("frequentist", "bayes"), "H1 (confirmatory)", "H1"),
    _a("H2:P1", "H2 PM - AM on 2-back d' (P1)", "confirmatory", ("frequentist",), "H2 (confirmatory)", "H2"),
    _a("H2:P2", "H2 PM - AM on recall proportion (P2)", "confirmatory", ("frequentist",), "H2 (confirmatory)", "H2"),
    _a("H3:S1", "H3 mechanism, Stroop (drift vs boundary)", "exploratory", ("ddm",), "Drift-diffusion models", "H3"),
    _a("H3:S2", "H3 mechanism, Posner (drift vs boundary)", "exploratory", ("ddm",), "Drift-diffusion models", "H3"),
    _a("S1", "S1 Stroop interference", "exploratory", ("frequentist",), "Secondary and exploratory outcomes", "S"),
    _a("S2", "S2 Posner validity effect", "exploratory", ("frequentist",), "Secondary and exploratory outcomes", "S"),
    _a("S3", "S3 contrast threshold", "exploratory", ("frequentist",), "Secondary and exploratory outcomes", "S"),
    _a("S4", "S4 yes/no d' and criterion c", "exploratory", ("frequentist",), "Secondary and exploratory outcomes", "S"),
    _a("S5", "S5 other measures", "exploratory", ("frequentist",), "Secondary and exploratory outcomes", "S"),
    _a("MC:S1", "Manipulation check: Stroop interference present", "descriptive", ("frequentist",), "Manipulation checks", "MC"),
    _a("MC:S2", "Manipulation check: Posner validity effect present", "descriptive", ("frequentist",), "Manipulation checks", "MC"),
    _a("MC:SERIAL", "Manipulation check: serial-position curve", "descriptive", ("frequentist",), "Manipulation checks", "MC"),
    _a("REL", "Test-retest reliability (ICC, split-half)", "exploratory", ("reliability",), "Reliability (exploratory)", "REL"),
]
_BY_ID = {a["id"]: a for a in ANALYSES}
GROUP_TITLES = {"H1": "H1: sleep (confirmatory)", "H2": "H2: time of day (confirmatory)", "H3": "H3: mechanism, drift-diffusion (exploratory)",
                "S": "Secondary and exploratory outcomes S1-S5", "MC": "Manipulation checks (descriptive)", "REL": "Reliability (exploratory)"}


def _blank():
    return {"conclusion": "pending", "estimate": None, "interval": None, "direction": None}


def build_results_table(results: dict) -> list[dict]:
    """One row per preregistered analysis. `results` maps analysis id -> source -> {conclusion, estimate, interval, direction}."""
    for aid, by_source in results.items():
        if aid not in _BY_ID:
            raise ValueError(f"unknown analysis id: {aid}")
        for src, r in by_source.items():
            if src not in SOURCES or src not in _BY_ID[aid]["sources"]:
                raise ValueError(f"source {src!r} is not planned for {aid}")
            if r.get("conclusion", "pending") not in CONCLUSIONS:
                raise ValueError(f"conclusion {r.get('conclusion')!r} is not one of {CONCLUSIONS}")
            if r.get("direction") not in (None, *DIRECTIONS):
                raise ValueError(f"direction {r.get('direction')!r} is not one of {DIRECTIONS}")
    rows = []
    for a in ANALYSES:
        given = results.get(a["id"], {})
        srcs = {s: {**_blank(), **given.get(s, {})} for s in a["sources"]}
        pending = [s for s, r in srcs.items() if r["conclusion"] == "pending"]
        status = "not yet run" if len(pending) == len(srcs) else ("partial" if pending else "complete")
        rows.append({**{k: a[k] for k in ("id", "label", "tier", "anchor", "group")}, "sources": srcs, "status": status,
                     "decision": _decision(a, srcs), "convergence": _convergence(srcs, pending)})
    return rows


def _decision(a: dict, srcs: dict) -> str:
    primary = srcs["frequentist"] if "frequentist" in srcs else srcs[a["sources"][0]]
    c = primary["conclusion"]
    if c == "pending":
        return "pending"
    if a["tier"] == "confirmatory":
        if a["id"].startswith("H1") and c == "supported" and primary["direction"] == "negative":
            return "not supported (wrong direction)"  # prereg: H1 is directional
        return c
    return f"{a['tier']}: {c}"


def _convergence(srcs: dict, pending: list) -> str:
    if pending:
        return "incomplete"
    if len(srcs) == 1:
        return "single source"
    return "converge" if len({r["direction"] for r in srcs.values()}) == 1 else "diverge"


def missing_prereg_ids(prereg_text: str, rows: list[dict]) -> list[str]:
    """Hypothesis/outcome IDs (H1-H3, P1-P2, S1-S5) used in the prereg that no results row covers."""
    used = set(re.findall(r"\b(H[1-3]|P[1-2]|S[1-5])\b", prereg_text))
    covered = set()
    for r in rows:
        covered |= set(re.findall(r"H[1-3]|P[1-2]|S[1-5]", r["id"]))
    return sorted(used - covered)


# ------------------------------------------------------------------------------------------------ rendering
def _cell(r: dict) -> str:
    if r["conclusion"] == "pending":
        return "pending"
    bits = [r["conclusion"]]
    if r["estimate"] is not None:
        bits.append(f"est {r['estimate']:g}")
    if r["interval"] is not None:
        bits.append(f"[{r['interval'][0]:g}, {r['interval'][1]:g}]")
    return " ".join(bits)


def render_markdown(rows: list[dict], title: bool = True, level: int = 2) -> str:
    """Markdown tables, one per hypothesis group. `title=False` omits the document title and intro (for embedding);
    `level` is the heading level of each group."""
    out = ["# Results synthesis", "",
           "One row per preregistered analysis. Confirmatory decisions use the frequentist result only; Bayesian, DDM, reliability and "
           "secondary results are exploratory or descriptive. Pending means not yet run.", ""] if title else []
    for group, group_title in GROUP_TITLES.items():
        sub = [r for r in rows if r["group"] == group]
        if not sub:
            continue
        out += [f"{'#' * level} {group_title}", "", "| ID | Analysis | Tier | Frequentist | Bayesian | DDM | Reliability | Decision | Status | Sources agree |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for r in sub:
            cells = [_cell(r["sources"][s]) if s in r["sources"] else "n/a" for s in SOURCES]
            out.append("| " + " | ".join([r["id"], r["label"], r["tier"], *cells, r["decision"], r["status"], r["convergence"]]) + " |")
        out.append("")
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------ deviations
AFTER_COLUMNS = ("Date", "Preregistered item", "Change", "Reason", "Effect on analysis", "Decided by")


def _cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def parse_deviations(text: str) -> dict:
    """Parse deviations.md: part A (before registration) and part B (after). Part B rows must be complete."""
    parts = {"before": [], "after": []}
    section = header = None
    for line in text.splitlines():
        if line.startswith("## A"):
            section, header = "before", None
        elif line.startswith("## B"):
            section, header = "after", None
        elif section and line.lstrip().startswith("|"):
            cells = _cells(line)
            if header is None:
                header = cells
            elif all(set(c) <= set("-: ") for c in cells):
                continue
            else:
                if len(cells) != len(header):
                    raise ValueError(f"row has {len(cells)} cells, expected {len(header)}: {line[:60]}")
                if not any(cells):
                    continue
                row = dict(zip(header, cells))
                if section == "after":
                    for col in AFTER_COLUMNS:
                        if not row.get(col):
                            raise ValueError(f"deviation row is missing '{col}': {line[:60]}")
                parts[section].append(row)
    return parts


def render_deviations_section(d: dict) -> str:
    out = ["## Deviations from preregistration", ""]
    if d["after"]:
        for r in d["after"]:
            out.append(f"- **{r['Date']}, {r['Preregistered item']}:** {r['Change']}. Reason: {r['Reason']}. "
                       f"Effect on the analysis: {r['Effect on analysis']}. Decided by {r['Decided by']}.")
    else:
        out.append("There were no deviations from the preregistration.")
    out += ["", "Changes to the original build plan made before registration (not deviations from the registration, but they shape the study):", ""]
    for r in d["before"]:
        out.append(f"- **{r['#']}:** {r['Original spec']} -> {r['What was done instead']} ({r['Date']}).")
    return "\n".join(out)
