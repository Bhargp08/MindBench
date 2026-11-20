"""MB-19: test-retest reliability (ICC) and split-half reliability.

Pure functions on arrays; this module never reads the database or real outcomes (tests use simulated data only).

Definition (prereg D6, docs/design/prereg_draft.md): ICC(3,1) consistency with days as targets and the AM and PM sessions as
the two measurements, computed on residuals from y ~ k + ln(k) (k = study session number minus 2); the raw ICC is
reported next to it, plus ICC(2,1) for absolute agreement. Shrout & Fleiss (1979) forms from a two-way ANOVA;
F-based confidence intervals (Shrout & Fleiss 1979 for forms 1 and 3, McGraw & Wong 1996 for form 2); a bootstrap over days (10,000 resamples by default).
"""
import numpy as np
from scipy import stats

FORMS = ("ICC(1,1)", "ICC(2,1)", "ICC(3,1)")

KOO_LI_NOTE = ("Koo & Li (2016) bands applied to the point estimate: below .50 poor, .50 to below .75 moderate, .75 to below .90 good, "
               ".90 and above excellent. [UNVERIFIED: thresholds not checked against the paper; Koo & Li apply them to the 95% CI.]")


def _matrix(X):
    X = np.asarray(X, dtype=float)
    if X.ndim != 2:
        raise ValueError("expected a targets x measurements matrix")
    n, k = X.shape
    if n < 3 or k < 2:
        raise ValueError("need at least 3 targets and 2 measurements")
    if not np.isfinite(X).all():
        raise ValueError("missing or non-finite values: pass complete rows only")
    return X, n, k


def _mean_squares(X, n, k):
    grand = X.mean()
    row_m, col_m = X.mean(axis=1), X.mean(axis=0)
    bms = k * np.sum((row_m - grand) ** 2) / (n - 1)          # between targets
    jms = n * np.sum((col_m - grand) ** 2) / (k - 1)          # between measurements (columns)
    sse = np.sum((X - row_m[:, None] - col_m[None, :] + grand) ** 2)
    ems = sse / ((n - 1) * (k - 1))                            # residual
    wms = (np.sum((X - row_m[:, None]) ** 2)) / (n * (k - 1))  # within targets
    return bms, jms, ems, wms


def icc(X):
    """ICC(1,1), ICC(2,1), ICC(3,1) (single measures) and the mean squares of a complete targets x measurements matrix."""
    X, n, k = _matrix(X)
    bms, jms, ems, wms = _mean_squares(X, n, k)

    def ratio(num, den):
        return float(num / den) if den > 0 else float("nan")

    return {
        "ICC(1,1)": ratio(bms - wms, bms + (k - 1) * wms),
        "ICC(2,1)": ratio(bms - ems, bms + (k - 1) * ems + k * (jms - ems) / n),
        "ICC(3,1)": ratio(bms - ems, bms + (k - 1) * ems),
        "BMS": float(bms), "JMS": float(jms), "EMS": float(ems), "WMS": float(wms), "n_targets": n, "n_raters": k,
    }


def icc_ci(X, form="ICC(3,1)", level=0.95):
    """F-based confidence interval for one ICC form (Shrout & Fleiss 1979 for forms 1 and 3; McGraw & Wong 1996 for form 2)."""
    if form not in FORMS:
        raise ValueError(f"unknown ICC form {form!r}; use one of {FORMS}")
    X, n, k = _matrix(X)
    r = icc(X)
    bms, jms, ems, wms = r["BMS"], r["JMS"], r["EMS"], r["WMS"]
    a = 1 - level
    if form == "ICC(1,1)":
        if wms <= 0:
            return (float("nan"), float("nan"))
        F = bms / wms
        fl = F / stats.f.ppf(1 - a / 2, n - 1, n * (k - 1))
        fu = F * stats.f.ppf(1 - a / 2, n * (k - 1), n - 1)
        return ((fl - 1) / (fl + k - 1), (fu - 1) / (fu + k - 1))
    if form == "ICC(3,1)":
        if ems <= 0:
            return (float("nan"), float("nan"))
        F = bms / ems
        dfe = (n - 1) * (k - 1)
        fl = F / stats.f.ppf(1 - a / 2, n - 1, dfe)
        fu = F * stats.f.ppf(1 - a / 2, dfe, n - 1)
        return ((fl - 1) / (fl + k - 1), (fu - 1) / (fu + k - 1))
    # ICC(2,1): Satterthwaite degrees of freedom (McGraw & Wong 1996)
    if ems <= 0:
        return (float("nan"), float("nan"))
    rho = r["ICC(2,1)"]
    fj = jms / ems
    c = n * (1 + (k - 1) * rho) - k * rho
    v = ((k - 1) * (n - 1) * (k * rho * fj + c) ** 2) / ((n - 1) * k ** 2 * rho ** 2 * fj ** 2 + c ** 2)
    f_u = stats.f.ppf(1 - a / 2, n - 1, v)
    f_l = stats.f.ppf(1 - a / 2, v, n - 1)
    lower = n * (bms - f_u * ems) / (f_u * (k * jms + (k * n - k - n) * ems) + n * bms)
    upper = n * (f_l * bms - ems) / (k * jms + (k * n - k - n) * ems + n * f_l * bms)
    return (float(lower), float(upper))


