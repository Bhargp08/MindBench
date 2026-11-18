import sqlite3

import pytest

from mindbench_etl.db import connect, init_db

TABLES = {"participants", "sessions", "questionnaire", "trials"}


def columns(conn, table):
    return {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}


def test_init_db_creates_the_four_tables(db):
    names = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert TABLES <= names


def test_sessions_have_pilot_and_exclusion_columns(db):
    cols = columns(db, "sessions")
    assert {"is_pilot", "excluded_reason", "participant_code", "session_number"} <= cols


def test_trials_have_the_common_columns(db):
    assert {"participant_code", "session_number", "trial_index", "task", "practice", "rt", "response", "correct", "data_json"} <= columns(db, "trials")


def test_init_db_is_idempotent(tmp_path):
    conn = connect(tmp_path / "x.sqlite")
    init_db(conn)
    init_db(conn)
    conn.close()


def test_connect_enables_foreign_keys(db):
    assert db.execute("PRAGMA foreign_keys").fetchone()[0] == 1


def test_foreign_keys_are_enforced(db):
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO sessions (participant_code, session_number, is_pilot) VALUES ('NOBODY00', 1, 0)")
    db.execute("INSERT INTO participants (participant_code) VALUES ('K7M2QX9P')")
    db.execute("INSERT INTO sessions (participant_code, session_number, is_pilot) VALUES ('K7M2QX9P', 1, 1)")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO trials (participant_code, session_number, trial_index, data_json) VALUES ('K7M2QX9P', 2, 0, '{}')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO questionnaire (participant_code, session_number, hours_slept) VALUES ('K7M2QX9P', 9, 7)")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("DELETE FROM participants WHERE participant_code = 'K7M2QX9P'")  # a session still refers to it


def test_is_pilot_must_be_0_or_1(db):
    db.execute("INSERT INTO participants (participant_code) VALUES ('K7M2QX9P')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO sessions (participant_code, session_number, is_pilot) VALUES ('K7M2QX9P', 1, 2)")


def test_trial_key_is_unique_per_session(db):
    db.execute("INSERT INTO participants (participant_code) VALUES ('K7M2QX9P')")
    db.execute("INSERT INTO sessions (participant_code, session_number, is_pilot) VALUES ('K7M2QX9P', 1, 1)")
    db.execute("INSERT INTO trials (participant_code, session_number, trial_index, data_json) VALUES ('K7M2QX9P', 1, 0, '{}')")
    with pytest.raises(sqlite3.IntegrityError):
        db.execute("INSERT INTO trials (participant_code, session_number, trial_index, data_json) VALUES ('K7M2QX9P', 1, 0, '{}')")
