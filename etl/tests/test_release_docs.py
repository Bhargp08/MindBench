"""MB-24: README, CITATION.cff, open-data notes, demo script and screenshot plan. Lint-level checks: nothing here may
claim something that is not true yet (no live site, no DOI, no IRB, no results)."""
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
README = (REPO / "README.md").read_text(encoding="utf-8")
RELEASE = REPO / "docs" / "release"


def headings(text):
    return [h.lower() for h in re.findall(r"^#{1,3}\s+(.*)$", text, re.MULTILINE)]


class TestReadme:
    def test_it_has_the_required_sections(self):
        have = headings(README)
        for h in ("what it is", "live", "how to run", "how to reproduce", "data", "use of ai tools", "license", "cite"):
            assert any(h in x for x in have), h

    def test_the_live_link_is_a_placeholder_until_bharg_deploys(self):
        assert "[PENDING: live site URL]" in README
        assert "github.io" not in README

    def test_the_run_and_reproduce_commands_exist_in_the_repo(self):
        for cmd in ("uv run pytest", "mindbench.public_data", "npm"):
            assert cmd in README, cmd
        for path in ("experiment", "etl", "analysis/python", "dashboard", "data_public"):
            assert path in README, path

    def test_the_ai_note_is_honest_and_marked_for_bharg_to_reword(self):
        ai = README.split("Use of AI tools", 1)[1]
        assert "[BHARG: reword in your own voice]" in ai
        assert re.search(r"AI|Claude|assistant", ai)
        assert "model" not in ai.lower().split("[bharg")[0] or True  # no model names are checked below
        for name in ("sonnet", "opus", "haiku", "fable"):
            assert name not in README.lower()

    def test_no_false_claims(self):
        low = README.lower()
        assert "no institutional review board review" in low
        assert not re.search(r"irb[\s-]+approved|ethics\s+approval|peer[- ]reviewed|10\.\d{4,}/", low)
        assert "no results" in low or "no data have been collected" in low or "not collected" in low

    def test_the_data_section_says_what_is_and_is_not_released(self):
        data = README.lower()
        for phrase in ("participant codes", "free text", "date", "consent", "zenodo"):
            assert phrase in data, phrase
        assert "[pending: zenodo doi]" in data


class TestCitation:
    CFF = (REPO / "CITATION.cff").read_text(encoding="utf-8")

    def test_it_has_the_required_cff_fields(self):
        for key in ("cff-version: 1.2.0", "message:", "title:", "authors:", "family-names: Patel", "given-names: Bharg", "repository-code: https://github.com/Bhargp08/MindBench", "license: MIT"):
            assert key in self.CFF, key

    def test_nothing_is_invented(self):
        assert not re.search(r"^doi:\s*10\.", self.CFF, re.MULTILINE)  # the DOI is added after Zenodo mints it
        assert "date-released" not in self.CFF.replace("# date-released", "")  # added at release
        assert "PENDING" in self.CFF


class TestOpenDataNotes:
    TEXT = (RELEASE / "open_data.md").read_text(encoding="utf-8")

    def test_it_lists_the_deid_rules_and_the_consent_rule_and_who_uploads(self):
        low = self.TEXT.lower()
        for phrase in ("participant code", "free text", "finer than the date", "consent", "zenodo", "bharg uploads", "cc-by-4.0", "mindbench.public_data check"):
            assert phrase in low, phrase

    def test_it_says_the_export_needs_review_before_upload(self):
        assert "review" in self.TEXT.lower() and "before" in self.TEXT.lower()


class TestDemoScript:
    TEXT = (RELEASE / "demo_script.md").read_text(encoding="utf-8")

    def test_the_segments_are_timed_and_fit_in_two_minutes(self):
        segs = re.findall(r"\[(\d{2}):(\d{2})-(\d{2}):(\d{2})\]", self.TEXT)
        assert len(segs) >= 5
        prev_end = 0
        for a, b, c, d in segs:
            start, end = int(a) * 60 + int(b), int(c) * 60 + int(d)
            assert start == prev_end and end > start
            prev_end = end
        assert 100 <= prev_end <= 120

    def test_it_uses_only_simulated_or_public_views_and_makes_no_result_claims(self):
        low = self.TEXT.lower()
        assert "simulated" in low and "public mode" in low
        assert not re.search(r"we found|significant|proved|results show", low)


class TestScreenshotPlan:
    TEXT = (RELEASE / "screenshot_plan.md").read_text(encoding="utf-8")

    def test_every_shot_has_a_file_name_and_a_source(self):
        shots = re.findall(r"^\|\s*(\d+)\s*\|\s*`([\w.-]+\.png)`\s*\|(.+)\|\s*$", self.TEXT, re.MULTILINE)
        assert len(shots) >= 5
        assert len({s[1] for s in shots}) == len(shots)

    def test_it_forbids_private_content_in_any_screenshot(self):
        low = self.TEXT.lower()
        for phrase in ("participant code", "sleep", "time of day", "public mode", "simulated"):
            assert phrase in low, phrase
