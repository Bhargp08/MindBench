"""Validation of uploaded session files (JSON schema per task, required fields, types)."""
import json
import re
from collections import Counter
from dataclasses import dataclass, field

from jsonschema import Draft202012Validator

CODE_PATTERN = "^[A-HJ-KM-NP-Z2-9]{8}$"  # participant codes: no 0, 1, I, L, O
TASKS = ["contrast", "posner", "stroop", "nback", "recall"]
FILENAME_RE = re.compile(r"^([A-HJ-KM-NP-Z2-9]{8})_session(\d+)\.json$")

NUM = {"type": "number"}
INT = {"type": "integer"}
BOOL = {"type": "boolean"}
STR = {"type": "string"}
RT = {"type": ["number", "null"]}
RESP = {"type": ["string", "null"]}
SIDE = {"enum": ["left", "right"]}
COLORS = ["red", "green", "blue", "yellow"]


def obj(required, properties):
    return {"type": "object", "required": list(required), "properties": properties}


REFRESH = {"type": ["object", "null"]}

# Extra requirements per task tag (rows are validated against BASE_SCHEMA as well).
TASK_SCHEMAS = {
    "setup": obj(["viewingDistanceInstructedCm", "refresh"], {"viewingDistanceInstructedCm": NUM, "refresh": REFRESH}),
    "threshold": obj(["thresholdLevel", "thresholdContrast", "usedFallback", "nReversals", "reversals"], {
        "thresholdLevel": NUM, "thresholdContrast": NUM, "usedFallback": BOOL, "nReversals": INT, "reversals": {"type": "array", "items": NUM}}),
    "timing": obj(["timing", "refresh", "taskOrder"], {
        "timing": obj(["tasks", "totalTaskMs", "unfinished"], {"tasks": {"type": "object"}, "totalTaskMs": NUM, "unfinished": {"type": "array"}}),
        "refresh": REFRESH}),
    "feedback": obj([], {}),
    "fixation": obj([], {}),
    "isi": obj([], {}),
    "posner_cue": obj([], {}),
    "posner_gap": obj([], {}),
    "staircase_interval": obj(["interval"], {"interval": {"enum": [1, 2]}}),
    "staircase": obj(["trial", "level", "targetInterval", "response", "correct", "rt"], {
        "trial": INT, "level": NUM, "contrast": NUM, "targetInterval": {"enum": [1, 2]}, "response": RESP, "correct": BOOL, "rt": RT}),
    "yesno": obj(["trial", "isSignal", "contrast", "respondedYes", "correct", "rt"], {
        "trial": INT, "isSignal": BOOL, "contrast": NUM, "response": RESP, "respondedYes": BOOL, "correct": BOOL, "rt": RT}),
    "posner": obj(["trial", "valid", "targetSide", "cueDirection", "soaMs", "response", "correct", "rt"], {
        "trial": INT, "valid": BOOL, "targetSide": SIDE, "cueDirection": SIDE, "soaMs": NUM, "response": RESP, "correct": BOOL, "rt": RT}),
    "stroop": obj(["trial", "condition", "word", "ink", "response", "correct", "rt"], {
        "trial": INT, "condition": {"enum": ["congruent", "incongruent", "neutral"]}, "word": STR, "ink": {"enum": COLORS},
        "response": RESP, "correct": BOOL, "rt": RT}),
    "nback": obj(["trial", "position", "letter", "type", "isTarget", "responded"], {
        "trial": INT, "position": INT, "letter": STR, "type": {"enum": ["start", "target", "lure1", "lure3", "nontarget"]},
        "isTarget": BOOL, "responded": BOOL, "response": RESP, "rt": RT}),
    "recall_word": obj(["list", "position", "word"], {"list": INT, "position": INT, "word": STR}),
    "recall": obj(["list", "listWords", "recallText", "recalled", "nCorrect", "proportion", "intrusions", "repeats"], {
        "list": INT, "listWords": {"type": "array", "items": STR}, "recallText": STR, "recalled": {"type": "array", "items": BOOL},
        "nCorrect": INT, "proportion": {"type": "number", "minimum": 0, "maximum": 1}, "intrusions": {"type": "array", "items": STR}, "repeats": INT}),
    "recall_summary": obj(["recallProportion", "nCorrect", "nWords"], {
        "recallProportion": {"type": "number", "minimum": 0, "maximum": 1}, "nCorrect": INT, "nWords": INT}),
}

