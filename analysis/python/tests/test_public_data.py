"""MB-24: the de-identified public export (data_public/), the de-identification check, and reproducing results from it.

Simulated data only. Raw participant codes below are invented. The tests describe what must never reach data_public/:
participant codes, free text, and timestamps finer than the date.
"""
import csv
import datetime as dt
import inspect
import random
import re
import sqlite3
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from mindbench import public_data as pd_
from mindbench import scoring, synthesis, writeup
from conftest import FIXTURE_EXPECTED, SCHEMA, make_session

OWNER, FRIEND_A, FRIEND_B = "K7M2QX9P", "F3R9TT2A", "H8N4WW6B"
LA = ZoneInfo("America/Los_Angeles")
WORDS = ["zebrawood", "quillfeather", "marmalade", "tangerine"]  # typed free text must never appear in the export


def utc_iso(local):
    return local.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def insert_session(conn, code, n, local, rng, is_pilot=0, excluded_reason=None, hours=7.0, **kw):
    s = make_session(posner=6, stroop=6, nback=6, yesno=4, lists=2, hours=hours, **kw)
    for t in s["trials"]:  # simulated RTs: Stroop interference ~100 ms, Posner validity effect ~50 ms
        if t["practice"] != 0:
            continue
        if t["task"] == "stroop":
            t["rt"] = (500 if t["data"]["condition"] == "congruent" else 600) + rng.gauss(0, 20)
        if t["task"] == "posner":
            t["rt"] = (400 if t["data"]["valid"] else 450) + rng.gauss(0, 20)
        if t["task"] == "recall":
            t["data"]["listWords"] = WORDS
            t["response"] = " ".join(WORDS)
    conn.execute("INSERT OR IGNORE INTO participants (participant_code) VALUES (?)", (code,))
    conn.execute(
        "INSERT INTO sessions (participant_code, session_number, is_pilot, excluded_reason, timestamp, timezone, user_agent, screen_width, screen_height, jspsych_version, source_filename) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (code, n, is_pilot, excluded_reason, utc_iso(local), "America/Los_Angeles", "Mozilla/5.0 (Macintosh) SimBrowser", 1440, 900, "8.4.0", f"{code}_session{n}.json"),
    )
    q = s["questionnaire"]
    conn.execute("INSERT INTO questionnaire VALUES (?,?,?,?,?,?,?,?)",
                 (code, n, q["hours_slept"], q["bed_time"], q["wake_time"], q["kss"], q["caffeine"], "laptop"))
    for t in s["trials"]:
        conn.execute("INSERT INTO trials VALUES (?,?,?,?,?,?,?,?,?)",
                     (code, n, t["trial_index"], t["task"], t["practice"], t["rt"], t["response"], t["correct"], __import__("json").dumps(t["data"])))
    conn.commit()


@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "private.sqlite")
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA.read_text())
    rng = random.Random(7)
    n = 0
    for d in range(6):  # six days: AM 08:15 and PM 18:30, owner; sessions 1-2 are smoke tests
        for hh, mm in ((8, 15), (18, 30)):
            n += 1
            insert_session(c, OWNER, n, dt.datetime(2026, 12, 1 + d, hh, mm, tzinfo=LA), rng, is_pilot=1 if n <= 2 else 0,
                           hours=5.5 + (d % 3))
    insert_session(c, OWNER, 13, dt.datetime(2026, 12, 8, 1, 30, tzinfo=LA), rng)  # 01:30 local: belongs to 7 December, PM
    insert_session(c, OWNER, 14, dt.datetime(2026, 12, 9, 8, 0, tzinfo=LA), rng, excluded_reason="had a headache, skipped half of it")  # manual free text
    for i in range(1, 4):
        insert_session(c, FRIEND_A, i, dt.datetime(2026, 12, 10 + i, 9, 0, tzinfo=LA), rng)
        insert_session(c, FRIEND_B, i, dt.datetime(2026, 12, 10 + i, 19, 0, tzinfo=LA), rng)
    yield c
    c.close()


