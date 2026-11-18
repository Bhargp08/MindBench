import PipeExtension from "@jspsych/extension-pipe";
import { isValidParticipantCode } from "./participantCode.js";

/** Unique, code-based filename, e.g. "K7M2QX9P_session3.json". */
export function pipeFilename({ participantCode, sessionNumber } = {}) {
  if (!isValidParticipantCode(participantCode)) throw new Error("Invalid participant code");
  if (!Number.isInteger(sessionNumber) || sessionNumber < 1) throw new Error("Invalid session number");
  return `${participantCode}_session${sessionNumber}.json`;
}

/**
 * DataPipe extension config for `initJsPsych({ extensions: [...] })`.
 * Verified against @jspsych/extension-pipe 0.2.0 (see docs/design/datapipe.md).
 * - `getFilename` is evaluated when the experiment starts (participant code known by then).
 * - `simulate: true` disables the extension so simulated runs never write to the dataset.
 * - `onSave(result)` receives the final upload result; `result.ok === false` means it failed.
 */
export function buildPipeExtension({ experimentId, getFilename, simulate = false, onSave } = {}) {
  if (typeof experimentId !== "string" || experimentId.trim() === "") {
    throw new Error("DataPipe experiment ID is required");
  }
  if (typeof getFilename !== "function") throw new Error("getFilename function is required");
  return {
    type: PipeExtension,
    params: {
      experiment_id: experimentId.trim(),
      filename: () => getFilename(),
      format: "json",
      stream: true,
      enabled: !simulate,
      on_save: (result) => onSave?.(result),
    },
  };
}
