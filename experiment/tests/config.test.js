import { describe, it, expect } from "vitest";
import { loadConfig } from "../src/lib/config.js";

describe("loadConfig", () => {
  it("rejects a missing experiment ID in production mode", () => {
    expect(() => loadConfig({ mode: "production" })).toThrow(/experiment ?id/i);
    expect(() => loadConfig({ mode: "production", experimentId: "" })).toThrow(/experiment ?id/i);
    expect(() => loadConfig({ mode: "production", experimentId: "   " })).toThrow(/experiment ?id/i);
  });

  it("accepts a production config with an experiment ID", () => {
    expect(loadConfig({ mode: "production", experimentId: "abc123" })).toEqual({
      mode: "production",
      experimentId: "abc123",
    });
  });

  it("does not require an experiment ID in mock mode", () => {
    expect(loadConfig({ mode: "mock" })).toEqual({ mode: "mock", experimentId: null });
  });

  it("rejects an unknown mode", () => {
    expect(() => loadConfig({ mode: "staging" })).toThrow(/mode/i);
  });
});
