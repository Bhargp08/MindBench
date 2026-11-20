"""Prereg D2 / D9 (MB-05b): day and AM/PM come from the logged local start time.

D2: a session starting from 00:00 up to (not including) 04:00 belongs to the previous calendar day and counts as its PM session.
D9: AM/PM comes from the start time, never from odd/even session numbers.
Two sessions in the same day and slot: only the first is analysed; the later one is flagged.
Fixture time zone is PST (UTC-8).
"""
import datetime as dt

import pytest

from mindbench_dashboard.metrics import schedule_status, session_overview

from conftest import FIXTURE_EXPECTED, build_db, set_timestamp


def row_for(db_path, iso, session=3):
    (row,) = session_overview(build_db(db_path, [(session, lambda r: set_timestamp(r, iso))]), expected=FIXTURE_EXPECTED)
    return row


@pytest.mark.parametrize("iso,tod,local_date,in_window", [
    ("2026-11-19T08:00:00.000Z", "PM", "2026-11-18", False),   # 00:00 PST on the 19th -> PM of the 18th
    ("2026-11-19T11:59:00.000Z", "PM", "2026-11-18", False),   # 03:59 -> still the previous day
    ("2026-11-19T12:00:00.000Z", "AM", "2026-11-19", False),   # 04:00 exactly -> AM of the 19th (before the AM window)
    ("2026-11-19T15:00:00.000Z", "AM", "2026-11-19", True),    # 07:00
])
def test_d2_early_morning_starts_belong_to_the_previous_day_and_count_as_pm(db_path, iso, tod, local_date, in_window):
    row = row_for(db_path, iso)
    assert (row["time_of_day"], row["local_date"]) == (tod, local_date)
    assert row["in_planned_window"] is in_window


def test_d2_late_night_start_is_outside_the_planned_window(db_path):
    assert row_for(db_path, "2026-11-19T07:59:00.000Z")["in_planned_window"] is False   # 23:59


def test_d2_day_number_uses_the_previous_day_for_a_00_to_04_start(db_path):
    conn = build_db(db_path, [(3, lambda r: set_timestamp(r, "2026-11-19T09:00:00.000Z"))])   # 01:00 PST on the 19th -> day of the 18th
    s = schedule_status(session_overview(conn, expected=FIXTURE_EXPECTED), today=dt.date(2026, 11, 20))
    assert s["first_confirmatory_date"] == "2026-11-18"
    assert s["day_number"] == 3


@pytest.mark.parametrize("session", [3, 4, 5, 6])
def test_d9_am_pm_does_not_depend_on_odd_even_session_numbers(db_path, session):
    am = row_for(db_path.with_name(f"am{session}.sqlite"), "2026-11-18T16:00:00.000Z", session=session)   # 08:00
    pm = row_for(db_path.with_name(f"pm{session}.sqlite"), "2026-11-19T02:30:00.000Z", session=session)   # 18:30
    assert (am["time_of_day"], pm["time_of_day"]) == ("AM", "PM")


def test_two_sessions_in_the_same_day_and_slot_flag_only_the_later_one(db_path):
    conn = build_db(db_path, [(3, lambda r: set_timestamp(r, "2026-11-18T16:00:00.000Z")),
                              (4, lambda r: set_timestamp(r, "2026-11-18T17:00:00.000Z")),
                              (5, lambda r: set_timestamp(r, "2026-11-19T02:30:00.000Z"))])
    rows = {r["session_number"]: r for r in session_overview(conn, expected=FIXTURE_EXPECTED)}
    assert rows[3]["duplicate_slot"] is False
    assert rows[4]["duplicate_slot"] is True
    assert rows[5]["duplicate_slot"] is False
