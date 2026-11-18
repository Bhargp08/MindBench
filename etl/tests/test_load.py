import copy
import json
import sqlite3

import pytest

from mindbench_etl.load import load_directory, load_file, load_session
from mindbench_etl.validate import ValidationError

from conftest import EXPECTED_ROWS, EXPECTED_TASK_COUNTS, FIXTURES, count, with_session


def totals(db):
    return {t: count(db, f"SELECT COUNT(*) FROM {t}") for t in ("participants", "sessions", "questionnaire", "trials")}


def test_first_load_fills_every_table(db, session3):
    summary = load_session(db, session3, filename="K7M2QX9P_session3.json")
    assert totals(db) == {"participants": 1, "sessions": 1, "questionnaire": 1, "trials": EXPECTED_ROWS}
    assert summary["participant_code"] == "K7M2QX9P"
    assert summary["session_number"] == 3
    assert summary["n_rows"] == EXPECTED_ROWS


def test_double_load_leaves_row_counts_unchanged(db, session3):
    load_session(db, session3)
    before = totals(db)
    load_session(db, session3)
    load_session(db, copy.deepcopy(session3))
    assert totals(db) == before


def test_counts_per_task_match_the_fixture_exactly(db, session3):
    load_session(db, session3)
    got = {t: n for t, n in db.execute("SELECT task, COUNT(*) FROM trials GROUP BY task")}
    assert got == EXPECTED_TASK_COUNTS


def test_two_sessions_and_a_second_participant_coexist(db, session3, session11):
    load_session(db, session3)
    load_session(db, session11)
    load_session(db, with_session(session3, code="M3N4P5Q6", session=1))
    assert totals(db) == {"participants": 2, "sessions": 3, "questionnaire": 3, "trials": 3 * EXPECTED_ROWS}


class TestPilotFlag:
    def flag(self, db, n, rows):
        load_session(db, with_session(rows, session=n))
        return db.execute("SELECT is_pilot FROM sessions WHERE session_number = ?", (n,)).fetchone()[0]

    def test_pilot_sessions_get_is_pilot_1(self, db, session3):
        assert self.flag(db, 3, session3) == 1

    def test_confirmatory_sessions_get_is_pilot_0(self, db, session11):
        assert self.flag(db, 11, session11) == 0

    def test_boundary_is_session_10_versus_11(self, db, session3):
        assert self.flag(db, 1, session3) == 1
        assert self.flag(db, 10, session3) == 1
        assert self.flag(db, 11, session3) == 0
        assert self.flag(db, 52, session3) == 0

    def test_number_of_pilot_sessions_is_configurable(self, db, session3):
        load_session(db, with_session(session3, session=5), pilot_sessions=4)
        assert db.execute("SELECT is_pilot FROM sessions").fetchone()[0] == 0


def test_excluded_reason_starts_null_and_survives_a_reload(db, session3):
    load_session(db, session3)
    assert db.execute("SELECT excluded_reason FROM sessions").fetchone()[0] is None
    db.execute("UPDATE sessions SET excluded_reason = 'incomplete: manual note'")
    db.commit()
    load_session(db, session3)
    assert db.execute("SELECT excluded_reason FROM sessions").fetchone()[0] == "incomplete: manual note"


def test_session_and_questionnaire_values_are_stored(db, session3):
    load_session(db, session3, filename="K7M2QX9P_session3.json")
    s = db.execute("SELECT timestamp, timezone, jspsych_version, screen_width, screen_height, task_order, viewing_distance_cm, refresh_hz, refresh_plausible, source_filename FROM sessions").fetchone()
    assert s[0] == "2026-11-18T15:30:00.000Z"
    assert s[1] == "America/Los_Angeles"
    assert s[2] == "8.4.0"
    assert (s[3], s[4]) == (1440, 900)
    assert json.loads(s[5]) == ["stroop", "nback", "posner", "recall", "contrast"]
    assert s[6] == 57
    assert s[7] == pytest.approx(59.94)
    assert s[8] == 1
    assert s[9] == "K7M2QX9P_session3.json"
    q = db.execute("SELECT hours_slept, bed_time, wake_time, kss, caffeine, device FROM questionnaire").fetchone()
    assert q == (7.5, "23:30", "07:00", 4, 0, "laptop")


