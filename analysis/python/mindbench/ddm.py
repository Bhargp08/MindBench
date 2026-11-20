"""Drift-diffusion models for H3 (MB-21; prereg D7; spec in docs/design/ddm.md).

Works on trial tables passed in by the caller. It never touches the database or real data files.
Trial columns: rt (ms), correct (0/1), cond (0/1 condition driving drift), group (0/1 session group).
PyDDM 0.9.0: the bound B is the half-width (bounds at +-B), so a = 2B.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from pyddm import Bound, Drift, Fittable, Model, Sample, fit_adjust_model
from pyddm.models import (BoundConstant, LossLikelihood, NoiseConstant, OverlayChain, OverlayNonDecision,
                          OverlayUniformMixture)

MIXTURE = 0.02  # fixed uniform-contaminant share (a modelling choice, not estimated)
RT_MIN_MS, RT_MAX_MS = 100.0, 2000.0
QUANTILES = (0.1, 0.3, 0.5, 0.7, 0.9)
MODELS = ("null", "drift", "boundary", "both")
BIC_TIE = 2.0
MIN_CELL = 5
ERROR_SHARE_MIN = 0.05
DX = DT = 0.01
T_DUR = 3.0


# ------------------------------------------------------------------------------------------------ analytic
def analytic_p_upper(v: float, B: float, sigma: float = 1.0) -> float:
    """P(upper bound) for an unbiased start and bounds +-B: 1 / (1 + exp(-2 v B / sigma^2))."""
    return 1.0 / (1.0 + math.exp(-2.0 * v * B / sigma**2))


def analytic_mdt(v: float, B: float, sigma: float = 1.0) -> float:
    """Mean decision time (B / v) tanh(v B / sigma^2); B^2 / sigma^2 in the zero-drift limit."""
    if abs(v) < 1e-12:
        return B**2 / sigma**2
    return (B / v) * math.tanh(v * B / sigma**2)


def solve_reference(v: float, B: float):
    """PyDDM's numerical solution for the same setting (checks the bound convention)."""
    m = Model(drift=_const_drift(v), bound=BoundConstant(B=B), noise=NoiseConstant(noise=1), dx=0.002, dt=0.002, T_dur=6)
    s = m.solve()
    pc, pe = s.prob("correct"), s.prob("error")
    t = s.t_domain
    mdt = float(((s.pdf("correct") + s.pdf("error")) * t).sum() * m.dt / (pc + pe))
    return float(pc), mdt


def _const_drift(v):
    from pyddm import DriftConstant

    return DriftConstant(drift=v)


# ------------------------------------------------------------------------------------------------ EZ-diffusion
def ez_diffusion(pc: float, vrt: float, mrt: float, s: float = 0.1, n: int | None = None) -> dict:
    """EZ-diffusion (Wagenmakers, van der Maas & Grasman, 2007): v, a, Ter from accuracy and the RT variance and
    mean of correct trials (seconds). Pc of exactly 0, 0.5 or 1 needs n and gets the edge correction
    (0 -> 1/(2n), 1 -> 1 - 1/(2n), 0.5 -> 0.5 + 1/(2n)); the result says so. Pc below .5 is handled by symmetry
    (negative drift)."""
    if not (0.0 <= pc <= 1.0):
        raise ValueError("pc must be in [0, 1]")
    if not vrt > 0:
        raise ValueError("vrt must be positive")
    if not mrt > 0:
        raise ValueError("mrt must be positive")
    corrected = False
    if pc in (0.0, 0.5, 1.0):
        if n is None or n <= 0:
            raise ValueError("an edge value of pc needs n for the correction")
        corrected = True
        pc = {0.0: 1 / (2 * n), 1.0: 1 - 1 / (2 * n), 0.5: 0.5 + 1 / (2 * n)}[pc]
    sign = 1.0
    if pc < 0.5:
        pc, sign = 1.0 - pc, -1.0
    L = math.log(pc / (1.0 - pc))
    x = L * (pc**2 * L - pc * L + pc - 0.5) / vrt
    v = s * x**0.25
    a = s**2 * L / v
    y = -v * a / s**2
    mdt = (a / (2 * v)) * (1 - math.exp(y)) / (1 + math.exp(y))
    return {"v": sign * v, "a": a, "ter": mrt - mdt, "edge_corrected": corrected}


