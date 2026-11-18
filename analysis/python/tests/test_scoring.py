import pytest

from mindbench import exclusions as ex
from mindbench.scoring import data_warnings, load_sessions, score_database, score_session, serial_position

from conftest import FIXTURE_EXPECTED, insert_fixture, make_session, trial


@pytest.fixture
def loaded(db):
    insert_fixture(db, "K7M2QX9P_session3.json")
    return load_sessions(db)


class TestScoreFixtureSession:
    """Values hand-derived from etl/tests/fixtures/generate_fixtures.py (scored trials only; practice rows ignored)."""

    @pytest.fixture
    def s(self, loaded):
        assert len(loaded) == 1
        return score_session(loaded[0])

    def test_p1_two_back_dprime_uses_the_log_linear_sdt_module(self, s):
        # positions 3-6: targets at 3 and 6 (2 hits), non-targets at 4 and 5 (0 false alarms)
        # H = 2.5/3, FA = 0.5/3 -> d' = 1.934843 (scipy), c = 0
        assert s["P1_hits"] == 2 and s["P1_n_targets"] == 2
        assert s["P1_false_alarms"] == 0 and s["P1_n_nontargets"] == 2
        assert s["P1_dprime"] == pytest.approx(1.934843, abs=1e-6)
        assert s["P1_criterion"] == pytest.approx(0.0, abs=1e-12)

    def test_p2_recall_proportion_is_pooled_over_the_scored_lists(self, s):
        assert (s["P2_n_correct"], s["P2_n_words"]) == (4, 8)
        assert s["P2_recall_proportion"] == 0.5

    def test_s1_stroop_interference_and_accuracy(self, s):
        # congruent RT 620, 620; incongruent RT 700 -> interference 80 ms
        assert s["S1_mean_congruent_rt"] == 620
        assert s["S1_mean_incongruent_rt"] == 700
        assert s["S1_stroop_interference"] == 80
        assert s["stroop_congruent_accuracy"] == 1.0
        assert s["stroop_accuracy_interference"] == 0.0

    def test_s2_posner_validity_effect(self, s):
        # valid RT 365, 395 (mean 380); invalid RT 380 -> effect 0
        assert s["S2_mean_valid_rt"] == 380
        assert s["S2_mean_invalid_rt"] == 380
        assert s["S2_posner_validity_effect"] == 0

    def test_s3_threshold_comes_from_the_threshold_row(self, s):
        assert s["S3_threshold_level"] == -11.5
        assert s["S3_threshold_contrast"] == pytest.approx(0.266)
        assert s["S3_used_fallback"] is False

    def test_s4_yes_no_dprime(self, s):
        # 4 trials: 2 signal (both yes), 2 noise (both no): H = 2.5/3, FA = 0.5/3
        assert s["S4_dprime"] == pytest.approx(1.934843, abs=1e-6)
        assert s["S4_criterion"] == pytest.approx(0.0, abs=1e-12)

    def test_covariates_for_the_models(self, s):
        assert (s["participant_code"], s["session_number"]) == ("K7M2QX9P", 3)
        assert (s["hours_slept"], s["kss"], s["caffeine"]) == (7.5, 4, 0)
        assert s["timestamp"] == "2026-11-18T15:30:00.000Z"

    def test_serial_position_curve_is_per_scored_list(self, s):
        assert s["recall_serial_position"] == [1.0, 1.0, 0.0, 0.0]


