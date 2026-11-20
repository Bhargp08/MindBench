"""MB-19: test-retest reliability (ICC) and split-half. Simulated data only; never real outcomes.

Definitions follow prereg D6 (docs/design/prereg_draft.md): ICC(3,1) consistency with days as targets and the AM and PM
sessions as the two measurements, computed on residuals from y ~ k + ln(k); the raw ICC is reported next to it; ICC(2,1)
as well. Shrout & Fleiss (1979) forms; confidence intervals from the F distribution (McGraw & Wong 1996) and a bootstrap over days.
"""
import numpy as np
import pytest

from mindbench import reliability as rel

SF = np.array([[9, 2, 5, 8], [6, 1, 3, 2], [8, 4, 6, 8], [7, 1, 2, 6], [10, 5, 6, 9], [6, 2, 4, 7]], dtype=float)


class TestShroutFleiss:
    def test_published_example_icc_1_1_2_1_3_1(self):
        r = rel.icc(SF)
        assert r["ICC(1,1)"] == pytest.approx(0.1657, abs=5e-5)
        assert r["ICC(2,1)"] == pytest.approx(0.2898, abs=5e-5)
        assert r["ICC(3,1)"] == pytest.approx(0.7148, abs=5e-5)

    def test_mean_squares_of_the_example(self):
        r = rel.icc(SF)
        assert r["n_targets"] == 6 and r["n_raters"] == 4
        assert r["BMS"] == pytest.approx(11.2417, abs=1e-3)
        assert r["EMS"] == pytest.approx(1.0556, abs=1e-3)
        assert r["JMS"] == pytest.approx(32.4861, abs=1e-3)

    def test_confidence_intervals_of_the_example(self):
        # reference values from the McGraw & Wong F-based intervals (as printed by common ICC software for this matrix)
        assert rel.icc_ci(SF, "ICC(1,1)") == pytest.approx((-0.133, 0.722), abs=0.01)
        assert rel.icc_ci(SF, "ICC(2,1)") == pytest.approx((0.019, 0.761), abs=0.01)
        assert rel.icc_ci(SF, "ICC(3,1)") == pytest.approx((0.342, 0.946), abs=0.01)

    def test_the_interval_contains_the_estimate(self):
        for form in ("ICC(1,1)", "ICC(2,1)", "ICC(3,1)"):
            lo, hi = rel.icc_ci(SF, form)
            assert lo < rel.icc(SF)[form] < hi

    def test_a_wider_confidence_level_gives_a_wider_interval(self):
        lo95, hi95 = rel.icc_ci(SF, "ICC(3,1)", level=0.95)
        lo80, hi80 = rel.icc_ci(SF, "ICC(3,1)", level=0.80)
        assert lo95 < lo80 and hi80 < hi95

    def test_unknown_form_is_an_error(self):
        with pytest.raises(ValueError):
            rel.icc_ci(SF, "ICC(9,9)")


class TestSpearmanBrown:
    def test_r_half_gives_two_thirds(self):
        assert rel.spearman_brown(0.5) == pytest.approx(0.6667, abs=5e-5)

    def test_fixed_points_and_factor(self):
        assert rel.spearman_brown(0.0) == 0.0 and rel.spearman_brown(1.0) == 1.0
        assert rel.spearman_brown(0.5, factor=3) == pytest.approx(0.75)   # 3*.5 / (1 + 2*.5)

    def test_negative_correlation_is_not_clipped_but_stays_finite(self):
        assert np.isfinite(rel.spearman_brown(-0.4))


class TestICCProperties:
    def test_perfect_agreement_gives_one_for_icc_3_1(self):
        x = np.arange(10, dtype=float)
        X = np.column_stack([x, x])
        r = rel.icc(X)
        assert r["ICC(3,1)"] == pytest.approx(1.0) and r["ICC(2,1)"] == pytest.approx(1.0)

    def test_consistency_ignores_a_constant_shift_but_agreement_does_not(self):
        rng = np.random.default_rng(1)
        x = rng.normal(size=30)
        X = np.column_stack([x, x + 5.0 + rng.normal(scale=0.1, size=30)])
        r = rel.icc(X)
        assert r["ICC(3,1)"] > 0.98
        assert r["ICC(2,1)"] < r["ICC(3,1)"] - 0.2

    def test_matches_the_known_simulated_icc_on_average(self):
        rng = np.random.default_rng(7)
        vals = []
        for _ in range(300):
            day = rng.normal(scale=1.0, size=21)
            X = np.column_stack([day + rng.normal(scale=1.0, size=21), day + rng.normal(scale=1.0, size=21)])   # true ICC = 0.5
            vals.append(rel.icc(X)["ICC(3,1)"])
        assert np.mean(vals) == pytest.approx(0.5, abs=0.04)

    def test_too_few_targets_or_raters_is_an_error(self):
        with pytest.raises(ValueError):
            rel.icc(np.ones((2, 2)))
        with pytest.raises(ValueError):
            rel.icc(np.ones((10, 1)))

    def test_nan_rows_are_rejected_not_silently_dropped(self):
        X = SF.copy()
        X[0, 0] = np.nan
        with pytest.raises(ValueError):
            rel.icc(X)

    def test_zero_variance_gives_nan_not_an_exception(self):
        r = rel.icc(np.ones((6, 2)))
        assert np.isnan(r["ICC(3,1)"])

    def test_coverage_of_the_f_interval_is_near_nominal(self):
        rng = np.random.default_rng(11)
        hit, n = 0, 400
        for _ in range(n):
            day = rng.normal(size=21)
            X = np.column_stack([day + rng.normal(size=21), day + rng.normal(size=21)])
            lo, hi = rel.icc_ci(X, "ICC(3,1)")
            hit += lo <= 0.5 <= hi
        assert 0.91 <= hit / n <= 0.99


