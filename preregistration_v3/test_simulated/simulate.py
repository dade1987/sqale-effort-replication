# Simulated scan files for testing confermativo_v3.py (no real SQALE): mode null (debt depends on size only) or effect (debt also tracks hours).
import sys, json, numpy as np, pandas as pd
feat, mode, out = sys.argv[1:4]; rng = np.random.default_rng(1)
f = pd.read_csv(feat); n = len(f)
lh = np.log(f.hours.values); ncloc = np.exp(5 + 0.5 * (lh - lh.mean()) + rng.normal(0, 1, n)).round()
sq = np.exp(np.log1p(ncloc) * 0.9 + rng.normal(0, 1, n) + (1.0 * (lh - lh.mean()) if mode == "effect" else 0)).round()
sq[rng.random(n) < 0.15] = 0
with open(out, "w") as o:
    for k, a, b in zip(f.key, ncloc, sq):
        miss = rng.random() < 0.05
        o.write(json.dumps({"key": k, "code_files_at_parent": 0 if miss else 3, "code_files_touched": 3, "sqale_min": float(b), "smells": 1, "ncloc": 0 if miss else float(a), "files_measured": 0 if miss else 3}) + "\n")
