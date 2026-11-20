"""Smoke tests: the Streamlit app renders without errors, shows the required panels, and respects public mode."""
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from conftest import CODE, build_db

APP = str(Path(__file__).resolve().parents[1] / "app.py")


@pytest.fixture
def env(db_path, raw_dir, tmp_path, monkeypatch):
    build_db(db_path, [(1, None), (3, None), (4, None), (6, None)]).close()
    (raw_dir / f"{CODE}_session5.partial.json").write_text("[]")
    monkeypatch.setenv("MINDBENCH_DB", str(db_path))
    monkeypatch.setenv("MINDBENCH_RAW", str(raw_dir))
    monkeypatch.setenv("MINDBENCH_REPORT", str(tmp_path / "none.json"))
    monkeypatch.setenv("MINDBENCH_EXPECTED", "fixture")  # tiny synthetic sessions: use the fixture trial counts
    return monkeypatch


def page_text(at):
    parts = [m.value for m in at.markdown] + [h.value for h in at.subheader] + [h.value for h in at.title] + [m.value for m in at.info] + [c.value for c in at.caption]
    parts += [df.value.to_string() for df in at.dataframe]
    return "\n".join(str(p) for p in parts)


def test_renders_with_the_required_panels_and_the_monitoring_notice(env):
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    text = page_text(at)
    assert "completion and data quality only" in text.lower()
    assert "never shows outcome values" in text.lower()
    for panel in ("Completion", "Session-number gaps", "Skipped partial uploads", "Data quality", "Sleep log"):
        assert panel in text, panel
    assert f"{CODE}_session5.partial.json" in text  # the skipped partial file is listed in local mode


def test_public_mode_hides_codes_and_the_sleep_log(env):
    env.setenv("MINDBENCH_DASHBOARD_PUBLIC", "1")
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert not at.exception
    text = page_text(at)
    assert CODE not in text and ".json" not in text
    assert "Sleep log" not in text
    assert "public" in text.lower()


def test_no_dataframe_column_names_an_outcome(env):
    import re

    at = AppTest.from_file(APP, default_timeout=60).run()
    bad = re.compile(r"d_?prime|recall_proportion|proportion|interference|validity|criterion|threshold|accuracy|score", re.I)
    for df in at.dataframe:
        for col in df.value.columns:
            assert not bad.search(str(col)), col
