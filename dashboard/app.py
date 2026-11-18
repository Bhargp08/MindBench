"""MindBench monitoring dashboard (Streamlit). Run from the repo root:  uv run --project dashboard streamlit run dashboard/app.py

Preregistered monitoring only: completion and data quality. It never shows outcome values and runs no hypothesis tests.
"""
import datetime as dt
import os

import pandas as pd
import streamlit as st

from mindbench_dashboard.config import load_config
from mindbench_dashboard.metrics import CONFIRMATORY_TARGET, build_dashboard_data

cfg = load_config(os.environ)
public = cfg["public"]
d = build_dashboard_data(cfg["db"], cfg["raw"], cfg["report"], cfg["expected"], dt.date.today(), public=public)

st.set_page_config(page_title="MindBench monitoring", layout="wide")
st.title("MindBench monitoring")
st.info(
    "This dashboard shows completion and data quality only. It never shows outcome values and runs no hypothesis tests "
    "during collection (preregistered monitoring only)."
)
if public:
    st.caption("Public view: aggregate counts only, with no participant codes, file names, timestamps finer than a date or sleep data.")
if not d["db_found"]:
    st.warning("No database found yet. Run the nightly ETL (dashboard/schedule/ has templates).")

s, sched, stop = d["summary"], d["schedule"], d["stopping"]

# ------------------------------------------------------------------ Completion
st.subheader("Completion")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Confirmatory sessions completed", f"{s['confirmatory_completed']} / {CONFIRMATORY_TARGET}")
c2.metric("Remaining to target", s["remaining_to_target"])
c3.metric("Smoke tests run", s["smoke_tests_run"])
c4.metric("Excluded sessions", s["excluded"])
if sched["day_number"] is not None:
    st.write(f"Day {sched['day_number']} of the 21 scheduled days since {sched['first_confirmatory_date']} "
             f"({sched['scheduled_days_remaining']} scheduled days left, {sched['extension_days_remaining']} including the extension).")
(st.error if stop["stop"] else st.success)(f"Stopping rule: {stop['reason']}")
if s["excluded_by_reason"]:
    st.dataframe(pd.DataFrame([{"reason": k, "sessions": v} for k, v in s["excluded_by_reason"].items()]), hide_index=True)

# ------------------------------------------------------------------ Gaps and partial uploads
st.subheader("Session-number gaps")
st.caption("Session numbers from 3 up to the highest seen that have no loaded session. The stopping rule counts completed sessions, "
           "so a stopped session shows up here as missing, not as excluded.")
if public:
    st.write(f"{d['gap_count']} gap(s).")
elif d["gaps"]:
    st.dataframe(pd.DataFrame(d["gaps"]), hide_index=True)
else:
    st.write("No gaps.")

st.subheader("Skipped partial uploads")
st.caption("Abandoned sessions are left by the upload service as partial files; the ETL skips them.")
if public:
    st.write(f"{d['partial_upload_count']} partial upload(s) skipped; {d['failed_file_count']} file(s) failed validation.")
else:
    partial = d["partial_files"]
    if partial["partial"]:
        st.dataframe(pd.DataFrame(partial["partial"])[["session_number", "filename"]], hide_index=True)
    else:
        st.write("No partial uploads.")
    if partial["unparsed"]:
        st.write("Partial files with unexpected names: " + ", ".join(partial["unparsed"]))
    if d["failed_files"]:
        st.write("Files that failed validation (see the ETL report):")
        st.dataframe(pd.DataFrame(d["failed_files"]), hide_index=True)

# ------------------------------------------------------------------ Data quality
st.subheader("Data quality")
if public:
    st.dataframe(pd.DataFrame([{"task": t, **v} for t, v in d["task_completion"].items()]), hide_index=True)
else:
    ov = pd.DataFrame(d["overview"])
    if not ov.empty:
        ov["excluded_codes"] = ov["excluded_codes"].map("; ".join)
        cols = ["session_number", "is_pilot", "local_date", "time_of_day", "in_planned_window", "battery_finished", "n_tasks_complete",
                "sleep_logged", "total_task_minutes", "refresh_hz", "refresh_plausible", "stroop_flag", "excluded_codes"]
        st.dataframe(ov[cols], hide_index=True)
        st.caption("stroop_flag compares congruent-trial accuracy with the preregistered 60% exclusion limit; the value is not shown.")
    q = pd.DataFrame(d["quality"])
    if not q.empty:
        st.write("Task duration (minutes) by session")
        st.line_chart(q.pivot(index="session_number", columns="task", values="duration_ms") / 60000)
        st.write("Share of trials with no response (timeouts) by session")
        st.line_chart(q[q["no_response_rate"].notna()].pivot(index="session_number", columns="task", values="no_response_rate"))
        st.write("Responses faster than 200 ms (anticipations) by session")
        st.line_chart(q[q["anticipations"].notna()].pivot(index="session_number", columns="task", values="anticipations"))

# ------------------------------------------------------------------ Sleep log (local only)
if not public:
    st.subheader("Sleep log")
    sl = pd.DataFrame(d["sleep_log"])
    if not sl.empty:
        st.dataframe(sl, hide_index=True)
        st.bar_chart(sl.set_index("session_number")["hours_slept"])
    else:
        st.write("No sessions yet.")
    if d["etl"]:
        st.subheader("Last nightly ETL")
        st.write(f"Ran at {d['etl']['ran_at']}; download: {(d['etl']['download'] or {}).get('status')}.")
