"""MB-22: synthesis table, preregistration coverage, deviations log. No real data; nothing is invented."""
import inspect
import re
from pathlib import Path

import pytest

from mindbench import synthesis as syn

ROOT = Path(__file__).resolve().parents[3]
PREREG = (ROOT / "docs" / "design" / "prereg_draft.md").read_text(encoding="utf-8")
DEVIATIONS = ROOT / "docs" / "design" / "deviations.md"


def ids():
    return [a["id"] for a in syn.ANALYSES]


# ------------------------------------------------------------------------------ coverage of the preregistration
class TestCoverage:
    def test_every_hypothesis_and_outcome_id_in_the_prereg_appears_in_the_results_table(self):
        tokens = set(re.findall(r"\b(H[1-3]|P[1-2]|S[1-5])\b", PREREG))
        assert {"H1", "H2", "H3", "P1", "P2", "S1", "S5"} <= tokens
        rows = syn.build_results_table({})
        covered = set()
        for r in rows:
            covered |= set(re.findall(r"H[1-3]|P[1-2]|S[1-5]", r["id"]))
        assert tokens <= covered, sorted(tokens - covered)

    def test_the_helper_finds_what_is_missing(self):
        assert syn.missing_prereg_ids(PREREG, syn.build_results_table({})) == []
        assert syn.missing_prereg_ids(PREREG + " and also S9", syn.build_results_table({})) == []  # S9 is not an analysis ID pattern
        rows = [r for r in syn.build_results_table({}) if "H3" not in r["id"]]
        assert "H3" in syn.missing_prereg_ids(PREREG, rows)

    def test_every_analysis_points_at_a_section_that_exists_in_the_prereg(self):
        for a in syn.ANALYSES:
            assert a["anchor"].lower() in PREREG.lower(), a

    def test_ids_are_unique(self):
        assert len(ids()) == len(set(ids()))

    def test_every_planned_source_is_a_known_unit(self):
        for a in syn.ANALYSES:
            assert set(a["sources"]) <= set(syn.SOURCES)


# ------------------------------------------------------------------------------ the table
class TestTable:
    def test_with_no_results_every_row_is_not_yet_run_and_holds_no_numbers(self):
        rows = syn.build_results_table({})
        assert len(rows) == len(syn.ANALYSES)
        for r in rows:
            assert r["status"] == "not yet run"
            for src in r["sources"].values():
                assert src["conclusion"] == "pending" and src["estimate"] is None and src["interval"] is None

    def test_only_h1_and_h2_rows_are_confirmatory_and_everything_else_is_labelled_exploratory(self):
        rows = {r["id"]: r for r in syn.build_results_table({})}
        confirmatory = {i for i, r in rows.items() if r["tier"] == "confirmatory"}
        assert confirmatory == {"H1:P1", "H1:P2", "H2:P1", "H2:P2"}
        assert all(r["tier"] in ("confirmatory", "exploratory", "descriptive") for r in rows.values())
        assert rows["H3:S1"]["tier"] == "exploratory" and rows["S3"]["tier"] == "exploratory"

    def test_results_are_filled_in_per_source_and_the_status_follows(self):
        res = {"H1:P1": {"frequentist": {"conclusion": "supported", "estimate": 0.12, "interval": (0.03, 0.21), "direction": "positive"}}}
        row = {r["id"]: r for r in syn.build_results_table(res)}["H1:P1"]
        assert row["sources"]["frequentist"]["estimate"] == 0.12
        assert row["status"] == "partial"  # Bayesian result still pending

    def test_status_is_complete_when_every_planned_source_has_reported(self):
        a = next(x for x in syn.ANALYSES if x["id"] == "H3:S1")
        res = {"H3:S1": {s: {"conclusion": "cannot tell", "direction": "unclear"} for s in a["sources"]}}
        assert {r["id"]: r for r in syn.build_results_table(res)}["H3:S1"]["status"] == "complete"

    def test_unknown_analysis_or_source_is_rejected(self):
        with pytest.raises(ValueError, match="unknown analysis"):
            syn.build_results_table({"H9:P1": {}})
        with pytest.raises(ValueError, match="source"):
            syn.build_results_table({"H1:P1": {"tarot": {"conclusion": "supported"}}})

    def test_conclusions_come_from_a_fixed_vocabulary(self):
        with pytest.raises(ValueError, match="conclusion"):
            syn.build_results_table({"H1:P1": {"frequentist": {"conclusion": "obviously true"}}})

    def test_the_decision_for_a_confirmatory_row_comes_from_the_frequentist_result_only(self):
        res = {"H1:P1": {"bayes": {"conclusion": "supported", "direction": "positive"},
                         "frequentist": {"conclusion": "not supported", "direction": "none"}}}
        row = {r["id"]: r for r in syn.build_results_table(res)}["H1:P1"]
        assert row["decision"] == "not supported"

    def test_a_bayesian_only_result_never_becomes_a_confirmatory_decision(self):
        res = {"H1:P1": {"bayes": {"conclusion": "supported", "direction": "positive"}}}
        row = {r["id"]: r for r in syn.build_results_table(res)}["H1:P1"]
        assert row["decision"] == "pending"

    def test_a_wrong_direction_h1_result_is_not_supported(self):
        res = {"H1:P1": {"frequentist": {"conclusion": "supported", "direction": "negative", "estimate": -0.1}}}
        row = {r["id"]: r for r in syn.build_results_table(res)}["H1:P1"]
        assert row["decision"] == "not supported (wrong direction)"

    def test_h2_is_two_sided_so_a_significant_negative_difference_is_supported(self):
        res = {"H2:P1": {"frequentist": {"conclusion": "supported", "direction": "negative"}}}
        assert {r["id"]: r for r in syn.build_results_table(res)}["H2:P1"]["decision"] == "supported"

    def test_exploratory_decisions_are_labelled_as_such(self):
        res = {"S3": {"frequentist": {"conclusion": "supported", "direction": "negative"}}}
        assert {r["id"]: r for r in syn.build_results_table(res)}["S3"]["decision"] == "exploratory: supported"


