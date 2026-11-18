from mindbench_dashboard.metrics import explain_gaps, partial_files, session_gaps


class TestSessionGaps:
    def test_lists_missing_numbers_from_the_first_confirmatory_session_to_the_highest(self):
        assert session_gaps([3, 4, 6, 9]) == [5, 7, 8]

    def test_smoke_test_slots_1_and_2_are_optional_and_never_gaps(self):
        assert session_gaps([1, 3, 5]) == [4]
        assert session_gaps([3, 4]) == []
        assert session_gaps([5]) == [3, 4]

    def test_nothing_loaded_means_no_gaps(self):
        assert session_gaps([]) == []

    def test_the_numbers_are_returned_sorted_and_deduplicated(self):
        assert session_gaps([9, 3, 3, 5]) == [4, 6, 7, 8]


class TestPartialFiles:
    def test_lists_partial_uploads_with_their_participant_code_and_session_number(self, raw_dir):
        for name in ("K7M2QX9P_session4.partial.json", "K7M2QX9P_session3.json", "notes.txt", "weird.partial.json"):
            (raw_dir / name).write_text("[]")
        r = partial_files(raw_dir)
        assert r["partial"] == [{"filename": "K7M2QX9P_session4.partial.json", "participant_code": "K7M2QX9P", "session_number": 4}]
        assert r["unparsed"] == ["weird.partial.json"]

    def test_sorted_by_session_number(self, raw_dir):
        for n in (8, 5, 6):
            (raw_dir / f"K7M2QX9P_session{n}.partial.json").write_text("[]")
        assert [p["session_number"] for p in partial_files(raw_dir)["partial"]] == [5, 6, 8]

    def test_a_missing_folder_is_not_an_error(self, tmp_path):
        assert partial_files(tmp_path / "nope") == {"partial": [], "unparsed": []}


class TestExplainGaps:
    def test_each_gap_is_explained_by_what_is_known_about_it(self):
        partials = [{"filename": "K7M2QX9P_session4.partial.json", "participant_code": "K7M2QX9P", "session_number": 4}]
        failed = [("K7M2QX9P_session5.json", "row 3: ...")]
        rows = explain_gaps([4, 5, 7], partials, failed)
        assert [(r["session_number"], r["status"]) for r in rows] == [(4, "partial_upload"), (5, "failed_validation"), (7, "no_file")]

    def test_a_failed_file_takes_precedence_over_a_partial_one(self):
        partials = [{"filename": "K7M2QX9P_session5.partial.json", "participant_code": "K7M2QX9P", "session_number": 5}]
        rows = explain_gaps([5], partials, [("K7M2QX9P_session5.json", "bad")])
        assert rows[0]["status"] == "failed_validation"

    def test_status_text_is_human_readable(self):
        rows = explain_gaps([7], [], [])
        assert "no file" in rows[0]["detail"].lower()
