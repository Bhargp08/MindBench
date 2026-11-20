"""Dashboard configuration from environment variables (nothing secret; paths and one mode switch)."""
from pathlib import Path

# Tiny synthetic sessions (tests only): MINDBENCH_EXPECTED=fixture uses the fixture trial counts instead of the design counts.
FIXTURE_EXPECTED = {"posner": 3, "stroop": 3, "nback": 6, "yesno": 4, "recall_lists": 2}


def load_config(env):
    """Paths default to the gitignored data/ folder; public mode is on only for an explicit 1/true/yes."""
    return {
        "db": Path(env.get("MINDBENCH_DB") or "data/mindbench.sqlite"),
        "raw": Path(env.get("MINDBENCH_RAW") or "data/raw"),
        "report": Path(env.get("MINDBENCH_REPORT") or "data/etl_report.json"),
        "public": (env.get("MINDBENCH_DASHBOARD_PUBLIC") or "").strip().lower() in ("1", "true", "yes"),
        "expected": FIXTURE_EXPECTED if (env.get("MINDBENCH_EXPECTED") or "").strip().lower() == "fixture" else None,
    }