QUESTIONNAIRE = obj(["hoursSlept", "bedTime", "wakeTime", "kss", "caffeine", "device"], {
    "hoursSlept": {"type": "number", "minimum": 0, "maximum": 16},
    "bedTime": {"type": "string", "pattern": r"^([01]\d|2[0-3]):[0-5]\d$"},
    "wakeTime": {"type": "string", "pattern": r"^([01]\d|2[0-3]):[0-5]\d$"},
    "kss": {"type": "integer", "minimum": 1, "maximum": 9},
    "caffeine": BOOL,
    "device": {"type": "string", "minLength": 1},
})

METADATA = obj(["timestamp", "timezone", "userAgent", "screenWidth", "screenHeight", "jsPsychVersion"], {
    "timestamp": STR, "timezone": STR, "userAgent": STR, "screenWidth": NUM, "screenHeight": NUM, "jsPsychVersion": STR})

BASE_SCHEMA = obj(["trial_index", "time_elapsed", "participantCode", "sessionNumber", "questionnaire", "sessionMetadata", "taskOrder"], {
    "trial_index": {"type": "integer", "minimum": 0},
    "time_elapsed": NUM,
    "participantCode": {"type": "string", "pattern": CODE_PATTERN},
    "sessionNumber": {"type": "integer", "minimum": 1},
    "questionnaire": QUESTIONNAIRE,
    "sessionMetadata": METADATA,
    "taskOrder": {"type": "array", "items": {"enum": TASKS}, "minItems": 5, "maxItems": 5, "uniqueItems": True},
    "task": STR,
    "practice": BOOL,
    "rt": RT,
})

_BASE = Draft202012Validator(BASE_SCHEMA)
_TASK = {name: Draft202012Validator(s) for name, s in TASK_SCHEMAS.items()}


class ValidationError(ValueError):
    """A session file is malformed. The message says which row and field."""


@dataclass
class Session:
    participant_code: str
    session_number: int
    rows: list
    questionnaire: dict
    metadata: dict
    task_order: list
    task_counts: Counter = field(default_factory=Counter)


def parse_json_bytes(raw):
    try:
        return json.loads(raw)
    except (ValueError, UnicodeDecodeError) as e:
        raise ValidationError(f"File is not valid JSON: {e}") from None


def _where(i, row):
    return f"row {i} (trial_index {row.get('trial_index', '?')}, task {row.get('task', 'none')})"


def _first_error(validator, row):
    errors = sorted(validator.iter_errors(row), key=lambda e: [str(p) for p in e.absolute_path])
    if not errors:
        return None
    e = errors[0]
    path = ".".join(str(p) for p in e.absolute_path)
    return f"{path}: {e.message}" if path else e.message


def validate_session(data, filename=None):
    """Validate one session upload (a JSON array of jsPsych rows, or the dev mock object with a `trials` array)."""
    rows = data.get("trials") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise ValidationError("Expected a JSON array of trial rows (or an object with a 'trials' array)")
    if not rows:
        raise ValidationError("The file has no trial rows")

    for i, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValidationError(f"row {i} is not an object")
        msg = _first_error(_BASE, row)
        if msg:
            raise ValidationError(f"{_where(i, row)}: {msg}")
        task = row.get("task")
        if task is not None:
            if task not in _TASK:
                raise ValidationError(f"{_where(i, row)}: unknown task '{task}'")
            msg = _first_error(_TASK[task], row)
            if msg:
                raise ValidationError(f"{_where(i, row)}: {msg}")

    first = rows[0]
    for i, row in enumerate(rows[1:], start=1):
        for key in ("participantCode", "sessionNumber", "questionnaire", "sessionMetadata", "taskOrder"):
            if row[key] != first[key]:
                raise ValidationError(f"{_where(i, row)}: {key} differs from row 0 ({row[key]!r} vs {first[key]!r}); a file must hold one session")
    last = -1
    for i, row in enumerate(rows):
        if row["trial_index"] <= last:
            raise ValidationError(f"{_where(i, row)}: trial_index must be strictly increasing (got {row['trial_index']} after {last})")
        last = row["trial_index"]

    code, number = first["participantCode"], first["sessionNumber"]
    if filename is not None:
        m = FILENAME_RE.match(filename)
        if m and (m.group(1) != code or int(m.group(2)) != number):
            raise ValidationError(f"filename {filename!r} does not match the content (participantCode {code}, sessionNumber {number})")

    return Session(
        participant_code=code,
        session_number=number,
        rows=rows,
        questionnaire=first["questionnaire"],
        metadata=first["sessionMetadata"],
        task_order=first["taskOrder"],
        task_counts=Counter(r.get("task") for r in rows),
    )
