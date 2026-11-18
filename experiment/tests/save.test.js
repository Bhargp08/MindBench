import { describe, it, expect } from "vitest";
import { createSaver } from "../src/lib/save.js";

describe("mock saver", () => {
  const data = {
    participantCode: "K7M2QX9P",
    sessionNumber: 3,
    questionnaire: { hoursSlept: 7.5, kss: 4 },
    trials: [{ task: "stroop", rt: 612, correct: true }],
  };

  it("receives the exact data object", async () => {
    const saver = createSaver({ mode: "mock" });
    await saver.save("K7M2QX9P_session3.json", data);
    expect(saver.saved).toEqual([{ filename: "K7M2QX9P_session3.json", data }]);
  });

  it("stores a copy, so later changes to the object do not alter what was saved", async () => {
    const saver = createSaver({ mode: "mock" });
    const mutable = structuredClone(data);
    await saver.save("f.json", mutable);
    mutable.trials.push({ task: "stroop", rt: 1, correct: false });
    expect(saver.saved[0].data).toEqual(data);
  });

  it("rejects data that cannot be serialized to JSON", async () => {
    const saver = createSaver({ mode: "mock" });
    const cyclic = {};
    cyclic.self = cyclic;
    await expect(saver.save("bad.json", cyclic)).rejects.toThrow();
    expect(saver.saved).toHaveLength(0);
  });
});
