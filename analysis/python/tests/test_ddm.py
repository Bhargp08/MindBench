"""MB-21: drift-diffusion models (PyDDM). Simulated data only; no real participant data is read."""
import inspect
import math

import numpy as np
import pandas as pd
import pytest

from mindbench import ddm

TRUE = dict(v=(1.5, 3.0), a=1.6, t0=0.3)  # a = 2B (B is the half-width)
HARD = dict(v=(1.0, 2.0), a=1.6, t0=0.3)  # about 10% errors, so the boundary is identifiable


# ------------------------------------------------------------------------------ analytic DDM (spec-verified)
class TestAnalytic:
    def test_formulas_for_v1_B1(self):
        assert ddm.analytic_p_upper(1, 1) == pytest.approx(0.88080, abs=1e-5)
        assert ddm.analytic_mdt(1, 1) == pytest.approx(0.76159, abs=1e-5)

    def test_zero_drift_limits(self):
        assert ddm.analytic_p_upper(0, 1) == pytest.approx(0.5)
        assert ddm.analytic_mdt(0, 1) == pytest.approx(1.0)  # B^2 / sigma^2

    def test_negative_drift_is_symmetric(self):
        assert ddm.analytic_p_upper(-1, 1) == pytest.approx(1 - ddm.analytic_p_upper(1, 1))
        assert ddm.analytic_mdt(-1, 1) == pytest.approx(ddm.analytic_mdt(1, 1))

    def test_pyddm_solution_matches_the_analytic_values(self):
        """Also confirms PyDDM's bound B is the half-width (bounds at +-B)."""
        p, mdt = ddm.solve_reference(v=1.0, B=1.0)
        assert p == pytest.approx(0.88080, abs=1e-3)
        assert mdt == pytest.approx(0.76159, abs=1e-2)


# ------------------------------------------------------------------------------ EZ-diffusion
class TestEZ:
    def test_wagenmakers_2007_worked_example(self):
        r = ddm.ez_diffusion(pc=0.802, vrt=0.112, mrt=0.723, s=0.1)
        assert r["v"] == pytest.approx(0.0999, abs=5e-4)
        assert r["a"] == pytest.approx(0.1400, abs=5e-4)
        assert r["ter"] == pytest.approx(0.3000, abs=5e-4)
        assert r["edge_corrected"] is False

    def test_error_prone_responding_gives_negative_drift(self):
        assert ddm.ez_diffusion(pc=0.3, vrt=0.1, mrt=0.7)["v"] < 0

    @pytest.mark.parametrize("pc", [0.0, 0.5, 1.0])
    def test_edge_values_are_corrected_and_flagged(self, pc):
        r = ddm.ez_diffusion(pc=pc, vrt=0.1, mrt=0.7, n=100)
        assert r["edge_corrected"] is True
        assert all(math.isfinite(r[k]) for k in ("v", "a", "ter"))

    def test_edge_value_without_n_is_refused(self):
        with pytest.raises(ValueError, match="n"):
            ddm.ez_diffusion(pc=1.0, vrt=0.1, mrt=0.7)

    @pytest.mark.parametrize("kwargs", [dict(pc=1.2, vrt=.1, mrt=.7), dict(pc=.8, vrt=0, mrt=.7), dict(pc=.8, vrt=.1, mrt=-1)])
    def test_bad_inputs_raise(self, kwargs):
        with pytest.raises(ValueError):
            ddm.ez_diffusion(**kwargs)

    def test_ez_on_simulated_data_is_close_to_the_truth(self):
        df = ddm.prepare(ddm.simulate(v=(2.0, 2.0), a=1.6, t0=0.3, n_per_cell=4000, seed=1))
        r = ddm.ez_by_cell(df)
        assert len(r) == 2  # two conditions, one group
        # EZ assumes s = 0.1; with s = 1 truth a=1.6, v=2 -> the same numbers rescaled by 10 (a/10, v/10)
        for row in r:
            assert row["v"] * 10 == pytest.approx(2.0, rel=0.15)
            assert row["a"] * 10 == pytest.approx(1.6, rel=0.15)
            assert row["ter"] == pytest.approx(0.3, abs=0.03)


# ------------------------------------------------------------------------------ data handling
class TestPrepare:
    def df(self, **over):
        d = pd.DataFrame({"rt": [500, 700, 900, 650] * 3, "correct": [1, 1, 0, 1] * 3,
                          "cond": [0, 1] * 6, "group": [0, 0, 0, 0, 1, 1, 1, 1, 0, 1, 0, 1]})
        for k, v in over.items():
            d[k] = v
        return d

    def test_converts_ms_to_seconds_and_codes_booleans(self):
        out = ddm.prepare(self.df())
        assert out["rt"].max() == pytest.approx(0.9)
        assert set(out["correct"].unique()) <= {0, 1}

    @pytest.mark.parametrize("bad_rt", [50, 2500, -10, float("nan")])
    def test_rts_outside_the_analysed_range_raise(self, bad_rt):
        d = self.df()
        d.loc[0, "rt"] = bad_rt
        with pytest.raises(ValueError, match="rt"):
            ddm.prepare(d)

    def test_needs_both_conditions_and_both_groups_to_compare(self):
        one_group = ddm.prepare(self.df(group=0))
        with pytest.raises(ValueError, match="group"):
            ddm.compare_models(one_group)
        with pytest.raises(ValueError, match="group"):
            ddm.prepare(self.df(group=2))
        with pytest.raises(ValueError, match="cond"):
            ddm.prepare(self.df(cond=0))

    def test_missing_columns_raise(self):
        with pytest.raises(ValueError, match="column"):
            ddm.prepare(self.df().drop(columns=["correct"]))


