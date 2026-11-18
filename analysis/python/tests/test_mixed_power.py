"""MB-05b: the preregistered primary H1 model (random intercept for day + AR(1) over calendar slots, REML, t with
df = included days - 5) and its simulation. The acceptance tests at the bottom read the committed results file."""
import json
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from mindbench import mixed_power as mp

REPO = Path(__file__).resolve().parents[3]
RESULTS = REPO / "docs" / "design" / "power_mixed_results.json"


# ------------------------------------------------------------------ slots, design, covariance
def test_slot_is_two_per_day_so_missed_sessions_leave_gaps():
    assert mp.slot_index(1, 0) == 1 and mp.slot_index(1, 1) == 2
    assert mp.slot_index(3, 0) == 5 and mp.slot_index(21, 1) == 42
    # day 2 PM missing: the slot after day 2 AM (3) is day 3 AM (5), a gap of 2
    assert [mp.slot_index(d, pm) for d, pm in [(2, 0), (3, 0)]] == [3, 5]


def test_design_matrix_has_intercept_sleep_centered_k_log_k_and_pm():
    sleep = np.array([6.0, 6.0, 8.0, 8.0])
    k = np.array([1, 2, 3, 4])
    pm = np.array([0, 1, 0, 1])
    X = mp.design_matrix(sleep, k, pm)
    assert X.shape == (4, 5)
    assert np.allclose(X[:, 0], 1)
    assert np.allclose(X[:, 1], [-1, -1, 1, 1])  # centered at the mean (7)
    assert np.allclose(X[:, 2], k) and np.allclose(X[:, 3], np.log(k)) and np.allclose(X[:, 4], pm)


def test_covariance_combines_day_intercept_and_ar1_over_slots():
    slots = np.array([1, 2, 3, 5])
    days = np.array([1, 1, 2, 3])
    V = mp.covariance(slots, days, sigma_u2=0.3, sigma_e2=0.7, phi=0.5)
    assert V[0, 0] == pytest.approx(0.3 + 0.7)                      # variance
    assert V[0, 1] == pytest.approx(0.3 + 0.7 * 0.5)                # same day, adjacent slots
    assert V[1, 2] == pytest.approx(0.7 * 0.5)                      # different days, adjacent slots
    assert V[2, 3] == pytest.approx(0.7 * 0.5 ** 2)                 # slots 3 and 5: a gap, distance 2
    assert V[0, 3] == pytest.approx(0.7 * 0.5 ** 4)
    assert np.allclose(V, V.T)


# ------------------------------------------------------------------ REML fit
def simulate(n_days, seed, beta=(0.0, 0.5, 0.0, 0.0, 0.0), su2=0.3, se2=0.7, phi=0.3):
    rng = np.random.default_rng(seed)
    data = mp.simulate_sessions(n_days, rng, r=0.0, day_share=0.0)  # structure only
    n = len(data["slot"])
    X = mp.design_matrix(data["sleep"], data["k"], data["pm"])
    V = mp.covariance(data["slot"], data["day"], su2, se2, phi)
    y = X @ np.array(beta) + np.linalg.cholesky(V) @ rng.standard_normal(n)
    return data, X, y


def test_with_variance_components_fixed_at_zero_reml_equals_ols():
    data, X, y = simulate(21, 1)
    fit = mp.fit_reml(y, X, data["slot"], data["day"], fixed={"sigma_u2": 0.0, "phi": 0.0})
    beta_ols, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta_ols
    s2 = resid @ resid / (len(y) - X.shape[1])
    se_ols = np.sqrt(s2 * np.diag(np.linalg.inv(X.T @ X)))
    assert np.allclose(fit["beta"], beta_ols, atol=1e-8)
    assert np.allclose(fit["se"], se_ols, rtol=1e-6)


def test_reml_recovers_the_variance_components_with_plenty_of_data():
    data, X, y = simulate(500, 2)
    fit = mp.fit_reml(y, X, data["slot"], data["day"])
    assert fit["converged"]
    assert fit["sigma_u2"] == pytest.approx(0.3, abs=0.08)
    assert fit["sigma_e2"] == pytest.approx(0.7, abs=0.08)
    assert fit["phi"] == pytest.approx(0.3, abs=0.08)
    assert fit["beta"][1] == pytest.approx(0.5, abs=0.1)


