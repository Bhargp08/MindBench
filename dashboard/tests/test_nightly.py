import json
import sqlite3

from mindbench_dashboard.nightly import main, run_nightly

from conftest import CODE, FIXTURES, FIXTURE_EXPECTED


def populate(raw_dir, bad=False):
    for name in ("K7M2QX9P_session3.json", "K7M2QX9P_session11.json"):
        (raw_dir / name).write_bytes((FIXTURES / name).read_bytes())
    (raw_dir / f"{CODE}_session5.partial.json").write_text("[]")
    if bad:
        (raw_dir / "M3N4P5Q6_session1.json").write_text("{broken")


def counts(db):
    conn = sqlite3.connect(db)
    return [conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in ("sessions", "trials")]


def test_loads_applies_exclusions_and_writes_a_report(db_path, raw_dir, tmp_path):
    populate(raw_dir, bad=True)
    report = run_nightly(db_path, raw_dir, tmp_path / "report.json", download_fn=None, expected=FIXTURE_EXPECTED)
    assert sorted(report["loaded"]) == ["K7M2QX9P_session11.json", "K7M2QX9P_session3.json"]
    assert [f["file"] for f in report["failed"]] == ["M3N4P5Q6_session1.json"]
    assert "JSON" in report["failed"][0]["message"]
    assert report["skipped_partial"] == [f"{CODE}_session5.partial.json"]
    assert report["exclusions"]["kept"] == 2
    assert json.loads((tmp_path / "report.json").read_text())["loaded"] == report["loaded"]


def test_running_twice_changes_nothing(db_path, raw_dir, tmp_path):
    populate(raw_dir)
    run_nightly(db_path, raw_dir, tmp_path / "r.json", download_fn=None, expected=FIXTURE_EXPECTED)
    first = counts(db_path)
    run_nightly(db_path, raw_dir, tmp_path / "r.json", download_fn=None, expected=FIXTURE_EXPECTED)
    assert counts(db_path) == first


def test_download_not_configured_is_reported_and_does_not_stop_the_load(db_path, raw_dir, tmp_path):
    from mindbench_etl.download import ConfigError

    def not_configured(dest):
        raise ConfigError("Set the environment variable(s): MINDBENCH_DRIVE_FOLDER_ID, GOOGLE_APPLICATION_CREDENTIALS")

    populate(raw_dir)
    report = run_nightly(db_path, raw_dir, tmp_path / "r.json", download_fn=not_configured, expected=FIXTURE_EXPECTED)
    assert report["download"]["status"] == "skipped"
    assert "MINDBENCH_DRIVE_FOLDER_ID" in report["download"]["message"]
    assert len(report["loaded"]) == 2


def test_a_download_error_is_reported_and_the_load_still_runs(db_path, raw_dir, tmp_path):
    def boom(dest):
        raise OSError("network down")

    populate(raw_dir)
    report = run_nightly(db_path, raw_dir, tmp_path / "r.json", download_fn=boom, expected=FIXTURE_EXPECTED)
    assert report["download"]["status"] == "error" and "network down" in report["download"]["message"]
    assert len(report["loaded"]) == 2


def test_a_successful_download_is_recorded(db_path, raw_dir, tmp_path):
    populate(raw_dir)
    report = run_nightly(db_path, raw_dir, tmp_path / "r.json", download_fn=lambda dest: {"downloaded": ["K7M2QX9P_session3.json"]}, expected=FIXTURE_EXPECTED)
    assert report["download"] == {"status": "ok", "downloaded": ["K7M2QX9P_session3.json"]}


def test_command_line_exit_codes(db_path, raw_dir, tmp_path, capsys):
    populate(raw_dir)
    args = ["--db", str(db_path), "--raw", str(raw_dir), "--report", str(tmp_path / "r.json"), "--no-download"]
    assert main(args) == 0
    (raw_dir / "M3N4P5Q6_session1.json").write_text("{broken")
    assert main(args) == 1
    assert "FAILED" in capsys.readouterr().out
