"""Power analysis for MindBench (MB-04).

Analytic paired-t power plus simulation power for the within-person regression of a DV on
prior-night sleep, with optional AR(1) residuals, shared nightly sleep (AM and PM sessions of a
day get the same sleep value), an AR(1) correction, and Holm correction over m outcomes.

Simulation model: y = r * x + sqrt(1 - r^2) * e, with x ~ N(0, 1) and e unit-variance AR(1)
with coefficient phi. r is therefore the population within-person correlation.
"""
from __future__ import annotations

import numpy as np
from scipy import stats

ALPHA = 0.05


# ---------- analytic paired t ----------
def paired_t_power(dz: float, n: int, alpha: float = ALPHA) -> float:
    """Two-sided paired t-test power for standardized difference dz with n pairs (noncentral t)."""
    df = n - 1
    ncp = dz * np.sqrt(n)
    tcrit = stats.t.ppf(1 - alpha / 2, df)
    return float(stats.nct.sf(tcrit, df, ncp) + stats.nct.cdf(-tcrit, df, ncp))


def paired_t_required_n(dz: float, power: float = 0.8, alpha: float = ALPHA) -> int:
    """Smallest n whose paired-t power is at least `power`."""
    n = 2
    while paired_t_power(dz, n, alpha) < power:
        n += 1
    return n


# ---------- simulation ----------
def _ar1_noise(rng: np.random.Generator, n: int, m: int, phi: float) -> np.ndarray:
    e = np.empty((n, m))
    e[0] = rng.standard_normal(m)
    scale = np.sqrt(1 - phi**2)
    for t in range(1, n):
        e[t] = phi * e[t - 1] + scale * rng.standard_normal(m)
    return e


def _predictor(rng: np.random.Generator, n: int, paired_sleep: bool) -> np.ndarray:
    if paired_sleep:
        return np.repeat(rng.standard_normal((n + 1) // 2), 2)[:n]
    return rng.standard_normal(n)


def _slope_pvalue(x: np.ndarray, y: np.ndarray, method: str) -> float:
    if method == "ols":
        return float(stats.linregress(x, y).pvalue)
    if method == "ar1":  # one-step Cochrane-Orcutt FGLS
        n = len(x)
        resid = y - np.polyval(np.polyfit(x, y, 1), x)
        rho = float(np.sum(resid[1:] * resid[:-1]) / np.sum(resid[:-1] ** 2))
        ys = y[1:] - rho * y[:-1]
        xs = x[1:] - rho * x[:-1]
        X = np.column_stack([np.ones(n - 1), xs])
        beta = np.linalg.lstsq(X, ys, rcond=None)[0]
        res = ys - X @ beta
        se = np.sqrt(res @ res / (n - 3) * np.linalg.inv(X.T @ X)[1, 1])
        return float(2 * stats.t.sf(abs(beta[1] / se), n - 3))
    raise ValueError(f"unknown method {method!r}")


def _holm_reject(p: np.ndarray, alpha: float) -> np.ndarray:
    order = np.argsort(p)
    reject = np.zeros(len(p), dtype=bool)
    for k, i in enumerate(order):
        if p[i] <= alpha / (len(p) - k):
            reject[i] = True
        else:
            break
    return reject


def simulate_corr_power(
    n: int,
    r: float,
    phi: float = 0.0,
    paired_sleep: bool = False,
    method: str = "ols",
    alpha: float = ALPHA,
    n_sims: int = 4000,
    seed: int = 1,
) -> float:
    """Rejection rate of the two-sided slope test. With r = 0 this is the type-I error."""
    rng = np.random.default_rng(seed)
    rejections = 0
    for _ in range(n_sims):
        x = _predictor(rng, n, paired_sleep)
        e = _ar1_noise(rng, n, 1, phi)[:, 0]
        y = r * x + np.sqrt(1 - r**2) * e
        rejections += _slope_pvalue(x, y, method) < alpha
    return rejections / n_sims


def simulate_holm_power(
    n: int,
    r: float,
    m: int = 5,
    n_true: int = 5,
    phi: float = 0.0,
    paired_sleep: bool = False,
    method: str = "ols",
    alpha: float = ALPHA,
    n_sims: int = 2000,
    seed: int = 1,
) -> float:
    """Mean per-outcome power over the n_true truly affected outcomes, after Holm over m outcomes.

    All outcomes share the same sleep predictor and have independent AR(1) errors.
    """
    rng = np.random.default_rng(seed)
    beta = np.array([r] * n_true + [0.0] * (m - n_true))
    hits = np.zeros(m)
    for _ in range(n_sims):
        x = _predictor(rng, n, paired_sleep)
        E = _ar1_noise(rng, n, m, phi)
        Y = np.outer(x, beta) + np.sqrt(1 - beta**2) * E
        p = np.array([_slope_pvalue(x, Y[:, j], method) for j in range(m)])
        hits += _holm_reject(p, alpha)
    return float(hits[:n_true].mean() / n_sims)


def power_curve(ns, r: float, n_sims: int = 1000, seed: int = 1, holm_m: int | None = None, **kw):
    """List of (n, power) for each n. If holm_m is given, uses Holm over that many true outcomes."""
    out = []
    for n in ns:
        if holm_m:
            p = simulate_holm_power(n=n, r=r, m=holm_m, n_true=holm_m, n_sims=n_sims, seed=seed, **kw)
        else:
            p = simulate_corr_power(n=n, r=r, n_sims=n_sims, seed=seed, **kw)
        out.append((n, p))
    return out
