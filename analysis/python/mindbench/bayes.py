"""MB-20: Bayesian regression with PyMC, matching preregistration D5 and the D3 model (docs/design/prereg_draft.md).

Model, per primary outcome (z-scored across included sessions), sessions ordered by calendar slot:

    y_t = b0 + b_sleep*sleep_c + b_k*k_z + b_lnk*lnk_z + b_pm*pm_z + u_day + e_t,      e AR(1) over slots

`sleep_c` is hours slept centered at its mean; `k` (study session number minus 2), `ln k` and PM are standardized.
Priors: b0 ~ N(0, 1); b_sleep ~ N(0, 0.5) per hour; b_k, b_lnk, b_pm ~ N(0, 1) per SD; day SD ~ HalfNormal(0.5);
residual (marginal) SD ~ HalfNormal(1); AR(1) phi ~ N(0, 0.5) truncated to (-1, 1).

The joint distribution is the D3 model with the day intercept integrated out: Cov(y) = sigma_u^2 * (same day) + sigma^2 * phi^|slot distance|
(AR(1) over calendar slots, so missed sessions leave gaps). The likelihood is written as one-step-ahead predictive densities p(y_t | y_1..y_(t-1))
(Cholesky innovations); their product is the joint density, and their pointwise values are used for LOO and WAIC. Because the day intercept is
integrated out, a session's predictive density uses the earlier session of its day. With dependent data these LOO and WAIC values are
approximate, not true leave-one-out. (Conditioning on explicit day effects was tried first and made LOO insensitive to the sleep term:
sleep is a day-level predictor that the free day effects absorb.)

Simulated data only: this module never reads the database or real outcomes.
"""
import numpy as np
import pymc as pm
import pytensor.tensor as pt
import arviz as az
from scipy.special import logsumexp

PARAMS = ["b0", "b_sleep", "b_k", "b_lnk", "b_pm", "sigma_u", "sigma", "phi"]
PRIORS = {"b0": "N(0, 1)", "b_sleep": "N(0, 0.5) per hour", "b_k": "N(0, 1) per SD", "b_lnk": "N(0, 1) per SD", "b_pm": "N(0, 1) per SD",
          "sigma_u": "HalfNormal(0.5)", "sigma": "HalfNormal(1)", "phi": "N(0, 0.5) truncated to (-1, 1)"}


def _z(x):
    x = np.asarray(x, dtype=float)
    return (x - x.mean()) / x.std()


def prepare(y, sleep, k, pm, days, slots, standardize_y=True):
    """Model inputs: sessions sorted by slot; outcome z-scored; sleep centered (hours); k, ln k, PM standardized; slot gaps and day index."""
    arrays = [np.asarray(a) for a in (y, sleep, k, pm, days, slots)]
    if len({len(a) for a in arrays}) != 1:
        raise ValueError("all inputs must have the same length")
    y, sleep, k, pm_, days, slots = arrays
    order = np.argsort(slots, kind="stable")
    y, sleep, k, pm_, days, slots = (a[order] for a in (y, sleep, k, pm_, days, slots))
    if (np.diff(slots) <= 0).any():
        raise ValueError("two sessions in the same slot (keep only the first before fitting)")
    if len(slots) < 3:
        raise ValueError("need at least 3 sessions")
    if (np.asarray(k, dtype=float) <= 0).any():
        raise ValueError("k must be positive (study session number minus 2)")
    uniq, day_idx = np.unique(days, return_inverse=True)
    y = np.asarray(y, dtype=float)
    return {
        "y": _z(y) if standardize_y else y,
        "sleep_c": np.asarray(sleep, dtype=float) - np.mean(sleep),
        "k_z": _z(k), "lnk_z": _z(np.log(np.asarray(k, dtype=float))), "pm_z": _z(pm_),
        "gap": np.diff(slots).astype(int), "day_idx": day_idx.astype(int), "n_days": len(uniq),
        "slots": slots.astype(int), "days": days,
    }


