"""Generates the synthetic session fixtures in this folder (no real data).

Run from etl/:  uv run python tests/fixtures/generate_fixtures.py
Rows follow what the experiment uploads through DataPipe: a JSON array of jsPsych data rows, with the participant
code, session number, questionnaire, session metadata and task order attached to every row (addProperties).
"""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
TASKS = ["contrast", "posner", "stroop", "nback", "recall"]


def build(code, session, task_order, day):
    props = {
        "participantCode": code,
        "sessionNumber": session,
        "questionnaire": {"hoursSlept": 7.5, "bedTime": "23:30", "wakeTime": "07:00", "kss": 4, "caffeine": False, "device": "laptop"},
        "sessionMetadata": {
            "timestamp": f"2026-11-{day:02d}T15:30:00.000Z",
            "timezone": "America/Los_Angeles",
            "userAgent": "SyntheticFixture/1.0",
            "screenWidth": 1440,
            "screenHeight": 900,
            "jsPsychVersion": "8.4.0",
        },
        "taskOrder": task_order,
    }
    rows = []

    def add(trial_type, **kw):
        i = len(rows)
        rt = kw.pop("rt", None)
        row = {"trial_type": trial_type, "trial_index": i, "time_elapsed": 1000 * (i + 1), "internal_node_id": f"0.0-{i}.0", "rt": rt}
        row.update(kw)
        row.update(props)
        rows.append(row)

    add("fullscreen")
    add("html-button-response", response=0, rt=900)
    add("survey-html-form", response={"code": code})
    add("survey-html-form", response={"hoursSlept": "7.5"})
    add("html-button-response", task="setup", viewingDistanceInstructedCm=57,
        refresh={"hz": 59.94, "medianFrameMs": 16.68, "sdMs": 0.21, "nDroppedFrames": 0, "nFrames": 60, "plausible": True, "nominalHz": 60})

    def fb(correct):
        add("html-keyboard-response", task="feedback", practice=True)

    for task in task_order:
        if task == "contrast":
            for practice, n in ((True, 2), (False, 3)):
                for t in range(1, n + 1):
                    tag = {"practice": practice} if practice else {}
                    add("html-keyboard-response", task="fixation")
                    add("canvas-keyboard-response", task="staircase_interval", interval=1, **tag)
                    add("canvas-keyboard-response", task="isi")
                    add("canvas-keyboard-response", task="staircase_interval", interval=2, **tag)
                    add("html-keyboard-response", task="staircase", trial=t, level=-10 + 3 * (t % 2), contrast=0.3, targetInterval=1 + t % 2,
                        response="f" if t % 2 else "j", correct=bool(t % 2), rt=600 + 10 * t, practice=practice)
                    if practice:
                        fb(True)
            add("html-button-response", task="threshold", thresholdLevel=-11.5, thresholdContrast=0.266, usedFallback=False, nReversals=10,
                reversals=[-10, -13, -10, -11.5, -10, -11.5, -10, -11.5, -10, -11.5])
            for t in range(1, 5):
                add("html-keyboard-response", task="fixation")
                add("canvas-keyboard-response", task="yesno", trial=t, isSignal=bool(t % 2), contrast=0.266 if t % 2 else 0,
                    response="f" if t % 2 else "j", respondedYes=bool(t % 2), correct=True, rt=550 + 20 * t, practice=False)
        elif task == "posner":
            for practice, n in ((True, 2), (False, 3)):
                for t in range(1, n + 1):
                    add("html-keyboard-response", task="fixation")
                    add("html-keyboard-response", task="posner_cue")
                    add("html-keyboard-response", task="posner_gap")
                    side = "left" if t % 2 else "right"
                    add("html-keyboard-response", task="posner", trial=t, valid=t != 2, targetSide=side, cueDirection=side if t != 2 else "right",
                        soaMs=300, response="f" if side == "left" else "j", correct=True, rt=350 + 15 * t, practice=practice)
                    if practice:
                        fb(True)
        elif task == "stroop":
            for practice, n in ((True, 2), (False, 3)):
                for t in range(1, n + 1):
                    add("html-keyboard-response", task="fixation")
                    cong = t % 2 == 1
                    add("html-keyboard-response", task="stroop", trial=t, condition="congruent" if cong else "incongruent", word="red",
                        ink="red" if cong else "blue", response="d" if cong else "j", correct=True, rt=620 + (0 if cong else 80), practice=practice)
                    if practice:
                        fb(True)
        elif task == "nback":
            for practice, n in ((True, 4), (False, 6)):
                for t in range(1, n + 1):
                    typ = "start" if t <= 2 else ("target" if t % 3 == 0 else "nontarget")
                    responded = typ == "target"
                    add("html-keyboard-response", task="nback", trial=t, position=t, letter="KTBDGH"[t % 6], type=typ,
                        isTarget=typ == "target", responded=responded, response=" " if responded else None, rt=700 if responded else None, practice=practice)
                    if practice:
                        fb(True)
        elif task == "recall":
            words = [["window", "pencil", "bridge"], ["alpha", "bravo", "cargo", "delta"], ["eagle", "flute", "grape", "hotel"]]
            for li, (practice, ws) in enumerate(((True, words[0]), (False, words[1]), (False, words[2]))):
                for p, w in enumerate(ws, 1):
                    add("html-keyboard-response", task="recall_word", list=1 if practice else li, position=p, word=w, practice=practice)
                add("html-keyboard-response", task="recall", list=1 if practice else li, listWords=ws, recallText=" ".join(ws[:2]),
                    recalled=[True, True] + [False] * (len(ws) - 2), nCorrect=2, proportion=2 / len(ws), intrusions=[], repeats=0, practice=practice, rt=None)
                if li in (0, 2):
                    # consistent with the recall rows above: practice 2 of 3 words, real 2 + 2 of 4 + 4 words
                    add("html-button-response", task="recall_summary", recallProportion=2 / 3 if practice else 0.5, nCorrect=2 if practice else 4,
                        nWords=3 if practice else 8, practice=practice)
    add("html-button-response", task="timing", timing={"tasks": {t: {"ms": 60000} for t in task_order}, "totalTaskMs": 300000, "unfinished": []},
        refresh={"hz": 59.94, "medianFrameMs": 16.68, "sdMs": 0.21, "nDroppedFrames": 0, "nFrames": 60, "plausible": True, "nominalHz": 60},
        viewingDistanceInstructedCm=57, innerWidth=1440, innerHeight=800, devicePixelRatio=2, fullscreen=True)
    return rows


def main():
    # orders from the Latin square (see experiment/src/lib/latinSquare.js)
    out = {
        "K7M2QX9P_session3.json": build("K7M2QX9P", 3, ["stroop", "nback", "posner", "recall", "contrast"], 18),
        "K7M2QX9P_session11.json": build("K7M2QX9P", 11, ["contrast", "posner", "recall", "stroop", "nback"], 25),
    }
    for name, rows in out.items():
        (HERE / name).write_text(json.dumps(rows, indent=1) + "\n")
        c = Counter(r.get("task") for r in rows)
        print(name, len(rows), dict(sorted(c.items(), key=lambda kv: str(kv[0]))))


if __name__ == "__main__":
    main()
