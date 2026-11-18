import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";

import pool from "../data/wordpool.json";
import { getSessionLists, LISTS_PER_SESSION } from "../lib/recallLists.js";
import { scoreRecall, sessionRecallProportion } from "../lib/recallScore.js";
import { tagTrialData } from "../lib/practice.js";
import { introHtml } from "./common.js";

// Design choices (docs/design/design.md): 2 s per word, no distractor, 90 s typed recall per list.
const WORD_MS = 2000;
const RECALL_MS = 90000;

/**
 * Free recall block: LISTS_PER_SESSION lists, shown one word at a time, then typed recall.
 * `getSessionNumber()` picks the unused word lists for that session. `getLists`, `wordMs` and `recallMs`
 * can be overridden for dev runs.
 */
export function buildRecallTimeline({ jsPsych, getSessionNumber, getLists, wordMs = WORD_MS, recallMs = RECALL_MS, practice = false, nLists = LISTS_PER_SESSION, taskLabel = () => "Task" }) {
  let lists = [];
  const results = [];
  let typed = "";

  const wordTrials = (listIndex) => ({
    timeline: [
      {
        type: htmlKeyboardResponse,
        choices: "NO_KEYS",
        trial_duration: wordMs,
        stimulus: () => `<div style="font-size:56px">${lists[listIndex][wordIdx]}</div>`,
        on_start(t) {
          t.data = tagTrialData({ task: "recall_word", list: listIndex + 1, position: wordIdx + 1, word: lists[listIndex][wordIdx] }, { practice });
        },
        on_finish() {
          wordIdx += 1;
        },
      },
    ],
    loop_function: () => wordIdx < lists[listIndex].length,
    on_timeline_start: () => {
      wordIdx = 0;
    },
  });
  let wordIdx = 0;

  const recallTrial = (listIndex) => ({
    type: htmlKeyboardResponse,
    choices: "NO_KEYS",
    trial_duration: recallMs,
    stimulus: `<p>Type the words you remember, in any order (separate them with spaces or new lines).</p>
      <textarea id="recall-box" rows="8" cols="40" autocomplete="off" autocapitalize="off" spellcheck="false"></textarea>
      <p><button id="recall-done" class="jspsych-btn">I'm done</button></p>`,
    on_load() {
      typed = "";
      const box = document.getElementById("recall-box");
      box.addEventListener("input", () => {
        typed = box.value;
      });
      document.getElementById("recall-done").addEventListener("click", () => jsPsych.finishTrial());
      box.focus();
    },
    on_start(t) {
      t.data = tagTrialData({ task: "recall", list: listIndex + 1, listWords: lists[listIndex].slice() }, { practice });
    },
    on_finish(data) {
      const s = scoreRecall({ listWords: lists[listIndex], recallText: typed, pool: pool.words });
      Object.assign(data, { recallText: typed, recalled: s.recalled, nCorrect: s.nCorrect, proportion: s.proportion, intrusions: s.intrusions, repeats: s.repeats });
      results.push({ nCorrect: s.nCorrect, listLength: lists[listIndex].length });
    },
  });

  const intro = (listIndex) => ({
    type: htmlButtonResponse,
    choices: [practice ? "Start practice" : "Start list"],
    stimulus: () => {
      if (listIndex === 0) {
        results.length = 0;
        try {
          lists = getLists ? getLists() : getSessionLists(getSessionNumber());
        } catch (e) {
          jsPsych.abortExperiment(`This study has no unused word lists left (${e.message}).`);
          lists = Array.from({ length: nLists }, () => ["error"]);
        }
      }
      return introHtml({
        label: taskLabel(),
        practice,
        title: `word lists (list ${listIndex + 1} of ${nLists})`,
        keysFor: null,
        body: `<p>Words will appear one at a time. Try to remember as many as you can. Afterwards you will type the words you remember, in any order.</p>`,
      });
    },
  });

  const timeline = [];
  for (let k = 0; k < nLists; k++) timeline.push(intro(k), wordTrials(k), recallTrial(k));
  timeline.push({
    type: htmlButtonResponse,
    choices: ["Continue"],
    stimulus: () =>
      practice
        ? `<p>Practice complete: you remembered ${results.reduce((a, r) => a + r.nCorrect, 0)} of ${results.reduce((a, r) => a + r.listLength, 0)} words.</p>`
        : "<p>Word lists complete.</p>",
    on_finish(data) {
      data.task = "recall_summary";
      data.practice = practice;
      data.recallProportion = sessionRecallProportion(results);
      data.nCorrect = results.reduce((a, r) => a + r.nCorrect, 0);
      data.nWords = results.reduce((a, r) => a + r.listLength, 0);
    },
  });
  return timeline;
}
