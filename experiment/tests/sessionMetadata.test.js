import { describe, it, expect } from "vitest";
import { buildSessionMetadata } from "../src/lib/sessionMetadata.js";

describe("buildSessionMetadata", () => {
  it("returns every required field", () => {
    const meta = buildSessionMetadata({
      now: new Date("2026-11-18T15:30:00.000Z"),
      timezone: "America/Los_Angeles",
      userAgent: "TestAgent/1.0",
      screen: { width: 1440, height: 900 },
      jsPsychVersion: "8.4.0",
    });
    expect(meta).toEqual({
      timestamp: "2026-11-18T15:30:00.000Z",
      timezone: "America/Los_Angeles",
      userAgent: "TestAgent/1.0",
      screenWidth: 1440,
      screenHeight: 900,
      jsPsychVersion: "8.4.0",
    });
  });

  it("throws if a field is missing", () => {
    expect(() => buildSessionMetadata({ now: new Date() })).toThrow();
  });
});
