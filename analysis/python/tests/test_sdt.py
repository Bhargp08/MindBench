import pytest

from mindbench.sdt import dprime_from_counts, dprime_from_rates


class TestRatesNoCorrection:
    def test_h80_fa20(self):
        r = dprime_from_rates(0.80, 0.20)
        assert r["d_prime"] == pytest.approx(1.6832, abs=5e-5)
        assert r["criterion"] == pytest.approx(0.0, abs=1e-12)

    def test_h90_fa30(self):
        r = dprime_from_rates(0.90, 0.30)
        assert r["d_prime"] == pytest.approx(1.8060, abs=5e-5)
        assert r["criterion"] == pytest.approx(-0.3786, abs=5e-5)

    @pytest.mark.parametrize("h,f", [(1.0, 0.2), (0.8, 0.0), (0.0, 0.5), (0.5, 1.0), (-0.1, 0.5), (0.5, 1.2)])
    def test_extreme_or_invalid_rates_are_rejected(self, h, f):
        with pytest.raises(ValueError):
            dprime_from_rates(h, f)


class TestCountsLogLinear:
    """Hautus (1995): H = (hits + 0.5) / (n_signal + 1), FA = (false alarms + 0.5) / (n_noise + 1)."""

    def test_50_of_50_hits_0_of_50_false_alarms(self):
        r = dprime_from_counts(hits=50, n_signal=50, false_alarms=0, n_noise=50)
        assert r["hit_rate"] == pytest.approx(0.990196, abs=1e-6)
        assert r["false_alarm_rate"] == pytest.approx(0.009804, abs=1e-6)
        assert r["d_prime"] == pytest.approx(4.6675, abs=5e-5)
        assert r["criterion"] == pytest.approx(0.0, abs=1e-12)

    def test_hand_worked_example_15_of_18_and_6_of_40(self):
        # H = 15.5/19, FA = 6.5/41: d' = 1.899925, c = 0.050528 (computed with scipy)
        r = dprime_from_counts(hits=15, n_signal=18, false_alarms=6, n_noise=40)
        assert r["hit_rate"] == pytest.approx(15.5 / 19)
        assert r["false_alarm_rate"] == pytest.approx(6.5 / 41)
        assert r["d_prime"] == pytest.approx(1.899925, abs=1e-6)
        assert r["criterion"] == pytest.approx(0.050528, abs=1e-6)

    def test_perfect_and_worst_performance_stay_finite(self):
        assert dprime_from_counts(18, 18, 0, 40)["d_prime"] == pytest.approx(4.188857, abs=1e-6)
        assert dprime_from_counts(0, 18, 40, 40)["d_prime"] == pytest.approx(-4.188857, abs=1e-6)

    def test_chance_is_zero(self):
        assert dprime_from_counts(9, 18, 20, 40)["d_prime"] == pytest.approx(0.0, abs=1e-12)

    def test_the_correction_is_applied_to_every_dataset_not_only_extreme_ones(self):
        r = dprime_from_counts(hits=16, n_signal=20, false_alarms=4, n_noise=20)
        assert r["d_prime"] != pytest.approx(1.6832, abs=1e-3)  # uncorrected would be H=.8, FA=.2
        assert r["hit_rate"] == pytest.approx(16.5 / 21)

    def test_none_correction_matches_the_rate_formula_and_rejects_extremes(self):
        r = dprime_from_counts(16, 20, 4, 20, correction="none")
        assert r["d_prime"] == pytest.approx(1.6832, abs=5e-5)
        with pytest.raises(ValueError):
            dprime_from_counts(20, 20, 4, 20, correction="none")
        with pytest.raises(ValueError):
            dprime_from_counts(10, 20, 0, 20, correction="none")

    def test_invalid_counts_are_rejected(self):
        for args in [(19, 18, 0, 40), (-1, 18, 0, 40), (0, 0, 0, 40), (0, 18, 0, 0), (0, 18, 41, 40)]:
            with pytest.raises(ValueError):
                dprime_from_counts(*args)
        with pytest.raises(ValueError):
            dprime_from_counts(1, 2, 1, 2, correction="bogus")
