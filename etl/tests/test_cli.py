import json
import sqlite3

from mindbench_etl.cli import main

from conftest import EXPECTED_ROWS, FIXTURES


def raw_dir(tmp_path, with_bad=False):
    d = tmp_path / "raw"
    d.mkdir()
    for name in ("K7M2QX9P_session3.json", "K7M2QX9P_session11.json"):
        (d / name).write_bytes((FIXTURES / name).read_bytes())
    if with_bad:
        (d / "M3N4P5Q6_session1.json").write_text(json.dumps([{"participantCode": "M3N4P5Q6"}]))
    return d


def test_init_db_creates_the_database(tmp_path, capsys):
    db = tmp_path / "x.sqlite"
    assert main(["init-db", "--db", str(db)]) == 0
    assert db.exists()


def test_load_reports_and_returns_zero_when_everything_loads(tmp_path, capsys):
    db = tmp_path / "x.sqlite"
    assert main(["load", "--raw", str(raw_dir(tmp_path)), "--db", str(db)]) == 0
    out = capsys.readouterr().out
    assert "K7M2QX9P_session3.json" in out
    conn = sqlite3.connect(db)
    assert conn.execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 2 * EXPECTED_ROWS


def test_load_is_idempotent_from_the_command_line(tmp_path):
    db = tmp_path / "x.sqlite"
    d = raw_dir(tmp_path)
    main(["load", "--raw", str(d), "--db", str(db)])
    main(["load", "--raw", str(d), "--db", str(db)])
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM trials").fetchone()[0] == 2 * EXPECTED_ROWS


def test_load_returns_1_when_a_file_fails_but_still_loads_the_rest(tmp_path, capsys):
    db = tmp_path / "x.sqlite"
    assert main(["load", "--raw", str(raw_dir(tmp_path, with_bad=True)), "--db", str(db)]) == 1
    out = capsys.readouterr().out
    assert "FAILED" in out and "M3N4P5Q6_session1.json" in out
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 2


def test_download_without_credentials_exits_2_and_names_the_variables(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("MINDBENCH_DRIVE_FOLDER_ID", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    assert main(["download", "--dest", str(tmp_path / "raw")]) == 2
    err = capsys.readouterr().err
    assert "MINDBENCH_DRIVE_FOLDER_ID" in err and "GOOGLE_APPLICATION_CREDENTIALS" in err


def test_default_command_line_load_does_not_flag_real_sessions_as_pilot(tmp_path):
    """The fixtures are sessions 3 and 11: with the default cutoff of 2 neither is a smoke-test session."""
    db = tmp_path / "x.sqlite"
    main(["load", "--raw", str(raw_dir(tmp_path)), "--db", str(db)])
    assert sqlite3.connect(db).execute("SELECT COUNT(*) FROM sessions WHERE is_pilot = 1").fetchone()[0] == 0
