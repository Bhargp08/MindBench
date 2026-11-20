from pathlib import Path

from mindbench_dashboard.config import load_config


def test_defaults_point_at_the_gitignored_data_folder_and_local_mode():
    c = load_config({})
    assert c["public"] is False
    assert c["db"] == Path("data/mindbench.sqlite") and c["raw"] == Path("data/raw") and c["report"] == Path("data/etl_report.json")


def test_environment_overrides():
    c = load_config({"MINDBENCH_DB": "/x/a.sqlite", "MINDBENCH_RAW": "/x/raw", "MINDBENCH_REPORT": "/x/r.json", "MINDBENCH_DASHBOARD_PUBLIC": "1"})
    assert (c["db"], c["raw"], c["report"], c["public"]) == (Path("/x/a.sqlite"), Path("/x/raw"), Path("/x/r.json"), True)


def test_only_an_explicit_true_value_turns_public_mode_on():
    for v in ("0", "", "false", "no"):
        assert load_config({"MINDBENCH_DASHBOARD_PUBLIC": v})["public"] is False
    for v in ("1", "true", "TRUE", "yes"):
        assert load_config({"MINDBENCH_DASHBOARD_PUBLIC": v})["public"] is True
