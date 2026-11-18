"""Preregistered exclusion and data rules (docs/design/design.md section 5), one function per rule.

Each rule function's docstring quotes its rule text from design.md (a test checks that the quote is present). Inputs
are session dicts from `mindbench.data.load_sessions`. Interpretations the rule text leaves open are stated in the
function docstrings; they are preregistration-relevant and must be repeated in the preregistration.
"""
from .data import load_sessions

AUTO_PREFIX = "auto: "
TASKS = ("contrast", "posner", "stroop", "nback", "recall")
RT_TRIMMED_TASKS = ("stroop", "posner")
RT_MIN_MS = 200
RT_MAX_MS = 2500
# Scored (practice = 0) trials per task in a complete session, from design.md section 3.
EXPECTED_SCORED = {"posner": 120, "stroop": 120, "nback": 60, "yesno": 60, "recall_lists": 2}


def scored_trials(session, task=None):
    """Rows with `practice == 0` (optionally of one task). Practice rows and untagged rows (fixation, cues) are not scored."""
    return [t for t in session["trials"] if t["practice"] == 0 and (task is None or t["task"] == task)]


def _rows(session, task):
    return [t for t in session["trials"] if t["task"] == task]


def rule1_trim_rt(trials, min_rt=RT_MIN_MS, max_rt=RT_MAX_MS):
    """Rule 1. 1. Trial RT trimming: drop Stroop and Posner trials with RT < 200 ms or > 2,500 ms (RT exactly 200 or 2,500 is kept). Design choice: the upper bound equals the response deadline.

    Interpretation: trimming applies to RT outcomes. The accuracy check in rule 3 is made on all scored trials before
    trimming, so anticipations count as trials (and as errors if wrong); otherwise fast guessing could dodge it. Trials
    with no response have no RT (rt is None) and are not trimmed; they stay in as errors. Other tasks are never trimmed.
    """
    return [
        t
        for t in trials
        if t["task"] not in RT_TRIMMED_TASKS or t["rt"] is None or min_rt <= t["rt"] <= max_rt
    ]


def rule2_correct_trials_only(trials):
    """Rule 2. 2. Error trials: RT outcomes (S1, S2) use correct trials only.

    Keeps rows with `correct == 1`; errors and missing responses are dropped, however fast they were.
    """
    return [t for t in trials if t["correct"] in (1, True)]


def _stroop_congruent_accuracy(session):
    # all scored congruent trials, before rule 1 trimming (see the rule 1 and rule 3 docstrings)
    trials = [t for t in scored_trials(session, "stroop") if t["data"].get("condition") == "congruent"]
    correct = sum(1 for t in trials if t["correct"] in (1, True))
    return correct, len(trials)


def missing_tasks(session, expected=None):
    """Names of tasks (and "questionnaire") that are missing or unfinished in a session.

    A task counts as present only if all its scored trials are there (contrast: a threshold row and all yes/no
    trials; recall: all scored lists and the summary row), because a session stopped part-way is incomplete (rule 6).
    """
    exp = {**EXPECTED_SCORED, **(expected or {})}
    n = lambda task: len(scored_trials(session, task))  # noqa: E731
    missing = []
    if not _rows(session, "threshold") or n("yesno") < exp["yesno"]:
        missing.append("contrast")
    if n("posner") < exp["posner"]:
        missing.append("posner")
    if n("stroop") < exp["stroop"]:
        missing.append("stroop")
    if n("nback") < exp["nback"]:
        missing.append("nback")
    if n("recall") < exp["recall_lists"] or not scored_trials(session, "recall_summary"):
        missing.append("recall")
    if session["questionnaire"] is None:
        missing.append("questionnaire")
    return missing


