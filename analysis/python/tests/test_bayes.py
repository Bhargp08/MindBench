"""MB-20: Bayesian regression (PyMC), prereg D5 matching the D3 model. Simulated data only; never real outcomes.

Model (standardized outcome): y = b0 + b_sleep*sleep_c + b_k*k_z + b_lnk*lnk_z + b_pm*pm_z + u_day + e, e AR(1) over calendar slots.
Priors: b0 ~ N(0,1); b_sleep ~ N(0, 0.5) per hour (sleep centered, in hours); b_k, b_lnk, b_pm ~ N(0,1) per SD of the standardized predictor;
day SD ~ HalfNormal(0.5); residual SD ~ HalfNormal(1); AR(1) phi ~ N(0, 0.5) truncated to (-1, 1) (prereg D5).
Pointwise log-likelihood is the one-step-ahead predictive density of the joint model (day intercept integrated out), used for LOO and WAIC.
"""
import numpy as np
import pytest

from mindbench import bayes

TRUE = {"b0": 0.1, "b_sleep": 0.4, "b_k": -0.3, "b_lnk": 0.4, "b_pm": 0.2, "sigma_u": 0.5, "sigma": 0.8, "phi": 0.3}
PARAMS = list(TRUE)


def small(n_days=21, seed=0, **over):
    return bayes.simulate(n_days, np.random.default_rng(seed), {**TRUE, **over})


class TestPrepare:
    def test_sleep_is_centered_in_hours_and_other_predictors_are_standardized(self):
        d = small(seed=1)
        assert abs(d["sleep_c"].mean()) < 1e-9
        for key in ("k_z", "lnk_z", "pm_z"):
            assert abs(d[key].mean()) < 1e-9 and d[key].std() == pytest.approx(1.0, abs=1e-9)


    def test_prepare_standardizes_the_outcome_and_centers_sleep(self):
        rng = np.random.default_rng(2)
        days = np.repeat(np.arange(1, 6), 2); pm = np.tile([0, 1], 5); k = 2 * (days - 1) + pm + 1
        d = bayes.prepare(y=rng.normal(50, 10, 10), sleep=np.repeat([6, 7, 8, 9, 5.0], 2), k=k, pm=pm, days=days, slots=2 * (days - 1) + pm + 1)
        assert abs(d["y"].mean()) < 1e-9 and d["y"].std() == pytest.approx(1.0)
        assert d["sleep_c"].tolist() == pytest.approx([-1, -1, 0, 0, 1, 1, 2, 2, -2, -2])

    def test_slot_gaps_and_day_index(self):
        days = np.array([1, 1, 2, 4, 4]); pm = np.array([0, 1, 1, 0, 1]); slots = 2 * (days - 1) + pm + 1
        d = bayes.prepare(y=np.arange(5.0), sleep=np.ones(5) * 7, k=slots, pm=pm, days=days, slots=slots)
        assert d["gap"].tolist() == [1, 2, 3, 1]               # slots 1,2,4,7,8 -> missed sessions leave gaps
        assert d["day_idx"].tolist() == [0, 0, 1, 2, 2] and d["n_days"] == 3

    def test_two_sessions_in_the_same_slot_are_an_error(self):
        with pytest.raises(ValueError, match="slot"):
            bayes.prepare(y=np.arange(4.0), sleep=np.ones(4), k=np.array([1, 2, 2, 3]), pm=np.array([0, 1, 1, 0]),
                          days=np.array([1, 1, 1, 2]), slots=np.array([1, 2, 2, 3]))

    def test_unsorted_input_is_sorted_by_slot(self):
        days = np.array([2, 1, 1]); pm = np.array([0, 1, 0]); slots = 2 * (days - 1) + pm + 1
        d = bayes.prepare(y=np.array([3.0, 2.0, 1.0]), sleep=np.array([7, 6, 6.0]), k=slots, pm=pm, days=days, slots=slots)
        assert d["slots"].tolist() == [1, 2, 3]


