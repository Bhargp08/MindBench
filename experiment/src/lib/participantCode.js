// 31 characters: A-Z without I, L, O, plus digits 2-9 (no 0, 1, O, I, L).
export const CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789";
export const CODE_LENGTH = 8;

function defaultBytes(n) {
  const c = globalThis.crypto;
  if (!c || typeof c.getRandomValues !== "function") {
    throw new Error("Secure random source (crypto.getRandomValues) is not available");
  }
  return c.getRandomValues(new Uint8Array(n));
}

/**
 * Random participant code. Uses rejection sampling so every character is
 * equally likely. `getBytes(n)` must return n random bytes (injectable for tests).
 */
export function generateParticipantCode(getBytes = defaultBytes) {
  const limit = 256 - (256 % CODE_ALPHABET.length);
  let code = "";
  while (code.length < CODE_LENGTH) {
    for (const b of getBytes(CODE_LENGTH * 2)) {
      if (b < limit) code += CODE_ALPHABET[b % CODE_ALPHABET.length];
      if (code.length === CODE_LENGTH) break;
    }
  }
  return code;
}

export function isValidParticipantCode(code) {
  return (
    typeof code === "string" &&
    code.length === CODE_LENGTH &&
    [...code].every((ch) => CODE_ALPHABET.includes(ch))
  );
}
