import htmlKeyboardResponse from "@jspsych/plugin-html-keyboard-response";
import { FEEDBACK_MS, feedbackFor } from "../lib/practice.js";
import { describeKeys } from "../lib/keymap.js";

/** Intro screen text: task label, practice marker, instructions and the key reference. */
export function introHtml({ label, practice, title, body, keysFor }) {
  const heading = `${practice ? "Practice: " : ""}${label}: ${title}`;
  const note = practice ? "<p>This is a short practice with feedback. Your answers here are not part of the study data.</p>" : "";
  return `<div style="max-width:640px;text-align:left"><p><b>${heading}</b></p>${note}${body}${keysFor ? `<p><i>Keys: ${describeKeys(keysFor)}</i></p>` : ""}</div>`;
}

/** Brief feedback screen for a practice trial. getResult() returns { correct, responded, goNoGo? }. */
export function feedbackTrial(getResult) {
  return {
    type: htmlKeyboardResponse,
    choices: "NO_KEYS",
    trial_duration: FEEDBACK_MS,
    stimulus: () => {
      const f = feedbackFor(getResult());
      const color = f.kind === "correct" ? "#2a7f3f" : "#b3261e";
      return `<p style="font-size:28px;color:${color}">${f.text}</p>`;
    },
    data: { task: "feedback", practice: true },
  };
}
