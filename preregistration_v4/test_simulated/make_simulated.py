# Simulated scan records for testing confermativo_v4.py BEFORE registration (no real SQALE is used or measured).
# Debt = size (st_loc_sum, from git) x lognormal noise with a component effect, plus an optional effect of the hours rank residual.
# Usage: python3 make_simulated.py <package_root> <effect> <out.jsonl>
import sys, json, numpy as np, pandas as pd
R, E, OUT = sys.argv[1], float(sys.argv[2]), sys.argv[3]
rng = np.random.default_rng(7)
keys = open(f"{R}/preregistration_v4/newsample_keys_moodle.txt").read().split()
f = pd.read_csv(f"{R}/data/features/moodle_features.csv", usecols=["key", "hours", "st_loc_sum", "components"]); f = f[f.key.isin(keys)].reset_index(drop=True)
comp = f.components.fillna("?").astype(str).str.split(";").str[0]; u = pd.Series(rng.normal(0, .3, comp.nunique()), index=comp.unique())[comp].values
size = f.st_loc_sum.fillna(0).values; lh = np.log(f.hours.clip(lower=1 / 60)).values; lh = (lh - lh.mean()) / lh.std()
with open(OUT, "w") as o:
    for i, k in enumerate(f.key):
        if i % 97 == 5: o.write(json.dumps({"key": k, "error": "simulated failure"}) + "\n"); continue
        n = float(size[i]); at = int(n > 0)
        sq = float(np.exp(np.log1p(n) * 0.9 + u[i] + rng.normal(0, .8) + E * 1.5 * lh[i])) if at else 0.0
        o.write(json.dumps({"key": k, "code_files_at_parent": at, "ncloc": n, "sqale_min": round(sq, 1), "c1_files_at_parent": at,
                            "righe_vecchie_modificate": int(rng.integers(1, 50)) if at else 0, "ncloc_c1_prima": n,
                            "sqale_righe_modificate": float(rng.poisson(2) * (1 + E * (lh[i] > 0))) if at else 0, "sonarqube_version": "simulated"}) + "\n")
