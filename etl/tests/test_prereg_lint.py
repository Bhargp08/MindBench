"""MB-05: lint for docs/design/prereg_draft.md (completeness, consistency with design.md / power.md, no false claims)."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DESIGN = ROOT / "docs" / "design"
DRAFT = DESIGN / "prereg_draft.md"

SECTIONS = ["Study Information", "Design Plan", "Sampling Plan", "Variables", "Analysis Plan", "Other"]
EXTRA_SECTIONS = ["Before you submit", "Coverage of the planned analyses"]

# Items Bharg required (Nov 18, 2026) plus the statements in prereg_notes.md.
REQUIRED_PHRASES = [
    "P1", "2-back d'", "P2", "recall proportion", "Holm",
    "2,000 ms", "before RT trimming", "60%",
    "44 planned sessions", "is_pilot", "smoke-test",
    "no formal pilot", "deviation",
    "no institutional review board review has been obtained",
    "MB-18", "MB-19", "MB-20", "MB-21",
    "[FREEZE COMMIT",
]
RESULTS = DESIGN / "power_mixed_results.json"
# Numbers that must match design.md.
DESIGN_NUMBERS = ["42 sessions", "sessions 3-44", "21 calendar days", "120", "60"]


def text():
    assert DRAFT.is_file(), "missing docs/design/prereg_draft.md"
    return DRAFT.read_text(encoding="utf-8")


def headings(t):
    return [re.sub(r"^#+\s*", "", l).strip().lower() for l in t.splitlines() if l.startswith("#")]


def test_draft_exists_and_says_it_is_not_submitted():
    t = text()
    assert "not submitted" in t.lower() or "draft - not submitted" in t.lower()


def test_osf_template_sections_and_extra_sections_are_present():
    h = headings(text())
    for name in SECTIONS + EXTRA_SECTIONS:
        assert any(name.lower() in x for x in h), f"missing section: {name}"


def test_required_items_are_present():
    t = text()
    missing = [p for p in REQUIRED_PHRASES if p.lower() not in t.lower()]
    assert not missing, f"missing: {missing}"


def test_numbers_agree_with_design_docs():
    t = text()
    design = (DESIGN / "design.md").read_text(encoding="utf-8")
    for n in DESIGN_NUMBERS:
        assert n in t, f"{n} not in the draft"
    for task_count in ("120", "60"):
        assert task_count in design


def test_headline_power_numbers_come_from_the_mixed_model_simulation_and_match_power_md():
    import json

    assert RESULTS.is_file(), "missing docs/design/power_mixed_results.json (run analysis/python/scripts/power_mixed_report.py)"
    res = json.loads(RESULTS.read_text())
    head = res["headline"]
    t, power = text(), (DESIGN / "power.md").read_text(encoding="utf-8")
    for key in ("r0.43_holm_both", "r0.30_holm_both", "detectable_r_80"):
        formatted = f"{head[key]:.2f}"
        assert formatted in t, f"{key} = {formatted} missing from the draft"
        assert formatted in power, f"{key} = {formatted} missing from power.md"
    assert res["meta"]["n_sims"] >= 2000


def test_the_old_gls_headline_numbers_are_no_longer_presented_as_the_planning_power():
    t = text()
    assert "effective power" in t.lower()
    assert "superseded" in (DESIGN / "power.md").read_text(encoding="utf-8").lower()


def test_every_outcome_and_hypothesis_is_named():
    t = text()
    for token in ["H1", "H2", "H3", "S1", "S2", "S3", "S4", "S5"]:
        assert token in t, token


def test_no_false_claims():
    t = text()
    assert not re.search(r"IRB[\s-]+approved|ethics\s+approval", t, re.IGNORECASE)
    assert not re.search(r"(informed by|based on|from) (a |the |our )?pilot", t, re.IGNORECASE), "must not claim pilot-informed design"
    assert not re.search(r"think-aloud (found|showed|results)", t, re.IGNORECASE)


def test_placeholders_for_bharg_are_explicit():
    t = text()
    assert "[FREEZE COMMIT" in t
    assert "[DECISION" in t  # open decisions are marked, not hidden


# ---------------------------------------------------------------------------------------------------- MB-05b
def search(pattern, t=None):
    return re.search(pattern, t if t is not None else text(), re.IGNORECASE | re.DOTALL)


def test_d3_primary_model_is_a_mixed_model_with_day_intercept_and_ar1_over_calendar_slots():
    t = text()
    for phrase in ("random intercept for day", "slot = 2*(day-1)+PM+1", "REML", "df = included days - 5"):
        assert phrase in t, phrase
    assert search(r"AR\(1\) over (the )?calendar slots")
    assert search(r"missed sessions? leave gaps?")


def test_d3_old_fits_are_kept_as_sensitivity_analyses_only():
    t = text()
    for phrase in ("corAR1", "corCAR1", "day-clustered robust"):
        assert phrase in t, phrase
    assert search(r"sensitivity[^#]{0,500}corAR1") or search(r"corAR1[^#]{0,500}sensitivity")
    assert not search(r"\| D3 \|[^|]*\|\s*GLS with AR\(1\) errors in session order")  # no longer the primary default


def test_d2_early_morning_sessions_belong_to_the_previous_day():
    t = text()
    assert "00:00" in t and "04:00" in t
    assert search(r"(00:00|midnight)[^.]{0,120}04:00[^.]{0,160}previous (calendar )?day") or search(r"previous (calendar )?day[^.]{0,160}04:00")


def test_d4_bca_bootstrap_over_whole_days():
    t = text()
    assert "BCa" in t
    assert "10,000" in t
    assert search(r"whole days")
    assert search(r"(Stroop|S1)[^.]{0,300}whole days|whole days[^.]{0,300}(Stroop|S1)")
    assert not search(r"percentile bootstrap \(10,000 resamples of days")  # replaced by BCa


def test_a_wrong_direction_h1_result_is_not_supported():
    assert search(r"wrong[- ]direction[^.]{0,200}not supported") or search(r"not supported[^.]{0,200}wrong[- ]direction")


def test_d5_bayesian_model_matches_the_d3_model_and_uses_the_stated_priors():
    t = text()
    assert search(r"match\w* the D3 model")
    for phrase in ("one-step-ahead", "standardized", "N(0, 0.5)", "N(0, 1)"):
        assert phrase in t, phrase
    assert search(r"sleep[^.]{0,120}centered")
    assert search(r"N\(0, 0\.5\)[^.]{0,40}per hour|per hour[^.]{0,40}N\(0, 0\.5\)")


def test_d6_icc_is_on_residuals_with_the_raw_icc_also_reported():
    t = text()
    assert "ICC(3,1)" in t
    assert "y ~ k + ln(k)" in t
    assert search(r"raw ICC")
    assert search(r"residuals")


def test_d7_ddm_models_let_congruency_and_cue_validity_drive_drift_and_boundary_can_be_not_identifiable():
    t = text()
    assert "congruency" in t.lower() and "cue validity" in t.lower()
    assert search(r"(congruency|cue validity)[^.]{0,200}drift")
    assert "not identifiable" in t
    assert search(r"not identifiable[^.]{0,200}5%|5%[^.]{0,200}not identifiable|under 5%[^.]{0,200}not identifiable")


def test_d8_option_a_only_and_tag_and_registration_timing():
    t = text()
    assert "Option A" in t
    assert "Option B" not in t
    assert search(r"re-?tag[^.]{0,200}prereg-v1|prereg-v1[^.]{0,200}re-?tag")
    assert search(r"before (the first confirmatory session|session 3)")


def test_d9_am_pm_comes_from_the_start_time_not_odd_even_session_numbers():
    t = text()
    assert search(r"start time[^.]{0,200}(not|rather than)[^.]{0,80}odd/even|odd/even[^.]{0,200}(not|rather than)[^.]{0,80}start time|not from odd/even")


def test_afex_is_dropped_because_no_anova_is_planned():
    t = text()
    assert "afex" not in t.lower()
    assert search(r"repeated-measures ANOVA is not planned")
