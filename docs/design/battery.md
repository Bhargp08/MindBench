# Battery integration (MB-12)

Assembly code: `experiment/src/tasks/battery.js` (shell), `experiment/src/lib/{latinSquare,keymap,practice,battery,timingLog}.js` (tested logic).

## Task order: balanced Latin square (construction confirmed)
10 orders for the 5 tasks: the Williams-type zigzag base row (t0, t1, t4, t2, t3), cyclically shifted 5 times, plus the mirror (reverse) of each. Checked numerically and by tests: every task is in every position exactly twice, and **all 20 ordered adjacent pairs occur exactly twice**.

A plain cyclic Latin square plus its mirror is **not** balanced: it covers only 10 of the 20 ordered adjacent pairs. The zigzag base row is what makes the mirrored 10-order set balanced for an odd number of tasks.

## Session -> order (AM/PM balanced)
A naive `session mod 10` would put each order only in AM sessions or only in PM sessions (sessions alternate AM/PM, and 10 is even), confounding task order with time of day, which H2 compares. Instead: day = ceil(session/2); AM order = (day-1) mod 10; PM order = (day-1+5) mod 10. Over any 10 days each order occurs once in the AM and once in the PM, the two sessions of a day differ, and across the 52 study sessions AM and PM counts per order differ by at most 1.
Caveat: this follows the **session schedule** (odd sessions = AM, even = PM), not the clock. If sessions are skipped or the AM/PM pattern changes, the balance degrades; the actual start time and the order are both logged.

## Practice, feedback, progress
Each task starts with a short practice block with feedback ("Correct" / "Incorrect" / "Too slow"; for the 2-back "Missed" and "not a match"): contrast 6 trials at a fixed -6 dB; Posner 8 (6 valid, 2 invalid); Stroop 8; 2-back 12 (3 targets, 2 lures); recall 1 list of 4 words that are not in the study pool. Practice data are tagged `practice: true`; **MB-15 must exclude `practice: true` rows** (practice does not feed the staircase threshold, scores, or the recall proportion). A progress bar advances by one fifth after each task.

## Consistent key map
All two-choice responses use F (first / left / yes) and J (second / right / no): staircase interval 1 = F, 2 = J; yes/no yes = F, no = J; Posner left = F, right = J. Stroop uses D F J K (red, green, blue, yellow); 2-back uses SPACE. **Design change:** the contrast task previously used 1/2 and Y/N. Each task's intro screen shows its keys.

## Viewing distance
Setup screen: sit about 57 cm (roughly 22 inches) from the screen, same distance every session (at 57 cm, 1 cm on screen is about 1 degree of visual angle). The distance is an **instruction only** and is logged as `viewingDistanceInstructedCm: 57`. Stimulus sizes are in CSS pixels and physical size on screen is **not calibrated** (no card or ruler calibration), so sizes in degrees are approximate and differ between devices; use the same device.

## Timing log
Logged in the `setup` and final `timing` rows: refresh-rate estimate from `requestAnimationFrame` (Hz, median frame time, SD, dropped frames, nominal rate, `plausible` flag, page visibility during measurement), per-task durations and total task time, task order, window size, devicePixelRatio, fullscreen state. A throttled or background tab gives an implausible rate (the flag is false); treat that value as unusable. Session length target 25-35 min is still an estimate: measure it in MB-13.

## Not done here
- GitHub Pages deploy: **not enabled** (needs Bharg's approval; `pages.yml` stays disabled).
- Full-length session timing and real-display checks: not done; the timing log of the 1-2 smoke-test sessions on the deployed site will give the first real-hardware numbers (MB-13 was skipped, see `deviations.md`).
- Dev-only `?quick` mode shortens every block for testing; it is ignored in production builds.
