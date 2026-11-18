"""MB-02: schema test for docs/design/literature.csv (slimmed scope: canonical task parameters)."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "docs" / "design" / "literature.csv"
COLUMNS = ["task", "parameter", "value", "source", "locator", "verified"]
TASKS = {"staircase", "posner", "stroop", "nback", "recall"}
REQUIRED_PARAMS = {
    "staircase": {"staircase_rule"},
    "posner": {"cue_validity"},
    "nback": {"target_rate"},
    "recall": {"list_length", "presentation_rate"},
}


def rows():
    with CSV.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == COLUMNS
        return list(reader)


def test_csv_exists_with_columns():
    assert CSV.is_file(), "missing docs/design/literature.csv"
    rows()


def test_every_row_complete_and_flagged():
    for r in rows():
        for c in COLUMNS:
            assert r[c].strip(), f"empty {c} in row {r}"
        assert r["verified"] in {"true", "false"}, f"verified must be true/false: {r}"
        assert r["task"] in TASKS, f"unknown task {r['task']}"


def test_all_five_tasks_covered():
    assert {r["task"] for r in rows()} == TASKS


def test_required_parameters_present():
    have = {(r["task"], r["parameter"]) for r in rows()}
    for task, params in REQUIRED_PARAMS.items():
        for p in params:
            assert (task, p) in have, f"missing {task}/{p}"


def test_unverified_rows_marked_in_value():
    for r in rows():
        if r["verified"] == "false":
            assert "[UNVERIFIED]" in r["value"], f"unverified row must say [UNVERIFIED]: {r}"