def subset(d, keep):
    """Drop sessions (missed or excluded), keeping the original standardization; gaps and day index are recomputed."""
    keep = np.asarray(keep, dtype=bool)
    out = {key: (v[keep] if isinstance(v, np.ndarray) and v.shape[:1] == keep.shape and key not in ("gap",) else v) for key, v in d.items()}
    uniq, out["day_idx"] = np.unique(out["days"], return_inverse=True)
    out["n_days"] = len(uniq)
    out["gap"] = np.diff(out["slots"]).astype(int)
    return out


def simulate(n_days, rng, truth, mean_sleep=7.0, sd_sleep=1.0):
    """Simulate two sessions a day from the model itself (standardized scale); `truth` holds the parameter values of PARAMS."""
    days = np.repeat(np.arange(1, n_days + 1), 2)
    pm_ = np.tile([0, 1], n_days)
    slots = 2 * (days - 1) + pm_ + 1
    k = slots.copy()
    sleep = np.repeat(rng.normal(mean_sleep, sd_sleep, n_days), 2)       # AM and PM share the night's sleep
    d = prepare(np.zeros(len(slots)), sleep, k, pm_, days, slots, standardize_y=False)
    mu = (truth["b0"] + truth["b_sleep"] * d["sleep_c"] + truth["b_k"] * d["k_z"] + truth["b_lnk"] * d["lnk_z"] + truth["b_pm"] * d["pm_z"]
          + rng.normal(0, truth["sigma_u"], n_days)[d["day_idx"]])
    e = np.empty(len(mu))
    e[0] = rng.normal(0, truth["sigma"])
    for t in range(1, len(e)):
        g = d["gap"][t - 1]
        e[t] = truth["phi"] ** g * e[t - 1] + rng.normal(0, truth["sigma"] * np.sqrt(1 - truth["phi"] ** (2 * g)))
    d["y"] = mu + e
    return d


def build_model(d, include_sleep=True):
    """The D5 model. `include_sleep=False` drops the sleep term (for LOO comparison)."""
    with pm.Model() as model:
        b0 = pm.Normal("b0", 0, 1)
        b_k = pm.Normal("b_k", 0, 1)
        b_lnk = pm.Normal("b_lnk", 0, 1)
        b_pm = pm.Normal("b_pm", 0, 1)
        mu = b0 + b_k * d["k_z"] + b_lnk * d["lnk_z"] + b_pm * d["pm_z"]
        if include_sleep:
            b_sleep = pm.Normal("b_sleep", 0, 0.5)
            mu = mu + b_sleep * d["sleep_c"]
        sigma_u = pm.HalfNormal("sigma_u", 0.5)
        sigma = pm.HalfNormal("sigma", 1)
        phi = pm.TruncatedNormal("phi", 0, 0.5, lower=-1, upper=1)
        # Joint covariance of the D3 model with the day intercept integrated out: V = sigma_u^2 * same-day + sigma^2 * phi^|slot distance|.
        # Its Cholesky factor gives the one-step-ahead predictive density of each session given the earlier ones.
        dist = np.abs(d["slots"][:, None] - d["slots"][None, :])
        same_day = (d["day_idx"][:, None] == d["day_idx"][None, :]).astype(float)
        V = sigma_u ** 2 * same_day + sigma ** 2 * phi ** dist + 1e-8 * np.eye(len(d["y"]))
        L = pt.linalg.cholesky(V)
        diag = pt.diag(L)
        eps = pt.linalg.solve_triangular(L, d["y"] - mu, lower=True)
        cond_mean = mu + (L - pt.diag(diag)) @ eps
        pm.Normal("y", mu=cond_mean, sigma=diag, observed=d["y"])
    return model


def fit(d, include_sleep=True, draws=1000, tune=1000, chains=4, seed=1, target_accept=0.9):
    """Sample with NUTS and attach the pointwise one-step-ahead log-likelihood (group log_likelihood, variable y)."""
    model = build_model(d, include_sleep)
    with model:
        idata = pm.sample(draws=draws, tune=tune, chains=chains, cores=1, random_seed=seed, target_accept=target_accept,
                          progressbar=False, compute_convergence_checks=False)
        pm.compute_log_likelihood(idata, progressbar=False)
    return idata


def _present(idata):
    return [p for p in PARAMS if p in idata.posterior.data_vars]


