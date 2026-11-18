"""Completion and data-quality metrics for monitoring during collection.

HARD RULE (preregistered monitoring only): this module reports completion and data quality, never outcome values
(the primary and secondary outcomes) and never a hypothesis test. It reads sessions through the loader and the
exclusion rules only; tests check that no outcome-like field exists, that changing performance data changes nothing
it returns, and that the outcome-scoring code is never imported here.
"""
import datetime as dt
import json
import re
import sqlite3
from collections import Counter
from pathlib import Path
from zoneinfo import ZoneInfo

from mindbench.data import load_sessions
from mindbench.exclusions import (
    EXPECTED_SCORED,
    _stroop_congruent_accuracy,
    exclusion_reasons,
    manual_reason,
    missing_tasks,
    rule6_stopped_session,
    scored_trials,
)

TASKS = ("contrast", "posner", "stroop", "nback", "recall")
CONFIRMATORY_TARGET = 42
FIRST_CONFIRMATORY_SESSION = 3
SLOT_LIMIT = 52
SCHEDULED_DAYS = 21
EXTENSION_DAYS = 7
AM_WINDOW = (7 * 60, 11 * 60)  # planned start times, inclusive, in minutes after local midnight
PM_WINDOW = (17 * 60, 21 * 60)
ANTICIPATION_MS = 200
PARTIAL_RE = re.compile(r"^([A-HJ-KM-NP-Z2-9]{8})_session(\d+)\.partial\.json$")
FILE_SESSION_RE = re.compile(r"_session(\d+)\.json$")


# --------------------------------------------------------------------------- gaps and partial uploads
def partial_files(raw_dir):
    """`.partial.json` files (abandoned sessions that the ETL skips), with the participant code and session number."""
    out = {"partial": [], "unparsed": []}
    d = Path(raw_dir)
    if not d.is_dir():
        return out
    for p in sorted(d.glob("*.partial.json")):
        m = PARTIAL_RE.match(p.name)
        if m:
            out["partial"].append({"filename": p.name, "participant_code": m.group(1), "session_number": int(m.group(2))})
        else:
            out["unparsed"].append(p.name)
    out["partial"].sort(key=lambda x: x["session_number"])
    return out


def session_gaps(session_numbers, upto=None):
    """Missing session numbers from the first confirmatory session (3) to the highest seen. Slots 1-2 (smoke tests) are optional."""
    nums = {n for n in session_numbers}
    top = max([*nums, *([upto] if upto else [])], default=0)
    return [n for n in range(FIRST_CONFIRMATORY_SESSION, top + 1) if n not in nums]


def explain_gaps(gaps, partials, failed):
    """Why each gap exists: a file that failed validation, a partial (stopped) upload, or no file at all."""
    failed_numbers = set()
    for filename, _msg in failed:
        m = FILE_SESSION_RE.search(filename)
        if m:
            failed_numbers.add(int(m.group(1)))
    partial_numbers = {p["session_number"] for p in partials}
    rows = []
    for n in gaps:
        if n in failed_numbers:
            rows.append({"session_number": n, "status": "failed_validation", "detail": "a file arrived but failed validation (see the ETL report)"})
        elif n in partial_numbers:
            rows.append({"session_number": n, "status": "partial_upload", "detail": "stopped: only a partial upload exists, so the session was not loaded"})
        else:
            rows.append({"session_number": n, "status": "no_file", "detail": "no file found for this session number (not started, not uploaded yet, or lost)"})
    return rows


# --------------------------------------------------------------------------- per-session overview
def _code(reason):
    """An exclusion reason as a short code without numbers (the accuracy value itself is never shown)."""
    if reason.startswith("smoke_test"):
        return "smoke_test"
    if reason.startswith("stroop congruent accuracy"):
        return "stroop congruent accuracy below threshold"
    return reason


def _local_start(timestamp, tz_name):
    if not timestamp:
        return None
    t = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    try:
        zone = ZoneInfo(tz_name) if tz_name else dt.timezone.utc
    except Exception:  # unknown time zone name: fall back to UTC
        zone = dt.timezone.utc
    return t.astimezone(zone)


def _time_of_day(local):
    """AM before 12:00 local, PM from 12:00; and whether the start was inside the planned 07:00-11:00 / 17:00-21:00 window."""
    minutes = local.hour * 60 + local.minute
    am = local.hour < 12
    lo, hi = AM_WINDOW if am else PM_WINDOW
    return ("AM" if am else "PM"), lo <= minutes <= hi


