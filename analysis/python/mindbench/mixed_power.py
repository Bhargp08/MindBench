"""Primary H1 model of the preregistration (docs/design/prereg_draft.md, D3) and its power simulation.

Model, per outcome, over included sessions:
    y = b0 + b1*sleep + b2*k + b3*ln(k) + b4*PM + u_day + e
with a random intercept for day (u_day) and AR(1) residuals e over calendar slots, slot = 2*(day-1) + PM + 1, so
missed sessions leave gaps (a gap of g slots has correlation phi**g). Fitted by REML. b1 is tested with a t statistic
on df = (number of included days) - 5.

Covariance of the sessions: V = sigma_u2 * B + sigma_e2 * R(phi), B_ij = 1 for sessions on the same day,
R_ij = phi ** |slot_i - slot_j|. The residual variance is profiled out analytically, so the optimizer searches only
the variance ratio rho = sigma_u2 / sigma_e2 and phi.
"""
import numpy as np
from scipy import optimize, stats

N_FIXED = 5  # intercept, sleep, k, ln k, PM
LOG_RHO_BOUNDS = (-10.0, 5.0)
PHI_BOUND = 0.95
ALPHA = 0.05


def slot_index(day, pm):
    """Calendar slot of a session: two per day (AM then PM), so a missed session leaves a gap."""
    return 2 * (day - 1) + pm + 1


def n_included_days(days):
    return int(len(np.unique(np.asarray(days))))


def design_matrix(sleep, k, pm):
    """Columns: intercept, sleep (centered at its mean over the included sessions), k, ln k, PM."""
    sleep, k, pm = (np.asarray(a, float) for a in (sleep, k, pm))
    return np.column_stack([np.ones(len(sleep)), sleep - sleep.mean(), k, np.log(k), pm])


def covariance(slots, days, sigma_u2, sigma_e2, phi):
    slots, days = np.asarray(slots), np.asarray(days)
    dist = np.abs(slots[:, None] - slots[None, :]).astype(float)
    same_day = (days[:, None] == days[None, :]).astype(float)
    return sigma_u2 * same_day + sigma_e2 * np.power(phi, dist)


def _cho_solve(L, B):
    from scipy.linalg import cho_solve

    return cho_solve((L, True), B)


def _profile(y, X, slots_dist, same_day, rho, phi):
    """Profiled REML pieces for W = rho*B + R(phi): returns (objective, beta, sigma_e2, XtWinvX)."""
    n, p = X.shape
    W = rho * same_day + np.power(phi, slots_dist)
    try:
        L = np.linalg.cholesky(W)
    except np.linalg.LinAlgError:
        return np.inf, None, None, None
    WX = _cho_solve(L, X)
    XtWX = X.T @ WX
    beta = np.linalg.solve(XtWX, X.T @ _cho_solve(L, y))
    r = y - X @ beta
    quad = float(r @ _cho_solve(L, r))
    if quad <= 0:
        return np.inf, None, None, None
    logdet_w = 2.0 * np.log(np.diag(L)).sum()
    logdet_xwx = np.linalg.slogdet(XtWX)[1]
    obj = 0.5 * ((n - p) * np.log(quad / (n - p)) + logdet_w + logdet_xwx)
    return obj, beta, quad / (n - p), XtWX