def rule3_session_exclusion(session, expected=None):
    """Rule 3. 3. Session exclusion: exclude the whole session if Stroop congruent accuracy < 60% (exactly 60% is kept), or if the session is incomplete (any of the 5 tasks or the questionnaire missing).

    Returns a list of reasons (empty if the session is kept). Stroop congruent accuracy is correct / all scored
    congruent trials, before RT trimming (so anticipations count and cannot dodge the check); a missing response
    counts as an error; no congruent trials means no accuracy reason (the session is then incomplete). Incomplete is
    defined by `missing_tasks`: fewer scored trials than the design count. More trials than the design count is not an
    exclusion (it is reported by `scoring.data_warnings`).
    """
    reasons = []
    correct, total = _stroop_congruent_accuracy(session)
    if total and correct * 5 < total * 3:  # correct / total < 60%, in integers so exactly 60% is kept
        reasons.append(f"stroop congruent accuracy {100 * correct / total:.1f}% < 60% ({correct}/{total})")
    reasons.extend(f"incomplete: missing {name}" for name in missing_tasks(session, expected))
    return reasons


def rule4_smoke_test_session(session):
    """Rule 4. 4. Smoke-test data: sessions flagged is_pilot = 1 (the 1-2 smoke-test runs, study sessions 1-2) are never analyzed. No formal pilot data exist.

    Returns ["smoke_test ..."] for flagged sessions, otherwise [].
    """
    return ["smoke_test: session flagged is_pilot = 1"] if session["is_pilot"] == 1 else []


def rule5_missing_sleep_log(session):
    """Rule 5. 5. Missing data: no imputation. Sessions missing the sleep log are dropped from H1 analyses only. Missing sessions are not made up, except the extension rule in section 7.

    Returns True if the sleep log is missing (no questionnaire, or hours_slept is None; 0 hours is a valid log). Such a
    session is not excluded; it is only left out of H1 (see `h1_eligible`). Nothing is imputed.
    """
    q = session["questionnaire"]
    return q is None or q["hours_slept"] is None


def rule6_stopped_session(session):
    """Rule 6. 6. Stop rule: a stopped session (see self_pilot_policy.md) counts as incomplete.

    A session is stopped if the battery did not finish: there is no final timing record, or it lists unfinished tasks.
    Returns the "incomplete: ..." reasons (empty if the battery finished).
    """
    timing = _rows(session, "timing")
    if not timing:
        return ["incomplete: the battery did not finish (no timing record)"]
    unfinished = (timing[-1]["data"].get("timing") or {}).get("unfinished") or []
    return [f"incomplete: stopped before finishing {', '.join(unfinished)}"] if unfinished else []


def exclusion_reasons(session, expected=None):
    """All reasons a session is excluded, smoke tests first (rule 4), then rule 3, then rule 6. Empty if kept."""
    return rule4_smoke_test_session(session) + rule3_session_exclusion(session, expected) + rule6_stopped_session(session)


def manual_reason(session):
    """A hand-entered `excluded_reason` (anything not starting with "auto: "), else None."""
    r = session.get("excluded_reason")
    return r if r and not r.startswith(AUTO_PREFIX) else None


def h1_eligible(session, expected=None):
    """True if the session is not excluded (by the rules or by a manual reason) and has a sleep log (rule 5 applies to H1 only)."""
    return manual_reason(session) is None and not exclusion_reasons(session, expected) and not rule5_missing_sleep_log(session)


def apply_exclusions(conn, expected=None):
    """Write the automatic exclusion reasons into `sessions.excluded_reason` (prefix "auto: ").

    Idempotent: a re-run rewrites automatic reasons and clears ones that no longer apply. A reason that does not start
    with "auto: " was entered by hand and is never overwritten. Returns counts and the sessions kept as manual.
    """
    summary = {"excluded": 0, "kept": 0, "manual_kept": []}
    for s in load_sessions(conn):
        current = s["excluded_reason"]
        if manual_reason(s):
            summary["manual_kept"].append((s["participant_code"], s["session_number"]))
            continue
        reasons = exclusion_reasons(s, expected)
        new = AUTO_PREFIX + "; ".join(reasons) if reasons else None
        if new != current:
            conn.execute(
                "UPDATE sessions SET excluded_reason = ? WHERE participant_code = ? AND session_number = ?",
                (new, s["participant_code"], s["session_number"]),
            )
        summary["excluded" if reasons else "kept"] += 1
    conn.commit()
    return summary