def ez_by_cell(df: pd.DataFrame, s: float = 0.1) -> list[dict]:
    """EZ-diffusion for every condition x group cell of a prepared table (RT in seconds)."""
    out = []
    for (cond, group), cell in df.groupby(["cond", "group"]):
        good = cell.loc[cell["correct"] == 1, "rt"]
        if len(good) < 2:
            out.append({"cond": cond, "group": group, "n": len(cell), "v": np.nan, "a": np.nan, "ter": np.nan, "edge_corrected": False})
            continue
        r = ez_diffusion(float(cell["correct"].mean()), float(good.var(ddof=1)), float(good.mean()), s=s, n=len(cell))
        out.append({"cond": cond, "group": group, "n": len(cell), **r})
    return out


# ------------------------------------------------------------------------------------------------ data
def prepare(df: pd.DataFrame) -> pd.DataFrame:
    """Validate a trial table, convert RT from ms to s, drop rows with no session group (e.g. sessions at the median)."""
    need = ["rt", "correct", "cond", "group"]
    missing = [c for c in need if c not in df.columns]
    if missing:
        raise ValueError(f"missing column(s): {missing}")
    d = df[need].copy()
    d = d[d["group"].notna()]
    rt = pd.to_numeric(d["rt"], errors="coerce")
    if rt.isna().any() or ((rt <= RT_MIN_MS) | (rt > RT_MAX_MS)).any():
        raise ValueError(f"rt must be a number in ({RT_MIN_MS:g}, {RT_MAX_MS:g}] ms; exclusions belong upstream")
    d["rt"] = rt / 1000.0
    d["correct"] = d["correct"].astype(bool).astype(int)
    d["cond"] = d["cond"].astype(int)
    d["group"] = d["group"].astype(int)
    if not set(d["group"]) <= {0, 1}:
        raise ValueError("group must be 0 or 1")
    if set(d["cond"]) != {0, 1}:
        raise ValueError("both conditions (cond 0 and 1) are needed")
    return d.reset_index(drop=True)


def assign_groups(sessions: pd.DataFrame, by: str) -> pd.DataFrame:
    """Add `group`: sleep = below (0) / above (1) the median hours slept, sessions at the median NaN (left out);
    tod = AM (0) / PM (1)."""
    out = sessions.copy()
    if by == "sleep":
        med = out["hours_slept"].median()
        out["group"] = np.where(out["hours_slept"] < med, 0.0, np.where(out["hours_slept"] > med, 1.0, np.nan))
    elif by == "tod":
        out["group"] = out["time_of_day"].map({"AM": 0.0, "PM": 1.0})
    else:
        raise ValueError("by must be 'sleep' or 'tod'")
    return out


# ------------------------------------------------------------------------------------------------ models
class DriftCG(Drift):
    name = "drift by condition and group"
    required_parameters = ["v0", "v1", "dv"]
    required_conditions = ["cond", "group"]

    def get_drift(self, conditions, **kwargs):
        return (self.v0 if conditions["cond"] == 0 else self.v1) + self.dv * conditions["group"]


class BoundG(Bound):
    name = "boundary separation by group (a = 2B)"
    required_parameters = ["a", "da"]
    required_conditions = ["group"]

    def get_bound(self, conditions, **kwargs):
        return max(self.a + self.da * conditions["group"], 0.05) / 2.0


def _overlay(t0):
    return OverlayChain(overlays=[OverlayNonDecision(nondectime=t0), OverlayUniformMixture(umixturecoef=MIXTURE)])


