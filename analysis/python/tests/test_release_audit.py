"""MB-25: the automated parts of the whole-repo audit (secrets in history, real-data guard, pins, open placeholders,
commit-message rules). The audit reports; it never edits, tags or publishes. Fake secrets are built at run time so this
file itself never contains one."""
import json
import subprocess
from pathlib import Path

import pytest

from mindbench import release_audit as ra

ROOT = Path(__file__).resolve().parents[3]
FAKE_AWS = "AK" + "IA" + "ABCDEFGHIJKLMNOP"
FAKE_GH = "gh" + "p_" + "a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8"
FAKE_PEM = "-----BEGIN " + "PRIVATE KEY-----"


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=T", "-c", "user.email=t@example.com", *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("hello\n")
    git(tmp_path, "add", "-A")
    git(tmp_path, "commit", "-q", "-m", "init")
    return tmp_path


def commit(repo, name, text, msg="change"):
    p = repo / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", msg)


class TestSecrets:
    @pytest.mark.parametrize("text", [FAKE_AWS, FAKE_GH, FAKE_PEM, 'api_key = "' + "x9Y8" * 8 + '"', '"private_key": "' + FAKE_PEM])
    def test_real_looking_secrets_are_found_in_text(self, text):
        assert ra.scan_secrets_text(text)

    @pytest.mark.parametrize("text", ["the token is read from the environment", "set GOOGLE_KEY in your env file", "api_key = os.environ['X']", "secret sauce", ""])
    def test_words_and_environment_lookups_are_not_secrets(self, text):
        assert ra.scan_secrets_text(text) == []

    def test_a_secret_added_and_later_deleted_is_still_found_in_history(self, repo):
        commit(repo, "config.txt", f"key={FAKE_AWS}\n")
        commit(repo, "config.txt", "key removed\n")
        found = ra.scan_history(repo)
        assert found and "config.txt" in found[0]
        assert FAKE_AWS not in " ".join(found)  # the report never repeats the secret

    def test_a_clean_history_has_no_findings(self, repo):
        assert ra.scan_history(repo) == []

    def test_other_branches_are_scanned_too(self, repo):
        git(repo, "checkout", "-q", "-b", "side")
        commit(repo, "x.txt", FAKE_GH)
        git(repo, "checkout", "-q", "-")
        assert ra.scan_history(repo)


class TestRealDataGuard:
    @pytest.mark.parametrize("name", ["data/mindbench.sqlite", "x/session.db", ".env", "data/raw/K7M2QX9P_session3.json", "abc.partial.json", "pid_map.json", "consent.json"])
    def test_private_data_files_must_not_be_tracked(self, repo, name):
        commit(repo, name, "x")
        assert any(name in p for p in ra.forbidden_tracked(repo))

    def test_fixtures_and_source_data_folders_are_fine(self, repo):
        commit(repo, "experiment/src/data/words.json", "[]")
        commit(repo, "etl/tests/fixtures/K7M2QX9P_session3.json", "[]")
        commit(repo, "data_public/.gitkeep", "")
        assert ra.forbidden_tracked(repo) == []

    def test_a_tracked_data_public_file_that_fails_the_deid_check_is_flagged(self, repo):
        commit(repo, "data_public/sessions.csv", "pid,notes\nK7M2QX9P,hello world\n")
        assert any("data_public" in p for p in ra.forbidden_tracked(repo))


class TestCommitMessages:
    def test_attribution_lines_are_flagged(self, repo):
        commit(repo, "b.txt", "b", msg="feat: x\n\nCo-Authored-By: Someone <s@example.com>")
        commit(repo, "c.txt", "c", msg="feat: y\n\nGenerated with a tool")
        assert len(ra.commit_message_problems(repo)) == 2

    def test_the_review_tools_own_trailer_is_counted_separately_not_failed(self, repo):
        commit(repo, "b.txt", "b", msg="docs: note\n\nCo-authored-by: Cursor <cursoragent@cursor.com>")
        assert ra.commit_message_problems(repo) == []
        assert ra.review_tool_trailers(repo) == 1

    def test_the_owners_own_name_in_a_squash_trailer_is_not_an_attribution_to_a_tool(self, repo):
        commit(repo, "b.txt", "b", msg="[MB-02] x (#3)\n\nCo-authored-by: Bharg Patel <bharg@example.com>")
        assert ra.commit_message_problems(repo) == []

    def test_clean_messages_pass(self, repo):
        commit(repo, "b.txt", "b", msg="feat(MB-99): something")
        assert ra.commit_message_problems(repo) == []


class TestPins:
    def test_floating_npm_versions_are_flagged(self, repo):
        commit(repo, "experiment/package.json", json.dumps({"dependencies": {"a": "^1.2.3", "b": "2.0.0", "c": "~3.0.0", "d": "*"}}))
        problems = ra.pin_problems(repo)
        assert sum(("experiment" in p and "lock" not in p) for p in problems) == 3  # the missing lock file is a separate finding

    def test_python_dependencies_need_an_exact_pin_or_an_upper_bound(self, repo):
        commit(repo, "etl/pyproject.toml", '[project]\nname="x"\ndependencies = ["a==1.0", "b>=2", "c>=1,<2", "d"]\n')
        problems = ra.pin_problems(repo)
        assert any("b>=2" in p for p in problems) and any('"d"' in p or " d" in p for p in problems)
        assert not any("a==1.0" in p or "c>=1,<2" in p for p in problems)

    def test_a_missing_lock_file_is_flagged(self, repo):
        commit(repo, "etl/pyproject.toml", '[project]\nname="x"\ndependencies = []\n')
        assert any("uv.lock" in p for p in ra.pin_problems(repo))


class TestOpenMarkers:
    def test_markers_for_bharg_are_listed_with_file_and_line(self, repo):
        commit(repo, "README.md", "a\n[PENDING: live site URL]\nb [BHARG: reword]\n[bibliographic details not verified]\n")
        m = ra.open_markers(repo)
        assert m["PENDING"][0].startswith("README.md:2") and m["BHARG"][0].startswith("README.md:3")
        assert m["UNVERIFIED"]

    def test_the_audit_does_not_list_its_own_source(self, repo):
        commit(repo, "analysis/python/mindbench/release_audit.py", "[PENDING: x]")
        assert ra.open_markers(repo)["PENDING"] == []


class TestAuditOnThisRepository:
    def test_there_are_no_secrets_in_any_commit(self):
        assert ra.scan_history(ROOT) == []

    def test_no_private_data_is_tracked(self):
        assert ra.forbidden_tracked(ROOT) == []

    def test_the_report_has_one_entry_per_check_with_a_status(self):
        report = ra.run_all(ROOT)
        assert {r["check"] for r in report} >= {"secrets in history", "private data tracked", "commit messages", "pins", "open placeholders", "paper traced", "preregistration coverage"}
        assert all(r["status"] in ("pass", "fail", "info") for r in report)

    def test_the_paper_and_the_preregistration_checks_pass(self):
        by = {r["check"]: r for r in ra.run_all(ROOT)}
        assert by["paper traced"]["status"] == "pass" and by["preregistration coverage"]["status"] == "pass"

    def test_the_audit_never_modifies_anything(self):
        import inspect

        src = inspect.getsource(ra)
        for forbidden in ("git tag", '"tag"', "git push", '"push"', "write_text", "unlink", "rmtree"):
            assert forbidden not in src

    def test_the_command_line_prints_a_report_and_exit_code_follows_failures(self, capsys):
        code = ra.main(["--root", str(ROOT)])
        out = capsys.readouterr().out
        assert "secrets in history" in out and code in (0, 1)
