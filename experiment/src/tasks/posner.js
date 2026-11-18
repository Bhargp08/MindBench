import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { buildPosnerTrials, isCorrectResponse } from "../lib/posner.js";
import { tagTrialData } from "../lib/practice.js";
import { feedbackTrial, introHtml } from "./common.js";

// Timings are design choices (docs/design/design.md): cue 100 ms + 200 ms gap = SOA 300 ms,
// target until response or 2,500 ms.
const CUE_MS = 100;
const GAP_MS = 200;
const TARGET_TIMEOUT_MS = 2500;
const ARROW = { left: "&larr;", right: "&rarr;" };

const box = (content) =>
  `<div style="width:90px;height:90px;border:3px solid #555;display:flex;align-items:center;justify-content:center;font-size:44px">${content}</div>`;

/** Three placeholder boxes with a central fixation/cue; the target (a filled circle) appears in one box. */
export function posnerDisplay({ center = "+", targetSide = null } = {}) {
  const target = "&#9679;";
  return `<div style="display:flex;gap:140px;align-items:center;justify-content:center;height:240px">
    ${box(targetSide === "left" ? target : "")}
    <div style="width:60px;text-align:center;font-size:44px">${center}</div>
    ${box(targetSide === "right" ? target : "")}
  </div>`;
}

/** Posner cueing block. `getSeed()` is read when the block starts; sizes can be reduced for dev runs. */
export function buildPosnerTimeline({ getSeed, nValid = 96, nInvalid = 24, practice = false, taskLabel = () => "Task" }) {
  let trials = [];
  let i = 0;
  let last = { correct: false, responded: false };
  const cur = () => trials[i];

  const intro = {
    type: htmlButtonResponse,
    choices: [practice ? "Start practice" : "Start"],
    stimulus: () => {
      trials = buildPosnerTrials({ seed: getSeed() + 2, nValid, nInvalid });
      i = 0;
      return introHtml({
        label: taskLabel(),
        practice,
        title: "where is the dot?",
        keysFor: "posner",
        body: `<p>Keep your eyes on the middle. An arrow will appear, then a dot will appear in the left or right box.
          The arrow usually points to where the dot will appear, but not always.</p>
          <p>Press <b>F</b> if the dot is in the <b>left</b> box and <b>J</b> if it is in the <b>right</b> box, as fast and accurately as you can.</p>`,
      });
    },
  };

  const trial = {
    timeline: [
      { type: htmlKeyboardResponse, stimulus: () => posnerDisplay({}), choices: "NO_KEYS", trial_duration: () => cur().fixationMs, data: { task: "fixation" },
        on_finish(data) {
          data.fixationMs = cur().fixationMs;
        } },
      { type: htmlKeyboardResponse, stimulus: () => posnerDisplay({ center: ARROW[cur().cueDirection] }), choices: "NO_KEYS", trial_duration: CUE_MS, data: { task: "posner_cue" } },
      { type: htmlKeyboardResponse, stimulus: () => posnerDisplay({}), choices: "NO_KEYS", trial_duration: GAP_MS, data: { task: "posner_gap" } },
      {
        type: htmlKeyboardResponse,
        stimulus: () => posnerDisplay({ targetSide: cur().targetSide }),
        choices: ["f", "j"],
        trial_duration: TARGET_TIMEOUT_MS,
        on_start(t) {
          const c = cur();
          t.data = tagTrialData({ task: "posner", trial: c.trial, valid: c.valid, targetSide: c.targetSide, cueDirection: c.cueDirection, soaMs: CUE_MS + GAP_MS }, { practice });
        },
        on_finish(data) {
          data.correct = isCorrectResponse(data.targetSide, data.response);
          last = { correct: data.correct, responded: data.response !== null };
          i += 1;
        },
      },
      ...(practice ? [feedbackTrial(() => last)] : []),
    ],
    loop_function: () => i < trials.length,
  };

  return [intro, trial];
}
