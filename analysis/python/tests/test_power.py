"""MB-04 power analysis tests.

Targets: analytic values and the correlation/paired simulations are from the spec (verified
numerically Nov 17, 2026). Holm and AR(1)+paired-sleep values were calibrated with a
prototype simulation (see docs/design/power.md); they are flagged as such.
"""
import pytest

from mindbench import power

SEED = 20261117


# ---- analytic paired t (spec-verified) ----
def test_paired_t_required_n_dz_05():
    assert power.paired_t_required_n(0.5) == 34
    assert power.paired_t_power(0.5, 34) == pytest.approx(0.808, abs=0.001)


def test_paired_t_required_n_dz_03():
    assert power.paired_t_required_n(0.3) == 90
    assert power.paired_t_power(0.3, 90) == pytest.approx(0.804, abs=0.001)


def test_paired_am_pm_21_pairs():
    assert power.paired_t_power(0.65, 21) == pytest.approx(0.809, abs=0.01)


# ---- simulated correlation test, i.i.d. sleep, no autocorrelation (spec-verified) ----
@pytest.mark.parametrize("n,r,expected", [(40, 0.43, 0.80), (28, 0.43, 0.65), (40, 0.30, 0.48)])
def test_simulated_correlation_power(n, r, expected):
    p = power.simulate_corr_power(n=n, r=r, n_sims=4000, seed=SEED)
    assert p == pytest.approx(expected, abs=0.03)


# ---- type-I error under AR(1) residuals, no correction ----
def test_ar1_with_iid_sleep_does_not_inflate_type1():
    """Documented nuance: AR(1) errors alone leave type-I near 0.05 when the predictor is i.i.d."""
    t1 = power.simulate_corr_power(n=40, r=0.0, phi=0.3, n_sims=4000, seed=SEED)
    assert t1 == pytest.approx(0.05, abs=0.015)


def test_ar1_with_shared_nightly_sleep_inflates_type1():
    """AM and PM share the same night's sleep, so the predictor is autocorrelated too.
    Uncorrected OLS then rejects more than 5% under the null (motivates the AR model in MB-18)."""
    t1 = power.simulate_corr_power(
        n=40, r=0.0, phi=0.3, paired_sleep=True, method="ols", n_sims=4000, seed=SEED
    )
    assert t1 > 0.06


def test_ar1_correction_reduces_inflation():
    naive = power.simulate_corr_power(
        n=40, r=0.0, phi=0.3, paired_sleep=True, method="ols", n_sims=4000, seed=SEED
    )
    fixed = power.simulate_corr_power(
        n=40, r=0.0, phi=0.3, paired_sleep=True, method="ar1", n_sims=4000, seed=SEED
    )
    assert fixed < naive
    assert fixed <= 0.07


# ---- effective power: Holm over 5 primary outcomes + AR(1) + shared nightly sleep ----
def test_effective_power_holm_all_five_true():
    eff = power.simulate_holm_power(
        n=42, r=0.43, m=5, n_true=5, phi=0.3, paired_sleep=True, method="ar1", n_sims=2000, seed=SEED
    )
    assert eff == pytest.approx(0.66, abs=0.05)


def test_effective_power_holm_one_true():
    eff = power.simulate_holm_power(
        n=42, r=0.43, m=5, n_true=1, phi=0.3, paired_sleep=True, method="ar1", n_sims=2000, seed=SEED
    )
    assert eff == pytest.approx(0.54, abs=0.05)


def test_holm_lowers_power_vs_uncorrected():
    kw = dict(n=42, r=0.43, phi=0.3, paired_sleep=True, method="ar1", n_sims=2000, seed=SEED)
    uncorrected = power.simulate_corr_power(**kw)
    holm = power.simulate_holm_power(m=5, n_true=5, **kw)
    assert holm < uncorrected - 0.05


def test_power_curve_20_to_60():
    curve = power.power_curve(range(20, 61, 10), r=0.43, n_sims=1000, seed=SEED)
    ns = [n for n, _ in curve]
    ps = [p for _, p in curve]
    assert ns == [20, 30, 40, 50, 60]
    assert ps[-1] > ps[0] + 0.3


def test_two_outcome_holm_costs_less_than_five():
    """Two-outcome Holm family (the preregistered family) keeps more power than five outcomes."""
    kw = dict(n=42, r=0.43, phi=0.3, paired_sleep=True, method="ar1", n_sims=2000, seed=SEED)
    uncorrected = power.simulate_corr_power(**kw)
    holm2 = power.simulate_holm_power(m=2, n_true=2, **kw)
    holm5 = power.simulate_holm_power(m=5, n_true=5, **kw)
    assert holm5 < holm2 < uncorrected + 0.03
    assert holm2 == pytest.approx(0.74, abs=0.05)
