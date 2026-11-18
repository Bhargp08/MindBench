import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { buildNBackSequence } from "../lib/nback.js";

// Timings are design choices (docs/design/design.md): letter 500 ms, response window 2,000 ms from onset
// is covered by a fixed 2,500 ms trial so pacing does not depend on the response.
const LETTER_MS = 500;
const TRIAL_MS = 2500;

/** 2-back block (go/no-go: SPACE for a match, nothing otherwise). `getSeed()` is read when the block starts. */
export function buildNBackTimeline({ getSeed, nTrials = 60, nTargets = 18, nLureOne = 3, nLureThree = 3 }) {
  let seq = [];
  let i = 0;
  const cur = () => seq[i];

  const intro = {
    type: htmlButtonResponse,
    choices: ["Start"],
    stimulus: () => {
      seq = buildNBackSequence({ seed: getSeed() + 4, nTrials, nTargets, nLureOne, nLureThree });
      i = 0;
      return `<p>Task 4 of 5: two back.</p>
        <p>Letters will appear one at a time. Press the <b>SPACE</b> bar when the letter on the screen is the <b>same as the letter two before it</b>. Otherwise do nothing.</p>
        <p>For example, in the sequence K, T, K you would press SPACE on the second K. Matches one or three letters back are not matches.</p>`;
    },
  };

  const trial = {
    type: htmlKeyboardResponse,
    stimulus: () => `<div style="font-size:80px;font-weight:700">${cur().letter}</div>`,
    choices: [" "],
    stimulus_duration: LETTER_MS,
    trial_duration: TRIAL_MS,
    response_ends_trial: false,
    on_start(t) {
      const c = cur();
      t.data = { task: "nback", trial: c.trial, position: c.trial, letter: c.letter, type: c.type, isTarget: c.isTarget };
    },
    on_finish(data) {
      data.responded = data.response !== null;
      i += 1;
    },
  };

  return [intro, { timeline: [trial], loop_function: () => i < seq.length }];
}
