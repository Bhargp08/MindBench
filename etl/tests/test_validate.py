import copy
import json

import pytest

from mindbench_etl.validate import ValidationError, validate_session

from conftest import EXPECTED_ROWS, EXPECTED_TASK_COUNTS


def first(rows, task):
    return next(r for r in rows if r.get("task") == task)


def set_everywhere(rows, key, value):
    for r in rows:
        r[key] = value


class TestValidFiles:
    def test_fixtures_validate(self, session3, session11):
        for rows, code, n in ((session3, "K7M2QX9P", 3), (session11, "K7M2QX9P", 11)):
            s = validate_session(rows, filename=f"{code}_session{n}.json")
            assert s.participant_code == code
            assert s.session_number == n
            assert len(s.rows) == EXPECTED_ROWS

    def test_counts_per_task(self, session3):
        s = validate_session(session3)
        assert dict(s.task_counts) == EXPECTED_TASK_COUNTS

    def test_accepts_the_dev_mock_format(self, session3):
        mock = {"participantCode": "K7M2QX9P", "sessionNumber": 3, "mode": "mock", "trials": session3}
        assert len(validate_session(mock).rows) == EXPECTED_ROWS

    def test_returns_questionnaire_and_metadata(self, session3):
        s = validate_session(session3)
        assert s.questionnaire["hoursSlept"] == 7.5
        assert s.metadata["jsPsychVersion"] == "8.4.0"
        assert s.task_order == ["stroop", "nback", "posner", "recall", "contrast"]


def case(name, mutate, expect):
    return pytest.param(mutate, expect, id=name)


def drop_key(task, key):
    def f(rows):
        del first(rows, task)[key]
    return f


def set_in(task, key, value):
    def f(rows):
        first(rows, task)[key] = value
    return f


def set_questionnaire(key, value):
    def f(rows):
        for r in rows:
            r["questionnaire"][key] = value
    return f


MALFORMED = [
    case("missing participantCode", lambda rows: rows[7].pop("participantCode"), "participantCode"),
    case("one row from another participant", lambda rows: rows[9].__setitem__("participantCode", "AAAAAAAA"), "participantCode"),
    case("ambiguous characters in code", lambda rows: set_everywhere(rows, "participantCode", "K7M2QX0O"), "participantCode"),
    case("session number zero", lambda rows: set_everywhere(rows, "sessionNumber", 0), "sessionNumber"),
    case("session number not an integer", lambda rows: set_everywhere(rows, "sessionNumber", "3"), "sessionNumber"),
    case("sleep hours above 16", set_questionnaire("hoursSlept", 17), "hoursSlept"),
    case("sleep hours negative", set_questionnaire("hoursSlept", -1), "hoursSlept"),
    case("kss out of range", set_questionnaire("kss", 0), "kss"),
    case("caffeine not boolean", set_questionnaire("caffeine", "no"), "caffeine"),
    case("missing questionnaire", lambda rows: rows[3].pop("questionnaire"), "questionnaire"),
    case("missing session metadata field", lambda rows: [r["sessionMetadata"].pop("timezone") for r in rows], "timezone"),
    case("task order not a permutation", lambda rows: set_everywhere(rows, "taskOrder", ["stroop", "stroop", "posner", "recall", "contrast"]), "taskOrder"),
    case("duplicate trial_index", lambda rows: rows[6].__setitem__("trial_index", rows[5]["trial_index"]), "trial_index"),
    case("trial_index missing", lambda rows: rows[2].pop("trial_index"), "trial_index"),
    case("unknown task", set_in("posner", "task", "mystery"), "unknown task"),
    case("posner bad side", set_in("posner", "targetSide", "up"), "targetSide"),
    case("posner valid not boolean", set_in("posner", "valid", "yes"), "valid"),
    case("stroop correct as string", set_in("stroop", "correct", "true"), "correct"),
    case("stroop bad condition", set_in("stroop", "condition", "weird"), "condition"),
    case("nback bad type", set_in("nback", "type", "foo"), "type"),
    case("staircase missing level", drop_key("staircase", "level"), "level"),
    case("staircase bad target interval", set_in("staircase", "targetInterval", 3), "targetInterval"),
    case("yesno missing respondedYes", drop_key("yesno", "respondedYes"), "respondedYes"),
    case("recall recalled not a list", set_in("recall", "recalled", "yes"), "recalled"),
    case("recall_summary proportion not a number", set_in("recall_summary", "recallProportion", "half"), "recallProportion"),
    case("practice not boolean", set_in("stroop", "practice", "no"), "practice"),
]


@pytest.mark.parametrize("mutate,expect", MALFORMED)
def test_malformed_files_are_rejected_with_a_clear_message(session3, mutate, expect):
    rows = copy.deepcopy(session3)
    mutate(rows)
    with pytest.raises(ValidationError) as e:
        validate_session(rows)
    assert expect in str(e.value)


def test_error_names_the_row_and_task(session3):
    rows = copy.deepcopy(session3)
    p = first(rows, "posner")
    p["targetSide"] = "up"
    with pytest.raises(ValidationError) as e:
        validate_session(rows)
    msg = str(e.value)
    assert f"trial_index {p['trial_index']}" in msg
    assert "posner" in msg


@pytest.mark.parametrize("bad", [[], 5, "text", None, {"no": "trials"}])
def test_wrong_top_level_shapes_are_rejected(bad):
    with pytest.raises(ValidationError):
        validate_session(bad)


def test_filename_must_match_the_content(session3):
    with pytest.raises(ValidationError) as e:
        validate_session(session3, filename="AAAAAAAA_session1.json")
    assert "filename" in str(e.value)
    validate_session(session3, filename="K7M2QX9P_session3.json")


def test_raw_text_that_is_not_json_is_rejected():
    from mindbench_etl.validate import parse_json_bytes

    with pytest.raises(ValidationError) as e:
        parse_json_bytes(b"{not json")
    assert "JSON" in str(e.value)
    assert parse_json_bytes(json.dumps([{"a": 1}]).encode()) == [{"a": 1}]