class TestBootstrapOverDays:
    def test_bootstrap_interval_is_reproducible_and_contains_the_estimate(self):
        a = rel.icc_bootstrap_ci(SF, "ICC(3,1)", n_boot=500, seed=3)
        b = rel.icc_bootstrap_ci(SF, "ICC(3,1)", n_boot=500, seed=3)
        assert a == b
        assert a[0] < rel.icc(SF)["ICC(3,1)"] < a[1]

    def test_default_uses_at_least_10000_resamples(self):
        import inspect
        assert inspect.signature(rel.icc_bootstrap_ci).parameters["n_boot"].default >= 10_000


def simulate(n_days=21, seed=0, trend=0.0, day_sd=1.0, noise_sd=1.0):
    """Two sessions per day (k = 2*(day-1)+PM+1), y = trend*(ln k) + day effect + noise."""
    rng = np.random.default_rng(seed)
    days = np.repeat(np.arange(1, n_days + 1), 2)
    pm = np.tile([0, 1], n_days)
    k = 2 * (days - 1) + pm + 1
    y = trend * np.log(k) + np.repeat(rng.normal(scale=day_sd, size=n_days), 2) + rng.normal(scale=noise_sd, size=2 * n_days)
    return days, pm, k, y


class TestResiduals:
    def test_residuals_are_orthogonal_to_the_practice_terms(self):
        days, pm, k, y = simulate(trend=2.0, seed=2)
        res = rel.practice_residuals(y, k)
        assert abs(res.sum()) < 1e-9
        assert abs(res @ k) < 1e-6 and abs(res @ np.log(k)) < 1e-6
        assert res.shape == y.shape

    def test_residuals_remove_a_pure_practice_curve(self):
        k = np.arange(1.0, 43.0)
        y = 3 + 0.2 * k + 1.5 * np.log(k)
        assert np.allclose(rel.practice_residuals(y, k), 0, atol=1e-9)

    def test_too_few_sessions_is_an_error(self):
        with pytest.raises(ValueError):
            rel.practice_residuals(np.array([1.0, 2.0, 3.0]), np.array([1.0, 2.0, 3.0]))


class TestPairedMatrix:
    def test_only_days_with_both_sessions_are_kept(self):
        days = np.array([1, 1, 2, 3, 3, 4])
        pm = np.array([0, 1, 0, 0, 1, 1])
        y = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])
        X, kept = rel.paired_matrix(days, pm, y)
        assert kept.tolist() == [1, 3]
        assert X.tolist() == [[1.0, 2.0], [4.0, 5.0]]

    def test_columns_are_am_then_pm_whatever_the_input_order(self):
        X, kept = rel.paired_matrix(np.array([1, 1]), np.array([1, 0]), np.array([20.0, 10.0]))
        assert X.tolist() == [[10.0, 20.0]]

    def test_duplicate_slots_are_an_error(self):
        with pytest.raises(ValueError):
            rel.paired_matrix(np.array([1, 1, 1]), np.array([0, 0, 1]), np.array([1.0, 2.0, 3.0]))