def test_trial_columns_are_filled_from_the_rows(db, session3):
    load_session(db, session3)
    r = db.execute("SELECT task, practice, rt, response, correct, data_json FROM trials WHERE task = 'posner' ORDER BY trial_index LIMIT 1").fetchone()
    assert r[0] == "posner"
    assert r[1] == 1  # the first posner row is a practice trial
    assert r[2] == pytest.approx(365)
    assert r[3] in ("f", "j")
    assert r[4] == 1
    assert json.loads(r[5])["targetSide"] in ("left", "right")
    assert db.execute("SELECT COUNT(*) FROM trials WHERE task = 'posner' AND practice = 0").fetchone()[0] == 3
    assert db.execute("SELECT COUNT(*) FROM trials WHERE task = 'fixation' AND practice IS NULL").fetchone()[0] == 19


def test_reloading_changed_data_updates_rows_and_removes_stale_ones(db, session3):
    load_session(db, session3)
    changed = copy.deepcopy(session3)
    changed = [r for r in changed if r["trial_index"] < 100]  # a shorter upload for the same session
    for r in changed:
        if r.get("task") == "setup":
            r["viewingDistanceInstructedCm"] = 60
    load_session(db, changed)
    assert count(db, "SELECT COUNT(*) FROM trials") == 100
    assert count(db, "SELECT viewing_distance_cm FROM sessions") == 60


class TestAtomicity:
    def test_malformed_file_is_rejected_and_nothing_is_inserted(self, db, session3):
        bad = copy.deepcopy(session3)
        next(r for r in bad if r.get("task") == "posner")["targetSide"] = "up"
        with pytest.raises(ValidationError) as e:
            load_session(db, bad)
        assert "targetSide" in str(e.value)
        assert totals(db) == {"participants": 0, "sessions": 0, "questionnaire": 0, "trials": 0}

    def test_failure_mid_load_leaves_earlier_data_untouched(self, db, session3, session11):
        load_session(db, session3)
        before = totals(db)
        # make the database refuse the 3rd-to-last kind of row, after participants/sessions/questionnaire were written
        db.execute("CREATE TRIGGER boom BEFORE INSERT ON trials WHEN NEW.task = 'nback' BEGIN SELECT RAISE(ABORT, 'simulated disk error'); END")
        with pytest.raises(sqlite3.DatabaseError):
            load_session(db, session11)
        assert totals(db) == before
        assert count(db, "SELECT COUNT(*) FROM sessions WHERE session_number = 11") == 0


def test_load_file_reads_json_and_checks_the_filename(db):
    summary = load_file(db, FIXTURES / "K7M2QX9P_session3.json")
    assert summary["session_number"] == 3


def test_load_file_rejects_a_misnamed_file(db, tmp_path, session3):
    p = tmp_path / "ZZZZZZZZ_session9.json"
    p.write_text(json.dumps(session3))
    with pytest.raises(ValidationError) as e:
        load_file(db, p)
    assert "filename" in str(e.value)
    assert totals(db)["trials"] == 0


class TestLoadDirectory:
    def make_dir(self, tmp_path, session3, session11):
        d = tmp_path / "raw"
        d.mkdir()
        (d / "K7M2QX9P_session3.json").write_text(json.dumps(session3))
        (d / "K7M2QX9P_session11.json").write_text(json.dumps(session11))
        bad = copy.deepcopy(session3)
        bad = with_session(bad, code="M3N4P5Q6", session=2)
        next(r for r in bad if r.get("task") == "stroop")["condition"] = "weird"
        (d / "M3N4P5Q6_session2.json").write_text(json.dumps(bad))
        (d / "K7M2QX9P_session5.partial.json").write_text("[]")
        (d / "notes.txt").write_text("ignore me")
        return d

    def test_good_files_load_bad_ones_are_reported_partials_are_skipped(self, db, tmp_path, session3, session11):
        report = load_directory(db, self.make_dir(tmp_path, session3, session11))
        assert sorted(report["loaded"]) == ["K7M2QX9P_session11.json", "K7M2QX9P_session3.json"]
        assert [f for f, _ in report["failed"]] == ["M3N4P5Q6_session2.json"]
        assert "condition" in report["failed"][0][1]
        assert report["skipped_partial"] == ["K7M2QX9P_session5.partial.json"]
        assert totals(db)["sessions"] == 2
        assert count(db, "SELECT COUNT(*) FROM participants WHERE participant_code = 'M3N4P5Q6'") == 0

    def test_loading_the_directory_twice_changes_nothing(self, db, tmp_path, session3, session11):
        d = self.make_dir(tmp_path, session3, session11)
        load_directory(db, d)
        before = totals(db)
        load_directory(db, d)
        assert totals(db) == before