def fit_reml(y, X, slots, days, fixed=None):
    """REML fit. `fixed` may hold sigma_u2 (only 0.0 is supported: no day effect) and/or phi (a fixed AR(1) value)."""
    fixed = fixed or {}
    if "sigma_u2" in fixed and fixed["sigma_u2"] != 0.0:
        raise ValueError("only sigma_u2 = 0 can be fixed")
    y, X = np.asarray(y, float), np.asarray(X, float)
    slots, days = np.asarray(slots), np.asarray(days)
    dist = np.abs(slots[:, None] - slots[None, :]).astype(float)
    same_day = (days[:, None] == days[None, :]).astype(float)
    free_rho = "sigma_u2" not in fixed
    free_phi = "phi" not in fixed

    def unpack(theta):
        i = 0
        rho = 0.0
        if free_rho:
            rho = float(np.exp(theta[i]))
            i += 1
        phi = float(np.tanh(theta[i])) if free_phi else float(fixed["phi"])
        return rho, phi

    def objective(theta):
        rho, phi = unpack(theta)
        return _profile(y, X, dist, same_day, rho, phi)[0]

    converged = True
    theta = np.array([])
    if free_rho or free_phi:
        x0, bounds = [], []
        if free_rho:
            x0.append(np.log(0.4))
            bounds.append(LOG_RHO_BOUNDS)
        if free_phi:
            x0.append(np.arctanh(0.2))
            bounds.append((-np.arctanh(PHI_BOUND), np.arctanh(PHI_BOUND)))
        res = optimize.minimize(objective, x0, method="L-BFGS-B", bounds=bounds, options={"ftol": 1e-11, "gtol": 1e-7})
        theta, converged = res.x, bool(res.success or np.isfinite(res.fun))
        if free_rho and theta[0] < LOG_RHO_BOUNDS[0] + 0.5:  # near the zero-day-variance boundary: also try the other side
            alt = optimize.minimize(objective, [np.log(0.4)] + ([0.0] if free_phi else []), method="L-BFGS-B", bounds=bounds, options={"ftol": 1e-11})
            if alt.fun < res.fun:
                theta = alt.x
    rho, phi = unpack(theta)
    obj, beta, sigma_e2, XtWX = _profile(y, X, dist, same_day, rho, phi)
    if beta is None:
        return {"converged": False, "beta": np.full(X.shape[1], np.nan), "se": np.full(X.shape[1], np.nan),
                "sigma_u2": np.nan, "sigma_e2": np.nan, "phi": phi}
    cov_beta = sigma_e2 * np.linalg.inv(XtWX)
    return {"beta": beta, "se": np.sqrt(np.diag(cov_beta)), "sigma_u2": rho * sigma_e2, "sigma_e2": sigma_e2, "phi": phi,
            "converged": converged, "reml_objective": obj}


def t_pvalue(b, se, days, n_fixed=N_FIXED):
    """Two-sided p for b/se from a t distribution with df = included days - 5."""
    df = n_included_days(days) - n_fixed
    if df < 1 or not np.isfinite(se) or se <= 0:
        return float("nan")
    return float(2 * stats.t.sf(abs(b / se), df))


def fit_and_test(y, sleep, k, pm, days, slots, model="mixed"):
    """Test of b1 (sleep). model="mixed" is the preregistered primary model; "gls_ar1" drops the day intercept
    (the sensitivity fit) and uses df = sessions - 5."""
    X = design_matrix(sleep, k, pm)
    if model == "mixed":
        fit = fit_reml(y, X, slots, days)
        df = n_included_days(days) - N_FIXED
        p = t_pvalue(fit["beta"][1], fit["se"][1], days)
    elif model == "gls_ar1":
        fit = fit_reml(y, X, slots, days, fixed={"sigma_u2": 0.0})
        df = len(y) - N_FIXED
        p = float(2 * stats.t.sf(abs(fit["beta"][1] / fit["se"][1]), df))
    else:
        raise ValueError(model)
    return {"b1": float(fit["beta"][1]), "se1": float(fit["se"][1]), "p": p, "df": df, "converged": fit["converged"]}