class TestPriors:
    def test_prior_scales_match_the_registered_values(self):
        with bayes.build_model(small(seed=3)) as m:
            import pymc as pm
            prior = pm.sample_prior_predictive(draws=4000, random_seed=5, var_names=PARAMS).prior
        sd = {p: float(prior[p].values.std()) for p in PARAMS}
        assert sd["b0"] == pytest.approx(1.0, rel=0.08)
        assert sd["b_sleep"] == pytest.approx(0.5, rel=0.08)
        for p in ("b_k", "b_lnk", "b_pm"):
            assert sd[p] == pytest.approx(1.0, rel=0.08)
        assert float(prior["sigma_u"].values.mean()) == pytest.approx(0.5 * np.sqrt(2 / np.pi), rel=0.08)   # HalfNormal(0.5)
        assert float(prior["sigma"].values.mean()) == pytest.approx(1.0 * np.sqrt(2 / np.pi), rel=0.08)     # HalfNormal(1)
        assert float(prior["phi"].values.min()) > -1 and float(prior["phi"].values.max()) < 1
        assert float(prior["phi"].values.std()) == pytest.approx(0.5, rel=0.15)

    def test_model_without_the_sleep_term_has_no_sleep_parameter(self):
        m = bayes.build_model(small(seed=3), include_sleep=False)
        assert "b_sleep" not in [v.name for v in m.free_RVs]
        assert "b_sleep" in [v.name for v in bayes.build_model(small(seed=3)).free_RVs]


class TestOneStepAheadLikelihood:
    def test_pointwise_loglik_is_the_one_step_ahead_predictive_density_of_the_joint_model(self):
        from scipy import stats
        d = small(n_days=6, seed=4)
        idata = bayes.fit(d, draws=40, tune=100, chains=1, seed=1)
        ll = idata.log_likelihood["y"].values[0, 0]       # first draw, all observations
        post = {p: float(idata.posterior[p].values[0, 0]) for p in PARAMS}
        mu = post["b0"] + post["b_sleep"] * d["sleep_c"] + post["b_k"] * d["k_z"] + post["b_lnk"] * d["lnk_z"] + post["b_pm"] * d["pm_z"]
        dist = np.abs(d["slots"][:, None] - d["slots"][None, :])
        same = (d["day_idx"][:, None] == d["day_idx"][None, :]).astype(float)
        V = post["sigma_u"] ** 2 * same + post["sigma"] ** 2 * post["phi"] ** dist
        expect = np.empty(len(mu))
        for t in range(len(mu)):
            if t == 0:
                expect[t] = stats.norm.logpdf(d["y"][0], mu[0], np.sqrt(V[0, 0]))
                continue
            S11, s12 = V[:t, :t], V[:t, t]
            w = np.linalg.solve(S11, s12)
            m = mu[t] + w @ (d["y"][:t] - mu[:t])
            var = V[t, t] - s12 @ w
            expect[t] = stats.norm.logpdf(d["y"][t], m, np.sqrt(var))
        assert ll == pytest.approx(expect, abs=1e-5)
        # the pointwise terms add up to the joint multivariate normal log density
        assert ll.sum() == pytest.approx(stats.multivariate_normal(mu, V).logpdf(d["y"]), abs=1e-5)

    def test_missed_sessions_use_the_gap_between_slots(self):
        d = small(n_days=8, seed=5)
        keep = np.ones(len(d["y"]), bool); keep[[3, 4, 9]] = False
        d2 = bayes.subset(d, keep)
        assert d2["gap"].max() >= 2 and len(d2["y"]) == len(d["y"]) - 3
        idata = bayes.fit(d2, draws=30, tune=80, chains=1, seed=1)
        assert idata.log_likelihood["y"].shape[-1] == len(d2["y"])


