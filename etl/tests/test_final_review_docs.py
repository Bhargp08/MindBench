"""MB-25: the release checklist and the prompt for the independent final review. Docs only; nothing here tags or publishes."""
import re
from pathlib import Path

STATUS = Path(__file__).resolve().parents[2] / "docs" / "status"


class TestReleaseChecklist:
    TEXT = (STATUS / "RELEASE_CHECKLIST.md").read_text(encoding="utf-8")

    def test_it_separates_what_claude_did_from_what_only_bharg_can_do(self):
        low = self.TEXT.lower()
        for phrase in ("bharg only", "osf", "zenodo", "tag v1.0", "github pages", "datapipe", "re-tag", "consent form", "unverified references"):
            assert phrase in low, phrase

    def test_the_acceptance_criteria_are_listed_unchecked_until_the_review_is_done(self):
        assert "no open critical" in self.TEXT.lower() and "ci green" in self.TEXT.lower()
        assert "- [ ]" in self.TEXT

    def test_it_says_the_final_review_is_cursors_and_that_no_tag_was_made(self):
        low = self.TEXT.lower()
        assert "final_review.md" in low and "cursor" in low and "no tag" in low


class TestSelfAudit:
    TEXT = (STATUS / "SELF_AUDIT.md").read_text(encoding="utf-8")

    def test_it_is_labelled_as_claudes_own_pre_review_check_not_the_independent_review(self):
        low = self.TEXT.lower()
        assert "not the independent review" in low and "release_audit" in low

    def test_it_does_not_pretend_to_be_the_cursor_review(self):
        assert not (STATUS / "FINAL_REVIEW.md").exists()


class TestCursorPrompt:
    TEXT = (STATUS / "FINAL_REVIEW_PROMPT.md").read_text(encoding="utf-8")

    def test_it_covers_every_item_in_the_review_spec_section_8(self):
        low = self.TEXT.lower()
        for phrase in ("acceptance criteria", "slow", "data_public", "every number", "deviations.md", "ethics", "pins", "git history", "docs/status/final_review.md",
                       "critical", "numbered fix list", "never merge", "do not tag"):
            assert phrase in low, phrase
