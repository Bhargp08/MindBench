import { describe, it, expect } from "vitest";
import { validateQuestionnaire } from "../src/lib/questionnaire.js";

const valid = {
  hoursSlept: 7.5,
  bedTime: "23:30",
  wakeTime: "07:00",
  kss: 4,
  caffeine: false,
  device: "laptop",
};

const fieldsOf = (r) => r.errors.map((e) => e.field);

describe("validateQuestionnaire", () => {
  it("accepts a valid response", () => {
    expect(validateQuestionnaire(valid)).toEqual({ valid: true, errors: [] });
  });

  it("rejects sleep hours below 0", () => {
    const r = validateQuestionnaire({ ...valid, hoursSlept: -0.5 });
    expect(r.valid).toBe(false);
    expect(fieldsOf(r)).toContain("hoursSlept");
  });

  it("rejects sleep hours above 16", () => {
    const r = validateQuestionnaire({ ...valid, hoursSlept: 16.5 });
    expect(r.valid).toBe(false);
    expect(fieldsOf(r)).toContain("hoursSlept");
  });

  it("accepts the boundary values 0 and 16", () => {
    expect(validateQuestionnaire({ ...valid, hoursSlept: 0 }).valid).toBe(true);
    expect(validateQuestionnaire({ ...valid, hoursSlept: 16 }).valid).toBe(true);
  });

  it("rejects non-numeric or missing sleep hours", () => {
    expect(fieldsOf(validateQuestionnaire({ ...valid, hoursSlept: "seven" }))).toContain("hoursSlept");
    const { hoursSlept, ...rest } = valid;
    expect(fieldsOf(validateQuestionnaire(rest))).toContain("hoursSlept");
  });

  it("requires KSS to be an integer from 1 to 9", () => {
    for (const bad of [0, 10, 4.5, "5"]) {
      expect(fieldsOf(validateQuestionnaire({ ...valid, kss: bad }))).toContain("kss");
    }
    for (const ok of [1, 9]) expect(validateQuestionnaire({ ...valid, kss: ok }).valid).toBe(true);
  });

  it("requires HH:MM times, a boolean caffeine flag and a device", () => {
    expect(fieldsOf(validateQuestionnaire({ ...valid, bedTime: "25:00" }))).toContain("bedTime");
    expect(fieldsOf(validateQuestionnaire({ ...valid, wakeTime: "7am" }))).toContain("wakeTime");
    expect(fieldsOf(validateQuestionnaire({ ...valid, caffeine: "no" }))).toContain("caffeine");
    expect(fieldsOf(validateQuestionnaire({ ...valid, device: "" }))).toContain("device");
  });
});
