export const MODES = ["mock", "production"];

/**
 * Validate runtime config. Production mode needs a DataPipe experiment ID
 * (not a secret); mock mode saves nothing remotely.
 */
export function loadConfig({ mode, experimentId } = {}) {
  if (!MODES.includes(mode)) {
    throw new Error(`Unknown mode "${mode}"; expected one of ${MODES.join(", ")}`);
  }
  if (mode === "production") {
    if (typeof experimentId !== "string" || experimentId.trim() === "") {
      throw new Error("Production mode requires a DataPipe experiment ID");
    }
    return { mode, experimentId: experimentId.trim() };
  }
  return { mode, experimentId: null };
}
