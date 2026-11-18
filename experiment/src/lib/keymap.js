/**
 * One consistent key map. Every two-choice task uses F for the first/left/yes option and J for the
 * second/right/no option; Stroop adds D and K on the home row; 2-back uses SPACE.
 */
export const KEYMAP = {
  twoChoice: { first: "f", second: "j" },
  contrast: { intervalOne: "f", intervalTwo: "j", yes: "f", no: "j" },
  posner: { left: "f", right: "j" },
  stroop: { red: "d", green: "f", blue: "j", yellow: "k" },
  nback: { match: " " },
};

const name = (k) => (k === " " ? "SPACE" : k.toUpperCase());

/** Text for the on-screen key reference of a task. */
export function describeKeys(task) {
  const k = KEYMAP[task];
  if (!k || task === "twoChoice") throw new Error(`Unknown task "${task}"`);
  switch (task) {
    case "contrast":
      return `${name(k.intervalOne)} = first flash or yes, ${name(k.intervalTwo)} = second flash or no`;
    case "posner":
      return `${name(k.left)} = left box, ${name(k.right)} = right box`;
    case "stroop":
      return Object.entries(k)
        .map(([color, key]) => `${name(key)} = ${color}`)
        .join(", ");
    case "nback":
      return `${name(k.match)} = same letter as two before`;
    default:
      throw new Error(`No key description for "${task}"`);
  }
}
