"""Per-session scores for every preregistered outcome (docs/design/design.md section 4), from scored trials only."""
from .data import load_sessions  # noqa: F401  (re-exported)
from .exclusions import (
    EXPECTED_SCORED,
    exclusion_reasons,
    h1_eligible,
    manual_reason,
    rule1_trim_rt,
    rule2_correct_trials_only,
    scored_trials,
    _rows,
)
from .sdt import dprime_from_counts


# Design (docs/design/design.md section 3): 2-back "response window 2,000 ms from onset" (the trial itself lasts 2,500 ms
# and the browser records later presses, so the window is enforced here, in scoring).
NBACK_RESPONSE_WINDOW_MS = 2000


def _responded_in_window(t):
    """A 2-back response counts only if it came within the response window (rt is measured from letter onset)."""
    return bool(t["data"]["responded"]) and (t["rt"] is None or t["rt"] <= NBACK_RESPONSE_WINDOW_MS)


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def _diff(a, b):
    return None if a is None or b is None else a - b


def _accuracy(trials):
    return sum(1 for t in trials if t["correct"] in (1, True)) / len(trials) if trials else None


def serial_position(flag_lists):
    """Proportion recalled at each serial position across lists (empty input gives [])."""
    if not flag_lists:
        return []
    n = len(flag_lists[0])
    if any(len(f) != n for f in flag_lists):
        raise ValueError("all lists must have the same length")
    return [sum(1 for f in flag_lists if f[p]) / len(flag_lists) for p in range(n)]


def _sdt(hits, n_signal, false_alarms, n_noise):
    if n_signal == 0 or n_noise == 0:
        return None
    return dprime_from_counts(hits, n_signal, false_alarms, n_noise)


def score_session(session):
    """Scores for one session. Missing measures are None (never 0)."""
    out = {
        "participant_code": session["participant_code"],
        "session_number": session["session_number"],
        "timestamp": session.get("timestamp"),
        "hours_slept": (session["questionnaire"] or {}).get("hours_slept"),
        "kss": (session["questionnaire"] or {}).get("kss"),
        "caffeine": (session["questionnaire"] or {}).get("caffeine"),
    }

    # P1: 2-back d' (positions 1-2 are not scored; lures count as non-targets; log-linear correction)
    nb = [t for t in scored_trials(session, "nback") if t["data"]["position"] >= 3]
    targets = [t for t in nb if t["data"]["type"] == "target"]
    others = [t for t in nb if t["data"]["type"] != "target"]
    hits = sum(1 for t in targets if _responded_in_window(t))
    fas = sum(1 for t in others if _responded_in_window(t))
    lure_fas = sum(1 for t in others if t["data"]["type"] in ("lure1", "lure3") and _responded_in_window(t))
    r = _sdt(hits, len(targets), fas, len(others))
    out.update(P1_hits=hits, P1_n_targets=len(targets), P1_false_alarms=fas, P1_n_nontargets=len(others), P1_lure_false_alarms=lure_fas,
               P1_dprime=r and r["d_prime"], P1_criterion=r and r["criterion"])

    # P2: recall proportion over the scored lists (browser-scored nCorrect per list)
    lists = scored_trials(session, "recall")
    n_correct = sum(t["data"]["nCorrect"] for t in lists)
    n_words = sum(len(t["data"]["listWords"]) for t in lists)
    out.update(P2_n_correct=n_correct, P2_n_words=n_words, P2_recall_proportion=n_correct / n_words if n_words else None)
    out["recall_serial_position"] = serial_position([t["data"]["recalled"] for t in lists])
    out["P2_consistent"] = _recall_consistent(session)

    # S1: Stroop. RT outcomes use rule 1 trimming then rule 2 (correct trials); accuracy uses all scored trials (see rule 1)
    stroop_all = scored_trials(session, "stroop")
    stroop = rule1_trim_rt(stroop_all)
    by = lambda trials, cond: [t for t in trials if t["data"]["condition"] == cond]  # noqa: E731
    cong_rt = _mean([t["rt"] for t in rule2_correct_trials_only(by(stroop, "congruent"))])
    inc_rt = _mean([t["rt"] for t in rule2_correct_trials_only(by(stroop, "incongruent"))])
    cong_acc, inc_acc = _accuracy(by(stroop_all, "congruent")), _accuracy(by(stroop_all, "incongruent"))
    out.update(S1_mean_congruent_rt=cong_rt, S1_mean_incongruent_rt=inc_rt, S1_stroop_interference=_diff(inc_rt, cong_rt),
               stroop_congruent_accuracy=cong_acc, stroop_incongruent_accuracy=inc_acc, stroop_accuracy_interference=_diff(cong_acc, inc_acc))

    # S2: Posner validity effect
    posner = rule1_trim_rt(scored_trials(session, "posner"))
    valid_rt = _mean([t["rt"] for t in rule2_correct_trials_only([t for t in posner if t["data"]["valid"]])])
    invalid_rt = _mean([t["rt"] for t in rule2_correct_trials_only([t for t in posner if not t["data"]["valid"]])])
    out.update(S2_mean_valid_rt=valid_rt, S2_mean_invalid_rt=invalid_rt, S2_posner_validity_effect=_diff(invalid_rt, valid_rt))

    # S3: contrast threshold (from the staircase's threshold row)
    th = _rows(session, "threshold")
    d = th[-1]["data"] if th else {}
    out.update(S3_threshold_level=d.get("thresholdLevel"), S3_threshold_contrast=d.get("thresholdContrast"), S3_used_fallback=d.get("usedFallback"))

    # S4: yes/no d' and criterion at threshold contrast
    yn = scored_trials(session, "yesno")
    signal = [t for t in yn if t["data"]["isSignal"]]
    noise = [t for t in yn if not t["data"]["isSignal"]]
    r = _sdt(sum(1 for t in signal if t["data"]["respondedYes"]), len(signal), sum(1 for t in noise if t["data"]["respondedYes"]), len(noise))
    # a yes/no trial with no response is coded "no"; report how many there were
    out.update(S4_dprime=r and r["d_prime"], S4_criterion=r and r["criterion"], S4_n_no_response=sum(1 for t in yn if t["response"] is None))
    return out