def export(conn, tmp_path, consent=None, name="data_public"):
    out = tmp_path / name
    report = pd_.export_public(conn, out, owners=[OWNER], consent=consent or {}, expected=FIXTURE_EXPECTED)
    return out, report


def read(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rewrite(path, rows, fieldnames=None):
    fieldnames = fieldnames or list(rows[0])
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


@pytest.fixture
def good(conn, tmp_path):
    out, _ = export(conn, tmp_path, consent={FRIEND_A: True})
    return out


# ------------------------------------------------------------------------------ the de-identification check
class TestDeidCheck:
    def test_a_clean_export_passes(self, good):
        assert pd_.check_public_dir(good, known_codes=[OWNER, FRIEND_A, FRIEND_B]) == []

    def test_a_participant_code_in_the_id_column_is_rejected(self, good):
        rows = read(good / "sessions.csv")
        rows[0]["pid"] = OWNER
        rewrite(good / "sessions.csv", rows)
        problems = pd_.check_public_dir(good)
        assert any("participant code" in p or "pid" in p for p in problems), problems

    def test_a_code_shaped_value_is_caught_even_without_a_list_of_known_codes(self, good):
        rows = read(good / "trials.csv")
        rows[0]["condition"] = "Q4W8ZK2M"
        rewrite(good / "trials.csv", rows)
        assert pd_.check_public_dir(good)

    def test_a_known_code_hidden_in_any_cell_or_file_name_is_rejected(self, good):
        rows = read(good / "sessions.csv")
        rows[1]["exclusion_rules"] = f"see {OWNER.lower()}"
        rewrite(good / "sessions.csv", rows)
        assert any("participant code" in p for p in pd_.check_public_dir(good, known_codes=[OWNER]))
        (good / f"{FRIEND_A}_notes.csv").write_text("a\n1\n")
        assert any(FRIEND_A in p for p in pd_.check_public_dir(good, known_codes=[FRIEND_A]))

    def test_a_free_text_column_is_rejected(self, good):
        rows = read(good / "sessions.csv")
        for r in rows:
            r["notes"] = "felt tired today"
        rewrite(good / "sessions.csv", rows)
        assert any("notes" in p for p in pd_.check_public_dir(good))

    def test_free_text_inside_an_allowed_column_is_rejected(self, good):
        rows = read(good / "sessions.csv")
        rows[0]["exclusion_rules"] = "had a headache, skipped half of it"
        rewrite(good / "sessions.csv", rows)
        assert pd_.check_public_dir(good)
        rows = read(good / "trials.csv")
        rows[0]["condition"] = "typed this word"
        rewrite(good / "trials.csv", rows)
        assert any("condition" in p for p in pd_.check_public_dir(good))

    @pytest.mark.parametrize("value", ["2026-12-01T08:15:00", "2026-12-01 08:15", "2026-12-01T16:15:00.000Z", "08:15", "1764605700000"])
    def test_a_timestamp_finer_than_the_date_is_rejected(self, good, value):
        rows = read(good / "sessions.csv")
        rows[0]["date"] = value
        rewrite(good / "sessions.csv", rows)
        assert any("date" in p for p in pd_.check_public_dir(good)), value

    @pytest.mark.parametrize("column", ["start_time", "timestamp", "bed_time", "wake_time", "time_elapsed", "user_agent"])
    def test_time_and_browser_columns_are_rejected(self, good, column):
        rows = read(good / "sessions.csv")
        for r in rows:
            r[column] = "x"
        rewrite(good / "sessions.csv", rows)
        assert any(column in p for p in pd_.check_public_dir(good)), column

    def test_a_clock_time_in_any_cell_is_rejected(self, good):
        rows = read(good / "sessions.csv")
        rows[2]["exclusion_rules"] = "23:30"
        rewrite(good / "sessions.csv", rows)
        assert pd_.check_public_dir(good)

    def test_the_period_column_only_holds_am_or_pm(self, good):
        rows = read(good / "sessions.csv")
        rows[0]["period"] = "08:15"
        rewrite(good / "sessions.csv", rows)
        assert any("period" in p for p in pd_.check_public_dir(good))

    def test_files_that_are_not_part_of_the_release_are_rejected(self, good):
        (good / "mindbench.sqlite").write_bytes(b"x")
        (good / "raw_session.json").write_text("{}")
        problems = pd_.check_public_dir(good)
        assert any("mindbench.sqlite" in p for p in problems) and any("raw_session.json" in p for p in problems)

    def test_a_missing_required_file_is_a_problem(self, good):
        (good / "trials.csv").unlink()
        assert any("trials.csv" in p for p in pd_.check_public_dir(good))


# ------------------------------------------------------------------------------ the export
class TestExport:
    def test_no_participant_code_or_typed_word_or_clock_time_appears_in_any_output_file(self, conn, tmp_path):
        out, _ = export(conn, tmp_path, consent={FRIEND_A: True, FRIEND_B: True})
        text = "".join(p.read_text(encoding="utf-8") for p in out.iterdir())
        for secret in (OWNER, FRIEND_A, FRIEND_B, *WORDS, "headache", "SimBrowser", "23:30", "07:00", "laptop"):
            assert secret not in text, secret
        assert not re.search(r"\d{1,2}:\d{2}", text)
        assert not re.search(r"\d{4}-\d{2}-\d{2}[T ]", text)
        assert pd_.check_public_dir(out, known_codes=[OWNER, FRIEND_A, FRIEND_B]) == []

    def test_the_export_refuses_to_leave_a_file_that_fails_the_check(self, conn, tmp_path, monkeypatch):
        monkeypatch.setattr(pd_, "_pid_label", lambda i: "K7M2QX9P")  # simulate a bug that leaks a code-shaped id
        with pytest.raises(pd_.DeidError):
            export(conn, tmp_path)

    def test_pseudonyms_are_assigned_in_a_fixed_order_and_the_map_stays_out_of_the_release(self, conn, tmp_path):
        out, report = export(conn, tmp_path, consent={FRIEND_A: True})
        assert sorted(report["pid_map"].values()) == ["P01", "P02"]
        assert set(report["pid_map"]) == {OWNER, FRIEND_A}
        assert not any("pid_map" in p.name for p in out.iterdir())
        _, again = export(conn, tmp_path, consent={FRIEND_A: True}, name="again")
        assert again["pid_map"] == report["pid_map"]

    def test_the_owners_own_data_is_released_but_a_friends_data_needs_the_consent_flag(self, conn, tmp_path):
        out, report = export(conn, tmp_path)
        assert {r["pid"] for r in read(out / "sessions.csv")} == {"P01"}
        assert report["omitted_participants"] == 2
        out, report = export(conn, tmp_path, consent={FRIEND_A: True}, name="a")
        assert {r["pid"] for r in read(out / "sessions.csv")} == {"P01", "P02"}
        assert report["omitted_participants"] == 1
        out, _ = export(conn, tmp_path, consent={FRIEND_A: True, FRIEND_B: True}, name="b")
        assert len({r["pid"] for r in read(out / "sessions.csv")}) == 3

    @pytest.mark.parametrize("flag", [False, None, "yes", "true", 1, 0, "", "False"])
    def test_only_a_literal_true_counts_as_consent(self, conn, tmp_path, flag):
        out, _ = export(conn, tmp_path, consent={FRIEND_A: flag, FRIEND_B: flag})
        assert {r["pid"] for r in read(out / "sessions.csv")} == {"P01"}

    def test_a_friend_who_withheld_consent_leaves_no_trace_in_the_trials_either(self, conn, tmp_path):
        out, report = export(conn, tmp_path, consent={FRIEND_A: True})
        assert {r["pid"] for r in read(out / "trials.csv")} <= {"P01", "P02"}
        assert len(read(out / "participants.csv")) == 2

    def test_the_date_and_period_follow_the_preregistered_day_rule(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        by = {int(r["session_number"]): r for r in read(out / "sessions.csv")}
        assert (by[3]["date"], by[3]["period"]) == ("2026-12-02", "AM")
        assert (by[4]["date"], by[4]["period"]) == ("2026-12-02", "PM")
        assert (by[13]["date"], by[13]["period"]) == ("2026-12-07", "PM")  # 01:30 local belongs to the previous day (D2)
        assert all(re.fullmatch(r"\d{4}-\d{2}-\d{2}", r["date"]) for r in by.values())

    def test_exclusions_are_coded_and_manual_text_never_leaves(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        by = {int(r["session_number"]): r for r in read(out / "sessions.csv")}
        assert by[1]["is_pilot"] == "1" and by[1]["excluded"] == "1" and "smoke_test" in by[1]["exclusion_rules"]
        assert by[14]["excluded"] == "1" and "manual" in by[14]["exclusion_rules"]
        assert by[3]["excluded"] == "0" and by[3]["exclusion_rules"] == ""

    def test_sleep_hours_are_released_but_bed_and_wake_times_are_not(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        header = list(read(out / "sessions.csv")[0])
        assert "hours_slept" in header and "kss" in header and "caffeine" in header
        assert not {"bed_time", "wake_time", "device", "timezone", "user_agent", "screen_width", "source_filename"} & set(header)

    def test_scores_in_the_export_equal_the_scores_computed_from_the_private_database(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        private = {(r["session_number"]): r for r in scoring.score_database(conn, FIXTURE_EXPECTED) if r["participant_code"] == OWNER}
        for r in read(out / "sessions.csv"):
            p = private[int(r["session_number"])]
            assert float(r["S1_stroop_interference"]) == pytest.approx(p["S1_stroop_interference"])
            assert float(r["S2_posner_validity_effect"]) == pytest.approx(p["S2_posner_validity_effect"])

    def test_trials_are_scored_rows_only_with_a_fixed_condition_vocabulary_and_no_response_text(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        rows = read(out / "trials.csv")
        assert rows and {r["task"] for r in rows} <= {"stroop", "posner", "nback", "yesno"}
        assert {r["condition"] for r in rows} <= {"congruent", "incongruent", "valid", "invalid", "target", "nontarget", "lure1", "lure3", "start",
                                                  "signal", "noise"}
        assert set(rows[0]) == {"pid", "session_number", "trial_index", "task", "condition", "rt", "correct"}

    def test_an_empty_consent_map_and_no_owner_exports_nothing(self, conn, tmp_path):
        out = tmp_path / "none"
        report = pd_.export_public(conn, out, owners=[], consent={}, expected=FIXTURE_EXPECTED)
        assert read(out / "sessions.csv") == [] and report["omitted_participants"] == 3

    def test_the_export_never_writes_into_the_tracked_folder_by_default_without_being_asked(self):
        sig = inspect.signature(pd_.export_public)
        assert sig.parameters["out_dir"].default is inspect.Parameter.empty


# ------------------------------------------------------------------------------ the analysis runs from data_public/
class TestReproduce:
    def private_mc(self, conn):
        """Descriptive manipulation-check numbers computed independently from the private database."""
        rows = [r for r in scoring.score_database(conn, FIXTURE_EXPECTED)
                if r["participant_code"] == OWNER and not r["excluded"]]
        return rows

    def test_it_never_opens_the_private_database(self):
        src = inspect.getsource(pd_.reproduce)
        for forbidden in ("sqlite3", "score_database", "load_sessions", "participant_code"):
            assert forbidden not in src

    def test_the_manipulation_check_estimates_equal_those_computed_from_the_private_database(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        res = pd_.reproduce(out)["results"]
        rows = self.private_mc(conn)
        by_day = {}
        for r in rows:
            by_day.setdefault(pd_.study_day(r["timestamp"], "America/Los_Angeles"), []).append(r["S1_stroop_interference"])
        day_means = [sum(v) / len(v) for v in by_day.values()]
        assert res["MC:S1"]["frequentist"]["estimate"] == pytest.approx(sum(day_means) / len(day_means))
        assert 90 < res["MC:S1"]["frequentist"]["estimate"] < 110
        assert 40 < res["MC:S2"]["frequentist"]["estimate"] < 60

    def test_smoke_tests_and_excluded_sessions_are_not_used_and_the_counts_are_exact(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        s = pd_.reproduce(out)["summary"]
        # 14 sessions; sessions 1-2 are smoke tests and session 14 has a manual exclusion; session 13 (01:30 local) is kept
        assert (s["n_sessions"], s["n_included"], s["n_participants"]) == (14, 11, 1)
        assert s["n_days"] == 6  # included days: 2-6 December plus 7 December (the 01:30 session); 1 December holds only smoke tests

    def test_the_results_fit_the_synthesis_table_and_the_confirmatory_rows_stay_pending(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        rows = {r["id"]: r for r in synthesis.build_results_table(pd_.reproduce(out)["results"])}
        assert rows["MC:S1"]["status"] == "complete" and rows["MC:S2"]["status"] == "complete"
        for rid in ("H1:P1", "H1:P2", "H2:P1", "H2:P2", "H3:S1", "S3"):
            assert rows[rid]["status"] == "not yet run", rid  # nothing is invented for analyses that are not run here

    def test_the_paper_built_from_the_reproduced_results_traces_every_number(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        results = pd_.reproduce(out)["results"]
        est = results["MC:S1"]["frequentist"]["estimate"]
        template = (writeup.ROOT / "docs" / "writeup" / "paper_template.md").read_text(encoding="utf-8")
        marked = writeup.build_paper(template, writeup.collect_values(results), mark=True)
        assert writeup.untraced_numbers(marked) == []
        assert f"est {est:g}" in writeup.strip_marks(marked)
        empty = writeup.collect_values({})
        filled = writeup.collect_values(results)
        for key in ("power.holm_r43", "power.holm_r30", "power.detectable_r", "power.sims"):
            assert empty[key] == filled[key]  # the placeholder numbers that come from the power simulation do not move

    def test_the_same_data_gives_the_same_results(self, conn, tmp_path):
        out, _ = export(conn, tmp_path)
        assert pd_.reproduce(out) == pd_.reproduce(out)

    def test_a_dataset_that_fails_the_deid_check_is_not_analysed(self, good):
        rows = read(good / "sessions.csv")
        rows[0]["pid"] = OWNER
        rewrite(good / "sessions.csv", rows)
        with pytest.raises(pd_.DeidError):
            pd_.reproduce(good)

    def test_a_friends_consented_data_enters_the_same_analysis(self, conn, tmp_path):
        out, _ = export(conn, tmp_path, consent={FRIEND_A: True})
        assert pd_.reproduce(out)["summary"]["n_participants"] == 2


class TestCommandLine:
    def test_export_check_and_reproduce_run_from_the_command_line(self, conn, tmp_path, capsys):
        conn.commit()
        db = tmp_path / "private.sqlite"
        out, consent = tmp_path / "pub", tmp_path / "consent.json"
        consent.write_text('{"%s": true}' % FRIEND_A)
        assert pd_.main(["export", "--db", str(db), "--out", str(out), "--owner", OWNER, "--consent", str(consent),
                         "--fixture-expected", "--map", str(tmp_path / "pid_map.json")]) == 0
        assert pd_.main(["check", "--dir", str(out)]) == 0
        assert pd_.main(["reproduce", "--dir", str(out)]) == 0
        assert "MC:S1" in capsys.readouterr().out
        assert (tmp_path / "pid_map.json").is_file()

    def test_check_exits_nonzero_on_a_problem(self, good):
        (good / "raw.json").write_text("{}")
        assert pd_.main(["check", "--dir", str(good)]) == 1