class TestGroups:
    def sessions(self):
        return pd.DataFrame({"session": range(1, 8), "hours_slept": [5.0, 6.0, 7.0, 7.0, 7.0, 8.0, 9.0],
                             "time_of_day": ["AM", "PM", "AM", "PM", "AM", "PM", "AM"]})

    def test_sleep_split_is_at_the_median_and_leaves_the_median_out(self):
        g = ddm.assign_groups(self.sessions(), by="sleep").set_index("session")["group"]
        assert g.loc[[1, 2]].tolist() == [0, 0] and g.loc[[6, 7]].tolist() == [1, 1]
        assert g.loc[[3, 4, 5]].isna().all()  # median is 7.0

    def test_time_of_day_split_is_am_vs_pm(self):
        g = ddm.assign_groups(self.sessions(), by="tod").set_index("session")["group"]
        assert g.tolist() == [0, 1, 0, 1, 0, 1, 0]

    def test_unknown_split_raises(self):
        with pytest.raises(ValueError):
            ddm.assign_groups(self.sessions(), by="weather")


# ------------------------------------------------------------------------------ fitting and recovery
class TestRecovery:
    def test_simulation_is_reproducible_and_has_the_right_shape(self):
        a = ddm.simulate(**TRUE, n_per_cell=50, seed=3)
        b = ddm.simulate(**TRUE, n_per_cell=50, seed=3)
        pd.testing.assert_frame_equal(a, b)
        assert 90 <= len(a) <= 100 and set(a.columns) >= {"rt", "correct", "cond", "group"}
        assert a["rt"].min() > 100  # ms, above the non-decision time

    def test_parameter_recovery_within_10_percent_on_average_over_10_seeds(self):
        """500 trials x 2 conditions with known (v, a, t0)."""
        errs = {"v0": [], "v1": [], "a": [], "t0": []}
        for seed in range(10):
            df = ddm.prepare(ddm.simulate(**TRUE, n_per_cell=500, seed=100 + seed))
            fit = ddm.fit_model(df, "null")
            p = fit["params"]
            errs["v0"].append(abs(p["v0"] - TRUE["v"][0]) / TRUE["v"][0])
            errs["v1"].append(abs(p["v1"] - TRUE["v"][1]) / TRUE["v"][1])
            errs["a"].append(abs(p["a"] - TRUE["a"]) / TRUE["a"])
            errs["t0"].append(abs(p["t0"] - TRUE["t0"]) / TRUE["t0"])
        for name, e in errs.items():
            assert np.mean(e) < 0.10, (name, np.mean(e))

    def test_fit_reports_bic_with_the_right_parameter_count(self):
        df = ddm.prepare(ddm.simulate(**TRUE, n_per_cell=200, groups=(0, 1), seed=5))
        nulls = ddm.fit_model(df, "null")
        both = ddm.fit_model(df, "both")
        assert nulls["k"] == 4 and both["k"] == 6 and nulls["n"] == len(df)
        assert math.isfinite(nulls["bic"]) and math.isfinite(both["bic"])

    def test_unknown_model_raises(self):
        df = ddm.prepare(ddm.simulate(**TRUE, n_per_cell=20, groups=(0, 1), seed=5))
        with pytest.raises(ValueError):
            ddm.fit_model(df, "magic")