def icc_bootstrap_ci(X, form="ICC(3,1)", level=0.95, n_boot=10_000, seed=20261119):
    """Percentile bootstrap interval resampling whole targets (days) with replacement; resamples with an undefined ICC are skipped."""
    if form not in FORMS:
        raise ValueError(f"unknown ICC form {form!r}; use one of {FORMS}")
    X, n, k = _matrix(X)
    if n_boot <= 0:   # bootstrap switched off (simulation loops)
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    vals = np.empty(n_boot)
    for b in range(n_boot):
        vals[b] = icc(X[rng.integers(0, n, n)])[form]
    vals = vals[np.isfinite(vals)]
    if len(vals) < 10:
        return (float("nan"), float("nan"))
    a = 1 - level
    lo, hi = np.quantile(vals, [a / 2, 1 - a / 2])
    return (float(lo), float(hi))


def _design(k):
    k = np.asarray(k, dtype=float)
    return np.column_stack([np.ones_like(k), k, np.log(k)])


def practice_residuals(y, k):
    """Residuals of y ~ k + ln(k) (ordinary least squares over all included sessions), removing the practice curve.

    `k` must be the real study session number minus 2 (gaps from stopped sessions are kept, not renumbered 1..n).
    """
    y = np.asarray(y, dtype=float)
    k = np.asarray(k, dtype=float)
    if len(y) != len(k) or len(y) < 5:
        raise ValueError("need at least 5 sessions with matching y and k")
    if not np.isfinite(k).all() or (k <= 0).any():
        raise ValueError("k must be finite and positive (k = study session number minus 2, so the first confirmatory session is 1)")
    X = _design(k)
    beta, _, rank, _ = np.linalg.lstsq(X, y, rcond=None)
    if rank < 3:
        raise ValueError("k has too few distinct values to fit y ~ k + ln(k)")
    return y - X @ beta


def paired_matrix(days, pm, values):
    """Days x 2 matrix (AM, PM) from per-session arrays, keeping only days that have both sessions. Returns (matrix, kept day ids)."""
    days, pm, values = np.asarray(days), np.asarray(pm), np.asarray(values, dtype=float)
    if pm.dtype.kind not in "biuf" or not np.isin(pm, (0, 1)).all():
        raise ValueError("slot (pm) must be 0 for AM and 1 for PM")
    cells = {}
    for d, p, v in zip(days, pm, values):
        if (d, int(p)) in cells:
            raise ValueError(f"two sessions in the same day and slot (day {d}); keep only the first before computing reliability")
        cells[(d, int(p))] = v
    kept = sorted(d for d in {d for d, _ in cells} if (d, 0) in cells and (d, 1) in cells)
    X = np.array([[cells[(d, 0)], cells[(d, 1)]] for d in kept], dtype=float).reshape(-1, 2)
    return X, np.array(kept)


def _summary(X, n_boot, seed, level):
    out = {k: v for k, v in icc(X).items() if k in ("ICC(3,1)", "ICC(2,1)")}
    for form in ("ICC(3,1)", "ICC(2,1)"):
        out[f"{form} CI"] = icc_ci(X, form, level)
        out[f"{form} bootstrap CI"] = icc_bootstrap_ci(X, form, level, n_boot=n_boot, seed=seed)
    return out


