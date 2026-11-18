import datetime as dt

from mindbench_dashboard.metrics import completion_summary, schedule_status, session_overview, stopping_status

from conftest import FIXTURE_EXPECTED, build_db, drop_timing, set_timestamp


def make(db_path):
    return build_db(db_path, [(1, None), (3, None), (4, drop_timing), (6, None)])


class TestOverview:
    def test_one_row_per_session_with_finish_and_exclusion_status(self, db_path):
        rows = session_overview(make(db_path), expected=FIXTURE_EXPECTED)
        by = {r["session_number"]: r for r in rows}
        assert sorted(by) == [1, 3, 4, 6]
        assert by[3]["battery_finished"] is True and by[3]["excluded"] is False
        assert by[4]["battery_finished"] is False and by[4]["excluded"] is True
        assert by[1]["is_pilot"] == 1 and by[1]["excluded"] is True
        assert "smoke_test" in by[1]["excluded_codes"][0]
        assert any("incomplete" in c for c in by[4]["excluded_codes"])

    def test_tasks_complete_flags_use_counts_not_values(self, db_path):
        (row,) = [r for r in session_overview(make(db_path), expected=FIXTURE_EXPECTED) if r["session_number"] == 3]
        assert row["tasks_complete"] == {"contrast": True, "posner": True, "stroop": True, "nback": True, "recall": True, "questionnaire": True}
        assert row["n_tasks_complete"] == 6
        assert row["sleep_logged"] is True

    def test_default_design_counts_mark_the_tiny_fixture_sessions_incomplete(self, db_path):
        (row,) = [r for r in session_overview(make(db_path)) if r["session_number"] == 3]
        assert row["tasks_complete"]["posner"] is False

    def test_duration_and_refresh_rate_come_from_the_logged_timing(self, db_path):
        (row,) = [r for r in session_overview(make(db_path), expected=FIXTURE_EXPECTED) if r["session_number"] == 3]
        assert row["total_task_minutes"] == 5.0
        assert abs(row["refresh_hz"] - 59.94) < 1e-9 and row["refresh_plausible"] is True


class TestCompletionSummary:
    def test_counts_completed_confirmatory_excluded_and_remaining(self, db_path):
        overview = session_overview(make(db_path), expected=FIXTURE_EXPECTED)
        s = completion_summary(overview)
        assert s["sessions_loaded"] == 4
        assert s["completed"] == 3  # sessions 1, 3, 6 finished the battery
        assert s["confirmatory_completed"] == 2  # 3 and 6
        assert s["remaining_to_target"] == 40
        assert s["smoke_tests_run"] == 1
        assert s["excluded"] == 2
        assert s["excluded_by_reason"] == {"smoke_test": 1, "incomplete: the battery did not finish (no timing record)": 1}

    def test_a_completed_session_that_is_later_excluded_still_counts_as_completed(self, db_path):
        # the preregistration counts completed sessions: battery finished, even if a rule excludes the session later
        def congruent_all_wrong(rows):
            for r in rows:
                if r.get("task") == "stroop" and r.get("practice") is False and r.get("condition") == "congruent":
                    r["correct"] = False
            return rows

        conn = build_db(db_path, [(3, congruent_all_wrong)])
        overview = session_overview(conn, expected=FIXTURE_EXPECTED)
        s = completion_summary(overview)
        assert overview[0]["excluded"] is True and overview[0]["battery_finished"] is True
        assert s["confirmatory_completed"] == 1

    def test_empty_database(self, db_path):
        s = completion_summary(session_overview(build_db(db_path, []), expected=FIXTURE_EXPECTED))
        assert s["sessions_loaded"] == 0 and s["confirmatory_completed"] == 0 and s["remaining_to_target"] == 42


class TestStoppingRule:
    def test_continue_during_the_scheduled_21_days(self):
        r = stopping_status(10, 5, 14)
        assert r["stop"] is False and r["phase"] == "scheduled"

    def test_stop_at_42_completed_sessions(self):
        r = stopping_status(42, 15, 48)
        assert r["stop"] is True and "42" in r["reason"]

    def test_days_22_to_28_are_the_extension_window(self):
        assert stopping_status(30, 21, 40)["phase"] == "scheduled"
        r = stopping_status(30, 22, 40)
        assert r["stop"] is False and r["phase"] == "extension"
        assert stopping_status(30, 28, 40)["phase"] == "extension"

    def test_stop_after_the_extension_window(self):
        r = stopping_status(30, 29, 40)
        assert r["stop"] is True and "extension" in r["reason"]

    def test_stop_when_session_slot_52_is_reached(self):
        r = stopping_status(38, 10, 52)
        assert r["stop"] is True and "52" in r["reason"]

    def test_target_reached_takes_precedence(self):
        assert "42" in stopping_status(42, 40, 52)["reason"]


class TestSchedule:
    def test_day_number_counts_from_the_first_confirmatory_session_local_date(self, db_path):
        conn = build_db(db_path, [(1, None), (3, lambda r: set_timestamp(r, "2026-11-18T15:30:00.000Z")),
                                  (5, lambda r: set_timestamp(r, "2026-11-19T15:30:00.000Z"))])
        overview = session_overview(conn, expected=FIXTURE_EXPECTED)
        s = schedule_status(overview, today=dt.date(2026, 11, 20))
        assert s["first_confirmatory_date"] == "2026-11-18"
        assert s["day_number"] == 3
        assert s["scheduled_days_remaining"] == 18

    def test_no_confirmatory_sessions_yet(self, db_path):
        overview = session_overview(build_db(db_path, [(1, None)]), expected=FIXTURE_EXPECTED)
        s = schedule_status(overview, today=dt.date(2026, 11, 20))
        assert s["first_confirmatory_date"] is None and s["day_number"] is None
