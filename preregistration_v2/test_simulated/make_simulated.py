# Simulated inputs for testing confermativo_v2.py (no real hours or SQALE are read). Usage: python3 make_simulated.py <outdir> <rho_effect>
import sys, json, numpy as np, pandas as pd
o, beta = sys.argv[1], float(sys.argv[2]); r = np.random.default_rng(1)
def make(prefix, n):
    dev = r.integers(0, 120, n); comp = r.integers(0, 25, n)
    nc = np.exp(r.normal(8.5, 1.2, n)); sq = nc * np.exp(r.normal(-2.5, 0.6, n)) * 0.3
    z = np.log1p(sq) - np.log1p(nc); z = (z - z.mean()) / z.std()
    h = np.exp(0.4 * np.log(nc) - 1.5 + beta * z + 0.3 * r.normal(0, 1, 120)[dev] + r.normal(0, 1, n))
    keys = [f"{prefix}-{i}" for i in range(n)]
    feat = pd.DataFrame({"key": keys, "hours": h.round(3), "fix_author": [f"a{d}" for d in dev], "components": [f"c{c}" for c in comp]})
    hist = pd.DataFrame({"key": keys, "assignee_T": [f"d{d}" if r.random() > .1 else None for d in dev], "hours_assignee": (h * r.uniform(.5, 1, n)).round(3)})
    recs = []
    for i, k in enumerate(keys):
        fa = int(r.integers(1, 6)); rec = {"key": k, "files_at_parent": fa, "files_measured": fa if r.random() > .1 else fa - 1,
               "sqale_min_official": float(round(sq[i])), "ncloc_official": float(round(nc[i])), "stmt_parsed_pct": 100.0, "analyser_version": "sim"}
        if r.random() < .03: rec = {"key": k, "error": "simulated failure"}
        recs.append(rec)
    return feat, hist, recs, keys
f1, h1, s1, k1 = make("NEW", 1475); f2, h2, s2, _ = make("TRAIN", 821)
pd.concat([f1, f2]).to_csv(f"{o}/feat.csv", index=False); pd.concat([h1, h2]).to_csv(f"{o}/hist.csv", index=False)
open(f"{o}/keys.txt", "w").write("\n".join(k1) + "\n")
open(f"{o}/new.jsonl", "w").write("".join(json.dumps(x) + "\n" for x in s1)); open(f"{o}/train.jsonl", "w").write("".join(json.dumps(x) + "\n" for x in s2))