def test_retest(days, pm, k, y, level=0.95, n_boot=10_000, seed=20261119):
    """Prereg D6 test-retest reliability of one outcome across the AM and PM sessions of a day.

    `raw` uses the outcome as is; `residual` uses residuals from y ~ k + ln(k) (fitted on all included sessions) so that
    learning across the study does not inflate stability. The primary result is the residual ICC(3,1).
    `k` is the real study session number minus 2 (not a 1..n row index). Only days with both sessions are used. Shared night, day component and adjacency mean this is within-day consistency
    as well as stability; the interval from the F distribution assumes independent days, so the bootstrap over days is reported too.
    """
    days, pm, k, y = (np.asarray(a) for a in (days, pm, k, y))
    y = y.astype(float)
    ok = np.isfinite(y)
    days, pm, k, y = days[ok], pm[ok], k[ok], y[ok]
    resid = practice_residuals(y, k)
    X_raw, kept = paired_matrix(days, pm, y)
    X_res, kept2 = paired_matrix(days, pm, resid)
    if len(kept) < 3:
        raise ValueError("need at least 3 days with both an AM and a PM session")
    if kept.tolist() != kept2.tolist():
        raise ValueError("internal error: raw and residual day sets differ")
    return {
        "n_days": len(kept), "n_sessions": int(len(y)), "days": kept.tolist(),
        "raw": _summary(X_raw, n_boot, seed, level),
        "residual": _summary(X_res, n_boot, seed, level),
        "primary": "residual ICC(3,1)",
    }


def spearman_brown(r, factor=2):
    """Spearman-Brown prophecy: reliability of a test `factor` times as long, from reliability r.

    A monotone transform: for negative r (and negative interval endpoints) the result can fall below -1 and is not a reliability bound.
    """
    r = float(r)
    den = 1 + (factor - 1) * r
    return float(factor * r / den) if den != 0 else float("nan")


def split_trials(trials):
    """Odd and even trials (1st, 3rd, ... and 2nd, 4th, ...) of a session's scored trials."""
    trials = list(trials)
    return trials[0::2], trials[1::2]


def split_half(halves, level=0.95):
    """Split-half reliability across sessions from an n x 2 matrix of (odd, even) scores: Pearson r, Spearman-Brown, Fisher-z intervals."""
    H = np.asarray(halves, dtype=float)
    if H.ndim != 2 or H.shape[1] != 2:
        raise ValueError("expected an n x 2 matrix of (odd, even) half scores")
    if len(H) < 4:
        raise ValueError("need at least 4 sessions for split-half reliability")
    if not np.isfinite(H).all():
        raise ValueError("missing half scores: drop those sessions first")
    if H[:, 0].std() == 0 or H[:, 1].std() == 0:
        return {"r": float("nan"), "spearman_brown": float("nan"), "r_ci": (float("nan"),) * 2, "spearman_brown_ci": (float("nan"),) * 2, "n_sessions": len(H)}
    r = float(np.corrcoef(H[:, 0], H[:, 1])[0, 1])
    out = {"r": r, "spearman_brown": spearman_brown(r), "n_sessions": len(H)}
    if abs(r) >= 1:
        out["r_ci"] = (r, r)
        out["spearman_brown_ci"] = (out["spearman_brown"],) * 2
        return out
    z, se = np.arctanh(r), 1 / np.sqrt(len(H) - 3)
    zc = stats.norm.ppf(1 - (1 - level) / 2)
    lo, hi = float(np.tanh(z - zc * se)), float(np.tanh(z + zc * se))
    out["r_ci"] = (lo, hi)
    out["spearman_brown_ci"] = (spearman_brown(lo), spearman_brown(hi))
    return out


def split_half_from_trials(sessions_trials, score, level=0.95):
    """Split-half reliability from per-session trial lists: odd/even trials are scored with `score(trials) -> float`.

    Sessions where either half has no finite score are dropped and counted (`n_dropped`).
    """
    rows = []
    for trials in sessions_trials:
        odd, even = split_trials(trials)
        a, b = (score(odd) if len(odd) else float("nan")), (score(even) if len(even) else float("nan"))
        rows.append((a, b))
    arr = np.array(rows, dtype=float).reshape(-1, 2)
    good = np.isfinite(arr).all(axis=1)
    out = split_half(arr[good], level) if good.sum() >= 4 else None
    if out is None:
        raise ValueError("fewer than 4 sessions with both half scores")
    out["halves"] = arr[good]
    out["n_dropped"] = int((~good).sum())
    return out


def interpret(value):
    """Koo & Li (2016) label for a reliability value; thresholds unverified (see KOO_LI_NOTE)."""
    if value is None or not np.isfinite(value):
        return "undefined"
    if value < 0.5:
        return "poor"
    if value < 0.75:
        return "moderate"
    if value < 0.9:
        return "good"
    return "excellent"
