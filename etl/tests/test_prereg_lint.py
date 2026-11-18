"""MB-05: lint for docs/design/prereg_draft.md (completeness, consistency with design.md / power.md, no false claims)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs" / "design"
DRAFT = DESIGN / "prereg_draft.md"

SECTIONS = ["Study Information", "Design Plan", "Sampling Plan", "Variables", "Analysis Plan", "Other"]
EXTRA_SECTIONS = ["Before you submit", "Coverage of the planned analyses"]

# Items Bharg required (Nov 18, 2026) plus the statements in prereg_notes.md.
REQUIRED_PHRASES = [
    "P1", "2-back d'", "P2", "recall proportion", "Holm",
    "2,000 ms", "before RT trimming", "60%",
    "44 planned sessions", "is_pilot", "smoke-test",
    "no formal pilot", "deviation",
    "no institutional review board review has been obtained",
    "MB-18", "MB-19", "MB-20", "MB-21",
    "[FREEZE COMMIT",
]
# Numbers that must match power.md and design.md.
POWER_NUMBERS = ["0.74", "0.46", "0.39"]
DESIGN_NUMBERS = ["42 sessions", "sessions 3-44", "21 calendar days", "120", "60"]


def text():
    assert DRAFT.is_file(), "missing docs/design/prereg_draft.md"
    return DRAFT.read_text(encoding="utf-8")


def headings(t):
    return [re.sub(r"^#+\s*", "", l).strip().lower() for l in t.splitlines() if l.startswith("#")]


def test_draft_exists_and_says_it_is_not_submitted():
    t = text()
    assert "not submitted" in t.lower() or "draft - not submitted" in t.lower()


def test_osf_template_sections_and_extra_sections_are_present():
    h = headings(text())
    for name in SECTIONS + EXTRA_SECTIONS:
        assert any(name.lower() in x for x in h), f"missing section: {name}"


def test_required_items_are_present():
    t = text()
    missing = [p for p in REQUIRED_PHRASES if p.lower() not in t.lower()]
    assert not missing, f"missing: {missing}"


def test_numbers_agree_with_power_and_design_docs():
    t = text()
    power = (DESIGN / "power.md").read_text(encoding="utf-8")
    design = (DESIGN / "design.md").read_text(encoding="utf-8")
    for n in POWER_NUMBERS:
        assert n in power, f"{n} not in power.md (test out of date)"
        assert n in t, f"{n} from power.md not in the draft"
    for n in DESIGN_NUMBERS:
        assert n in t, f"{n} not in the draft"
    for task_count in ("120", "60"):
        assert task_count in design


def test_every_outcome_and_hypothesis_is_named():
    t = text()
    for token in ["H1", "H2", "H3", "S1", "S2", "S3", "S4", "S5"]:
        assert token in t, token


def test_no_false_claims():
    t = text()
    assert not re.search(r"IRB[\s-]+approved|ethics\s+approval", t, re.IGNORECASE)
    assert not re.search(r"(informed by|based on|from) (a |the |our )?pilot", t, re.IGNORECASE), "must not claim pilot-informed design"
    assert not re.search(r"think-aloud (found|showed|results)", t, re.IGNORECASE)


def test_placeholders_for_bharg_are_explicit():
    t = text()
    assert "[FREEZE COMMIT" in t
    assert "[DECISION" in t  # open decisions are marked, not hidden