class TestConvergence:
    def row(self, **sources):
        return {r["id"]: r for r in syn.build_results_table({"H1:P1": sources})}["H1:P1"]

    def test_incomplete_until_every_planned_source_reports(self):
        assert self.row(frequentist={"conclusion": "supported", "direction": "positive"})["convergence"] == "incomplete"

    def test_converge_when_directions_agree(self):
        r = self.row(frequentist={"conclusion": "supported", "direction": "positive"}, bayes={"conclusion": "supported", "direction": "positive"})
        assert r["convergence"] == "converge"

    def test_diverge_when_directions_differ(self):
        r = self.row(frequentist={"conclusion": "supported", "direction": "positive"}, bayes={"conclusion": "not supported", "direction": "none"})
        assert r["convergence"] == "diverge"


# ------------------------------------------------------------------------------ rendering
class TestRender:
    def test_markdown_lists_every_row_labels_tiers_and_states_what_is_pending(self):
        md = syn.render_markdown(syn.build_results_table({}))
        for i in ids():
            assert i in md
        assert "exploratory" in md and "confirmatory" in md and "not yet run" in md
        assert not re.search(r"\d\.\d", md.split("\n", 3)[-1].replace("MB-", "")), "no invented numbers in an empty table"

    def test_the_table_is_one_per_hypothesis(self):
        md = syn.render_markdown(syn.build_results_table({}))
        for h in ("H1", "H2", "H3"):
            assert re.search(rf"^#+ .*{h}", md, re.MULTILINE), h


# ------------------------------------------------------------------------------ deviations
GOOD = """# Deviations
## A. Before
| # | Original spec | What was done instead | Date | Consequence |
|---|---|---|---|---|
| S1 | x | y | Nov 18, 2026 | z |

## B. After
| Date | Preregistered item | Change | Reason | Effect on analysis | Decided by |
|---|---|---|---|---|---|
| Dec 2, 2026 | H1 model | dropped slot AR(1) | would not converge | fell back to the GLS | Bharg |
"""


class TestDeviations:
    def test_the_real_file_parses_with_part_a_filled_and_part_b_empty(self):
        d = syn.parse_deviations(DEVIATIONS.read_text(encoding="utf-8"))
        assert len(d["before"]) >= 8 and {"S1", "S8"} <= {r["#"] for r in d["before"]}
        assert d["after"] == []

    def test_a_filled_row_is_parsed(self):
        d = syn.parse_deviations(GOOD)
        assert d["after"][0]["Preregistered item"] == "H1 model" and d["after"][0]["Decided by"] == "Bharg"

    def test_an_incomplete_after_registration_row_is_rejected(self):
        bad = GOOD.replace("| Bharg |", "|  |")
        with pytest.raises(ValueError, match="Decided by"):
            syn.parse_deviations(bad)

    def test_the_writeup_section_says_none_when_there_are_no_deviations(self):
        text = syn.render_deviations_section(syn.parse_deviations(DEVIATIONS.read_text(encoding="utf-8")))
        assert "Deviations from preregistration" in text and "no deviations" in text.lower()
        assert "S1" in text  # the pre-registration build-plan changes stay visible

    def test_the_writeup_section_lists_logged_deviations(self):
        text = syn.render_deviations_section(syn.parse_deviations(GOOD))
        assert "dropped slot AR(1)" in text and "would not converge" in text and "no deviations" not in text.lower()


# ------------------------------------------------------------------------------ guards
class TestGuards:
    def test_the_module_never_reads_the_database_or_real_data(self):
        src = inspect.getsource(syn)
        for forbidden in ("sqlite3", "score_database", "load_sessions", "read_csv"):
            assert forbidden not in src