# ------------------------------------------------------------------------------ model comparison
class TestComparison:
    def test_drift_only_effect_is_picked_in_at_least_8_of_10_simulations(self):
        picked = 0
        for seed in range(10):
            raw = ddm.simulate(**HARD, dv=1.0, n_per_cell=300, groups=(0, 1), seed=200 + seed)
            res = ddm.compare_models(ddm.prepare(raw))
            picked += res["verdict"] == "drift"
        assert picked >= 8, picked

    def test_a_boundary_only_effect_is_not_called_drift(self):
        raw = ddm.simulate(**HARD, da=-0.6, n_per_cell=500, groups=(0, 1), seed=302)
        res = ddm.compare_models(ddm.prepare(raw))
        assert res["boundary_identifiable"] is True
        assert res["verdict"] in ("boundary", "both", "cannot tell")
        assert res["verdict"] != "drift"

    def test_a_wider_boundary_that_removes_errors_makes_the_boundary_unidentifiable_and_says_so(self):
        """Prereg D7 rule at work: the drift model then mimics the boundary change, so the result carries a caveat."""
        raw = ddm.simulate(**HARD, da=0.8, n_per_cell=500, groups=(0, 1), seed=300)
        res = ddm.compare_models(ddm.prepare(raw))
        assert res["boundary_identifiable"] is False
        assert "cannot exclude a boundary change" in res["note"]

    def test_no_effect_is_not_reported_as_an_effect_in_most_simulations(self):
        wrong = 0
        for seed in range(6):
            raw = ddm.simulate(**HARD, n_per_cell=250, groups=(0, 1), seed=400 + seed)
            wrong += ddm.compare_models(ddm.prepare(raw))["verdict"] in ("drift", "boundary", "both")
        assert wrong <= 2, wrong

    def test_a_difference_under_2_bic_units_is_reported_as_cannot_tell(self):
        v = ddm.verdict({"null": 100.0, "drift": 99.0, "boundary": 105.0, "both": 104.0})
        assert v["verdict"] == "cannot tell" and v["best"] == "drift"
        assert ddm.verdict({"null": 100.0, "drift": 90.0, "boundary": 105.0, "both": 104.0})["verdict"] == "drift"
        assert ddm.verdict({"null": 90.0, "drift": 100.0, "boundary": 105.0, "both": 104.0})["verdict"] == "neither"

    def test_boundary_is_not_identifiable_when_errors_are_under_5_percent(self):
        raw = ddm.simulate(v=(4.0, 4.5), a=1.6, t0=0.3, n_per_cell=300, groups=(0, 1), seed=7)
        df = ddm.prepare(raw)
        assert (1 - df["correct"].mean()) < 0.05
        res = ddm.compare_models(df)
        assert res["boundary_identifiable"] is False
        assert set(res["bic"]) == {"null", "drift"}
        assert res["verdict"] in ("neither", "drift", "cannot tell")

    def test_boundary_is_identifiable_with_enough_errors(self):
        df = ddm.prepare(ddm.simulate(**HARD, n_per_cell=200, groups=(0, 1), seed=8))
        res = ddm.compare_models(df)
        assert res["boundary_identifiable"] is True
        assert set(res["bic"]) == {"null", "drift", "boundary", "both"}

    def test_error_share_is_checked_in_each_group(self):
        df = ddm.prepare(ddm.simulate(**HARD, n_per_cell=200, groups=(0, 1), seed=8))
        low = df.copy()
        low.loc[low["group"] == 1, "correct"] = 1  # no errors in group 1
        assert ddm.boundary_identifiable(df) is True
        assert ddm.boundary_identifiable(low) is False


# ------------------------------------------------------------------------------ predictive checks
class TestPredictiveChecks:
    def test_quantiles_levels_and_small_cells(self):
        df = ddm.prepare(ddm.simulate(**TRUE, n_per_cell=400, seed=9))
        q = ddm.rt_quantiles(df)
        assert sorted(q["quantile"].unique()) == [0.1, 0.3, 0.5, 0.7, 0.9]
        ok = q[(q["response"] == "correct") & (q["cond"] == 1)]
        assert ok["rt"].is_monotonic_increasing
        # a cell with fewer than 5 trials of one response type has NaN quantiles, not invented values
        tiny = df[(df["cond"] == 0)].copy()
        tiny["correct"] = 1
        tiny.iloc[:3, tiny.columns.get_loc("correct")] = 0
        qt = ddm.rt_quantiles(tiny)
        assert qt[(qt["response"] == "error") & (qt["cond"] == 0)]["rt"].isna().all()

    def test_the_true_model_reproduces_the_observed_quantiles(self):
        df = ddm.prepare(ddm.simulate(**TRUE, n_per_cell=3000, seed=10))
        fit = ddm.fit_model(df, "null")
        chk = ddm.predictive_check(fit, df)
        assert set(chk.columns) >= {"cond", "group", "response", "quantile", "observed", "predicted"}
        both = chk.dropna(subset=["observed", "predicted"])
        correct = both[both["response"] == "correct"]
        assert (correct["observed"] - correct["predicted"]).abs().max() < 0.06  # seconds
        assert len(chk) == 2 * 2 * 5  # conditions x responses x quantiles (one group)

    def test_the_figure_is_written(self, tmp_path):
        df = ddm.prepare(ddm.simulate(**TRUE, n_per_cell=300, seed=11))
        fit = ddm.fit_model(df, "null")
        out = ddm.plot_predictive_check(ddm.predictive_check(fit, df), tmp_path / "ppc.png")
        assert out.exists() and out.stat().st_size > 1000


# ------------------------------------------------------------------------------ guards
class TestGuards:
    def test_the_module_never_reads_the_database_or_real_data(self):
        src = inspect.getsource(ddm)
        for forbidden in ("sqlite3", "score_database", "load_sessions", "read_csv"):
            assert forbidden not in src
