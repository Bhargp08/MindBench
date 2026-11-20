"""MB-23: build docs/writeup/paper.md from the template. Results come from a JSON file if given (analysis id -> source -> result)."""
import argparse
import json
import sys
from pathlib import Path

from mindbench import writeup

ap = argparse.ArgumentParser()
ap.add_argument("--results", help="JSON file of analysis results (omit while nothing has been analysed)")
ap.add_argument("--registration-url")
args = ap.parse_args()
results = json.loads(Path(args.results).read_text()) if args.results else {}
tpl = (writeup.ROOT / "docs" / "writeup" / "paper_template.md").read_text(encoding="utf-8")
text = writeup.build_paper(tpl, writeup.collect_values(results, args.registration_url))
bad = writeup.untraced_numbers(writeup.build_paper(tpl, writeup.collect_values(results, args.registration_url), mark=True))
if bad:
    sys.exit(f"untraced numbers in the paper: {bad}")
(writeup.ROOT / "docs" / "writeup" / "paper.md").write_text(text, encoding="utf-8")
print("wrote docs/writeup/paper.md; for a PDF (needs pandoc and a LaTeX engine, not installed here): cd docs/writeup && pandoc paper.md -o paper.pdf")
