import canvasKeyboardResponse from "@jspsych/plugin-canvas-keyboard-response";
import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { createStaircase } from "../lib/staircase.js";
import { balancedIntervals } from "../lib/intervals.js";
import { buildYesNoBlock } from "../lib/yesNoBlock.js";
import { createRng } from "../lib/rng.js";
import { levelToContrast } from "../lib/contrast.js";
import { drawGabor, GABOR } from "../lib/drawGabor.js";

// Timings are design choices (docs/design/design.md section 3).
const FIXATION_MS = 500;
const STIMULUS_MS = 200;
const ISI_MS = 500;
const SIZE = [GABOR.size, GABOR.size];

export function seedFrom(participantCode, sessionNumber) {
  let h = 0;
  for (const ch of participantCode) h = (h * 31 + ch.charCodeAt(0)) | 0;
  return (h ^ (sessionNumber * 7919)) | 0;
}

/**
 * Contrast staircase (2-interval forced choice, 1-up/2-down) followed by the fixed-contrast
 * yes/no SDT block at the staircase threshold. `getSeed()` is read when the block starts.
 * Timeline trials are tagged task: "staircase" | "yesno" and log level/contrast per trial.
 */
export function buildContrastTimeline({ getSeed }) {
  let stair;
  let intervals;
  let thresholdLevel;
  let usedFallback = false;
  let yesNo;
  const start = { type: htmlButtonResponse, choices: ["Start"], stimulus: () => {
    const seed = getSeed();
    stair = createStaircase({});
    intervals = balancedIntervals(60, createRng(seed));
    yesNo = buildYesNoBlock({ seed: seed + 1 });
    return "<p>Task 1 of 5: faint patterns.</p><p>On each trial you will see two flashes. One contains a faint striped patch; the other is blank. Press <b>1</b> if the patch was in the first flash, <b>2</b> if in the second.</p>";
  } };

  const grey = (c) => drawGabor(c, 0);
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
      { type: htmlKeyboardResponse, stimulus: "<div style='font-size:48px'>+</div>", choices: "NO_KEYS", trial_duration: FIXATION_MS, data: { task: "fixation" } },
      interval(1),
      { type: canvasKeyboardResponse, canvas_size: SIZE, stimulus: grey, choices: "NO_KEYS", trial_duration: ISI_MS, data: { task: "isi" } },
      interval(2),
      {
        type: htmlKeyboardResponse,
        stimulus: "<p>Which flash had the patch? Press 1 or 2.</p>",
        choices: ["1", "2"],
        on_start(trial) {
          trial.data = { task: "staircase", trial: stair.trialCount + 1, level: stair.level, contrast: levelToContrast(stair.level), targetInterval: target() };
        },
        on_finish(data) {
          data.correct = data.response === String(data.targetInterval);
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
      return "<p>Next: a yes/no version. On each trial one flash appears. Press <b>Y</b> if you saw the faint patch and <b>N</b> if you did not. Sometimes there is no patch.</p>";
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
    choices: ["y", "n"],
    stimulus_duration: STIMULUS_MS,
    trial_duration: 3000,
    prompt: "<p>Did you see the patch? Y = yes, N = no</p>",
    stimulus: (c) => drawGabor(c, yesNo[curYesNo].isSignal ? levelToContrast(thresholdLevel) : 0),
    on_start(trial) {
      trial.data = { task: "yesno", trial: curYesNo + 1, isSignal: yesNo[curYesNo].isSignal, contrast: yesNo[curYesNo].isSignal ? levelToContrast(thresholdLevel) : 0 };
    },
    on_finish(data) {
      data.respondedYes = data.response === "y";
      data.correct = data.respondedYes === data.isSignal;
      curYesNo += 1;
    },
  };
  let curYesNo = 0;

  const yesNoBlock = {
    timeline: [
      { type: htmlKeyboardResponse, stimulus: "<div style='font-size:48px'>+</div>", choices: "NO_KEYS", trial_duration: FIXATION_MS, data: { task: "fixation" } },
      yesNoTrial,
    ],
    loop_function: () => curYesNo < yesNo.length,
    on_timeline_start: () => {
      curYesNo = 0;
    },
  };

  return [start, staircaseTrial, yesNoIntro, yesNoBlock];
}
