import datetime as dt
import json

from mindbench_dashboard.metrics import build_dashboard_data

from conftest import CODE, FIXTURE_EXPECTED, build_db


def build(db_path, raw_dir, public):
    (raw_dir / f"{CODE}_session5.partial.json").write_text("[]")
    return build_dashboard_data(db_path=db_path, raw_dir=raw_dir, report_path=None, expected=FIXTURE_EXPECTED,
                                today=dt.date(2026, 11, 20), public=public)


def setup(db_path):
    build_db(db_path, [(1, None), (3, None), (4, None), (6, None)]).close()


def test_local_mode_shows_codes_gaps_partial_files_and_the_sleep_log(db_path, raw_dir):
    setup(db_path)
    d = build(db_path, raw_dir, public=False)
    assert d["public"] is False
    assert {r["participant_code"] for r in d["overview"]} == {CODE}
    assert [g["session_number"] for g in d["gaps"]] == [5]
    assert d["partial_files"]["partial"][0]["filename"] == f"{CODE}_session5.partial.json"
    assert [r["hours_slept"] for r in d["sleep_log"]] == [7.5, 7.5, 7.5, 7.5]


def test_public_mode_drops_participant_codes_filenames_free_text_and_the_sleep_log(db_path, raw_dir):
    setup(db_path)
    text = json.dumps(build(db_path, raw_dir, public=True), default=str)
    for secret in (CODE, "session5", ".json", "SyntheticFixture", "window", "pencil", "alpha", "laptop", "America/Los_Angeles", "7.5"):
        assert secret not in text, f"public view leaks {secret!r}"
    d = build(db_path, raw_dir, public=True)
    assert d["public"] is True
    assert "sleep_log" not in d and "overview" not in d


def test_public_mode_keeps_only_aggregates(db_path, raw_dir):
    setup(db_path)
    d = build(db_path, raw_dir, public=True)
    assert d["summary"]["sessions_loaded"] == 4
    assert d["summary"]["confirmatory_completed"] == 3  # sessions 3, 4 and 6 all finished
    assert d["gap_count"] == 1 and d["partial_upload_count"] == 1
    assert d["task_completion"]["posner"] == {"sessions": 4, "complete": 4}


def test_public_mode_has_no_timestamps_finer_than_a_date(db_path, raw_dir):
    setup(db_path)
    text = json.dumps(build(db_path, raw_dir, public=True), default=str)
    assert "T15:30" not in text and "07:30" not in text
