"""One test group per rule in docs/design/design.md section 5, with boundary values."""
import re

import pytest

from mindbench import exclusions as ex

from conftest import FIXTURE_EXPECTED, REPO, make_session, trial

EXP0 = {**FIXTURE_EXPECTED, "stroop": 0}  # for accuracy tests that build their own Stroop trials


def reasons_containing(reasons, text):
    return [r for r in reasons if text in r]


# ---------------------------------------------------------------- the rule text is in the docstrings
def design_rules():
    text = (REPO / "docs" / "design" / "design.md").read_text()
    section = text.split("## 5.")[1].split("## 6.")[0]
    return {int(m.group(1)): m.group(2) for m in re.finditer(r"^(\d)\. (.+)$", section, re.MULTILINE)}


def plain(s):
    return re.sub(r"\s+", " ", s.replace("**", "").replace("`", "")).strip()


RULE_FUNCTIONS = {
    1: ex.rule1_trim_rt,
    2: ex.rule2_correct_trials_only,
    3: ex.rule3_session_exclusion,
    4: ex.rule4_smoke_test_session,
    5: ex.rule5_missing_sleep_log,
    6: ex.rule6_stopped_session,
}


@pytest.mark.parametrize("n", range(1, 7))
def test_each_rule_function_quotes_its_design_rule_in_the_docstring(n):
    rule = design_rules()[n]
    assert plain(rule) in plain(RULE_FUNCTIONS[n].__doc__), f"rule {n} text not found in {RULE_FUNCTIONS[n].__name__}.__doc__"


def test_design_has_exactly_six_rules():
    assert sorted(design_rules()) == [1, 2, 3, 4, 5, 6]


# ---------------------------------------------------------------- rule 1: trim RT (Stroop and Posner only)
class TestRule1:
    def kept(self, task, rts):
        trials = [trial(task, i, practice=0, rt=rt, correct=1) for i, rt in enumerate(rts)]
        return [t["rt"] for t in ex.rule1_trim_rt(trials)]

    @pytest.mark.parametrize("task", ["stroop", "posner"])
    def test_bounds_are_kept_and_values_outside_are_dropped(self, task):
        assert self.kept(task, [199, 199.999, 200, 2500, 2500.001, 2501, 600]) == [200, 2500, 600]

    @pytest.mark.parametrize("task", ["stroop", "posner"])
    def test_trials_without_a_response_have_no_rt_to_trim_and_are_kept(self, task):
        assert self.kept(task, [None, 100]) == [None]

    @pytest.mark.parametrize("task", ["nback", "yesno", "staircase", "recall"])
    def test_other_tasks_are_never_trimmed(self, task):
        assert self.kept(task, [50, 5000]) == [50, 5000]

    def test_custom_bounds(self):
        trials = [trial("stroop", i, rt=rt, correct=1) for i, rt in enumerate([100, 150, 300])]
        assert [t["rt"] for t in ex.rule1_trim_rt(trials, min_rt=150, max_rt=300)] == [150, 300]


# ---------------------------------------------------------------- rule 2: correct trials only
class TestRule2:
    def test_only_correct_trials_remain(self):
        trials = [trial("stroop", 0, rt=500, correct=1), trial("stroop", 1, rt=500, correct=0), trial("stroop", 2, rt=None, correct=None)]
        assert [t["trial_index"] for t in ex.rule2_correct_trials_only(trials)] == [0]

    def test_an_error_with_a_fast_rt_is_still_dropped(self):
        assert ex.rule2_correct_trials_only([trial("posner", 0, rt=250, correct=0)]) == []


# ---------------------------------------------------------------- rule 3: session exclusion
def stroop_session(congruent, correct, wrong_rt=300):
    s = make_session(stroop=0)
    i = len(s["trials"])
    for k in range(congruent):
        ok = k < correct
        s["trials"].append(trial("stroop", i + k, practice=0, rt=600 if ok else wrong_rt, correct=1 if ok else 0, condition="congruent"))
    return s