def diagnostics(idata):
    """R-hat, effective sample sizes and divergence count (preregistered thresholds: R-hat < 1.01, ESS > 400, no divergences)."""
    names = _present(idata)
    rhat = az.rhat(idata, var_names=names)
    bulk = az.ess(idata, var_names=names, method="bulk")
    tail = az.ess(idata, var_names=names, method="tail")
    get = lambda tree: [float(np.asarray(tree[n].values).min()) for n in names]
    rhat_max = [float(np.asarray(rhat[n].values).max()) for n in names]
    return {"max_rhat": max(rhat_max), "min_ess_bulk": min(get(bulk)), "min_ess_tail": min(get(tail)),
            "n_divergences": int(idata.sample_stats["diverging"].values.sum()), "n_draws": int(idata.posterior.sizes["chain"] * idata.posterior.sizes["draw"])}


def summarize(idata):
    """Posterior mean, SD, 90% and 95% equal-tailed intervals per parameter, plus P(b_sleep > 0) when the sleep term is in the model."""
    out = {}
    for p in _present(idata):
        x = np.asarray(idata.posterior[p].values).ravel()
        out[p] = {"mean": float(x.mean()), "sd": float(x.std(ddof=1)), "ci95": tuple(float(v) for v in np.quantile(x, [0.025, 0.975])),
                  "ci90": tuple(float(v) for v in np.quantile(x, [0.05, 0.95]))}
    if "b_sleep" in out:
        out["P(b_sleep>0)"] = float((np.asarray(idata.posterior["b_sleep"].values) > 0).mean())
    return out


def waic_from_loglik(ll):
    """WAIC (Watanabe) from a (chain, draw, obs) pointwise log-likelihood array: elpd_waic = sum(lppd - p_waic), on the log-score scale."""
    ll = np.asarray(ll, dtype=float)
    flat = ll.reshape(-1, ll.shape[-1])
    lppd = logsumexp(flat, axis=0) - np.log(flat.shape[0])
    p = flat.var(axis=0, ddof=1)
    pointwise = lppd - p
    n = pointwise.shape[0]
    return {"elpd_waic": float(pointwise.sum()), "p_waic": float(p.sum()), "se": float(np.sqrt(n * np.var(pointwise, ddof=1))), "elpd_i": pointwise}


def _loglik(idata):
    return np.asarray(idata.log_likelihood["y"].values)


def loo_report(idata):
    """PSIS-LOO and WAIC on the one-step-ahead log-likelihood, with Pareto-k counts (good <= .5, ok <= .7, bad <= 1, very bad > 1)."""
    loo = az.loo(idata)
    k = np.asarray(loo.pareto_k.values if hasattr(loo.pareto_k, "values") else loo.pareto_k).ravel()
    w = waic_from_loglik(_loglik(idata))
    return {"elpd_loo": float(loo.elpd), "se": float(loo.se), "p_loo": float(loo.p), "pareto_k_max": float(np.nanmax(k)),
            "n_good": int((k <= 0.5).sum()), "n_ok": int(((k > 0.5) & (k <= 0.7)).sum()), "n_bad": int(((k > 0.7) & (k <= 1)).sum()),
            "n_very_bad": int((k > 1).sum()), "n_obs": int(len(k)), "elpd_waic": w["elpd_waic"], "p_waic": w["p_waic"], "se_waic": w["se"],
            "approximate": "pointwise terms are one-step-ahead conditional densities; with dependent observations LOO is approximate"}


def _elpd_i(idata):
    loo = az.loo(idata)
    return np.asarray(loo.elpd_i.values if hasattr(loo.elpd_i, "values") else loo.elpd_i).ravel()


def compare_sleep(full, null, threshold=2.0):
    """LOO comparison of the model with the sleep term against the model without it (same observations)."""
    a, b = _elpd_i(full), _elpd_i(null)
    diff = a - b
    n = len(diff)
    d, se = float(diff.sum()), float(np.sqrt(n * np.var(diff, ddof=1)))
    preferred = "with sleep" if d > threshold * se else ("without sleep" if d < -threshold * se else "no clear preference")
    return {"elpd_diff": d, "se_diff": se, "preferred": preferred, "elpd_full": float(a.sum()), "elpd_null": float(b.sum())}