class TestTestRetest:
    def test_a_shared_practice_trend_inflates_the_raw_icc_but_not_the_residual_icc(self):
        raw, res = [], []
        for seed in range(60):
            days, pm, k, y = simulate(seed=seed, trend=1.5, day_sd=0.0, noise_sd=1.0)   # no true day-to-day stability
            out = rel.test_retest(days, pm, k, y)
            raw.append(out["raw"]["ICC(3,1)"]); res.append(out["residual"]["ICC(3,1)"])
        assert np.mean(raw) > 0.15            # the trend alone creates apparent stability
        assert abs(np.mean(res)) < 0.15       # removed by the y ~ k + ln(k) residuals

    def test_residual_icc_recovers_a_true_day_effect(self):
        vals = []
        for seed in range(80):
            days, pm, k, y = simulate(seed=seed, trend=1.0, day_sd=1.0, noise_sd=1.0)   # true ICC = 0.5
            vals.append(rel.test_retest(days, pm, k, y)["residual"]["ICC(3,1)"])
        assert np.mean(vals) == pytest.approx(0.5, abs=0.07)

    def test_output_has_raw_and_residual_with_icc_3_1_icc_2_1_and_intervals(self):
        days, pm, k, y = simulate(seed=5)
        out = rel.test_retest(days, pm, k, y, n_boot=200)
        assert out["n_days"] == 21
        for part in ("raw", "residual"):
            o = out[part]
            for form in ("ICC(3,1)", "ICC(2,1)"):
                assert form in o and len(o[f"{form} CI"]) == 2 and len(o[f"{form} bootstrap CI"]) == 2
        assert out["primary"] == "residual ICC(3,1)"

    def test_missing_sessions_use_only_complete_days_and_report_how_many(self):
        days, pm, k, y = simulate(seed=6)
        keep = np.ones(len(y), bool); keep[[0, 5, 9]] = False     # three sessions missing
        out = rel.test_retest(days[keep], pm[keep], k[keep], y[keep], n_boot=100)
        assert out["n_days"] == 18 and out["n_sessions"] == 39

    def test_fewer_than_three_complete_days_is_an_error(self):
        with pytest.raises(ValueError):
            rel.test_retest(np.array([1, 1, 2, 2]), np.array([0, 1, 0, 1]), np.array([1, 2, 3, 4.0]), np.array([1, 2, 3, 5.0]))


class TestSplitHalf:
    def test_odd_even_split_of_trials(self):
        odd, even = rel.split_trials(list(range(1, 11)))
        assert odd == [1, 3, 5, 7, 9] and even == [2, 4, 6, 8, 10]

    def test_perfectly_consistent_halves_give_one(self):
        x = np.arange(12, dtype=float)
        out = rel.split_half(np.column_stack([x, 2 * x + 1]))
        assert out["r"] == pytest.approx(1.0) and out["spearman_brown"] == pytest.approx(1.0)

    def test_spearman_brown_is_applied_to_the_half_correlation(self):
        rng = np.random.default_rng(4)
        t = rng.normal(size=40)
        halves = np.column_stack([t + rng.normal(size=40), t + rng.normal(size=40)])
        out = rel.split_half(halves)
        assert out["spearman_brown"] == pytest.approx(rel.spearman_brown(out["r"]))
        assert out["spearman_brown"] > out["r"]
        lo, hi = out["spearman_brown_ci"]
        assert lo < out["spearman_brown"] < hi

    def test_from_trials_uses_the_supplied_score_function(self):
        sessions = [[1, 2, 3, 4], [2, 3, 4, 5], [5, 6, 7, 8], [3, 3, 9, 9]]
        out = rel.split_half_from_trials(sessions, score=lambda xs: sum(xs) / len(xs))
        assert out["n_sessions"] == 4
        assert out["halves"].shape == (4, 2)
        assert out["halves"][0].tolist() == [2.0, 3.0]    # odd trials 1,3 -> 2.0 ; even trials 2,4 -> 3.0

    def test_sessions_with_a_missing_half_score_are_dropped_and_counted(self):
        out = rel.split_half_from_trials([[1, 2, 3, 4], [1, 2, 3, 4], [5, 6, 7, 8], [5], [2, 4, 9, 9]],
                                         score=lambda xs: float(np.mean(xs)) if len(xs) else float("nan"))
        assert out["n_sessions"] == 4 and out["n_dropped"] == 1

    def test_fewer_than_four_sessions_is_an_error(self):
        with pytest.raises(ValueError):
            rel.split_half(np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 5.0]]))


class TestInterpretation:
    @pytest.mark.parametrize("value,label", [(0.2, "poor"), (0.5, "moderate"), (0.74, "moderate"), (0.75, "good"), (0.89, "good"), (0.9, "excellent")])
    def test_koo_and_li_bands(self, value, label):
        assert rel.interpret(value) == label

    def test_negative_or_nan_values(self):
        assert rel.interpret(-0.1) == "poor" and rel.interpret(float("nan")) == "undefined"

    def test_the_thresholds_are_flagged_unverified(self):
        assert "UNVERIFIED" in rel.KOO_LI_NOTE


class TestGuards:
    def test_module_does_not_read_real_data(self):
        import inspect
        src = inspect.getsource(rel)
        assert "sqlite3" not in src and "score_database" not in src and "load_sessions" not in src
