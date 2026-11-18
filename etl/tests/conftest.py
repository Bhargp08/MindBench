import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"

# Hand-derived from the fixture design (see fixtures/generate_fixtures.py): rows per task in each fixture file.
EXPECTED_TASK_COUNTS = {
    None: 4, "setup": 1, "threshold": 1, "timing": 1, "feedback": 10, "fixation": 19,
    "staircase": 5, "staircase_interval": 10, "isi": 5, "yesno": 4,
    "posner": 5, "posner_cue": 5, "posner_gap": 5, "stroop": 5, "nback": 10,
    "recall_word": 11, "recall": 3, "recall_summary": 2,
}
EXPECTED_ROWS = 106


def load_fixture(name):
    return json.loads((FIXTURES / name).read_text())


@pytest.fixture
def session3():
    return load_fixture("K7M2QX9P_session3.json")


@pytest.fixture
def session11():
    return load_fixture("K7M2QX9P_session11.json")


@pytest.fixture
def db(tmp_path):
    from mindbench_etl.db import connect, init_db

    conn = connect(tmp_path / "test.sqlite")
    init_db(conn)
    yield conn
    conn.close()


def count(conn, sql, *args):
    return conn.execute(sql, args).fetchone()[0]


def with_session(rows, code=None, session=None):
    """Copy of a session's rows with the participant code / session number changed on every row."""
    out = json.loads(json.dumps(rows))
    for r in out:
        if code is not None:
            r["participantCode"] = code
        if session is not None:
            r["sessionNumber"] = session
    return out