def _model(drift, bound, t0, dx=DX, dt=DT, T_dur=T_DUR):
    return Model(drift=drift, bound=bound, noise=NoiseConstant(noise=1), overlay=_overlay(t0), dx=dx, dt=dt, T_dur=T_dur)


def _free_model(kind: str) -> tuple[Model, int]:
    if kind not in MODELS:
        raise ValueError(f"model must be one of {MODELS}")
    drift_shift = Fittable(minval=-4, maxval=4) if kind in ("drift", "both") else 0
    bound_shift = Fittable(minval=-2, maxval=2) if kind in ("boundary", "both") else 0
    m = _model(DriftCG(v0=Fittable(minval=-2, maxval=8), v1=Fittable(minval=-2, maxval=8), dv=drift_shift),
               BoundG(a=Fittable(minval=0.3, maxval=4), da=bound_shift), Fittable(minval=0, maxval=0.8))
    k = 4 + (kind in ("drift", "both")) + (kind in ("boundary", "both"))
    return m, k


def _sample(df: pd.DataFrame) -> Sample:
    d = df.assign(choice=np.where(df["correct"] == 1, 1, 0))
    return Sample.from_pandas_dataframe(d, rt_column_name="rt", choice_column_name="choice", choice_names=("correct", "error"))


def fit_model(df: pd.DataFrame, kind: str, seed: int = 0) -> dict:
    """Maximum-likelihood fit of one of the four models; BIC = 2 NLL + k ln n."""
    model, k = _free_model(kind)
    np.random.seed(seed)  # PyDDM's differential evolution draws from the global generator
    fitted = fit_adjust_model(_sample(df), model, fitting_method="differential_evolution", lossfunction=LossLikelihood, verbose=False)
    nll = float(fitted.fitresult.value())
    names = {"v0": "v0", "v1": "v1", "dv": "dv", "a": "a", "da": "da", "nondectime": "t0"}
    params = {}
    for comp in (fitted.get_dependence("drift"), fitted.get_dependence("bound"), fitted.get_dependence("overlay")):
        for sub in getattr(comp, "overlays", [comp]):
            for p in sub.required_parameters:
                if p in names:
                    params[names[p]] = float(getattr(sub, p))
    n = len(df)
    return {"model": kind, "params": params, "k": k, "n": n, "nll": nll, "bic": 2.0 * nll + k * math.log(n), "fitted": fitted}


def boundary_identifiable(df: pd.DataFrame) -> bool:
    """Prereg D7: not identifiable if errors are under 5% of the pooled trials in either session group."""
    share = df.groupby("group")["correct"].apply(lambda c: 1.0 - c.mean())
    return bool((share >= ERROR_SHARE_MIN).all())


def verdict(bic: dict) -> dict:
    """Lowest BIC wins; a runner-up within 2 BIC units makes it 'cannot tell'."""
    order = sorted(bic, key=bic.get)
    best, second = order[0], order[1]
    gap = bic[second] - bic[best]
    label = "neither" if best == "null" else best
    return {"verdict": "cannot tell" if gap < BIC_TIE else label, "best": best, "gap": gap}


def compare_models(df: pd.DataFrame, seed: int = 0) -> dict:
    """Fit the competing models and apply the BIC rule. Without identifiable boundaries only null and drift."""
    if set(df["group"]) != {0, 1}:
        raise ValueError("both session groups (group 0 and 1) are needed to compare models")
    identifiable = boundary_identifiable(df)
    kinds = MODELS if identifiable else ("null", "drift")
    fits = {k: fit_model(df, k, seed=seed) for k in kinds}
    bic = {k: f["bic"] for k, f in fits.items()}
    out = {**verdict(bic), "bic": bic, "boundary_identifiable": identifiable, "fits": fits, "note": ""}
    if not identifiable:
        out["note"] = ("boundary separation is not identifiable (errors under 5% in a session group); "
                       "a drift verdict cannot exclude a boundary change")
    return out


