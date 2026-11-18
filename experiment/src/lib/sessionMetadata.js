/** Session metadata recorded with every session (all fields required). */
export function buildSessionMetadata({ now, timezone, userAgent, screen, jsPsychVersion } = {}) {
  if (!(now instanceof Date) || Number.isNaN(now.getTime())) throw new Error("now must be a valid Date");
  if (!timezone) throw new Error("timezone is required");
  if (!userAgent) throw new Error("userAgent is required");
  if (!screen || !Number.isFinite(screen.width) || !Number.isFinite(screen.height)) {
    throw new Error("screen {width, height} is required");
  }
  if (!jsPsychVersion) throw new Error("jsPsychVersion is required");
  return {
    timestamp: now.toISOString(),
    timezone,
    userAgent,
    screenWidth: screen.width,
    screenHeight: screen.height,
    jsPsychVersion,
  };
}
