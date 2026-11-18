import canvasKeyboardResponse from "@jspsych/plugin-canvas-keyboard-response";
import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { createStaircase } from "../lib/staircase.js";
import { balancedIntervals } from "../lib/intervals.js";
import { buildYesNoBlock } from "../lib/yesNoBlock.js";
import { createRng } from "../lib/rng.js";
import { levelToContrast } from "../lib/contrast.js";
import { drawGabor, GABOR } from "../lib/drawGabor.js";
import { KEYMAP } from "../lib/keymap.js";
import { PRACTICE, tagTrialData } from "../lib/practice.js";
import { feedbackTrial, introHtml } from "./common.js";

// Timings are design choices (docs/design/design.md section 3).
const FIXATION_MS = 500;
const STIMULUS_MS = 200;
const ISI_MS = 500;
const SIZE = [GABOR.size, GABOR.size];
const K = KEYMAP.contrast;

export function seedFrom(participantCode, sessionNumber) {
  let h = 0;
  for (const ch of participantCode) h = (h * 31 + ch.charCodeAt(0)) | 0;
  return (h ^ (sessionNumber * 7919)) | 0;
}

const fixation = { type: htmlKeyboardResponse, stimulus: "<div style='font-size:48px'>+</div>", choices: "NO_KEYS", trial_duration: FIXATION_MS, data: { task: "fixation" } };
const grey = (c) => drawGabor(c, 0);
const correctKey = (target) => (target === 1 ? K.intervalOne : K.intervalTwo);

const taskBody = `<p>On each trial you will see two flashes. One contains a faint striped patch; the other is blank. Press <b>F</b> if the patch was in the <b>first</b> flash, <b>J</b> if in the <b>second</b>.</p>`;

/** Practice: 6 forced-choice trials at a fixed, clearly visible level, with feedback. Not used for the threshold. */
export function buildContrastPractice({ getSeed, taskLabel = () => "Task" }) {
  let intervals = [];
  let i = 0;
  let last = { correct: false, responded: false };
  const interval = (n) => ({
    type: canvasKeyboardResponse,
    canvas_size: SIZE,
    choices: "NO_KEYS",
    trial_duration: STIMULUS_MS,
    stimulus: (c) => drawGabor(c, intervals[i] === n ? levelToContrast(PRACTICE.contrast.levelDb) : 0),
    data: { task: "staircase_interval", practice: true, interval: n },
  });
  const intro = {
    type: htmlButtonResponse,
    choices: ["Start practice"],
    stimulus: () => {
      intervals = balancedIntervals(PRACTICE.contrast.trials, createRng(getSeed() + 11));
      i = 0;
      return introHtml({ label: taskLabel(), practice: true, title: "faint patterns", body: taskBody, keysFor: "contrast" });
    },
  };
  const trial = {
    timeline: [
      fixation,
      interval(1),
      { type: canvasKeyboardResponse, canvas_size: SIZE, stimulus: grey, choices: "NO_KEYS", trial_duration: ISI_MS, data: { task: "isi" } },
      interval(2),
      {
        type: htmlKeyboardResponse,
        stimulus: "<p>Which flash had the patch? Press F (first) or J (second).</p>",
        choices: [K.intervalOne, K.intervalTwo],
        on_start(t) {
          t.data = tagTrialData({ task: "staircase", trial: i + 1, level: PRACTICE.contrast.levelDb, targetInterval: intervals[i] }, { practice: true });
        },
        on_finish(data) {
          data.correct = data.response === correctKey(data.targetInterval);
          last = { correct: data.correct, responded: data.response !== null };
          i += 1;
        },
      },
      feedbackTrial(() => last),
    ],
    loop_function: () => i < intervals.length,
  };
  return [intro, trial];
}

/**
 * Contrast staircase (2-interval forced choice, 1-up/2-down) followed by the fixed-contrast yes/no SDT block
 * at the staircase threshold. `getSeed()` is read when the block starts.
 */