def _meta(conn):
    q = "SELECT participant_code, session_number, timezone, refresh_hz, refresh_plausible, total_task_ms, source_filename FROM sessions"
    return {(c, n): {"timezone": tz, "refresh_hz": hz, "refresh_plausible": pl, "total_task_ms": ms, "source_filename": fn}
            for c, n, tz, hz, pl, ms, fn in conn.execute(q)}


def session_overview(conn, expected=None):
    """One row per loaded session: finish and exclusion status, per-task completion, timing, planned-window compliance."""
    meta = _meta(conn)
    rows = []
    for s in load_sessions(conn):
        m = meta[(s["participant_code"], s["session_number"])]
        reasons = exclusion_reasons(s, expected)
        manual = manual_reason(s)
        missing = set(missing_tasks(s, expected))
        complete = {name: name not in missing for name in (*TASKS, "questionnaire")}
        local = _local_start(s["timestamp"], s["timezone"] or m["timezone"])
        tod, in_window = _time_of_day(local) if local else (None, None)
        correct, total = _stroop_congruent_accuracy(s)
        flag = "no_trials" if total == 0 else ("below_60_percent" if correct * 5 < total * 3 else "ok")
        codes = [_code(r) for r in reasons] + (["manual exclusion (see database note)"] if manual else [])
        q = s["questionnaire"]
        rows.append({
            "participant_code": s["participant_code"],
            "session_number": s["session_number"],
            "is_pilot": s["is_pilot"],
            "local_date": local.date().isoformat() if local else None,
            "local_start": local.isoformat(timespec="minutes") if local else None,
            "time_of_day": tod,
            "in_planned_window": in_window,
            "battery_finished": not rule6_stopped_session(s),
            "tasks_complete": complete,
            "n_tasks_complete": sum(complete.values()),
            "excluded": bool(codes),
            "excluded_codes": codes,
            "sleep_logged": q is not None and q["hours_slept"] is not None,
            "total_task_minutes": None if m["total_task_ms"] is None else m["total_task_ms"] / 60000,
            "refresh_hz": m["refresh_hz"],
            "refresh_plausible": None if m["refresh_plausible"] is None else bool(m["refresh_plausible"]),
            "stroop_flag": flag,
            "source_filename": m["source_filename"],
        })
    return rows


def completion_summary(overview, target=CONFIRMATORY_TARGET):
    """Counts for the stopping rule. A completed session is one whose battery finished, even if a rule excludes it later."""
    confirmatory = [r for r in overview if not r["is_pilot"]]
    done = sum(1 for r in confirmatory if r["battery_finished"])
    reasons = Counter(c for r in overview if r["excluded"] for c in r["excluded_codes"])
    return {
        "sessions_loaded": len(overview),
        "completed": sum(1 for r in overview if r["battery_finished"]),
        "confirmatory_completed": done,
        "remaining_to_target": max(0, target - done),
        "smoke_tests_run": sum(1 for r in overview if r["is_pilot"] == 1),
        "excluded": sum(1 for r in overview if r["excluded"]),
        "excluded_by_reason": dict(reasons),
    }


def schedule_status(overview, today):
    """Day of the 21-day schedule, counted from the first confirmatory session's local start date."""
    dates = [r["local_date"] for r in overview if not r["is_pilot"] and r["local_date"]]
    if not dates:
        return {"first_confirmatory_date": None, "day_number": None, "scheduled_days_remaining": None, "extension_days_remaining": None}
    first = min(dates)
    day = (today - dt.date.fromisoformat(first)).days + 1
    return {"first_confirmatory_date": first, "day_number": day,
            "scheduled_days_remaining": max(0, SCHEDULED_DAYS - day), "extension_days_remaining": max(0, SCHEDULED_DAYS + EXTENSION_DAYS - day)}


def stopping_status(confirmatory_completed, day_number, highest_session_number):
    """The preregistered stopping rule: stop at 42 completed sessions, or after the 21 days plus up to 7 extension days, or at session slot 52."""
    day = day_number or 0
    if confirmatory_completed >= CONFIRMATORY_TARGET:
        return {"stop": True, "phase": "stopped", "reason": f"target reached: {CONFIRMATORY_TARGET} completed confirmatory sessions"}
    if highest_session_number >= SLOT_LIMIT:
        return {"stop": True, "phase": "stopped", "reason": f"no session slots left (slot {SLOT_LIMIT} reached)"}
    if day > SCHEDULED_DAYS + EXTENSION_DAYS:
        return {"stop": True, "phase": "stopped", "reason": f"the extension period is over ({SCHEDULED_DAYS} + {EXTENSION_DAYS} days)"}
    if day > SCHEDULED_DAYS:
        return {"stop": False, "phase": "extension", "reason": "past the 21 scheduled days: extension days to recover missed sessions"}
    return {"stop": False, "phase": "scheduled", "reason": "within the 21 scheduled days"}


