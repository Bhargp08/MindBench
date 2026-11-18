import { buildPipeExtension } from "./pipeExtension.js";

/**
 * Saver factory. Mock mode keeps JSON copies in memory (and the shell offers a
 * download). Production mode returns the DataPipe extension, which saves by itself
 * (no manual save(); see docs/design/datapipe.md).
 */
export function createSaver({ mode, experimentId, getFilename, simulate, onSave } = {}) {
  if (mode === "mock") {
    const saved = [];
    return {
      saved,
      async save(filename, data) {
        const copy = JSON.parse(JSON.stringify(data)); // throws on cycles / non-JSON
        saved.push({ filename, data: copy });
      },
    };
  }
  if (mode === "production") {
    return { extensions: [buildPipeExtension({ experimentId, getFilename, simulate, onSave })] };
  }
  throw new Error(`Saver for mode "${mode}" is not implemented yet`);
}
