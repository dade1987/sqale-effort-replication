# Probability of each H1 verdict when the true partial rho is 0 (and at 0.05 and 0.10), with the registered n, covariate, developer clusters,
# bootstrap (90% CI) and decision rules (exploratory, not preregistered). Usage: python3 v4_null_verdict_sim.py <project> <n_sim> [B]
# Each run keeps the real hours, sizes and developers of the H1 hold-out issues and builds a synthetic debt measure:
# x = fitted log1p(SQALE) from log1p(ncloc) + a residual that is (a) permuted at random (true rho = 0), or (b) mixed with the rank residual of hours
# to give a target partial rho. Writes results/exploratory/v4_null_verdict_sim_<project>.json
import sys, json, os, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
p, NSIM = sys.argv[1], int(sys.argv[2])
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")]); exec(src[src.index("def rank_resid"):src.index("out = {")])
if len(sys.argv) > 3: B = int(sys.argv[3])
st = pd.read_csv(f"{H}/data/history/{p}_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{H}/data/features/{p}_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df = df[df.hours > 0]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev"]], on="key")
a = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy().reset_index(drop=True)
l = np.log1p(a.ncloc.values); s = np.log1p(a.sqale_min.values); X = np.column_stack([np.ones(len(l)), l])
fit = X @ np.linalg.lstsq(X, s, rcond=None)[0]; res = s - fit; sd = res.std()
eh = rank_resid(a, "hours", ["ncloc"]); eh = (eh - eh.mean()) / eh.std()
sim_rng = np.random.default_rng(20261031); rng = np.random.default_rng(SEED)
out = {"project": p, "n": int(len(a)), "n_dev": int(a.dev.nunique()), "n_sim": NSIM, "B": B, "runs": {}}
for target in [0.0, 0.05, 0.10]:
    counts, rhos = {}, []
    for k in range(NSIM):
        z = sim_rng.permutation(res) / sd
        z = target * eh + np.sqrt(1 - target ** 2) * (z - z.mean()) / z.std() if target else z
        a["x"] = fit + sd * z
        r = test_rho(a, "x", ["ncloc"]); counts[r["esito"]] = counts.get(r["esito"], 0) + 1; rhos.append(r["rho_parziale"])
        if k == 9: print(f"target {target}: first 10 runs", counts, "mean rho", round(float(np.mean(rhos)), 3), flush=True)
    out["runs"][str(target)] = {"verdict_share": {v: c / NSIM for v, c in counts.items()}, "mean_rho": float(np.mean(rhos)), "sd_rho": float(np.std(rhos))}
json.dump(out, open(f"{H}/results/exploratory/v4_null_verdict_sim_{p}.json", "w"), indent=1)
print(json.dumps(out, indent=1))