# --------------------------------------------------------------------------- data quality per task
def task_quality(conn, expected=None):
    """Per session and task: scored trial count against the design count, completion, no-response rate, anticipations, duration."""
    exp = {**EXPECTED_SCORED, **(expected or {})}
    rows = []
    for s in load_sessions(conn):
        missing = set(missing_tasks(s, expected))
        timing = next((t for t in s["trials"] if t["task"] == "timing"), None)
        durations = ((timing["data"].get("timing") or {}).get("tasks") or {}) if timing else {}

        def rate(trials):
            return sum(1 for t in trials if t["response"] is None) / len(trials) if trials else None

        for task in TASKS:
            if task == "contrast":
                trials = scored_trials(s, "yesno")
                extra = {"staircase_trials": len(scored_trials(s, "staircase"))}
                nores = rate(trials + scored_trials(s, "staircase"))
                scored, expected_n, anticip = len(trials), exp["yesno"], None
            elif task in ("posner", "stroop"):
                trials = scored_trials(s, task)
                extra, nores = {}, rate(trials)
                scored, expected_n = len(trials), exp[task]
                anticip = sum(1 for t in trials if t["rt"] is not None and t["rt"] < ANTICIPATION_MS)
            elif task == "nback":  # not responding is a correct answer here, so no response rate is meaningful
                extra, nores, anticip = {}, None, None
                scored, expected_n = len(scored_trials(s, "nback")), exp["nback"]
            else:
                extra, nores, anticip = {}, None, None
                scored, expected_n = len(scored_trials(s, "recall")), exp["recall_lists"]
            rows.append({
                "session_number": s["session_number"], "task": task, "scored_trials": scored, "expected_trials": expected_n,
                "complete": task not in missing, "no_response_rate": nores, "anticipations": anticip,
                "duration_ms": (durations.get(task) or {}).get("ms"), **extra,
            })
    return rows


def sleep_log(conn):
    """Logged hours slept per session (the predictor, not an outcome). Local view only."""
    return [{"session_number": s["session_number"], "hours_slept": (s["questionnaire"] or {}).get("hours_slept"),
             "logged": s["questionnaire"] is not None and s["questionnaire"]["hours_slept"] is not None} for s in load_sessions(conn)]


def etl_report(path):
    """The last nightly ETL report, or None."""
    if not path or not Path(path).is_file():
        return None
    try:
        return json.loads(Path(path).read_text())
    except (OSError, ValueError):
        return None


# --------------------------------------------------------------------------- everything the app shows
def build_dashboard_data(db_path, raw_dir, report_path, expected, today, public=False):
    """All dashboard content. Public mode keeps aggregates only: no participant codes, file names, free text, user agent,
    time of day, sleep values or timestamps finer than a date."""
    partials = partial_files(raw_dir)
    report = etl_report(report_path)
    failed = [(f["file"], f["message"]) for f in (report or {}).get("failed", [])]
    db = Path(db_path)
    if db.is_file():
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            overview, quality, sleep = session_overview(conn, expected), task_quality(conn, expected), sleep_log(conn)
        finally:
            conn.close()
    else:
        overview, quality, sleep = [], [], []
    summary = completion_summary(overview)
    schedule = schedule_status(overview, today)
    numbers = [r["session_number"] for r in overview]
    partial_numbers = [p["session_number"] for p in partials["partial"]]
    failed_numbers = [int(m.group(1)) for f, _ in failed if (m := FILE_SESSION_RE.search(f))]
    highest = max([*numbers, *partial_numbers, *failed_numbers], default=0)  # a failed or partial file also shows how far numbering got
    gaps = explain_gaps(session_gaps(numbers, upto=highest), partials["partial"], failed)
    stopping = stopping_status(summary["confirmatory_completed"], schedule["day_number"], highest)
    base = {"public": public, "db_found": db.is_file(), "summary": summary, "schedule": schedule, "stopping": stopping, "highest_session_number": highest}
    if public:
        completion = {}
        for t in TASKS:
            mine = [q for q in quality if q["task"] == t]
            completion[t] = {"sessions": len(mine), "complete": sum(1 for q in mine if q["complete"])}
        return {**base, "gap_count": len(gaps), "partial_upload_count": len(partials["partial"]), "failed_file_count": len(failed), "task_completion": completion}
    return {**base, "overview": overview, "gaps": gaps, "partial_files": partials, "failed_files": [{"file": f, "message": m} for f, m in failed],
            "quality": quality, "sleep_log": sleep,
            "etl": None if report is None else {"ran_at": report.get("ran_at"), "download": report.get("download"), "exclusions": report.get("exclusions")}}
