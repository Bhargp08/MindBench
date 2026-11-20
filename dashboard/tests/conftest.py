import copy
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "etl" / "tests" / "fixtures"
CODE = "K7M2QX9P"

# Scored trials per task in the synthetic fixtures (the design counts are the defaults in the app).
FIXTURE_EXPECTED = {"posner": 3, "stroop": 3, "nback": 6, "yesno": 4, "recall_lists": 2}


def load_fixture(name="K7M2QX9P_session3.json"):
    return json.loads((FIXTURES / name).read_text())


def with_session(rows, session=None):
    out = copy.deepcopy(rows)
    for r in out:
        if session is not None:
            r["sessionNumber"] = session
    return out


def set_timestamp(rows, iso):
    for r in rows:
        r["sessionMetadata"]["timestamp"] = iso
    return rows


def drop_timing(rows):
    return [r for r in rows if r.get("task") != "timing"]


def build_db(path, specs):
    """specs: [(session_number, mutate_fn_or_None)] -> SQLite database built with the real ETL loader."""
    from mindbench_etl.db import connect, init_db
    from mindbench_etl.load import load_session

    conn = connect(path)
    init_db(conn)
    for number, mutate in specs:
        rows = with_session(load_fixture(), session=number)
        if mutate:
            rows = mutate(rows) or rows
        load_session(conn, rows)
    return conn


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "t.sqlite"


@pytest.fixture
def raw_dir(tmp_path):
    d = tmp_path / "raw"
    d.mkdir()
    return d