def test_fit_handles_gaps_in_the_slots():
    data, X, y = simulate(21, 3)
    keep = np.ones(len(y), bool)
    keep[[3, 10, 11, 30]] = False  # drop sessions: slots keep their calendar positions
    fit = mp.fit_reml(y[keep], X[keep], data["slot"][keep], data["day"][keep])
    assert fit["converged"] and np.all(np.isfinite(fit["se"]))


def test_t_test_uses_included_days_minus_5_degrees_of_freedom():
    days = np.array([1, 1, 2, 2, 3, 5, 5, 6, 6, 7, 7, 8, 8])
    assert mp.n_included_days(days) == 7  # days 1, 2, 3, 5, 6, 7, 8
    p = mp.t_pvalue(b=2.0, se=1.0, days=days)
    assert p == pytest.approx(2 * stats.t.sf(2.0, df=7 - 5))
    assert mp.t_pvalue(b=-2.0, se=1.0, days=days) == pytest.approx(p)


def test_fit_and_test_returns_the_sleep_effect_and_its_p_value():
    data, X, y = simulate(21, 4, beta=(0, 0.0, 0, 0, 0))
    out = mp.fit_and_test(y, data["sleep"], data["k"], data["pm"], data["day"], data["slot"])
    assert set(out) >= {"b1", "se1", "p", "df"}
    assert out["df"] == 21 - 5
    assert 0 <= out["p"] <= 1


# ------------------------------------------------------------------ simulation smoke test (fast, loose bounds)
def test_null_type_one_error_is_not_wildly_off_in_a_small_simulation():
    res = mp.simulate_scenario(r=0.0, day_share=0.3, n_sims=150, seed=11)
    assert 0.0 <= res["type1_single"] <= 0.15
    assert 0.0 <= res["type1_fwer_holm"] <= 0.15


def test_a_strong_effect_is_usually_detected():
    res = mp.simulate_scenario(r=0.7, day_share=0.0, n_sims=100, seed=12)
    assert res["power_single"] > 0.7


# ------------------------------------------------------------------ acceptance criteria for the committed results
@pytest.fixture(scope="module")
def results():
    assert RESULTS.is_file(), "run: uv run python scripts/power_mixed_report.py (writes docs/design/power_mixed_results.json)"
    return json.loads(RESULTS.read_text())


def test_results_record_the_setup_and_at_least_2000_simulations_per_scenario(results):
    m = results["meta"]
    assert m["n_sims"] >= 2000 and m["n_days"] == 21 and m["phi"] == 0.3
    assert "REML" in m["model"] and "df" in m["model"]
    assert set(results["scenarios"]) == {"day_share_0.00", "day_share_0.30"}


@pytest.mark.parametrize("share", ["day_share_0.00", "day_share_0.30"])
def test_type_one_error_of_the_primary_model_is_close_to_nominal(results, share):
    null = results["scenarios"][share]["r0.00"]
    assert 0.03 <= null["type1_single"] <= 0.07, null
    assert null["type1_fwer_holm"] <= 0.07, null


@pytest.mark.parametrize("share", ["day_share_0.00", "day_share_0.30"])
def test_power_rises_with_r_and_holm_never_exceeds_the_uncorrected_test(results, share):
    sc = results["scenarios"][share]
    rs = sorted(k for k in sc if k != "r0.00")
    both = [sc[k]["power_holm_both"] for k in rs]
    for a, b in zip(both, both[1:]):
        assert b >= a - 0.03  # monotone up to simulation noise
    for k in rs:
        assert sc[k]["power_holm_both"] <= sc[k]["power_single"] + 0.03
        assert sc[k]["power_holm_one"] <= sc[k]["power_single"] + 0.03


def test_headline_numbers_are_consistent_with_the_scenario_table(results):
    h = results["headline"]
    sc = results["scenarios"][h["planning_scenario"]]
    assert h["r0.43_holm_both"] == sc["r0.43"]["power_holm_both"]
    assert h["r0.30_holm_both"] == sc["r0.30"]["power_holm_both"]
    assert 0.3 < h["detectable_r_80"] < 0.8
