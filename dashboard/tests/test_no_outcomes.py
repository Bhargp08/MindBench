"""Structural guards: the dashboard shows completion and data quality only, never outcome values (P1, P2, S1-S4)."""
import copy
import datetime as dt
import json
import re
from pathlib import Path

from mindbench_dashboard.metrics import build_dashboard_data

from conftest import FIXTURE_EXPECTED, build_db

SRC = Path(__file__).resolve().parents[1]
FORBIDDEN_KEYS = re.compile(
    r"(^|_)(p1|p2|s[1-4])(_|$)|d_?prime|criterion|recall_proportion|proportion|interference|validity|serial|"
    r"hits?$|false_alarm|n_?correct|recalled|intrusion|threshold|accuracy|score", re.IGNORECASE)


def keys(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from keys(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from keys(v)


def data(db_path, raw_dir, **kw):
    return build_dashboard_data(db_path=db_path, raw_dir=raw_dir, report_path=None, expected=FIXTURE_EXPECTED, today=dt.date(2026, 11, 20), **kw)


def test_no_field_name_refers_to_an_outcome_or_a_performance_score(db_path, raw_dir):
    build_db(db_path, [(1, None), (3, None), (4, None)]).close()
    bad = sorted({k for k in keys(data(db_path, raw_dir)) if FORBIDDEN_KEYS.search(k)})
    assert bad == [], f"outcome-like fields in the dashboard data: {bad}"


def test_changing_performance_data_changes_nothing_the_dashboard_shows(db_path, raw_dir, tmp_path):
    """Two databases that differ only in performance on P1/P2/S2/S3/S4 data: the dashboard output must be identical."""
    def scramble(rows):
        for r in rows:
            t = r.get("task")
            if t == "nback":                                           # P1: hits and false alarms
                r["responded"] = not r["responded"]
                r["response"] = " " if r["responded"] else None
            elif t in ("recall",):                                      # P2: recalled words
                r["recalled"] = [not x for x in r["recalled"]]
                r["nCorrect"] = sum(r["recalled"])
                r["proportion"] = r["nCorrect"] / len(r["listWords"])
                r["recallText"] = "zzz yyy"
            elif t == "recall_summary":
                r["nCorrect"], r["recallProportion"] = 8 - r["nCorrect"], 1 - r["recallProportion"]
            elif t == "yesno":                                          # S4: yes/no answers
                r["respondedYes"] = not r["respondedYes"]
                r["response"] = "j" if r["respondedYes"] is False else "f"
                r["correct"] = not r["correct"]
            elif t == "threshold":                                      # S3: threshold
                r["thresholdLevel"], r["thresholdContrast"] = -3.0, 0.7
            elif t == "posner":                                         # S2: correctness and RT (kept above 200 ms)
                r["correct"] = not r["correct"]
                if r["rt"] is not None:
                    r["rt"] = r["rt"] + 50
            elif t == "stroop" and r.get("condition") == "incongruent":  # S1: incongruent answers (the congruent-accuracy flag is data quality)
                r["correct"] = not r["correct"]
                r["rt"] = r["rt"] + 100
        return rows

    build_db(db_path, [(1, None), (3, None), (4, None)]).close()
    other = tmp_path / "other.sqlite"
    build_db(other, [(1, scramble), (3, scramble), (4, scramble)]).close()
    a = json.dumps(data(db_path, raw_dir), sort_keys=True, default=str)
    b = json.dumps(data(other, raw_dir), sort_keys=True, default=str)
    assert a == b


def test_the_dashboard_never_imports_the_scoring_code():
    sources = [*SRC.glob("mindbench_dashboard/*.py"), SRC / "app.py"]
    assert sources
    for p in sources:
        text = p.read_text()
        for pattern in (r"mindbench\.scoring", r"from \.scoring", r"score_session", r"score_database", r"dprime_from", r"serial_position", r"mindbench\.sdt"):
            assert not re.search(pattern, text), f"{p.name} references {pattern}"
