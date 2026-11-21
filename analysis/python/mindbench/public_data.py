"""MB-24: the de-identified public release (data_public/), its check, and a reproduction that reads only that release.

Only the files written by `export_public` may sit in data_public/. Nothing identifying leaves the private database:
participant codes become P01, P02, ...; the start time becomes a date (study day, prereg D2) plus AM/PM (D1/D9);
free text (typed recall words, manual exclusion notes, device strings) is never exported; bed and wake times and
browser details are dropped. A friend's data is exported only when the consent map holds a literal `true` for them.
Releasing the files (Zenodo) is Bharg's own step; this module only prepares and checks them.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

from . import synthesis
from .data import load_sessions
from .exclusions import exclusion_reasons, h1_eligible, manual_reason
from .scoring import score_session


class DeidError(Exception):
    """The data to be released (or analysed) breaks a de-identification rule."""


SESSION_SCORES = ("P1_dprime", "P1_criterion", "P1_hits", "P1_n_targets", "P1_false_alarms", "P1_n_nontargets",
                  "P2_n_correct", "P2_n_words", "P2_recall_proportion",
                  "S1_mean_congruent_rt", "S1_mean_incongruent_rt", "S1_stroop_interference",
                  "stroop_congruent_accuracy", "stroop_incongruent_accuracy",
                  "S2_mean_valid_rt", "S2_mean_invalid_rt", "S2_posner_validity_effect",
                  "S3_threshold_level", "S3_threshold_contrast", "S4_dprime", "S4_criterion")
COLUMNS = {
    "sessions.csv": ("pid", "session_number", "date", "period", "is_pilot", "excluded", "exclusion_rules", "h1_eligible",
                     "hours_slept", "kss", "caffeine", *SESSION_SCORES),
    "trials.csv": ("pid", "session_number", "trial_index", "task", "condition", "rt", "correct"),
    "participants.csv": ("pid", "role", "n_sessions"),
}
OPTIONAL_FILES = {"codebook.md", ".gitkeep"}
EXCLUSION_CODES = ("smoke_test", "stroop_accuracy", "incomplete", "manual")
TASKS = ("stroop", "posner", "nback", "yesno")
CONDITIONS = ("congruent", "incongruent", "valid", "invalid", "target", "nontarget", "lure1", "lure3", "start", "signal", "noise")
ROLES = ("owner", "consenting_participant")

PID_RE = re.compile(r"^P\d{2,3}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CODE_SHAPE_RE = re.compile(r"\b(?=[A-Z0-9]*[A-Z])[A-Z0-9]{8}\b")  # participant codes are 8 characters of capitals and digits
CLOCK_RE = re.compile(r"\d{1,2}:\d{2}")
DATETIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d")
EPOCH_RE = re.compile(r"^\d{10,13}$")  # unix s/ms when a whole cell (not a substring of a decimal)


# ------------------------------------------------------------------------------------------------ time rules
def _local(timestamp: str, tz_name: str | None) -> dt.datetime:
    t = dt.datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    try:
        zone = ZoneInfo(tz_name) if tz_name else dt.timezone.utc
    except Exception:  # unknown zone name: fall back to UTC (as the dashboard does)
        zone = dt.timezone.utc
    return t.astimezone(zone)


def day_and_period(timestamp: str, tz_name: str | None) -> tuple[str, str]:
    """Prereg D2/D1: the study day (a start from 00:00 to before 04:00 belongs to the previous calendar day and is PM)
    and AM (04:00 to before 12:00) or PM. Returns (ISO date, "AM"/"PM"); no time of day is kept."""
    local = _local(timestamp, tz_name)
    if local.hour < 4:
        return (local.date() - dt.timedelta(days=1)).isoformat(), "PM"
    return local.date().isoformat(), "AM" if local.hour < 12 else "PM"


def study_day(timestamp: str, tz_name: str | None) -> str:
    return day_and_period(timestamp, tz_name)[0]


# ------------------------------------------------------------------------------------------------ the check
def _is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _int_in(lo, hi):
    return lambda s: s == "" or (re.fullmatch(r"-?\d+", s) is not None and lo <= int(s) <= hi)


def _float_in(lo, hi):
    return lambda s: s == "" or (_is_number(s) and lo <= float(s) <= hi)


def _valid_date(s: str) -> bool:
    if not DATE_RE.match(s):
        return False
    try:
        dt.date.fromisoformat(s)
        return True
    except ValueError:
        return False


def _rules_ok(s: str) -> bool:
    return s == "" or all(part in EXCLUSION_CODES for part in s.split(";"))


VALIDATORS = {
    "pid": (lambda s: PID_RE.match(s) is not None, "must look like P01 (a pseudonym), never a participant code"),
    "session_number": (_int_in(1, 10_000), "must be a whole number"),
    "date": (_valid_date, "must be a calendar date YYYY-MM-DD and nothing finer"),
    "period": (lambda s: s in ("AM", "PM"), "must be AM or PM"),
    "is_pilot": (_int_in(0, 1), "must be 0 or 1"), "excluded": (_int_in(0, 1), "must be 0 or 1"),
    "h1_eligible": (_int_in(0, 1), "must be 0 or 1"), "caffeine": (_int_in(0, 1), "must be 0 or 1"),
    "exclusion_rules": (_rules_ok, f"must be empty or codes from {EXCLUSION_CODES} joined by ;"),
    "hours_slept": (_float_in(0, 24), "must be a number of hours"), "kss": (_int_in(1, 9), "must be 1 to 9"),
    "task": (lambda s: s in TASKS, f"must be one of {TASKS}"),
    "condition": (lambda s: s in CONDITIONS, f"must be one of {CONDITIONS}"),
    "trial_index": (_int_in(0, 1_000_000), "must be a whole number"),
    "rt": (_float_in(0, 100_000), "must be a number of milliseconds"),
    "correct": (_int_in(0, 1), "must be 0 or 1"),
    "role": (lambda s: s in ROLES, f"must be one of {ROLES}"),
    "n_sessions": (_int_in(0, 10_000), "must be a whole number"),
}
for _c in SESSION_SCORES:
    VALIDATORS[_c] = (lambda s: s == "" or _is_number(s), "must be a number or empty")


def check_public_dir(path, known_codes=()) -> list[str]:
    """Problems that make a folder unfit for release (empty list = passes). `known_codes` are real participant codes
    to search for in every cell and file name; code-shaped values are caught even without the list."""
    root = Path(path)
    if not root.is_dir():
        return [f"{root}: not a folder"]
    problems: list[str] = []
    codes = [c.lower() for c in known_codes if c]

    for f in sorted(root.iterdir()):
        if any(c in f.name.lower() for c in codes) or CODE_SHAPE_RE.search(f.name):
            problems.append(f"file name contains a participant code: {f.name}")
        if f.name not in COLUMNS and f.name not in OPTIONAL_FILES:
            problems.append(f"file is not part of the release: {f.name}")
    for f in sorted(root.glob("*.md")):
        text = f.read_text(encoding="utf-8").lower()
        if any(c in text for c in codes):
            problems.append(f"{f.name}: contains a participant code")
    for name, expected in COLUMNS.items():
        f = root / name
        if not f.is_file():
            problems.append(f"missing required file: {name}")
            continue
        with open(f, newline="", encoding="utf-8") as fh:
            reader = csv.reader(fh)
            header = next(reader, [])
            for col in header:
                if col not in expected:
                    problems.append(f"{name}: unexpected column: {col}")
            for col in expected:
                if col not in header:
                    problems.append(f"{name}: missing column: {col}")
            seen: set[str] = set()
            for line, row in enumerate(reader, start=2):
                if len(row) != len(header):
                    problems.append(f"{name} line {line}: {len(row)} cells, expected {len(header)}")
                    continue
                for col, cell in zip(header, row):
                    msg = None
                    if col in VALIDATORS and not VALIDATORS[col][0](cell):
                        msg = f"{name} line {line}: column {col}: {VALIDATORS[col][1]}"
                    if msg and msg not in seen:
                        seen.add(msg)
                        problems.append(msg)
                    low = cell.lower()
                    hit = next((c for c in codes if c in low), None)
                    if hit or CODE_SHAPE_RE.search(cell):
                        m = f"{name} line {line}: column {col}: contains a participant code"
                        if m not in seen:
                            seen.add(m)
                            problems.append(m)
                    if CLOCK_RE.search(cell) or DATETIME_RE.search(cell) or EPOCH_RE.match(cell.strip()):
                        m = f"{name} line {line}: column {col}: contains a time of day (nothing finer than the date may be released)"
                        if m not in seen:
                            seen.add(m)
                            problems.append(m)
    return problems


# ------------------------------------------------------------------------------------------------ the export
def _pid_label(i: int) -> str:
    return f"P{i:02d}"


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, bool):
        return str(int(v))
    if isinstance(v, float):
        return repr(v)
    return str(v)


def _rule_codes(session, expected) -> list[str]:
    codes = []
    for r in exclusion_reasons(session, expected):
        code = ("smoke_test" if r.startswith("smoke_test") else "stroop_accuracy" if r.startswith("stroop congruent accuracy")
                else "incomplete")
        if code not in codes:
            codes.append(code)
    if manual_reason(session):
        codes.append("manual")  # the hand-written note itself is never exported
    return codes


def _condition(t) -> str | None:
    d = t["data"]
    if t["task"] == "stroop":
        return d.get("condition")
    if t["task"] == "posner":
        return "valid" if d.get("valid") else "invalid"
    if t["task"] == "nback":
        return d.get("type")
    if t["task"] == "yesno":
        return "signal" if d.get("isSignal") else "noise"
    return None


def export_public(conn, out_dir, owners, consent, expected=None, known_codes=()) -> dict:
    """Write the de-identified release into `out_dir` and check it. Participants in `owners` are released; anyone else
    only if `consent[code] is True` (a literal true, nothing else counts). Raises DeidError (and removes what it wrote)
    if the result fails `check_public_dir`. Returns a report with the private pseudonym map; keep the map out of the release."""
    sessions = load_sessions(conn)
    all_codes = sorted({s["participant_code"] for s in sessions})
    owner_set = set(owners)
    released = [c for c in all_codes if c in owner_set or consent.get(c) is True]
    ordered = [c for c in released if c in owner_set] + [c for c in released if c not in owner_set]
    pid_map = {code: _pid_label(i) for i, code in enumerate(ordered, start=1)}

    sess_rows, trial_rows, counts, omitted_sessions = [], [], {}, 0
    for s in sessions:
        code = s["participant_code"]
        if code not in pid_map:
            continue
        if not s["timestamp"]:
            omitted_sessions += 1  # no start time, so no study day to release
            continue
        pid = pid_map[code]
        date, period = day_and_period(s["timestamp"], s["timezone"])
        codes = _rule_codes(s, expected)
        q = s["questionnaire"] or {}
        score = score_session(s)
        row = {"pid": pid, "session_number": s["session_number"], "date": date, "period": period, "is_pilot": s["is_pilot"],
               "excluded": int(bool(codes)), "exclusion_rules": ";".join(codes), "h1_eligible": int(bool(h1_eligible(s, expected))),
               "hours_slept": q.get("hours_slept"), "kss": q.get("kss"), "caffeine": q.get("caffeine"),
               **{c: score.get(c) for c in SESSION_SCORES}}
        sess_rows.append({k: _fmt(v) for k, v in row.items()})
        counts[pid] = counts.get(pid, 0) + 1
        for t in s["trials"]:
            if t["practice"] == 0 and t["task"] in TASKS:
                trial_rows.append({"pid": pid, "session_number": s["session_number"], "trial_index": t["trial_index"], "task": t["task"],
                                   "condition": _condition(t) or "", "rt": _fmt(t["rt"]), "correct": _fmt(t["correct"])})
    part_rows = [{"pid": pid, "role": "owner" if code in owner_set else "consenting_participant", "n_sessions": counts.get(pid, 0)}
                 for code, pid in pid_map.items()]

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, rows in (("sessions.csv", sess_rows), ("trials.csv", trial_rows), ("participants.csv", part_rows)):
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS[name])
            w.writeheader()
            w.writerows(rows)
        written.append(out / name)
    _write_codebook(out)
    written.append(out / "codebook.md")
    problems = check_public_dir(out, known_codes=[*all_codes, *known_codes])
    if problems:
        for f in written:
            f.unlink(missing_ok=True)
        raise DeidError("export failed the de-identification check and was removed:\n  " + "\n  ".join(problems))
    return {"pid_map": pid_map, "omitted_participants": len(all_codes) - len(released), "omitted_sessions": omitted_sessions,
            "n_sessions": len(sess_rows), "n_trials": len(trial_rows)}


DESCRIPTIONS = {
    "pid": "pseudonym (P01, P02, ...); the key to real participant codes is private and never released",
    "session_number": "study session number", "date": "study day, YYYY-MM-DD (a start between midnight and 4 am belongs to the previous day, prereg D2); no time of day",
    "period": "AM (4 am to before noon) or PM, from the logged local start time (prereg D1/D9)",
    "is_pilot": "1 for the smoke-test sessions", "excluded": "1 if a preregistered exclusion rule or a manual exclusion applies",
    "exclusion_rules": f"codes joined by `;`: {', '.join(EXCLUSION_CODES)} (a manual note is never released, only the code `manual`)",
    "h1_eligible": "1 if the session is not excluded and has a sleep log (rule 5)", "hours_slept": "self-reported hours slept the previous night",
    "kss": "Karolinska Sleepiness Scale, 1-9", "caffeine": "1 if caffeine in the last 4 hours",
    "trial_index": "trial order within the session", "task": f"one of {', '.join(TASKS)}",
    "condition": "stroop: congruent/incongruent; posner: valid/invalid; nback: target/nontarget/lure1/lure3/start; yesno: signal/noise",
    "rt": "reaction time in ms (empty if no response)", "correct": "1 correct, 0 error (empty if not defined)",
    "role": "owner (the researcher) or consenting_participant", "n_sessions": "sessions released for this pseudonym",
    **{c: "session score (see docs/design/scoring.md); empty if not computable" for c in SESSION_SCORES},
}


def _write_codebook(out: Path, simulated: bool = False) -> None:
    lines = ["# MindBench public data: codebook", ""]
    if simulated:
        lines += ["**SIMULATED DATA. Not from any participant. Made by `mindbench.public_data simulate` to show the format and to test the analysis.**", ""]
    lines += ["Released only in de-identified form: no participant codes, no free text, nothing finer than the date. Scores follow "
              "`docs/design/scoring.md`; exclusions follow `docs/design/design.md` section 5. Licence CC-BY-4.0.", ""]
    for name, cols in COLUMNS.items():
        lines += [f"## {name}", "", "| column | meaning |", "|---|---|", *[f"| `{c}` | {DESCRIPTIONS[c]} |" for c in cols], ""]
    (out / "codebook.md").write_text("\n".join(lines), encoding="utf-8")


def simulate_public(out_dir, seed: int = 1, n_days: int = 21) -> None:
    """A fully simulated release in the real format (no trials), for demos and tests. Interference ~100 ms and validity
    effect ~50 ms by construction. Sessions 1-2 are smoke tests (flagged and excluded)."""
    import random

    rng = random.Random(seed)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    start = dt.date(2027, 1, 4)
    for d in range(n_days):
        hours = round(rng.gauss(7.0, 1.0), 1)
        for k, period in enumerate(("AM", "PM")):
            n = 2 * d + k + 1
            pilot = int(n <= 2)
            score = {c: "" for c in SESSION_SCORES}
            ri, rv = 100 + rng.gauss(0, 15), 50 + rng.gauss(0, 10)
            score.update(P1_dprime=repr(round(1.5 + rng.gauss(0, 0.4), 3)), P2_recall_proportion=repr(round(0.45 + rng.gauss(0, 0.05), 3)),
                         S1_mean_congruent_rt="550.0", S1_mean_incongruent_rt=repr(550.0 + ri), S1_stroop_interference=repr(ri),
                         S2_mean_valid_rt="420.0", S2_mean_invalid_rt=repr(420.0 + rv), S2_posner_validity_effect=repr(rv),
                         S4_dprime=repr(round(1.2 + rng.gauss(0, 0.3), 3)))
            rows.append({"pid": "P01", "session_number": n, "date": (start + dt.timedelta(days=d)).isoformat(), "period": period,
                         "is_pilot": pilot, "excluded": pilot, "exclusion_rules": "smoke_test" if pilot else "", "h1_eligible": int(not pilot),
                         "hours_slept": hours, "kss": rng.randint(2, 6), "caffeine": rng.randint(0, 1), **score})
    with open(out / "sessions.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS["sessions.csv"])
        w.writeheader()
        w.writerows(rows)
    for name, body in (("trials.csv", []), ("participants.csv", [{"pid": "P01", "role": "owner", "n_sessions": len(rows)}])):
        with open(out / name, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLUMNS[name])
            w.writeheader()
            w.writerows(body)
    _write_codebook(out, simulated=True)


# ------------------------------------------------------------------------------------------------ reproduction
def load_public(path) -> dict:
    """Read a release folder after checking it; refuses anything that fails the check."""
    problems = check_public_dir(path)
    if problems:
        raise DeidError("not analysed, fails the de-identification check:\n  " + "\n  ".join(problems))

    def read(name):
        with open(Path(path) / name, newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    return {"sessions": read("sessions.csv"), "trials": read("trials.csv"), "participants": read("participants.csv")}


def _num(s: str):
    return float(s) if s != "" else None


def _day_level_check(sessions, column, n_min=2):
    """Mean per (pseudonym, day), then the mean and a 95% t interval over days. Descriptive only."""
    from scipy import stats

    by_day: dict = {}
    for r in sessions:
        v = _num(r[column])
        if v is not None:
            by_day.setdefault((r["pid"], r["date"]), []).append(v)
    means = [sum(v) / len(v) for _, v in sorted(by_day.items())]
    if not means:
        return None
    est = sum(means) / len(means)
    interval = None
    if len(means) >= n_min:
        sd = (sum((m - est) ** 2 for m in means) / (len(means) - 1)) ** 0.5
        half = stats.t.ppf(0.975, len(means) - 1) * sd / len(means) ** 0.5
        interval = (est - half, est + half)
    direction = "unclear" if interval is None else "positive" if interval[0] > 0 else "negative" if interval[1] < 0 else "none"
    return {"conclusion": "descriptive", "estimate": est, "interval": interval, "direction": direction}


def reproduce(path) -> dict:
    """Recompute what can be computed from the release alone: counts and the two descriptive manipulation checks
    (Stroop interference, Posner validity effect), as day-level means over included sessions. Confirmatory and other
    analyses are not run here and stay pending in the synthesis table."""
    data = load_public(path)
    sessions = data["sessions"]
    included = [r for r in sessions if r["excluded"] == "0"]
    summary = {"n_participants": len({r["pid"] for r in sessions}), "n_sessions": len(sessions), "n_included": len(included),
               "n_days": len({(r["pid"], r["date"]) for r in included})}
    results = {}
    for aid, column in (("MC:S1", "S1_stroop_interference"), ("MC:S2", "S2_posner_validity_effect")):
        r = _day_level_check(included, column)
        if r:
            results[aid] = {"frequentist": r}
    return {"summary": summary, "results": results}


# ------------------------------------------------------------------------------------------------ command line
def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mindbench.public_data")
    sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("export", help="write the de-identified release from the private database")
    e.add_argument("--db", default="data/mindbench.sqlite")
    e.add_argument("--out", required=True, help="output folder (use a folder outside the repository until you have reviewed it)")
    e.add_argument("--owner", action="append", default=[], help="participant code of the researcher's own data (repeatable)")
    e.add_argument("--consent", help="private JSON file {participant_code: true}; only a literal true releases a friend's data")
    e.add_argument("--map", default="data/pid_map.json", help="private file for the code-to-pseudonym map (never release it)")
    e.add_argument("--fixture-expected", action="store_true", help="tests only: use the tiny synthetic session sizes")
    c = sub.add_parser("check", help="check a folder against the de-identification rules")
    c.add_argument("--dir", default="data_public")
    c.add_argument("--db", help="optional private database: its participant codes are searched for in every cell")
    sm = sub.add_parser("simulate", help="write a fully simulated release (for demos and tests)")
    sm.add_argument("--out", required=True)
    sm.add_argument("--seed", type=int, default=1)
    r = sub.add_parser("reproduce", help="recompute the descriptive results from a release folder")
    r.add_argument("--dir", default="data_public")
    args = p.parse_args(argv)

    if args.command == "export":
        import sqlite3

        expected = {"posner": 3, "stroop": 3, "nback": 6, "yesno": 4, "recall_lists": 2} if args.fixture_expected else None
        consent = json.loads(Path(args.consent).read_text()) if args.consent else {}
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
        try:
            report = export_public(conn, args.out, owners=args.owner, consent=consent, expected=expected)
        except DeidError as err:
            print(err, file=sys.stderr)
            return 1
        finally:
            conn.close()
        Path(args.map).parent.mkdir(parents=True, exist_ok=True)
        Path(args.map).write_text(json.dumps(report.pop("pid_map"), indent=2))
        print(f"wrote {report['n_sessions']} sessions and {report['n_trials']} trials to {args.out}; omitted {report['omitted_participants']} "
              f"participant(s) without consent; the private pseudonym map is in {args.map} (do not release it)")
        return 0
    if args.command == "check":
        codes = []
        if args.db:
            import sqlite3

            conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
            codes = [row[0] for row in conn.execute("SELECT participant_code FROM participants")]
            conn.close()
        problems = check_public_dir(args.dir, known_codes=codes)
        for pr in problems:
            print(pr)
        print("de-identification check: " + ("FAILED" if problems else "passed"))
        return 1 if problems else 0
    if args.command == "simulate":
        simulate_public(args.out, seed=args.seed)
        print(f"wrote a SIMULATED release to {args.out}")
        return 0
    try:
        out = reproduce(args.dir)
    except DeidError as err:
        print(err, file=sys.stderr)
        return 1
    print(json.dumps(out["summary"]))
    print(synthesis.render_markdown(synthesis.build_results_table(out["results"]), title=False, level=3))
    return 0


if __name__ == "__main__":
    sys.exit(main())
