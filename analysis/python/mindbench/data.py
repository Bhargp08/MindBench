"""Read sessions from the SQLite database built by the ETL (docs/design/etl.md)."""
import json
from collections import defaultdict

SESSIONS_SQL = """
SELECT s.participant_code, s.session_number, s.is_pilot, s.excluded_reason, s.timestamp, s.timezone,
       q.participant_code AS has_questionnaire, q.hours_slept, q.bed_time, q.wake_time, q.kss, q.caffeine, q.device
FROM sessions s
LEFT JOIN questionnaire q ON q.participant_code = s.participant_code AND q.session_number = s.session_number
ORDER BY s.participant_code, s.session_number
"""


def load_sessions(conn):
    """All sessions as dicts: metadata, `questionnaire` (None if missing) and `trials` (each with parsed `data`)."""
    trials = defaultdict(list)
    for code, n, idx, task, practice, rt, response, correct, data_json in conn.execute(
        "SELECT participant_code, session_number, trial_index, task, practice, rt, response, correct, data_json FROM trials ORDER BY trial_index"
    ):
        trials[(code, n)].append(
            {"trial_index": idx, "task": task, "practice": practice, "rt": rt, "response": response, "correct": correct, "data": json.loads(data_json)}
        )
    sessions = []
    for code, n, is_pilot, reason, ts, tz, has_q, hours, bed, wake, kss, caffeine, device in conn.execute(SESSIONS_SQL):
        sessions.append(
            {
                "participant_code": code,
                "session_number": n,
                "is_pilot": is_pilot,
                "excluded_reason": reason,
                "timestamp": ts,
                "timezone": tz,
                "questionnaire": None
                if has_q is None
                else {"hours_slept": hours, "bed_time": bed, "wake_time": wake, "kss": kss, "caffeine": caffeine, "device": device},
                "trials": trials[(code, n)],
            }
        )
    return sessions
