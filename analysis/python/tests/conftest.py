import json
import sqlite3
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
SCHEMA = REPO / "etl" / "mindbench_etl" / "schema.sql"
FIXTURES = REPO / "etl" / "tests" / "fixtures"

# Scored trials per task in the synthetic fixtures (the real design counts are the defaults in mindbench.exclusions).
FIXTURE_EXPECTED = {"posner": 3, "stroop": 3, "nback": 6, "yesno": 4, "recall_lists": 2}


def trial(task, i, practice=0, rt=None, correct=None, response=None, **data):
    return {"trial_index": i, "task": task, "practice": practice, "rt": rt, "response": response, "correct": correct, "data": data}


def make_session(
    posner=3, stroop=3, nback=6, yesno=4, lists=2, staircase=3, threshold=True, summary=True, timing=True, unfinished=(),
    is_pilot=0, questionnaire=True, hours=7.5, practice_noise=True,
):
    """A synthetic session with exactly the given numbers of scored trials (defaults = FIXTURE_EXPECTED)."""
    t, i = [], 0

    def add(*a, **k):
        nonlocal i
        t.append(trial(*a, i, **k))
        i += 1

    if practice_noise:  # practice rows must never count
        for _ in range(4):
            add("stroop", practice=1, rt=500, correct=0, condition="congruent", ink="red", word="red")
            add("posner", practice=1, rt=500, correct=0, valid=True)
    for _ in range(staircase):
        add("staircase", practice=0, rt=600, correct=1, level=-10)
    if threshold:
        add("threshold", practice=None, thresholdLevel=-11.5, thresholdContrast=0.266, usedFallback=False, nReversals=10)
    for k in range(yesno):
        add("yesno", practice=0, rt=600, correct=1, isSignal=bool(k % 2), respondedYes=bool(k % 2))
    for k in range(posner):
        add("posner", practice=0, rt=400, correct=1, valid=k != 1)
    for k in range(stroop):
        add("stroop", practice=0, rt=600, correct=1, condition="congruent" if k % 2 == 0 else "incongruent")
    for k in range(nback):
        position = k + 1
        typ = "start" if position <= 2 else ("target" if position % 3 == 0 else "nontarget")
        responded = typ == "target"
        add("nback", practice=0, rt=700 if responded else None, position=position, type=typ, isTarget=typ == "target", responded=responded)
    for k in range(lists):
        add("recall", practice=0, listWords=["a", "b", "c", "d"], recalled=[True, True, False, False], nCorrect=2, list=k + 1)
    if summary:
        add("recall_summary", practice=0, recallProportion=0.5, nCorrect=2 * lists, nWords=4 * lists)
    if timing:
        add("timing", practice=None, timing={"tasks": {}, "totalTaskMs": 1, "unfinished": list(unfinished)})
    return {
        "participant_code": "K7M2QX9P",
        "session_number": 3,
        "is_pilot": is_pilot,
        "excluded_reason": None,
        "questionnaire": {"hours_slept": hours, "bed_time": "23:30", "wake_time": "07:00", "kss": 4, "caffeine": 0, "device": "laptop"} if questionnaire else None,
        "trials": t,
    }


@pytest.fixture
def db(tmp_path):
    conn = sqlite3.connect(tmp_path / "t.sqlite")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA.read_text())
    yield conn
    conn.close()


def insert_fixture(conn, filename, session_number=None, is_pilot=0):
    """Insert a synthetic session file the way the ETL does (same columns), without importing the ETL package."""
    rows = json.loads((FIXTURES / filename).read_text())
    first = rows[0]
    code = first["participantCode"]
    n = session_number or first["sessionNumber"]
    m, q = first["sessionMetadata"], first["questionnaire"]
    conn.execute("INSERT OR IGNORE INTO participants (participant_code) VALUES (?)", (code,))
    conn.execute(
        "INSERT INTO sessions (participant_code, session_number, is_pilot, timestamp, timezone, jspsych_version) VALUES (?, ?, ?, ?, ?, ?)",
        (code, n, is_pilot, m["timestamp"], m["timezone"], m["jsPsychVersion"]),
    )
    conn.execute(
        "INSERT INTO questionnaire (participant_code, session_number, hours_slept, bed_time, wake_time, kss, caffeine, device) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (code, n, q["hoursSlept"], q["bedTime"], q["wakeTime"], q["kss"], int(q["caffeine"]), q["device"]),
    )
    keys = ("participantCode", "sessionNumber", "questionnaire", "sessionMetadata", "taskOrder")
    for r in rows:
        correct = r.get("correct")
        conn.execute(
            "INSERT INTO trials (participant_code, session_number, trial_index, task, practice, rt, response, correct, data_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, n, r["trial_index"], r.get("task"), None if r.get("practice") is None else int(r["practice"]), r.get("rt"),
             r.get("response") if isinstance(r.get("response"), (str, type(None))) else json.dumps(r["response"]),
             None if correct is None else int(correct), json.dumps({k: v for k, v in r.items() if k not in keys}, sort_keys=True)),
        )
    conn.commit()
