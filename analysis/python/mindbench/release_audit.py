"""MB-25: the automated parts of the whole-repo audit. Read-only: it reports problems and never edits, tags or publishes.

This is Claude's own pre-review check (docs/status/SELF_AUDIT.md). It is not the independent review: that is Cursor's
(docs/status/FINAL_REVIEW.md). Findings never repeat a secret's value.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

from . import public_data, synthesis, writeup

SECRET_PATTERNS = [
    ("private key block", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("AWS access key id", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[0-9A-Za-z]{36,}\b")),
    ("secret-key style token", re.compile(r"\bsk-[A-Za-z0-9]{20,}\b")),
    ("Slack token", re.compile(r"\bxox[baprs]-[0-9A-Za-z\-]{10,}")),
    ("quoted credential literal", re.compile(r"""(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*["'][A-Za-z0-9/+_\-]{20,}["']""")),
]
PRIVATE_NAME_RE = re.compile(r"(\.sqlite3?$|\.db$|(^|/)\.env($|\.(?!example))|\.partial\.json$|(^|/)pid_map[^/]*\.json$|(^|/)consent[^/]*\.json$|^data/)")
ATTRIBUTION_RE = re.compile(r"(?im)^co-authored-by:|generated with|🤖")
MARKERS = {"PENDING": re.compile(r"\[PENDING"), "BHARG": re.compile(r"\[BHARG"),
           "UNVERIFIED": re.compile(r"UNVERIFIED|not verified", re.IGNORECASE), "FREEZE": re.compile(r"FREEZE COMMIT")}
EXACT_NPM = re.compile(r"^\d+\.\d+\.\d+([-+][\w.\-+]+)?$")


def _git(root, *args) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True, text=True, errors="replace").stdout


def tracked(root) -> list[str]:
    return [p for p in _git(root, "ls-files", "-z").split("\0") if p]


def scan_secrets_text(text: str) -> list[str]:
    return [label for label, rx in SECRET_PATTERNS if rx.search(text)]


def scan_history(root) -> list[str]:
    """Secret-like additions in any commit on any branch, including ones deleted later. Names the file, kind and commit only."""
    proc = subprocess.Popen(["git", "-C", str(root), "log", "--all", "-p", "--no-color", "--format=commit %H"],
                            stdout=subprocess.PIPE, text=True, errors="replace")
    found, seen, sha, path = [], set(), "", ""
    for line in proc.stdout:
        if line.startswith("commit "):
            sha = line[7:15]
        elif line.startswith("+++ "):
            path = line[6:].strip() if line.startswith("+++ b/") else path
        elif line.startswith("+"):
            for label in scan_secrets_text(line[1:]):
                key = (path, label, sha)
                if key not in seen:
                    seen.add(key)
                    found.append(f"{path}: {label} (commit {sha})")
    proc.wait()
    return found


def forbidden_tracked(root) -> list[str]:
    root = Path(root)
    files = tracked(root)
    problems = [f"tracked private-data file: {f}" for f in files if PRIVATE_NAME_RE.search(f)]
    if any(f.startswith("data_public/") and not f.endswith(".gitkeep") for f in files):
        problems += [f"data_public: {p}" for p in public_data.check_public_dir(root / "data_public")]
    return problems


def commit_message_problems(root) -> list[str]:
    out = _git(root, "log", "--all", "--format=%H%x00%B%x01")
    problems = []
    for rec in out.split("\x01"):
        if "\x00" not in rec:
            continue
        sha, body = rec.strip().split("\x00", 1)
        m = ATTRIBUTION_RE.search(body)
        if m:
            problems.append(f"{sha[:8]}: attribution line ({m.group(0).strip()[:30]})")
    return problems


def _python_req_ok(req: str) -> bool:
    name = re.split(r"[<>=!~\[ ;]", req.strip(), maxsplit=1)[0]
    return name.startswith("mindbench-") or "==" in req or "<" in req or "~=" in req


