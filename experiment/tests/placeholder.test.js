import { describe, it, expect } from "vitest";
import { PACKAGE_NAME } from "../src/index.js";

describe("experiment package", () => {
  it("imports", () => {
    expect(PACKAGE_NAME).toBe("mindbench-experiment");
  });
});
