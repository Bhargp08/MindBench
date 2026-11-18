export const SLEEP_HOURS_MAX = 16;
const TIME = /^([01]\d|2[0-3]):[0-5]\d$/;

/** Validate the session questionnaire. Returns { valid, errors: [{field, message}] }. */
export function validateQuestionnaire(q = {}) {
  const errors = [];
  const bad = (field, message) => errors.push({ field, message });

  const h = q.hoursSlept;
  if (typeof h !== "number" || !Number.isFinite(h)) bad("hoursSlept", "Hours slept must be a number");
  else if (h < 0 || h > SLEEP_HOURS_MAX) bad("hoursSlept", `Hours slept must be between 0 and ${SLEEP_HOURS_MAX}`);

  if (typeof q.bedTime !== "string" || !TIME.test(q.bedTime)) bad("bedTime", "Bed time must be HH:MM");
  if (typeof q.wakeTime !== "string" || !TIME.test(q.wakeTime)) bad("wakeTime", "Wake time must be HH:MM");
  if (!Number.isInteger(q.kss) || q.kss < 1 || q.kss > 9) bad("kss", "Sleepiness (KSS) must be an integer from 1 to 9");
  if (typeof q.caffeine !== "boolean") bad("caffeine", "Caffeine must be yes or no");
  if (typeof q.device !== "string" || q.device.trim() === "") bad("device", "Device is required");

  return { valid: errors.length === 0, errors };
}