class TestRule3StroopAccuracy:
    def excluded(self, s):
        return bool(reasons_containing(ex.rule3_session_exclusion(s, EXP0), "stroop congruent accuracy"))

    @pytest.mark.parametrize("correct,total,expected", [(60, 100, False), (59, 100, True), (3, 5, False), (2, 5, True), (6, 10, False), (5, 10, True), (10, 10, False), (0, 10, True)])
    def test_exactly_60_percent_is_kept_below_is_excluded(self, correct, total, expected):
        assert self.excluded(stroop_session(total, correct)) is expected

    def test_the_accuracy_check_is_made_before_rt_trimming_so_anticipations_count_as_errors(self):
        # 3 correct + 3 errors with RT 100 ms (rule 1 would drop them from RT outcomes): accuracy is 3/6, not 3/3
        assert self.excluded(stroop_session(6, 3, wrong_rt=100)) is True
        assert self.excluded(stroop_session(6, 3, wrong_rt=300)) is True

    def test_key_mashing_under_200_ms_cannot_dodge_the_check(self):
        # every congruent response is an error faster than 200 ms: all would be trimmed, but the session must still be excluded
        assert self.excluded(stroop_session(10, 0, wrong_rt=120)) is True

    def test_fast_but_correct_responses_count_as_correct(self):
        s = stroop_session(5, 5)
        for t in s["trials"][-5:]:
            t["rt"] = 150
        assert self.excluded(s) is False

    def test_a_missing_response_counts_as_an_error(self):
        s = stroop_session(5, 3)
        for t in s["trials"][-2:]:
            t["rt"] = None
        assert self.excluded(s) is False  # 3/5 = 60%
        s["trials"][-3]["correct"] = 0
        s["trials"][-3]["rt"] = None
        assert self.excluded(s) is True  # 2/5

    def test_practice_trials_never_count(self):
        s = stroop_session(5, 3)
        assert any(t["practice"] == 1 and t["task"] == "stroop" and t["correct"] == 0 for t in s["trials"])
        assert self.excluded(s) is False

    def test_incongruent_errors_do_not_matter(self):
        s = stroop_session(5, 3)
        s["trials"].extend(trial("stroop", 900 + k, practice=0, rt=700, correct=0, condition="incongruent") for k in range(10))
        assert self.excluded(s) is False

    def test_no_congruent_trials_gives_no_accuracy_reason_the_session_is_incomplete_instead(self):
        reasons = ex.rule3_session_exclusion(stroop_session(0, 0), FIXTURE_EXPECTED)
        assert not reasons_containing(reasons, "stroop congruent accuracy")
        assert reasons_containing(reasons, "missing stroop")


class TestRule3Incomplete:
    def reasons(self, **kw):
        return ex.rule3_session_exclusion(make_session(**kw), FIXTURE_EXPECTED)

    def test_a_complete_session_has_no_reasons(self):
        assert self.reasons() == []

    @pytest.mark.parametrize("kw,task", [
        ({"posner": 0}, "posner"), ({"stroop": 0}, "stroop"), ({"nback": 0}, "nback"), ({"lists": 0, "summary": False}, "recall"),
        ({"threshold": False}, "contrast"), ({"yesno": 0}, "contrast"),
    ])
    def test_each_missing_task_is_reported_by_name(self, kw, task):
        assert reasons_containing(self.reasons(**kw), f"missing {task}")

    def test_missing_questionnaire(self):
        assert reasons_containing(self.reasons(questionnaire=False), "questionnaire")

    @pytest.mark.parametrize("key,task", [("posner", "posner"), ("stroop", "stroop"), ("nback", "nback"), ("yesno", "contrast"), ("lists", "recall")])
    def test_one_short_is_incomplete_exact_is_complete_and_extra_is_not_an_exclusion(self, key, task):
        exact = {"posner": 3, "stroop": 3, "nback": 6, "yesno": 4, "lists": 2}[key]
        assert reasons_containing(self.reasons(**{key: exact - 1}), f"missing {task}")
        assert self.reasons(**{key: exact}) == []
        assert self.reasons(**{key: exact + 1}) == []  # more than the design count is only a data warning (scoring.data_warnings)

    def test_recall_without_its_summary_row_is_incomplete(self):
        assert reasons_containing(self.reasons(summary=False), "missing recall")

    def test_practice_rows_do_not_make_up_for_missing_scored_trials(self):
        s = make_session(posner=0, practice_noise=True)
        assert reasons_containing(ex.rule3_session_exclusion(s, FIXTURE_EXPECTED), "missing posner")

    def test_several_missing_tasks_are_all_named(self):
        reasons = self.reasons(posner=0, stroop=0)
        text = " ".join(reasons)
        assert "posner" in text and "stroop" in text

    def test_a_full_size_session_passes_with_the_default_design_counts_and_one_short_fails(self):
        full = dict(posner=120, stroop=120, nback=60, yesno=60, lists=2)
        assert ex.rule3_session_exclusion(make_session(**full)) == []
        for key, task in [("posner", "posner"), ("stroop", "stroop"), ("nback", "nback"), ("yesno", "contrast"), ("lists", "recall")]:
            short = {**full, key: full[key] - 1}
            assert reasons_containing(ex.rule3_session_exclusion(make_session(**short)), f"missing {task}"), key

    def test_default_expected_counts_are_the_design_counts(self):
        assert ex.EXPECTED_SCORED == {"posner": 120, "stroop": 120, "nback": 60, "yesno": 60, "recall_lists": 2}
        assert reasons_containing(ex.rule3_session_exclusion(make_session()), "missing posner")  # 3 < 120