class TestScoringRules:
    def test_practice_rows_never_enter_scores(self):
        s = make_session()
        noisy = score_session(s)
        clean = score_session(make_session(practice_noise=False))
        for k in ("S1_stroop_interference", "S2_posner_validity_effect", "P2_recall_proportion", "P1_dprime"):
            assert noisy[k] == clean[k]

    def test_rt_trimming_and_correct_only_apply_to_rt_scores(self):
        s = make_session(stroop=0)
        base = len(s["trials"])
        rows = [("congruent", 600, 1), ("congruent", 100, 1), ("congruent", 700, 0), ("incongruent", 800, 1), ("incongruent", 2600, 1), ("incongruent", 900, 1)]
        for k, (cond, rt, ok) in enumerate(rows):
            s["trials"].append(trial("stroop", base + k, practice=0, rt=rt, correct=ok, condition=cond))
        r = score_session(s)
        assert r["S1_mean_congruent_rt"] == 600  # 100 ms trimmed, error dropped
        assert r["S1_mean_incongruent_rt"] == 850  # 2600 ms trimmed
        assert r["S1_stroop_interference"] == 250

    def test_missing_scores_are_none_not_zero(self):
        s = make_session(posner=0, stroop=0, nback=0, yesno=0, lists=0, summary=False, threshold=False)
        r = score_session(s)
        for k in ("S1_stroop_interference", "S2_posner_validity_effect", "P1_dprime", "S4_dprime", "P2_recall_proportion", "S3_threshold_level"):
            assert r[k] is None


def test_serial_position_function():
    assert serial_position([[True, True, False], [True, False, False]]) == [1.0, 0.5, 0.0]
    assert serial_position([]) == []