# ------------------------------------------------------------------ simulation
def simulate_sessions(n_days, rng, r, day_share, phi=0.3, n_outcomes=1):
    """One study: n_days days x 2 sessions. Sleep is drawn per day (AM and PM share the night's sleep). Each outcome is
    y = r*sleep + sqrt(1-r^2)*e, with e of unit variance: a day component (share `day_share`) plus AR(1) noise over the
    slots (coefficient phi). `y` has shape (sessions, n_outcomes); outcomes have independent noise."""
    n = 2 * n_days
    day = np.repeat(np.arange(1, n_days + 1), 2)
    pm = np.tile([0, 1], n_days)
    slot = np.array([slot_index(d, p) for d, p in zip(day, pm)])
    k = np.arange(1, n + 1)
    sleep_day = rng.standard_normal(n_days)
    sleep = np.repeat(sleep_day, 2)
    y = np.empty((n, n_outcomes))
    for j in range(n_outcomes):
        u = np.repeat(rng.standard_normal(n_days), 2)
        a = np.empty(n)
        a[0] = rng.standard_normal()
        z = rng.standard_normal(n)
        for t in range(1, n):
            a[t] = phi * a[t - 1] + np.sqrt(1 - phi**2) * z[t]
        e = np.sqrt(day_share) * u + np.sqrt(1 - day_share) * a
        y[:, j] = r * sleep + np.sqrt(1 - r**2) * e
    return {"day": day, "pm": pm, "slot": slot, "k": k, "sleep": sleep, "y": y}


def _holm_two(p_a, p_b, alpha=ALPHA):
    """Holm over two p-values: returns (reject_a, reject_b)."""
    lo, hi = sorted([p_a, p_b])
    first = lo <= alpha / 2
    second = first and hi <= alpha
    rej = {p_a: False, p_b: False}
    if first:
        rej[lo] = True
    if second:
        rej[hi] = True
    if p_a == p_b:
        return second, second
    return rej[p_a], rej[p_b]


def scenario_counts(r, day_share, n_sims, seed, n_days=21, phi=0.3, model="mixed"):
    """Counts for one scenario (so chunks can be combined). Outcome A (and B) have effect r; outcome C has none."""
    rng = np.random.default_rng(seed)
    c = dict(n_sims=n_sims, single_hits=0, single_tests=0, fwer_hits=0, both_hits=0, both_tests=0, one_hits=0, fails=0)
    for _ in range(n_sims):
        d = simulate_sessions(n_days, rng, r, day_share, phi, n_outcomes=3 if r > 0 else 2)
        res = [fit_and_test(d["y"][:, j], d["sleep"], d["k"], d["pm"], d["day"], d["slot"], model=model) for j in range(d["y"].shape[1])]
        c["fails"] += sum(not x["converged"] for x in res)
        pA, pB = res[0]["p"], res[1]["p"]
        if r == 0:
            c["single_hits"] += int(pA < ALPHA) + int(pB < ALPHA)  # two-sided rejection in either direction
            c["single_tests"] += 2
            c["fwer_hits"] += int(min(pA, pB) <= ALPHA / 2)
        else:
            c["single_hits"] += int(pA < ALPHA and res[0]["b1"] > 0) + int(pB < ALPHA and res[1]["b1"] > 0)
            c["single_tests"] += 2
            ra, rb = _holm_two(pA, pB)
            c["both_hits"] += int(ra and res[0]["b1"] > 0) + int(rb and res[1]["b1"] > 0)
            c["both_tests"] += 2
            r_one, _ = _holm_two(pA, res[2]["p"])
            c["one_hits"] += int(r_one and res[0]["b1"] > 0)
    return c


def counts_to_rates(c, r):
    if r == 0:
        return {"type1_single": c["single_hits"] / c["single_tests"], "type1_fwer_holm": c["fwer_hits"] / c["n_sims"], "n_sims": c["n_sims"], "fit_failures": c["fails"]}
    return {"power_single": c["single_hits"] / c["single_tests"], "power_holm_both": c["both_hits"] / c["both_tests"],
            "power_holm_one": c["one_hits"] / c["n_sims"], "n_sims": c["n_sims"], "fit_failures": c["fails"]}


def simulate_scenario(r, day_share, n_sims=2000, seed=1, n_days=21, phi=0.3, model="mixed"):
    """Rates for one scenario. r = 0: type-I error (two-sided rejection of a null outcome, and the Holm family-wise
    rate over two null outcomes). r > 0: power for "supported" (Holm-adjusted p < .05 and b1 > 0): uncorrected,
    Holm with both outcomes true, and Holm with one true and one null outcome."""
    return counts_to_rates(scenario_counts(r, day_share, n_sims, seed, n_days, phi, model), r)
