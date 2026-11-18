"""Signal detection helpers: d' and criterion c, with the log-linear correction of Hautus (1995).

Formulas (docs/design/design.md, spec MB-15):
    d' = z(H) - z(FA)        c = -(z(H) + z(FA)) / 2
    log-linear correction:   H = (hits + 0.5) / (n_signal + 1),  FA = (false_alarms + 0.5) / (n_noise + 1)

The correction is applied to every dataset (not only extreme ones), as preregistered. The browser has a matching
JavaScript implementation (experiment/src/lib/sdt.js); tests/test_sdt_crosslang.py checks that both agree.
"""
from scipy.stats import norm


def dprime_from_rates(hit_rate, false_alarm_rate):
    """d' and criterion from rates strictly between 0 and 1 (no correction)."""
    for name, r in (("hit_rate", hit_rate), ("false_alarm_rate", false_alarm_rate)):
        if not 0 < r < 1:
            raise ValueError(f"{name} must be strictly between 0 and 1, got {r}")
    zh, zf = norm.ppf(hit_rate), norm.ppf(false_alarm_rate)
    return {"hit_rate": hit_rate, "false_alarm_rate": false_alarm_rate, "d_prime": float(zh - zf), "criterion": float(-(zh + zf) / 2)}


def dprime_from_counts(hits, n_signal, false_alarms, n_noise, correction="loglinear"):
    """d' and criterion from counts. correction="loglinear" (default, Hautus 1995) or "none" (raw rates; rates of
    exactly 0 or 1 raise ValueError)."""
    if n_signal <= 0 or n_noise <= 0:
        raise ValueError("n_signal and n_noise must be positive")
    if not (0 <= hits <= n_signal and 0 <= false_alarms <= n_noise):
        raise ValueError("counts must satisfy 0 <= hits <= n_signal and 0 <= false_alarms <= n_noise")
    if correction == "loglinear":
        hit_rate = (hits + 0.5) / (n_signal + 1)
        fa_rate = (false_alarms + 0.5) / (n_noise + 1)
    elif correction == "none":
        hit_rate = hits / n_signal
        fa_rate = false_alarms / n_noise
    else:
        raise ValueError(f"unknown correction {correction!r}")
    return dprime_from_rates(hit_rate, fa_rate)
