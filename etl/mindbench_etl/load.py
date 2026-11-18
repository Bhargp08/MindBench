"""Idempotent load of validated sessions into SQLite (one transaction per session file)."""
import json
import sqlite3
from pathlib import Path

from .validate import ValidationError, parse_json_bytes, validate_session

PILOT_SESSIONS = 10
SESSION_LEVEL_KEYS = ("participantCode", "sessionNumber", "questionnaire", "sessionMetadata", "taskOrder")


def _first(rows, task):
    return next((r for r in rows if r.get("task") == task), None)


def _response(value):
    if value is None or isinstance(value, str):
        return value
    return json.dumps(value)


def _flag(value):
    return None if value is None else int(bool(value))


def load_session(conn, data, filename=None, pilot_sessions=PILOT_SESSIONS):
    """Validate, then write participants, session, questionnaire and trials in one transaction.

    Validation happens before any write, and a database error part-way through rolls everything back.
    Re-loading a session upserts it: row counts stay the same, rows that disappeared from a newer upload
    are removed, and `excluded_reason` is never overwritten.
    """
    s = validate_session(data, filename=filename)
    code, number = s.participant_code, s.session_number
    setup = _first(s.rows, "setup") or {}
    timing = _first(s.rows, "timing") or {}
    refresh = setup.get("refresh") or {}
    m, q = s.metadata, s.questionnaire

    with conn:
        conn.execute("INSERT OR IGNORE INTO participants (participant_code) VALUES (?)", (code,))
        conn.execute(
            """INSERT INTO sessions (participant_code, session_number, is_pilot, timestamp, timezone, user_agent, screen_width,
                   screen_height, jspsych_version, task_order, viewing_distance_cm, refresh_hz, refresh_plausible, total_task_ms, source_filename)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (participant_code, session_number) DO UPDATE SET
                   is_pilot = excluded.is_pilot, timestamp = excluded.timestamp, timezone = excluded.timezone,
                   user_agent = excluded.user_agent, screen_width = excluded.screen_width, screen_height = excluded.screen_height,
                   jspsych_version = excluded.jspsych_version, task_order = excluded.task_order,
                   viewing_distance_cm = excluded.viewing_distance_cm, refresh_hz = excluded.refresh_hz,
                   refresh_plausible = excluded.refresh_plausible, total_task_ms = excluded.total_task_ms,
                   source_filename = excluded.source_filename""",
            (code, number, 1 if number <= pilot_sessions else 0, m["timestamp"], m["timezone"], m["userAgent"], m["screenWidth"],
             m["screenHeight"], m["jsPsychVersion"], json.dumps(s.task_order), setup.get("viewingDistanceInstructedCm"),
             refresh.get("hz"), _flag(refresh.get("plausible")), (timing.get("timing") or {}).get("totalTaskMs"), filename),
        )
        conn.execute(
            """INSERT INTO questionnaire (participant_code, session_number, hours_slept, bed_time, wake_time, kss, caffeine, device)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (participant_code, session_number) DO UPDATE SET
                   hours_slept = excluded.hours_slept, bed_time = excluded.bed_time, wake_time = excluded.wake_time,
                   kss = excluded.kss, caffeine = excluded.caffeine, device = excluded.device""",
            (code, number, q["hoursSlept"], q["bedTime"], q["wakeTime"], q["kss"], int(q["caffeine"]), q["device"]),
        )
        conn.executemany(
            """INSERT INTO trials (participant_code, session_number, trial_index, task, practice, rt, response, correct, data_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT (participant_code, session_number, trial_index) DO UPDATE SET
                   task = excluded.task, practice = excluded.practice, rt = excluded.rt, response = excluded.response,
                   correct = excluded.correct, data_json = excluded.data_json""",
            [
                (code, number, r["trial_index"], r.get("task"), _flag(r.get("practice")), r.get("rt"), _response(r.get("response")),
                 _flag(r.get("correct")), json.dumps({k: v for k, v in r.items() if k not in SESSION_LEVEL_KEYS}, sort_keys=True))
                for r in s.rows
            ],
        )
        conn.execute(
            "DELETE FROM trials WHERE participant_code = ? AND session_number = ? AND trial_index NOT IN (SELECT value FROM json_each(?))",
            (code, number, json.dumps([r["trial_index"] for r in s.rows])),
        )
    return {"participant_code": code, "session_number": number, "n_rows": len(s.rows), "is_pilot": number <= pilot_sessions}


def load_file(conn, path, pilot_sessions=PILOT_SESSIONS):
    path = Path(path)
    return load_session(conn, parse_json_bytes(path.read_bytes()), filename=path.name, pilot_sessions=pilot_sessions)


def load_directory(conn, directory, pilot_sessions=PILOT_SESSIONS):
    """Load every *.json file in a folder. `.partial.json` files (abandoned sessions) are skipped."""
    report = {"loaded": [], "failed": [], "skipped_partial": []}
    for path in sorted(Path(directory).glob("*.json")):
        if path.name.endswith(".partial.json"):
            report["skipped_partial"].append(path.name)
            continue
        try:
            load_file(conn, path, pilot_sessions=pilot_sessions)
            report["loaded"].append(path.name)
        except (ValidationError, sqlite3.DatabaseError) as e:
            report["failed"].append((path.name, str(e)))
    return report