def pin_problems(root) -> list[str]:
    root = Path(root)
    files = tracked(root)
    problems = []
    for f in files:
        d = str(Path(f).parent)
        prefix = "" if d == "." else d + "/"
        if f.endswith("package.json") and "node_modules" not in f:
            spec = json.loads((root / f).read_text(encoding="utf-8"))
            for sect in ("dependencies", "devDependencies"):
                for name, v in spec.get(sect, {}).items():
                    if not EXACT_NPM.match(v):
                        problems.append(f"{f}: {name} {v} is not an exact version")
            if prefix + "package-lock.json" not in files:
                problems.append(f"{prefix}package-lock.json missing (lock file)")
        if f.endswith("pyproject.toml"):
            data = tomllib.loads((root / f).read_text(encoding="utf-8"))
            reqs = list(data.get("project", {}).get("dependencies", []))
            for group in data.get("dependency-groups", {}).values():
                reqs += [r for r in group if isinstance(r, str)]
            for r in reqs:
                if not _python_req_ok(r):
                    problems.append(f"{f}: {r} has no exact pin or upper bound")
            if prefix + "uv.lock" not in files:
                problems.append(f"{prefix}uv.lock missing (lock file)")
    return problems


def open_markers(root) -> dict[str, list[str]]:
    """Where placeholders for Bharg and unverified items still sit in product files (status docs and tests are skipped)."""
    root = Path(root)
    out = {k: [] for k in MARKERS}
    for f in tracked(root):
        if "/tests/" in f or f.startswith("tests/") or f.endswith("release_audit.py") or f.startswith("docs/status/") or f.endswith((".lock", "package-lock.json")):
            continue
        try:
            text = (root / f).read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for n, line in enumerate(text.splitlines(), start=1):
            for key, rx in MARKERS.items():
                if rx.search(line):
                    out[key].append(f"{f}:{n}: {line.strip()[:80]}")
    return out


def run_all(root) -> list[dict]:
    root = Path(root)

    def entry(check, problems, ok="none found", kind="fail"):
        return {"check": check, "status": "pass" if not problems else kind, "details": problems or [ok]}

    report = [entry("secrets in history", scan_history(root)), entry("private data tracked", forbidden_tracked(root)),
              entry("commit messages", commit_message_problems(root), ok="no attribution lines"), entry("pins", pin_problems(root), ok="all pinned")]
    markers = open_markers(root)
    report.append({"check": "open placeholders", "status": "info", "details": [f"{k}: {len(v)}" for k, v in markers.items()]})
    if root.resolve() == writeup.ROOT.resolve():
        tpl = (root / "docs" / "writeup" / "paper_template.md").read_text(encoding="utf-8")
        values = writeup.collect_values({})
        problems = [f"untraced number: {n}" for n in writeup.untraced_numbers(writeup.build_paper(tpl, values, mark=True))]
        if (root / "docs" / "writeup" / "paper.md").read_text(encoding="utf-8") != writeup.build_paper(tpl, values):
            problems.append("paper.md is not the builder's output")
        report.append(entry("paper traced", problems, ok="every number traced; paper.md matches the builder"))
    else:
        report.append({"check": "paper traced", "status": "info", "details": ["skipped (not this repository)"]})
    prereg = (root / "docs" / "design" / "prereg_draft.md").read_text(encoding="utf-8")
    missing = synthesis.missing_prereg_ids(prereg, synthesis.build_results_table({}))
    report.append(entry("preregistration coverage", [f"not covered: {m}" for m in missing], ok="every H/P/S id has a results row"))
    absent = [f for f in ("README.md", "LICENSE", "CITATION.cff", "docs/status/STATUS.md") if not (root / f).is_file()]
    report.append(entry("release files", [f"missing: {f}" for f in absent], ok="present"))
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mindbench.release_audit")
    p.add_argument("--root", default=str(writeup.ROOT))
    args = p.parse_args(argv)
    report = run_all(args.root)
    for r in report:
        print(f"[{r['status'].upper()}] {r['check']}")
        for d in r["details"]:
            print(f"    {d}")
    return 1 if any(r["status"] == "fail" for r in report) else 0


if __name__ == "__main__":
    sys.exit(main())
