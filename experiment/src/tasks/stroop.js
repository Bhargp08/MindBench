import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { buildStroopTrials, isCorrectStroopResponse, STROOP_HEX, STROOP_KEYS } from "../lib/stroop.js";

// Timings are design choices (docs/design/design.md): ITI 500 ms, stimulus until response or 2,500 ms.
const ITI_MS = 500;
const TIMEOUT_MS = 2500;

export function stroopDisplay({ word, ink }) {
  return `<div style="font-size:64px;font-weight:700;letter-spacing:2px;color:${STROOP_HEX[ink]}">${word.toUpperCase()}</div>`;
}

/** Stroop block. `getSeed()` is read when the block starts; sizes can be reduced for dev runs. */
export function buildStroopTimeline({ getSeed, nCongruent = 60, nIncongruent = 60, nNeutral = 0 }) {
  let trials = [];
  let i = 0;
  const cur = () => trials[i];
  const keyList = Object.values(STROOP_KEYS);

  const swatch = (c) => `<span style="color:${STROOP_HEX[c]};font-weight:700">${STROOP_KEYS[c].toUpperCase()} = ${c}</span>`;

  const intro = {
    type: htmlButtonResponse,
    choices: ["Start"],
    stimulus: () => {
      trials = buildStroopTrials({ seed: getSeed() + 3, nCongruent, nIncongruent, nNeutral });
      i = 0;
      return `<p>Task 3 of 5: ink colors.</p>
        <p>A color word will appear. Ignore what the word says and press the key for the <b>ink color</b> it is printed in, as fast and accurately as you can:</p>
        <p>${["red", "green", "blue", "yellow"].map(swatch).join(" &nbsp; ")}</p>`;
    },
  };

  const trial = {
    timeline: [
      { type: htmlKeyboardResponse, stimulus: "<div style='font-size:48px'>+</div>", choices: "NO_KEYS", trial_duration: ITI_MS, data: { task: "fixation" } },
      {
        type: htmlKeyboardResponse,
        stimulus: () => stroopDisplay(cur()),
        choices: keyList,
        trial_duration: TIMEOUT_MS,
        on_start(t) {
          const c = cur();
          t.data = { task: "stroop", trial: c.trial, condition: c.condition, word: c.word, ink: c.ink };
        },
        on_finish(data) {
          data.correct = isCorrectStroopResponse(data.ink, data.response);
          i += 1;
        },
      },
    ],
    loop_function: () => i < trials.length,
  };

  return [intro, trial];
}