def _recall_consistent(session):
    """True if every scored list's nCorrect equals its recalled flags and the summary row agrees; None with no lists."""
    lists = scored_trials(session, "recall")
    if not lists:
        return None
    ok = all(t["data"]["nCorrect"] == sum(t["data"]["recalled"]) and len(t["data"]["recalled"]) == len(t["data"]["listWords"]) for t in lists)
    summary = scored_trials(session, "recall_summary")
    if summary:
        d = summary[-1]["data"]
        ok = ok and d["nCorrect"] == sum(t["data"]["nCorrect"] for t in lists) and d["nWords"] == sum(len(t["data"]["listWords"]) for t in lists)
    return ok


def data_warnings(session, expected=None):
    """Data-quality notes that are NOT exclusions: more scored trials than the design count, and recall scores that
    disagree with the recalled flags or the summary row."""
    exp = {**EXPECTED_SCORED, **(expected or {})}
    warnings = []
    for task, key in (("posner", "posner"), ("stroop", "stroop"), ("nback", "nback"), ("yesno", "yesno"), ("recall", "recall_lists")):
        n = len(scored_trials(session, task))
        if n > exp[key]:
            label = "recall lists" if task == "recall" else f"{task} trials"
            warnings.append(f"{n} scored {label}, more than the design count of {exp[key]}")
    for t in scored_trials(session, "recall"):
        d = t["data"]
        if d["nCorrect"] != sum(d["recalled"]):
            warnings.append(f"recall list {d['list']}: nCorrect {d['nCorrect']} disagrees with the recalled flags ({sum(d['recalled'])})")
    summary = scored_trials(session, "recall_summary")
    lists = scored_trials(session, "recall")
    if summary and lists and summary[-1]["data"]["nCorrect"] != sum(t["data"]["nCorrect"] for t in lists):
        warnings.append("recall summary nCorrect disagrees with the sum over the lists")
    return warnings


def score_database(conn, expected=None):
    """Scores for every session plus exclusion status. Manual reasons in `excluded_reason` are respected."""
    rows = []
    for s in load_sessions(conn):
        reasons = exclusion_reasons(s, expected)
        manual = manual_reason(s)
        row = score_session(s)
        row.update(excluded=bool(reasons) or manual is not None, excluded_reason=manual or ("; ".join(reasons) or None),
                   h1_eligible=h1_eligible(s, expected), warnings=data_warnings(s, expected))
        rows.append(row)
    return rows