# ---------------------------------------------------------------- rule 4: smoke-test sessions
class TestRule4:
    def test_flagged_sessions_are_excluded(self):
        assert reasons_containing(ex.rule4_smoke_test_session(make_session(is_pilot=1)), "smoke")

    @pytest.mark.parametrize("flag", [0, None])
    def test_unflagged_sessions_are_not(self, flag):
        s = make_session()
        s["is_pilot"] = flag
        assert ex.rule4_smoke_test_session(s) == []


# ---------------------------------------------------------------- rule 5: missing sleep log (H1 only)
class TestRule5:
    def test_zero_hours_is_a_sleep_log_not_a_missing_one(self):
        assert ex.rule5_missing_sleep_log(make_session(hours=0)) is False

    def test_none_or_no_questionnaire_is_missing(self):
        assert ex.rule5_missing_sleep_log(make_session(hours=None)) is True
        assert ex.rule5_missing_sleep_log(make_session(questionnaire=False)) is True

    def test_a_present_log_is_not_missing(self):
        assert ex.rule5_missing_sleep_log(make_session(hours=7.5)) is False

    def test_missing_sleep_drops_the_session_from_h1_only(self):
        s = make_session(hours=None)
        assert ex.exclusion_reasons(s, FIXTURE_EXPECTED) == []  # still analyzed for everything else
        assert ex.h1_eligible(s, FIXTURE_EXPECTED) is False

    def test_h1_eligible_respects_a_manual_exclusion_reason(self):
        s = make_session()
        s["excluded_reason"] = "manual: hardware crash"
        assert ex.h1_eligible(s, FIXTURE_EXPECTED) is False
        s["excluded_reason"] = "auto: something recomputed elsewhere"
        assert ex.h1_eligible(s, FIXTURE_EXPECTED) is True  # automatic reasons are recomputed from the rules, not trusted

    def test_h1_eligible_needs_an_unexcluded_session_with_a_sleep_log(self):
        assert ex.h1_eligible(make_session(), FIXTURE_EXPECTED) is True
        assert ex.h1_eligible(make_session(is_pilot=1), FIXTURE_EXPECTED) is False
        assert ex.h1_eligible(make_session(posner=0), FIXTURE_EXPECTED) is False


# ---------------------------------------------------------------- rule 6: stopped session counts as incomplete
class TestRule6:
    def test_a_session_with_a_finished_battery_is_not_stopped(self):
        assert ex.rule6_stopped_session(make_session()) == []

    def test_no_timing_row_means_the_battery_did_not_finish(self):
        assert reasons_containing(ex.rule6_stopped_session(make_session(timing=False)), "incomplete")

    def test_unfinished_tasks_in_the_timing_row_mean_it_was_stopped(self):
        reasons = ex.rule6_stopped_session(make_session(unfinished=["posner"]))
        assert reasons_containing(reasons, "incomplete") and reasons_containing(reasons, "posner")


# ---------------------------------------------------------------- combination
class TestExclusionReasons:
    def test_reasons_follow_rule_order_and_all_apply(self):
        s = make_session(is_pilot=1, posner=0, timing=False)
        reasons = ex.exclusion_reasons(s, FIXTURE_EXPECTED)
        assert reasons_containing(reasons, "smoke") and reasons_containing(reasons, "missing posner") and reasons_containing(reasons, "incomplete")
        assert reasons[0].startswith("smoke")

    def test_a_clean_session_has_no_reasons(self):
        assert ex.exclusion_reasons(make_session(), FIXTURE_EXPECTED) == []


# ---------------------------------------------------------------- selecting scored trials
def test_scored_trials_are_the_practice_zero_rows():
    s = make_session()
    scored = ex.scored_trials(s, "stroop")
    assert len(scored) == 3
    assert all(t["practice"] == 0 and t["task"] == "stroop" for t in scored)