# ------------------------------------------------------------------------------------------------ simulation
def simulate(v, a, t0, n_per_cell, seed, dv=0.0, da=0.0, groups=(0,)) -> pd.DataFrame:
    """Simulate trials (RT in ms) for 2 conditions x len(groups) cells from known parameters (a = 2B). Trials slower
    than 2,000 ms are dropped, as the prereg exclusion would drop them, so a cell can hold slightly fewer trials."""
    rows = []
    for gi, g in enumerate(groups):
        for c in (0, 1):
            m = Model(drift=_const_drift(v[c] + dv * g), bound=BoundConstant(B=max(a + da * g, 0.05) / 2.0),
                      noise=NoiseConstant(noise=1), overlay=OverlayNonDecision(nondectime=t0), dx=0.005, dt=0.005, T_dur=5)
            smp = m.solve().resample(n_per_cell, seed=seed * 1000 + gi * 10 + c)
            d = smp.to_pandas_dataframe(drop_undecided=True)
            rows.append(pd.DataFrame({"rt": d["RT"].to_numpy() * 1000.0, "correct": d["choice"].to_numpy().astype(int), "cond": c, "group": g}))
    out = pd.concat(rows, ignore_index=True)
    return out[out["rt"] <= RT_MAX_MS].reset_index(drop=True)


# ------------------------------------------------------------------------------------------------ predictive checks
def rt_quantiles(df: pd.DataFrame) -> pd.DataFrame:
    """Observed RT quantiles (seconds) per condition x group x response; NaN where a cell has under 5 trials."""
    out = []
    for cond in sorted(df["cond"].unique()):
        for group in sorted(df["group"].unique()):
            for resp, flag in (("correct", 1), ("error", 0)):
                x = df.loc[(df["cond"] == cond) & (df["group"] == group) & (df["correct"] == flag), "rt"].to_numpy()
                for q in QUANTILES:
                    out.append({"cond": cond, "group": group, "response": resp, "quantile": q, "n": len(x),
                                "rt": float(np.quantile(x, q)) if len(x) >= MIN_CELL else np.nan})
    return pd.DataFrame(out)


def _predicted_quantiles(model: Model, cond: int, group: int, response: str) -> list[float]:
    sol = model.solve(conditions={"cond": cond, "group": group})
    pdf = np.asarray(sol.pdf(response), dtype=float)
    if pdf.sum() <= 0:
        return [np.nan] * len(QUANTILES)
    cdf = np.cumsum(pdf) / pdf.sum()
    return [float(np.interp(q, cdf, sol.t_domain)) for q in QUANTILES]


def predictive_check(fit: dict, df: pd.DataFrame) -> pd.DataFrame:
    """Observed vs model-predicted RT quantiles (seconds), correct and error responses, per condition x group."""
    obs = rt_quantiles(df)
    rows = []
    for (cond, group, resp), cell in obs.groupby(["cond", "group", "response"]):
        pred = _predicted_quantiles(fit["fitted"], int(cond), int(group), resp)
        for (_, r), p in zip(cell.iterrows(), pred):
            rows.append({"cond": cond, "group": group, "response": resp, "quantile": r["quantile"], "n": r["n"],
                         "observed": r["rt"], "predicted": p})
    return pd.DataFrame(rows)


def plot_predictive_check(chk: pd.DataFrame, path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    path = Path(path)
    fig, axes = plt.subplots(1, 2, figsize=(8, 4), sharex=True, sharey=True)
    for ax, resp in zip(axes, ("correct", "error")):
        sub = chk[chk["response"] == resp].dropna(subset=["observed", "predicted"])
        ax.scatter(sub["predicted"], sub["observed"], c=sub["quantile"], cmap="viridis", s=30)
        lim = [0, max(0.1, float(max(sub["predicted"].max(), sub["observed"].max())) * 1.05)] if len(sub) else [0, 1]
        ax.plot(lim, lim, color="grey", lw=1)
        ax.set_title(f"{resp} responses")
        ax.set_xlabel("predicted RT quantile (s)")
    axes[0].set_ylabel("observed RT quantile (s)")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)
    return path