class TestDatabaseScoring:
    def test_loads_every_session_with_questionnaire_and_trials(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json")
        insert_fixture(db, "K7M2QX9P_session11.json")
        sessions = load_sessions(db)
        assert [s["session_number"] for s in sessions] == [3, 11]
        assert sessions[0]["questionnaire"]["hours_slept"] == 7.5
        assert len(sessions[0]["trials"]) == 106
        assert sessions[0]["trials"][0]["data"] is not None

    def test_score_database_flags_exclusions_and_h1_eligibility(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json", session_number=1, is_pilot=1)
        insert_fixture(db, "K7M2QX9P_session3.json", session_number=3)
        rows = score_database(db, expected=FIXTURE_EXPECTED)
        by_n = {r["session_number"]: r for r in rows}
        assert by_n[1]["excluded"] is True and "smoke" in by_n[1]["excluded_reason"]
        assert by_n[3]["excluded"] is False and by_n[3]["h1_eligible"] is True
        assert by_n[3]["P1_dprime"] == pytest.approx(1.934843, abs=1e-6)

    def test_default_expected_counts_exclude_the_tiny_fixture_sessions_as_incomplete(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json")
        (row,) = score_database(db)
        assert row["excluded"] is True and "missing posner" in row["excluded_reason"]


class TestApplyExclusions:
    def reason(self, db, n):
        return db.execute("SELECT excluded_reason FROM sessions WHERE session_number = ?", (n,)).fetchone()[0]

    def test_writes_automatic_reasons_into_excluded_reason(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json", session_number=1, is_pilot=1)
        insert_fixture(db, "K7M2QX9P_session3.json", session_number=3)
        summary = ex.apply_exclusions(db, expected=FIXTURE_EXPECTED)
        assert self.reason(db, 1).startswith("auto: smoke")
        assert self.reason(db, 3) is None
        assert summary["excluded"] == 1 and summary["kept"] == 1

    def test_is_idempotent_and_clears_reasons_that_no_longer_apply(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json", session_number=3)
        ex.apply_exclusions(db)  # default design counts: fixture is incomplete
        assert self.reason(db, 3).startswith("auto: ")
        first = self.reason(db, 3)
        ex.apply_exclusions(db)
        assert self.reason(db, 3) == first
        ex.apply_exclusions(db, expected=FIXTURE_EXPECTED)
        assert self.reason(db, 3) is None

    def test_manual_reasons_are_never_overwritten(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json", session_number=3)
        db.execute("UPDATE sessions SET excluded_reason = 'manual: hardware crash'")
        db.commit()
        summary = ex.apply_exclusions(db)  # would otherwise write an automatic reason
        assert self.reason(db, 3) == "manual: hardware crash"
        assert summary["manual_kept"] == [("K7M2QX9P", 3)]


def nback_session(rows):
    """A session whose scored 2-back trials are exactly `rows`: (position, type, responded, rt)."""
    s = make_session(nback=0)
    base = len(s["trials"])
    for k, (position, typ, responded, rt) in enumerate(rows):
        s["trials"].append(trial("nback", base + k, practice=0, rt=rt, position=position, type=typ, isTarget=typ == "target", responded=responded))
    return s


class TestTwoBackScoring:
    def test_a_response_counts_only_within_the_2000_ms_window_from_letter_onset(self):
        s = nback_session([
            (3, "target", True, 2000),      # exactly 2,000 ms: a hit
            (4, "target", True, 2001),      # too late: a miss
            (5, "nontarget", True, 2000),   # a false alarm
            (6, "nontarget", True, 2500),   # too late: a correct rejection
            (7, "nontarget", False, None),
        ])
        r = score_session(s)
        assert (r["P1_hits"], r["P1_n_targets"]) == (1, 2)
        assert (r["P1_false_alarms"], r["P1_n_nontargets"]) == (1, 3)

    def test_positions_1_and_2_are_not_scored_even_if_responded_to(self):
        s = nback_session([(1, "start", True, 400), (2, "start", True, 500), (3, "target", True, 700), (4, "nontarget", False, None)])
        r = score_session(s)
        assert (r["P1_n_targets"], r["P1_n_nontargets"]) == (1, 1)
        assert r["P1_false_alarms"] == 0

    def test_lures_are_non_targets_and_their_false_alarms_are_reported(self):
        s = nback_session([
            (3, "target", True, 700), (4, "lure1", True, 600), (5, "lure3", False, None), (6, "nontarget", True, 800), (7, "lure1", False, None),
        ])
        r = score_session(s)
        assert r["P1_n_nontargets"] == 4
        assert r["P1_false_alarms"] == 2
        assert r["P1_lure_false_alarms"] == 1


class TestYesNoReporting:
    def test_trials_without_a_response_are_counted(self):
        s = make_session(yesno=0)
        base = len(s["trials"])
        for k, (sig, yes, response) in enumerate([(True, True, "f"), (False, False, "j"), (True, False, None), (False, False, None)]):
            t = trial("yesno", base + k, practice=0, rt=600 if response else None, correct=int(sig == yes), response=response, isSignal=sig, respondedYes=yes)
            s["trials"].append(t)
        r = score_session(s)
        assert r["S4_n_no_response"] == 2


class TestDataWarnings:
    def test_a_clean_session_has_none(self):
        assert data_warnings(make_session(), FIXTURE_EXPECTED) == []

    def test_more_trials_than_the_design_count_is_a_warning_not_an_exclusion(self):
        w = data_warnings(make_session(posner=4), FIXTURE_EXPECTED)
        assert any("posner" in x and "more than" in x for x in w)

    def test_recall_scores_that_disagree_with_the_recalled_flags_or_summary_are_flagged(self):
        s = make_session()
        next(t for t in s["trials"] if t["task"] == "recall" and t["practice"] == 0)["data"]["nCorrect"] = 3  # flags say 2
        assert any("recall" in x for x in data_warnings(s, FIXTURE_EXPECTED))
        s = make_session()
        next(t for t in s["trials"] if t["task"] == "recall_summary" and t["practice"] == 0)["data"]["nCorrect"] = 99
        assert any("summary" in x for x in data_warnings(s, FIXTURE_EXPECTED))

    def test_p2_consistency_flag(self):
        assert score_session(make_session())["P2_consistent"] is True
        s = make_session()
        next(t for t in s["trials"] if t["task"] == "recall" and t["practice"] == 0)["data"]["nCorrect"] = 3
        assert score_session(s)["P2_consistent"] is False
        assert score_session(make_session(lists=0, summary=False))["P2_consistent"] is None

    def test_score_database_reports_the_warnings_and_uses_the_single_h1_definition(self, db):
        insert_fixture(db, "K7M2QX9P_session3.json")
        db.execute("UPDATE sessions SET excluded_reason = 'manual: hardware crash'")
        db.commit()
        (row,) = score_database(db, expected=FIXTURE_EXPECTED)
        assert row["warnings"] == []
        assert row["excluded"] is True and row["excluded_reason"] == "manual: hardware crash"
        assert row["h1_eligible"] is False
