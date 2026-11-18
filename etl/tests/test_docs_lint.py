"""MB-01 doc lint: required ethics sections exist; no claims of institutional approval."""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ETHICS = ROOT / "docs" / "ethics"

REQUIRED = {
    "consent_form.md": [
        "Purpose",
        "What you will do",
        "Voluntary participation",
        "Withdrawal and deletion",
        "What is stored",
        "Who sees your data",
        "Open data option",
        "Age confirmation",
        "Signature and date",
    ],
    "data_management.md": [
        "ID scheme",
        "Storage",
        "Retention",
        "De-identification",
        "Release rule",
    ],
    "self_pilot_policy.md": [
        "No induced sleep loss",
        "Stop rules",
    ],
}

FORBIDDEN = re.compile(r"IRB[\s-]+approved|ethics\s+approval", re.IGNORECASE)


def headings(path: Path) -> list[str]:
    return [
        re.sub(r"^#+\s*", "", line).strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith("#")
    ]


def test_required_documents_exist():
    for name in REQUIRED:
        assert (ETHICS / name).is_file(), f"missing docs/ethics/{name}"


def test_required_headings_present():
    for name, wanted in REQUIRED.items():
        path = ETHICS / name
        assert path.is_file(), f"missing docs/ethics/{name}"
        have = headings(path)
        for h in wanted:
            assert any(h.lower() in x for x in have), f"{name}: missing heading '{h}'"


def test_open_data_is_separate_checkbox():
    text = (ETHICS / "consent_form.md").read_text(encoding="utf-8")
    assert "- [ ]" in text, "consent form needs checkbox(es)"
    assert re.search(r"- \[ \].*open", text, re.IGNORECASE), "open-data option must be its own checkbox"


def test_no_institutional_approval_claims():
    files = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.splitlines()
    this_file = Path(__file__).resolve()
    offenders = []
    for rel in files:
        p = ROOT / rel
        if not p.is_file() or p.resolve() == this_file or p.is_relative_to(ETHICS):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if FORBIDDEN.search(text):
            offenders.append(rel)
    assert not offenders, f"forbidden approval wording in: {offenders}"
