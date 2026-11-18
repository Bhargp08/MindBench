import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import { buildNBackSequence } from "../lib/nback.js";
import { KEYMAP } from "../lib/keymap.js";
import { tagTrialData } from "../lib/practice.js";
import { feedbackTrial, introHtml } from "./common.js";

// Timings are design choices (docs/design/design.md): letter 500 ms, response window 2,000 ms from onset
// is covered by a fixed 2,500 ms trial so pacing does not depend on the response.
const LETTER_MS = 500;
const TRIAL_MS = 2500;

/** 2-back block (go/no-go: SPACE for a match, nothing otherwise). `getSeed()` is read when the block starts. */
export function buildNBackTimeline({ getSeed, nTrials = 60, nTargets = 18, nLureOne = 3, nLureThree = 3, practice = false, taskLabel = () => "Task" }) {
  let seq = [];
  let i = 0;
  let last = { correct: false, responded: false, goNoGo: true };
  const cur = () => seq[i];

  const intro = {
    type: htmlButtonResponse,
    choices: [practice ? "Start practice" : "Start"],
    stimulus: () => {
      seq = buildNBackSequence({ seed: getSeed() + 4, nTrials, nTargets, nLureOne, nLureThree });
      i = 0;
      return introHtml({
        label: taskLabel(),
        practice,
        title: "two back",
        keysFor: "nback",
        body: `<p>Letters will appear one at a time. Press the <b>SPACE</b> bar when the letter on the screen is the <b>same as the letter two before it</b>. Otherwise do nothing.</p>
          <p>For example, in the sequence K, T, K you would press SPACE on the second K. Matches one or three letters back are not matches.</p>`,
      });
    },
  };

  const trial = {
    type: htmlKeyboardResponse,
    stimulus: () => `<div style="font-size:80px;font-weight:700">${cur().letter}</div>`,
    choices: [KEYMAP.nback.match],
    stimulus_duration: LETTER_MS,
    trial_duration: TRIAL_MS,
    response_ends_trial: false,
    on_start(t) {
      const c = cur();
      t.data = tagTrialData({ task: "nback", trial: c.trial, position: c.trial, letter: c.letter, type: c.type, isTarget: c.isTarget }, { practice });
    },
    on_finish(data) {
      data.responded = data.response !== null;
      last = { correct: data.responded === data.isTarget, responded: data.responded, goNoGo: true };
      i += 1;
    },
  };

  return [intro, { timeline: [trial, ...(practice ? [feedbackTrial(() => last)] : [])], loop_function: () => i < seq.length }];
}
