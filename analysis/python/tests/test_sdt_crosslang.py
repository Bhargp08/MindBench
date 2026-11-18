"""The 2-back d' stored nowhere in the browser data; analysis computes it here. These tests check that the browser's
JavaScript implementation (experiment/src/lib/sdt.js, used by the in-browser 2-back scorer) and this Python module
agree on a grid of count combinations, so the two cannot silently drift apart."""
import json
import shutil
import subprocess

import pytest

from mindbench.sdt import dprime_from_counts

from conftest import REPO

CASES = [(15, 18, 6, 40), (18, 18, 0, 40), (0, 18, 40, 40), (9, 18, 20, 40), (50, 50, 0, 50), (1, 2, 1, 2), (30, 60, 12, 60), (2, 2, 0, 2), (0, 5, 5, 5)]


@pytest.mark.skipif(shutil.which("node") is None, reason="node is not installed")
def test_javascript_and_python_dprime_agree():
    js = (REPO / "experiment" / "src" / "lib" / "sdt.js").as_uri()
    script = f"""
import {{ dPrimeFromCounts }} from {json.dumps(js)};
const cases = {json.dumps(CASES)};
console.log(JSON.stringify(cases.map(([hits, nSignal, falseAlarms, nNoise]) => {{
  const r = dPrimeFromCounts({{ hits, nSignal, falseAlarms, nNoise }});
  return [r.hitRate, r.falseAlarmRate, r.dPrime, r.criterion];
}})));
"""
    out = subprocess.run(["node", "--input-type=module", "-e", script], capture_output=True, text=True, check=True).stdout
    for (hits, n_signal, fa, n_noise), js_vals in zip(CASES, json.loads(out)):
        py = dprime_from_counts(hits, n_signal, fa, n_noise)
        py_vals = [py["hit_rate"], py["false_alarm_rate"], py["d_prime"], py["criterion"]]
        assert js_vals == pytest.approx(py_vals, abs=1e-7), (hits, n_signal, fa, n_noise)
