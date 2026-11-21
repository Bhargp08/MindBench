"""MB-23: paper built from a template; every number must trace to a script output or a registered design constant."""
import inspect
import re
from pathlib import Path

import pytest

from mindbench import synthesis, writeup

ROOT = Path(__file__).resolve().parents[3]
TEMPLATE = ROOT / "docs" / "writeup" / "paper_template.md"
PAPER = ROOT / "docs" / "writeup" / "paper.md"
PREREG = (ROOT / "docs" / "design" / "prereg_draft.md").read_text(encoding="utf-8")


# ------------------------------------------------------------------------------ placeholders
class TestPlaceholders:
    def test_finds_keys(self):
        assert writeup.placeholders("a {{x.y}} b {{z}} {{x.y}}") == {"x.y", "z"}

    def test_fills_values_and_marks_them(self):
        out = writeup.render("n = {{n}}", {"n": "42"}, mark=True)
        assert out == "n = ⟦n|42⟧"
        assert writeup.render("n = {{n}}", {"n": "42"}) == "n = 42"

    def test_a_missing_value_is_an_error_not_a_blank(self):
        with pytest.raises(KeyError, match="n"):
            writeup.render("n = {{n}}", {})

    def test_pending_ok_writes_an_explicit_marker(self):
        assert writeup.render("n = {{n}}", {}, pending_ok=True) == "n = [PENDING: n]"


# ------------------------------------------------------------------------------ number tracing
class TestTraceability:
    def test_a_number_typed_into_the_prose_is_flagged(self):
        marked = writeup.render("The effect was 0.37 ({{p}}).", {"p": "0.01"}, mark=True)
        assert writeup.untraced_numbers(marked) == ["0.37"]

    def test_numbers_inside_placeholders_are_traced(self):
        assert writeup.untraced_numbers(writeup.render("b = {{b}}", {"b": "0.37"}, mark=True)) == []

    def test_registered_design_constants_are_allowed(self):
        assert writeup.untraced_numbers("42 sessions over 21 days, alpha .05, 10,000 resamples.") == []

    def test_labels_and_ids_are_not_numbers(self):
        text = "H1:P1 and S3 (2-back d'), ICC(3,1), AR(1), MB-20, D3, 1-up/2-down."
        assert writeup.untraced_numbers(text) == []

    def test_every_allowed_constant_appears_in_the_preregistration(self):
        for c in writeup.ALLOWED_CONSTANTS:
            assert c in PREREG, c

    def test_the_references_block_is_exempt_from_the_check_but_must_have_a_heading(self):
        text = "## References\n\nLim, J. & Dinges, D. (2010). 136(3), 375-389.\n"
        assert writeup.untraced_numbers(text) == []


# ------------------------------------------------------------------------------ the real paper
class TestPaper:
    def values(self):
        return writeup.collect_values(results={})

    def build(self):
        return writeup.build_paper(TEMPLATE.read_text(encoding="utf-8"), self.values(), mark=True)

    def test_the_template_has_the_required_sections_in_order(self):
        heads = [h.lower() for h in re.findall(r"^#{2}\s+(.*)$", TEMPLATE.read_text(encoding="utf-8"), re.MULTILINE)]
        order = ["introduction", "methods", "results", "deviations from preregistration", "limitations", "references"]
        idx = [next(i for i, h in enumerate(heads) if k in h) for k in order]
        assert idx == sorted(idx), heads

    def test_results_have_a_confirmatory_part_before_an_exploratory_part(self):
        t = TEMPLATE.read_text(encoding="utf-8").lower()
        assert t.index("confirmatory") < t.index("exploratory")

    def test_every_placeholder_in_the_template_gets_a_value(self):
        t = TEMPLATE.read_text(encoding="utf-8")
        assert writeup.placeholders(t) <= set(self.values()) | {"references"}

    def test_every_number_in_the_built_paper_traces_to_a_script_output_or_a_design_constant(self):
        assert writeup.untraced_numbers(self.build()) == []

    def test_with_no_results_the_paper_says_nothing_has_been_analysed_and_makes_no_claims(self):
        text = writeup.strip_marks(self.build())
        assert "no data have been analysed" in text.lower()
        for claim in (r"significantly", r"we found", r"was supported\b", r"effect of sleep was"):
            assert not re.search(claim, text, re.IGNORECASE), claim

    def test_power_numbers_come_from_the_mixed_model_simulation_json(self):
        import json

        head = json.loads((ROOT / "docs" / "design" / "power_mixed_results.json").read_text())["headline"]
        v = self.values()
        assert v["power.holm_r43"] == f"{head['r0.43_holm_both']:.2f}"
        assert v["power.detectable_r"] == f"{head['detectable_r_80']:.2f}"

    def test_the_no_irb_statement_and_the_no_pilot_statement_are_present_and_no_false_claims(self):
        text = writeup.strip_marks(self.build())
        assert "no institutional review board review" in text.lower()
        assert "no formal pilot" in text.lower()
        assert not re.search(r"IRB[\s-]+approved|ethics\s+approval", text, re.IGNORECASE)
        assert not re.search(r"think-aloud (found|showed|results)", text, re.IGNORECASE)

    def test_deviations_section_comes_from_deviations_md(self):
        text = writeup.strip_marks(self.build())
        assert "There were no deviations from the preregistration." in text
        assert "S1" in text

    def test_the_committed_paper_is_the_output_of_the_builder(self):
        assert PAPER.read_text(encoding="utf-8") == writeup.build_paper(TEMPLATE.read_text(encoding="utf-8"), self.values())

    def test_registration_link_is_pending_until_bharg_registers(self):
        assert "[PENDING: registration.url]" in PAPER.read_text(encoding="utf-8")


# ------------------------------------------------------------------------------ references and figures
class TestReferences:
    def test_every_citation_key_has_a_reference_and_every_reference_is_cited(self):
        t = TEMPLATE.read_text(encoding="utf-8")
        cited = set(re.findall(r"\[@([\w-]+)\]", t))
        assert cited == set(writeup.REFERENCES), cited ^ set(writeup.REFERENCES)

    def test_references_not_checked_against_the_source_are_flagged(self):
        refs = writeup.render_references()
        for key, r in writeup.REFERENCES.items():
            line = next(l for l in refs.splitlines() if r["text"] in l)
            assert ("[bibliographic details not verified]" in line) == (not r["verified"]), key

    def test_the_lim_dinges_reference_is_the_verified_one_used_for_the_outcome_choice(self):
        assert writeup.REFERENCES["limdinges2010"]["verified"] is True


class TestFigures:
    def test_every_figure_has_an_existing_script_and_output_and_is_in_the_template(self):
        t = TEMPLATE.read_text(encoding="utf-8")
        assert writeup.FIGURES
        for f in writeup.FIGURES:
            assert (ROOT / f["script"]).is_file(), f
            assert (ROOT / "docs" / "writeup" / f["image"]).resolve().is_file(), f
            assert f["image"] in t, f

    def test_the_module_never_reads_the_database_or_real_data(self):
        src = inspect.getsource(writeup)
        for forbidden in ("sqlite3", "score_database", "load_sessions", "read_csv"):
            assert forbidden not in src
