import { initJsPsych } from "jspsych";
import "jspsych/css/jspsych.css";
import htmlButtonResponse from "@jspsych/plugin-html-button-response";
import surveyHtmlForm from "@jspsych/plugin-survey-html-form";
import fullscreen from "@jspsych/plugin-fullscreen";

import { loadConfig } from "./lib/config.js";
import { CODE_ALPHABET, CODE_LENGTH, generateParticipantCode, isValidParticipantCode } from "./lib/participantCode.js";
import { validateQuestionnaire } from "./lib/questionnaire.js";
import { createSaver } from "./lib/save.js";
import { pipeFilename } from "./lib/pipeExtension.js";
import { buildSessionMetadata } from "./lib/sessionMetadata.js";
import { INFO_SCREEN_TEXT } from "./lib/info.js";
import { buildContrastTimeline, seedFrom } from "./tasks/contrast.js";

const JSPSYCH_VERSION = "8.4.0";

function showError(message) {
  document.body.innerHTML = `<p style="font:16px sans-serif;margin:2rem">${message}</p>`;
}

function storage() {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function rememberedCode() {
  const code = storage()?.getItem("mindbench.code");
  return isValidParticipantCode(code) ? code : generateParticipantCode();
}

function nextSessionNumber(code) {
  const s = storage();
  const key = `mindbench.sessions.${code}`;
  const n = Number(s?.getItem(key) ?? 0) + 1;
  try {
    s?.setItem(key, String(n));
  } catch {
    /* storage unavailable: session number falls back to 1 */
  }
  return n;
}

function downloadJson(filename, data) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

let config;
try {
  config = loadConfig({
    mode: import.meta.env.VITE_MINDBENCH_MODE ?? "mock",
    experimentId: import.meta.env.VITE_DATAPIPE_EXPERIMENT_ID,
  });
} catch (e) {
  showError(`Configuration error: ${e.message}`);
  throw e;
}

const state = { participantCode: null, sessionNumber: null, questionnaire: null };
const SIMULATE = new URLSearchParams(window.location.search).has("simulate");

let saver;
try {
  saver = createSaver({
    mode: config.mode,
    experimentId: config.experimentId,
    simulate: SIMULATE,
    // Evaluated at start (code not known yet, so it throws) and again at the end, as the extension documents.
    getFilename: () => pipeFilename({ participantCode: state.participantCode, sessionNumber: state.sessionNumber }),
    onSave: (result) => {
      if (!result.ok) showError("Your data could not be saved. Please contact the researcher and keep this page open.");
    },
  });
} catch (e) {
  showError(`This build cannot save data yet: ${e.message}`);
  throw e;
}

const jsPsych = initJsPsych({ extensions: saver.extensions ?? [], on_finish: finish });

function sessionMetadata() {
  return buildSessionMetadata({
    now: new Date(),
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    userAgent: navigator.userAgent,
    screen: { width: window.screen.width, height: window.screen.height },
    jsPsychVersion: JSPSYCH_VERSION,
  });
}

async function finish() {
  // Production: the DataPipe extension uploads jsPsych's data (which carries the properties added
  // after the questionnaire) and shows its own done message. Only mock mode saves here.
  if (SIMULATE && config.mode !== "mock") {
    showError("Simulated session complete (DataPipe disabled; nothing was saved).");
    return;
  }
  if (config.mode !== "mock") return;
  const metadata = sessionMetadata();
  const data = {
    participantCode: state.participantCode,
    sessionNumber: state.sessionNumber,
    mode: config.mode,
    metadata,
    questionnaire: state.questionnaire,
    trials: jsPsych.data.get().values(),
  };
  const filename = `${state.participantCode}_session${state.sessionNumber}.json`;
  await saver.save(filename, data);
  downloadJson(filename, data);
  document.body.innerHTML = `<p style="font:16px sans-serif;margin:2rem">Session complete (mock mode: a JSON file was downloaded, nothing was sent anywhere).</p>`;
}

const html = (s) => s.split("\n\n").map((p) => `<p>${p}</p>`).join("");

const timeline = [
  { type: fullscreen, fullscreen_mode: true, message: "<p>This study runs in full screen. Click to continue.</p>" },
  {
    type: htmlButtonResponse,
    stimulus: `<div style="max-width:640px;text-align:left">${html(INFO_SCREEN_TEXT)}</div>`,
    choices: ["I understand, continue"],
  },
  {
    type: surveyHtmlForm,
    preamble: "<p>Your participant code (random; keep it for later sessions):</p>",
    html: `<input name="code" type="text" required maxlength="${CODE_LENGTH}" value="${rememberedCode()}"
             pattern="[${CODE_ALPHABET.replace(/\d+/, "2-9")}]{${CODE_LENGTH}}" style="font-family:monospace;text-transform:uppercase" />`,
    button_label: "Continue",
    on_finish(trial) {
      const code = String(trial.response.code ?? "").trim().toUpperCase();
      if (!isValidParticipantCode(code)) {
        jsPsych.abortExperiment("Invalid participant code.");
        return;
      }
      state.participantCode = code;
      state.sessionNumber = nextSessionNumber(code);
      try {
        storage()?.setItem("mindbench.code", code);
      } catch {
        /* ignore */
      }
    },
  },
  {
    type: surveyHtmlForm,
    preamble: "<p>Before we start (about last night):</p>",
    html: `
      <p><label>Hours slept: <input name="hoursSlept" type="number" min="0" max="16" step="0.25" required></label></p>
      <p><label>Bed time: <input name="bedTime" type="time" required></label></p>
      <p><label>Wake time: <input name="wakeTime" type="time" required></label></p>
      <p><label>Sleepiness right now (1 = extremely alert, 9 = very sleepy):
        <select name="kss" required><option value="">Choose</option>${[1, 2, 3, 4, 5, 6, 7, 8, 9].map((n) => `<option>${n}</option>`).join("")}</select></label></p>
      <p>Caffeine in the last 4 hours?
        <label><input type="radio" name="caffeine" value="yes" required> Yes</label>
        <label><input type="radio" name="caffeine" value="no"> No</label></p>
      <p><label>Device: <select name="device" required><option value="">Choose</option><option>laptop</option><option>desktop</option></select></label></p>`,
    button_label: "Start",
    on_finish(trial) {
      const r = trial.response;
      const q = {
        hoursSlept: r.hoursSlept === "" ? NaN : Number(r.hoursSlept),
        bedTime: r.bedTime,
        wakeTime: r.wakeTime,
        kss: Number(r.kss),
        caffeine: r.caffeine === "yes" ? true : r.caffeine === "no" ? false : null,
        device: r.device,
      };
      const result = validateQuestionnaire(q);
      if (!result.valid) {
        jsPsych.abortExperiment(`Please check your answers: ${result.errors.map((e) => e.message).join("; ")}`);
        return;
      }
      state.questionnaire = q;
      // Attach to every trial row so the uploaded jsPsych data is self-describing.
      jsPsych.data.addProperties({
        participantCode: state.participantCode,
        sessionNumber: state.sessionNumber,
        questionnaire: q,
        sessionMetadata: sessionMetadata(),
      });
    },
  },
  ...buildContrastTimeline({ getSeed: () => seedFrom(state.participantCode, state.sessionNumber) }),
  {
    type: htmlButtonResponse,
    stimulus: "<p>Contrast tasks complete. The other tasks are added in later steps of the project (MB-08 to MB-12).</p>",
    choices: ["Finish"],
  },
];

jsPsych.run(timeline);
