import { describe, it, expect } from "vitest";
import { buildBatteryPlan, progressFraction, VIEWING_DISTANCE_CM, viewingInstruction } from "../src/lib/battery.js";
import { orderForSession } from "../src/lib/latinSquare.js";

describe("buildBatteryPlan(sessionNumber)", () => {
  it("lists the 5 tasks in the session's Latin-square order with labels and progress", () => {
    const plan = buildBatteryPlan(1);
    expect(plan.map((p) => p.task)).toEqual(orderForSession(1));
    expect(plan.map((p) => p.label)).toEqual(["Task 1 of 5", "Task 2 of 5", "Task 3 of 5", "Task 4 of 5", "Task 5 of 5"]);
    plan.forEach((p, i) => {
      expect(p.position).toBe(i + 1);
      expect(p.progressBefore).toBeCloseTo(i / 5, 10);
      expect(p.progressAfter).toBeCloseTo((i + 1) / 5, 10);
    });
  });

  it("changes order from session to session and is deterministic", () => {
    expect(buildBatteryPlan(2).map((p) => p.task)).not.toEqual(buildBatteryPlan(1).map((p) => p.task));
    expect(buildBatteryPlan(9)).toEqual(buildBatteryPlan(9));
  });
});

describe("progressFraction", () => {
  it("is done / total, clamped by validation", () => {
    expect(progressFraction(0, 5)).toBe(0);
    expect(progressFraction(2, 5)).toBe(0.4);
    expect(progressFraction(5, 5)).toBe(1);
    expect(() => progressFraction(6, 5)).toThrow();
    expect(() => progressFraction(-1, 5)).toThrow();
    expect(() => progressFraction(1, 0)).toThrow();
  });
});

describe("viewing distance instruction", () => {
  it("is about 57 cm, so 1 cm on screen is about 1 degree of visual angle", () => {
    expect(VIEWING_DISTANCE_CM).toBe(57);
    const t = viewingInstruction();
    expect(t).toContain("57 cm");
    expect(t.toLowerCase()).toContain("same distance");
  });
});
