import { describe, it, expect, vi } from "vitest";
import PipeExtension from "@jspsych/extension-pipe";
import { buildPipeExtension, pipeFilename } from "../src/lib/pipeExtension.js";
import { createSaver } from "../src/lib/save.js";

const ID = "abcdef123456"; // DataPipe experiment IDs are 12 characters (not secret)

describe("pipeFilename", () => {
  it("builds a unique, code-based filename", () => {
    expect(pipeFilename({ participantCode: "K7M2QX9P", sessionNumber: 3 })).toBe("K7M2QX9P_session3.json");
  });

  it("rejects an invalid participant code or session number", () => {
    expect(() => pipeFilename({ participantCode: "bad", sessionNumber: 1 })).toThrow();
    expect(() => pipeFilename({ participantCode: "K7M2QX9P", sessionNumber: 0 })).toThrow();
  });
});

describe("buildPipeExtension", () => {
  const getFilename = () => "K7M2QX9P_session3.json";

  it("returns the DataPipe extension with the verified parameters", () => {
    const ext = buildPipeExtension({ experimentId: ID, getFilename });
    expect(ext.type).toBe(PipeExtension);
    expect(ext.params.experiment_id).toBe(ID);
    expect(ext.params.format).toBe("json");
    expect(ext.params.stream).toBe(true);
    expect(ext.params.enabled).toBe(true);
    expect(typeof ext.params.filename).toBe("function");
    expect(ext.params.filename()).toBe("K7M2QX9P_session3.json");
  });

  it("requires an experiment ID", () => {
    for (const bad of [undefined, "", "   "]) {
      expect(() => buildPipeExtension({ experimentId: bad, getFilename })).toThrow(/experiment ?id/i);
    }
  });

  it("is disabled when simulating, so fake data never reaches the dataset", () => {
    const ext = buildPipeExtension({ experimentId: ID, getFilename, simulate: true });
    expect(ext.params.enabled).toBe(false);
  });

  it("reports a failed save through on_save", () => {
    const onSave = vi.fn();
    const ext = buildPipeExtension({ experimentId: ID, getFilename, onSave });
    const result = { ok: false };
    ext.params.on_save(result);
    expect(onSave).toHaveBeenCalledWith(result);
  });
});

describe("createSaver (production)", () => {
  it("exposes the DataPipe extension and has no manual save()", () => {
    const saver = createSaver({ mode: "production", experimentId: ID, getFilename: () => "f.json" });
    expect(saver.extensions).toHaveLength(1);
    expect(saver.extensions[0].params.experiment_id).toBe(ID);
    expect(saver.save).toBeUndefined();
  });

  it("requires an experiment ID in production mode", () => {
    expect(() => createSaver({ mode: "production", getFilename: () => "f.json" })).toThrow(/experiment ?id/i);
  });
});
