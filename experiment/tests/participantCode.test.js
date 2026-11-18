import { describe, it, expect } from "vitest";
import { generateParticipantCode, CODE_ALPHABET } from "../src/lib/participantCode.js";

const AMBIGUOUS = ["0", "O", "1", "I", "L"];

describe("generateParticipantCode", () => {
  it("alphabet has no ambiguous characters", () => {
    for (const ch of AMBIGUOUS) expect(CODE_ALPHABET).not.toContain(ch);
    expect(new Set(CODE_ALPHABET).size).toBe(CODE_ALPHABET.length);
  });

  it("returns 8 characters from the alphabet", () => {
    const code = generateParticipantCode();
    expect(code).toHaveLength(8);
    for (const ch of code) expect(CODE_ALPHABET).toContain(ch);
  });

  it("is deterministic for an injected byte source (maps bytes into the alphabet)", () => {
    const bytes = () => Uint8Array.from([0, 1, 2, 3, 4, 5, 6, 7]);
    const a = generateParticipantCode(bytes);
    const b = generateParticipantCode(bytes);
    expect(a).toBe(b);
    expect(a).toHaveLength(8);
  });

  it("gives 10,000 unique codes", () => {
    const codes = new Set();
    for (let i = 0; i < 10_000; i++) codes.add(generateParticipantCode());
    expect(codes.size).toBe(10_000);
  });
});
