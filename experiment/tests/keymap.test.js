import { describe, it, expect } from "vitest";
import { KEYMAP, describeKeys } from "../src/lib/keymap.js";
import { isCorrectResponse } from "../src/lib/posner.js";
import { STROOP_KEYS } from "../src/lib/stroop.js";

describe("consistent key map: every two-choice task uses F (first/left/yes) and J (second/right/no)", () => {
  it("defines F and J", () => {
    expect(KEYMAP.twoChoice).toEqual({ first: "f", second: "j" });
  });

  it("contrast: interval 1 = F, interval 2 = J; yes = F, no = J", () => {
    expect(KEYMAP.contrast).toEqual({ intervalOne: "f", intervalTwo: "j", yes: "f", no: "j" });
  });

  it("posner: left = F, right = J (agrees with the Posner scorer)", () => {
    expect(KEYMAP.posner).toEqual({ left: "f", right: "j" });
    expect(isCorrectResponse("left", KEYMAP.posner.left)).toBe(true);
    expect(isCorrectResponse("right", KEYMAP.posner.right)).toBe(true);
  });

  it("stroop: D F J K on the home row (agrees with the Stroop scorer)", () => {
    expect(KEYMAP.stroop).toEqual({ red: "d", green: "f", blue: "j", yellow: "k" });
    expect(KEYMAP.stroop).toEqual(STROOP_KEYS);
  });

  it("2-back: SPACE for a match", () => {
    expect(KEYMAP.nback).toEqual({ match: " " });
  });

  it("never assigns one key to two responses within a response screen", () => {
    // contrast reuses F/J on purpose across its two phases (interval 1/2 in the staircase, yes/no in the SDT block)
    const screens = {
      "contrast staircase": [KEYMAP.contrast.intervalOne, KEYMAP.contrast.intervalTwo],
      "contrast yes/no": [KEYMAP.contrast.yes, KEYMAP.contrast.no],
      posner: Object.values(KEYMAP.posner),
      stroop: Object.values(KEYMAP.stroop),
      nback: Object.values(KEYMAP.nback),
    };
    for (const keys of Object.values(screens)) expect(new Set(keys).size).toBe(keys.length);
  });
});

describe("describeKeys (on-screen key reference)", () => {
  it("lists every key of a task in upper case, with SPACE spelled out", () => {
    expect(describeKeys("posner")).toMatch(/F/);
    expect(describeKeys("posner")).toMatch(/J/);
    for (const k of ["D", "F", "J", "K"]) expect(describeKeys("stroop")).toContain(k);
    expect(describeKeys("nback")).toMatch(/SPACE/);
    expect(describeKeys("contrast")).toMatch(/F/);
  });

  it("throws for an unknown task", () => {
    expect(() => describeKeys("nope")).toThrow();
  });
});
