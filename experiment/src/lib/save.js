/**
 * Saver factory. Mock mode keeps JSON copies in memory (and the shell offers a
 * download). Production saving uses the DataPipe extension and is added in a
 * separate, tested step (see docs/design/datapipe.md).
 */
export function createSaver({ mode } = {}) {
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
  throw new Error(`Saver for mode "${mode}" is not implemented yet`);
}