class TestWAICAndLOO:
    def test_waic_matches_the_textbook_formula(self):
        rng = np.random.default_rng(0)
        ll = rng.normal(-1.0, 0.3, size=(2, 50, 12))
        w = bayes.waic_from_loglik(ll)
        flat = ll.reshape(-1, 12)
        from scipy.special import logsumexp
        lppd = logsumexp(flat, axis=0) - np.log(flat.shape[0])
        p = flat.var(axis=0, ddof=1)
        assert w["elpd_waic"] == pytest.approx(float((lppd - p).sum()))
        assert w["p_waic"] == pytest.approx(float(p.sum()))
        assert w["se"] == pytest.approx(float(np.sqrt(12 * np.var(lppd - p, ddof=1))))

    def test_loo_report_includes_pareto_k_counts_and_max(self):
        idata = bayes.fit(small(n_days=10, seed=6), draws=200, tune=200, chains=2, seed=2)
        r = bayes.loo_report(idata)
        for key in ("elpd_loo", "se", "p_loo", "pareto_k_max", "n_good", "n_ok", "n_bad", "n_very_bad", "elpd_waic", "p_waic", "n_obs"):
            assert key in r
        assert r["n_good"] + r["n_ok"] + r["n_bad"] + r["n_very_bad"] == r["n_obs"] == 20
        assert np.isfinite(r["pareto_k_max"])


class TestDiagnostics:
    def test_rhat_ess_and_no_divergences_on_small_simulated_data(self):
        idata = bayes.fit(small(n_days=10, seed=7), draws=500, tune=800, chains=4, seed=3)
        d = bayes.diagnostics(idata)
        assert d["max_rhat"] < 1.01
        assert d["n_divergences"] == 0
        assert d["min_ess_bulk"] > 100 and d["min_ess_tail"] > 100

    def test_summary_has_means_intervals_and_the_sleep_probability(self):
        idata = bayes.fit(small(n_days=10, seed=7), draws=200, tune=300, chains=2, seed=3)
        s = bayes.summarize(idata)
        for p in PARAMS:
            row = s[p]
            assert row["ci95"][0] < row["mean"] < row["ci95"][1] and row["ci90"][0] >= row["ci95"][0]
        assert 0 <= s["P(b_sleep>0)"] <= 1


class TestRecovery:
    def test_90_percent_intervals_cover_the_true_values_for_at_least_80_percent_of_parameters_over_20_sims(self):
        hits = {p: 0 for p in PARAMS}
        for s in range(20):
            d = small(seed=100 + s)
            idata = bayes.fit(d, draws=300, tune=400, chains=2, seed=s)
            summ = bayes.summarize(idata)
            for p in PARAMS:
                lo, hi = summ[p]["ci90"]
                hits[p] += lo <= TRUE[p] <= hi
        cover = {p: hits[p] / 20 for p in PARAMS}
        pooled = sum(hits.values()) / (20 * len(PARAMS))
        assert pooled >= 0.80, cover
        assert min(cover.values()) >= 0.6, cover


class TestModelComparison:
    def test_loo_prefers_the_model_with_sleep_when_the_effect_is_large(self):
        d = small(seed=13, b_sleep=1.2)    # a large effect: 1.2 SD of the outcome per hour of sleep
        full = bayes.fit(d, draws=400, tune=500, chains=2, seed=1)
        null = bayes.fit(d, include_sleep=False, draws=400, tune=500, chains=2, seed=1)
        c = bayes.compare_sleep(full, null)
        assert c["elpd_diff"] > 0 and c["elpd_diff"] > 2 * c["se_diff"]
        assert c["preferred"] == "with sleep"

    def test_loo_does_not_clearly_prefer_the_sleep_model_when_there_is_no_effect(self):
        d = small(seed=12, b_sleep=0.0)
        full = bayes.fit(d, draws=400, tune=500, chains=2, seed=1)
        null = bayes.fit(d, include_sleep=False, draws=400, tune=500, chains=2, seed=1)
        c = bayes.compare_sleep(full, null)
        assert c["elpd_diff"] < 2 * c["se_diff"]


class TestGuards:
    def test_module_does_not_read_real_data(self):
        import inspect
        src = inspect.getsource(bayes)
        assert "sqlite3" not in src and "score_database" not in src and "load_sessions" not in src
