import pytest

from mindbench_dashboard.metrics import session_overview, sleep_log, task_quality

from conftest import FIXTURE_EXPECTED, build_db, set_timestamp


def by_task(rows, session=3):
    return {r["task"]: r for r in rows if r["session_number"] == session}


class TestTaskQuality:
    def test_counts_completion_and_durations_for_the_fixture_session(self, db_path):
        q = by_task(task_quality(build_db(db_path, [(3, None)]), expected=FIXTURE_EXPECTED))
        assert set(q) == {"contrast", "posner", "stroop", "nback", "recall"}
        assert (q["contrast"]["scored_trials"], q["contrast"]["expected_trials"], q["contrast"]["complete"]) == (4, 4, True)
        assert q["contrast"]["staircase_trials"] == 3
        assert (q["posner"]["scored_trials"], q["posner"]["complete"]) == (3, True)
        assert (q["stroop"]["scored_trials"], q["stroop"]["complete"]) == (3, True)
        assert (q["nback"]["scored_trials"], q["nback"]["complete"]) == (6, True)
        assert (q["recall"]["scored_trials"], q["recall"]["expected_trials"], q["recall"]["complete"]) == (2, 2, True)
        assert all(r["duration_ms"] == 60000 for r in q.values())

    def test_a_short_task_is_reported_incomplete(self, db_path):
        def short_posner(rows):
            return [r for r in rows if not (r.get("task") == "posner" and r.get("practice") is False and r.get("trial") == 3)]

        q = by_task(task_quality(build_db(db_path, [(3, short_posner)]), expected=FIXTURE_EXPECTED))
        assert (q["posner"]["scored_trials"], q["posner"]["complete"]) == (2, False)

    def test_no_response_rate_and_anticipations_are_data_quality_counts(self, db_path):
        def degrade(rows):
            for r in rows:
                if r.get("task") == "posner" and r.get("practice") is False and r.get("trial") == 1:
                    r["response"], r["rt"], r["correct"] = None, None, False  # a timeout
                if r.get("task") == "stroop" and r.get("practice") is False and r.get("trial") == 2:
                    r["rt"] = 150  # an anticipation (under 200 ms)
            return rows

        q = by_task(task_quality(build_db(db_path, [(3, degrade)]), expected=FIXTURE_EXPECTED))
        assert q["posner"]["no_response_rate"] == pytest.approx(1 / 3)
        assert q["stroop"]["anticipations"] == 1
        assert q["stroop"]["no_response_rate"] == 0

    def test_tasks_where_not_responding_is_a_correct_answer_have_no_response_rate(self, db_path):
        q = by_task(task_quality(build_db(db_path, [(3, None)]), expected=FIXTURE_EXPECTED))
        assert q["nback"]["no_response_rate"] is None and q["recall"]["no_response_rate"] is None


class TestOverviewQualityFlags:
    def test_stroop_congruent_accuracy_is_shown_only_as_a_flag(self, db_path):
        (ok,) = session_overview(build_db(db_path, [(3, None)]), expected=FIXTURE_EXPECTED)
        assert ok["stroop_flag"] == "ok"

        def congruent_all_wrong(rows):
            for r in rows:
                if r.get("task") == "stroop" and r.get("practice") is False and r.get("condition") == "congruent":
                    r["correct"] = False
            return rows

        (bad,) = session_overview(build_db(db_path.with_name("b.sqlite"), [(3, congruent_all_wrong)]), expected=FIXTURE_EXPECTED)
        assert bad["stroop_flag"] == "below_60_percent"
        assert all("%" not in c and not any(ch.isdigit() for ch in c) for c in bad["excluded_codes"] if "stroop" in c)  # no accuracy value shown

    @pytest.mark.parametrize("iso,tod,in_window,local_date", [
        ("2026-11-18T15:30:00.000Z", "AM", True, "2026-11-18"),    # 07:30 PST
        ("2026-11-18T15:00:00.000Z", "AM", True, "2026-11-18"),    # 07:00 exactly: inside
        ("2026-11-18T14:59:00.000Z", "AM", False, "2026-11-18"),   # 06:59: before the window
        ("2026-11-18T19:00:00.000Z", "AM", True, "2026-11-18"),    # 11:00 exactly: inside
        ("2026-11-18T19:01:00.000Z", "AM", False, "2026-11-18"),   # 11:01: after the window, still before noon
        ("2026-11-18T20:00:00.000Z", "PM", False, "2026-11-18"),   # 12:00: PM, but before the evening window
        ("2026-11-19T02:30:00.000Z", "PM", True, "2026-11-18"),    # 18:30 PST on the 18th (UTC date is the 19th)
        ("2026-11-19T05:00:00.000Z", "PM", True, "2026-11-18"),    # 21:00 exactly: inside
        ("2026-11-19T05:01:00.000Z", "PM", False, "2026-11-18"),   # 21:01: after the window
    ])
    def test_time_of_day_uses_the_logged_local_start_time(self, db_path, iso, tod, in_window, local_date):
        (row,) = session_overview(build_db(db_path, [(3, lambda r: set_timestamp(r, iso))]), expected=FIXTURE_EXPECTED)
        assert (row["time_of_day"], row["in_planned_window"], row["local_date"]) == (tod, in_window, local_date)


class TestSleepLog:
    def test_lists_the_logged_hours_per_session(self, db_path):
        log = sleep_log(build_db(db_path, [(3, None), (4, None)]))
        assert [(r["session_number"], r["hours_slept"], r["logged"]) for r in log] == [(3, 7.5, True), (4, 7.5, True)]
