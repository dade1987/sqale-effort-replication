"""Re-runs the frozen preregistered analysis (confermativo.py, unchanged since registration) on the distributed data,
applies the Holm correction across the four one-sided tests (H1, H2 in Moodle and MariaDB), and writes English copies.
Outputs: results/confermativo_<p>.json and results/holm_4test.json (original Italian keys, as produced by the frozen script),
../results/confirmatory/confirmatory_<p>.json and holm_4_tests.json (same numbers, English keys and verdicts).
Usage (from this folder): python3 run_confirmatory.py"""
import json, os, subprocess, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; ROOT = HERE.parent; D = ROOT / "data"
OUT_IT, OUT_EN = HERE / "results", ROOT / "results" / "confirmatory"
OUT_IT.mkdir(exist_ok=True); OUT_EN.mkdir(parents=True, exist_ok=True)
for p in ["moodle", "mariadb"]:
    subprocess.run([sys.executable, str(HERE / "confermativo.py"), str(D / f"features/{p}_features.csv"), str(D / f"history/{p}_history.csv"), p,
                    str(D / f"confirmatory/holdout_scan_{p}.jsonl"), str(D / f"confirmatory/exploratory_sample_scan_{p}.jsonl")],
                   cwd=OUT_IT, check=True, stdout=subprocess.DEVNULL)
R = {p: json.load(open(OUT_IT / f"confermativo_{p}.json")) for p in ["moodle", "mariadb"]}
# Holm step-down over the four preregistered one-sided p values
ps = sorted(((f"{p} {h}", R[p][h]["p_unilaterale_rho_gt_0"]) for p in R for h in ["H1", "H2"]), key=lambda x: x[1])
holm, run = {}, 0.0
for i, (k, v) in enumerate(ps):
    run = max(run, min(1, (len(ps) - i) * v)); holm[k] = {"p": v, "p_holm": run}
json.dump(holm, open(OUT_IT / "holm_4test.json", "w"), indent=1)
json.dump(holm, open(OUT_EN / "holm_4_tests.json", "w"), indent=1)
M = json.load(open(ROOT / "docs" / "translation_map_confirmatory.json"))
def tr(o):
    if isinstance(o, dict): return {M["result_keys"].get(k, k): tr(v) for k, v in o.items()}
    if isinstance(o, list): return [tr(v) for v in o]
    return M["verdicts"].get(o, o) if isinstance(o, str) else o
for p in R: json.dump(tr(R[p]), open(OUT_EN / f"confirmatory_{p}.json", "w"), indent=1)
print(json.dumps(holm, indent=1))
