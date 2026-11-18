import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { TASKS } from "../lib/latinSquare.js";
import { buildBatteryPlan, viewingInstruction, VIEWING_DISTANCE_CM } from "../lib/battery.js";
import { PRACTICE } from "../lib/practice.js";
import { createTimingLog, measureRefreshRate } from "../lib/timingLog.js";
import { buildContrastPractice, buildContrastTimeline } from "./contrast.js";
import { buildPosnerTimeline } from "./posner.js";
import { buildStroopTimeline } from "./stroop.js";
import { buildNBackTimeline } from "./nback.js";
import { buildRecallTimeline } from "./recall.js";

// Dev-only shortened sizes (npm run dev with ?quick) so the whole flow can be exercised quickly.
const QUICK = {
  contrast: { staircaseOptions: { stopReversals: 2, maxTrials: 6 }, yesNoSize: { nSignal: 2, nNoise: 2 } },
  posner: { nValid: 3, nInvalid: 1 },
  stroop: { nCongruent: 2, nIncongruent: 2 },
  nback: { nTrials: 12, nTargets: 3, nLureOne: 1, nLureThree: 1 },
  recall: { wordMs: 150, recallMs: 6000 },
};

/**
 * Everything after the questionnaire: setup screen (viewing distance, refresh-rate measurement), the five tasks in
 * the session's Latin-square order (practice with feedback, then the real block), progress bar and timing log.
 * Order depends on the session number, known only after the code screen, so all 5 slots x 5 tasks are built and
 * the conditional_function picks which one runs.
 */
export function buildBatteryTimeline({ jsPsych, state, getSeed, quick = false }) {
  const timing = createTimingLog();
  const env = { refresh: null };
  const plan = () => buildBatteryPlan(state.sessionNumber);
  const q = quick ? QUICK : {};

  const builders = (id, taskLabel) => {
    const common = { getSeed, taskLabel };
    switch (id) {
      case "contrast":
        return [...buildContrastPractice(common), ...buildContrastTimeline({ ...common, ...q.contrast })];
      case "posner":
        return [...buildPosnerTimeline({ ...common, ...PRACTICE.posner, practice: true }), ...buildPosnerTimeline({ ...common, ...q.posner })];
      case "stroop":
        return [...buildStroopTimeline({ ...common, ...PRACTICE.stroop, practice: true }), ...buildStroopTimeline({ ...common, ...q.stroop })];
      case "nback":
        return [...buildNBackTimeline({ ...common, ...PRACTICE.nback, practice: true }), ...buildNBackTimeline({ ...common, ...q.nback })];
      case "recall": {
        const r = { jsPsych, getSessionNumber: () => state.sessionNumber, taskLabel };
        return [
          ...buildRecallTimeline({ ...r, practice: true, nLists: 1, getLists: () => [PRACTICE.recall.words], recallMs: PRACTICE.recall.recallMs, ...(quick ? { wordMs: 150, recallMs: 4000 } : {}) }),
          ...buildRecallTimeline({ ...r, ...q.recall }),
        ];
      }
      default:
        throw new Error(`Unknown task ${id}`);
    }
  };

  const setup = {
    type: htmlButtonResponse,
    choices: ["I'm ready"],
    stimulus: `<div style="max-width:640px;text-align:left">
      <p><b>Before you start</b></p>
      <p>${viewingInstruction()}</p>
      <p>Stay in full screen, close other tabs and apps, and rest your index fingers on F and J. There are five short tasks, each with a practice first; the bar at the top shows your progress.</p></div>`,
    on_load() {
      env.refreshVisibility = document.visibilityState;
      measureRefreshRate().then((r) => {
        env.refresh = r;
      });
    },
    on_finish(data) {
      data.task = "setup";
      data.viewingDistanceInstructedCm = VIEWING_DISTANCE_CM;
      data.refresh = env.refresh;
    },
  };

  const slots = [];
  for (let k = 0; k < TASKS.length; k++) {
    for (const id of TASKS) {
      slots.push({
        conditional_function: () => plan()[k].task === id,
        timeline: builders(id, () => plan()[k].label),
        on_timeline_start: () => {
          jsPsych.progressBar.progress = plan()[k].progressBefore;
          timing.start(id);
        },
        on_timeline_finish: () => {
          timing.end(id);
          jsPsych.progressBar.progress = plan()[k].progressAfter;
        },
      });
    }
  }

  const done = {
    type: htmlButtonResponse,
    choices: ["Finish"],
    stimulus: "<p>All five tasks are complete. Thank you!</p>",
    on_finish(data) {
      data.task = "timing";
      data.timing = timing.toJSON();
      data.refresh = env.refresh;
      data.refreshPageVisibility = env.refreshVisibility; // measurement is unreliable if not "visible"
      data.taskOrder = plan().map((p) => p.task);
      data.viewingDistanceInstructedCm = VIEWING_DISTANCE_CM;
      data.innerWidth = window.innerWidth;
      data.innerHeight = window.innerHeight;
      data.devicePixelRatio = window.devicePixelRatio;
      data.fullscreen = !!document.fullscreenElement;
    },
  };

  return { timeline: [setup, ...slots, done], timing, env };
}
