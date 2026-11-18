import { orderForSession, TASKS } from "./latinSquare.js";

export const VIEWING_DISTANCE_CM = 57;

/** Fraction of the battery completed. */
export function progressFraction(done, total) {
  if (!(total > 0) || done < 0 || done > total) throw new RangeError(`Invalid progress ${done}/${total}`);
  return done / total;
}

/** The tasks of a session in Latin-square order, with labels and progress-bar positions. */
export function buildBatteryPlan(sessionNumber) {
  const order = orderForSession(sessionNumber);
  return order.map((task, i) => ({
    task,
    position: i + 1,
    label: `Task ${i + 1} of ${TASKS.length}`,
    progressBefore: progressFraction(i, TASKS.length),
    progressAfter: progressFraction(i + 1, TASKS.length),
  }));
}

/** Setup instruction shown before the tasks. At 57 cm, 1 cm on the screen is about 1 degree of visual angle. */
export function viewingInstruction() {
  return `Sit about ${VIEWING_DISTANCE_CM} cm (roughly 22 inches, a little less than an arm's length) from the screen, with your eyes level with the middle of the screen. At this distance 1 cm on the screen is about 1 degree of visual angle. Sit at the same distance every session.`;
}