export function buildContrastTimeline({ getSeed, taskLabel = () => "Task", staircaseOptions = {}, yesNoSize = {} }) {
  let stair;
  let intervals;
  let thresholdLevel;
  let usedFallback = false;
  let yesNo;
  let curYesNo = 0;

  const start = {
    type: htmlButtonResponse,
    choices: ["Start"],
    stimulus: () => {
      const seed = getSeed();
      stair = createStaircase(staircaseOptions);
      intervals = balancedIntervals(staircaseOptions.maxTrials ?? 60, createRng(seed));
      yesNo = buildYesNoBlock({ seed: seed + 1, ...yesNoSize });
      return introHtml({ label: taskLabel(), practice: false, title: "faint patterns", body: taskBody, keysFor: "contrast" });
    },
  };

  const target = () => intervals[stair.trialCount];
  const interval = (n) => ({
    type: canvasKeyboardResponse,
    canvas_size: SIZE,
    choices: "NO_KEYS",
    trial_duration: STIMULUS_MS,
    stimulus: (c) => drawGabor(c, target() === n ? levelToContrast(stair.level) : 0),
    data: { task: "staircase_interval", interval: n },
  });

  const staircaseTrial = {
    timeline: [
      fixation,
      interval(1),
      { type: canvasKeyboardResponse, canvas_size: SIZE, stimulus: grey, choices: "NO_KEYS", trial_duration: ISI_MS, data: { task: "isi" } },
      interval(2),
      {
        type: htmlKeyboardResponse,
        stimulus: "<p>Which flash had the patch? Press F (first) or J (second).</p>",
        choices: [K.intervalOne, K.intervalTwo],
        on_start(trial) {
          trial.data = tagTrialData(
            { task: "staircase", trial: stair.trialCount + 1, level: stair.level, contrast: levelToContrast(stair.level), targetInterval: target() },
            { practice: false },
          );
        },
        on_finish(data) {
          data.correct = data.response === correctKey(data.targetInterval);
          stair.respond(data.correct);
        },
      },
    ],
    loop_function: () => !stair.done,
  };

  const yesNoIntro = {
    type: htmlButtonResponse,
    choices: ["Continue"],
    stimulus: () => {
      const t = stair.threshold();
      usedFallback = t === null;
      thresholdLevel = t ?? stair.level;
      return `<div style="max-width:640px;text-align:left"><p>Next: a yes/no version. On each trial one flash appears. Press <b>F</b> if you saw the faint patch (<b>yes</b>) and <b>J</b> if you did not (<b>no</b>). Sometimes there is no patch.</p></div>`;
    },
    on_finish(data) {
      data.task = "threshold";
      data.thresholdLevel = thresholdLevel;
      data.thresholdContrast = levelToContrast(thresholdLevel);
      data.usedFallback = usedFallback; // true if fewer than 6 reversals: final level used instead
      data.nReversals = stair.reversals.length;
      data.reversals = stair.reversals.slice();
    },
  };

  const yesNoTrial = {
    type: canvasKeyboardResponse,
    canvas_size: SIZE,
    choices: [K.yes, K.no],
    stimulus_duration: STIMULUS_MS,
    trial_duration: 3000,
    prompt: "<p>Did you see the patch? F = yes, J = no</p>",
    stimulus: (c) => drawGabor(c, yesNo[curYesNo].isSignal ? levelToContrast(thresholdLevel) : 0),
    on_start(trial) {
      const isSignal = yesNo[curYesNo].isSignal;
      trial.data = tagTrialData({ task: "yesno", trial: curYesNo + 1, isSignal, contrast: isSignal ? levelToContrast(thresholdLevel) : 0 }, { practice: false });
    },
    on_finish(data) {
      data.respondedYes = data.response === K.yes;
      data.correct = data.respondedYes === data.isSignal;
      curYesNo += 1;
    },
  };

  const yesNoBlock = {
    timeline: [fixation, yesNoTrial],
    loop_function: () => curYesNo < yesNo.length,
    on_timeline_start: () => {
      curYesNo = 0;
    },
  };

  return [start, staircaseTrial, yesNoIntro, yesNoBlock];
}
