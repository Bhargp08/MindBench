import { describe, it, expect } from "vitest";
import { INFO_SCREEN_TEXT } from "../src/lib/info.js";

describe("participant information screen text", () => {
  it("states voluntary participation, withdrawal and that sleep is not manipulated", () => {
    const t = INFO_SCREEN_TEXT.toLowerCase();
    expect(t).toContain("voluntary");
    expect(t).toContain("withdraw");
    expect(t).toMatch(/not (ask|asked) (you )?to change/);
  });

  it("does not claim institutional approval", () => {
    expect(INFO_SCREEN_TEXT).not.toMatch(/IRB[\s-]+approved|ethics\s+approval/i);
  });

  it("does not collect names, emails or IP addresses", () => {
    expect(INFO_SCREEN_TEXT.toLowerCase()).toContain("no names");
  });
});
