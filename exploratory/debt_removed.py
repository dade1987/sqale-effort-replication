# EXPLORATORY (not preregistered): does the SQALE debt removed by the first fix commit relate to logged hours beyond size?
# Uses the changed-lines scans of the old and hold-out samples (sqale_lines.py output).
# removed = sqale before - sqale after the first fix commit, on the code files the commit changed (net; negative = debt added).
import json, sys, numpy as np, pandas as pd
from scipy import stats
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
def rank_resid(a, y, covs):
    r = a[[y] + covs].rank().values; X = np.column_stack([np.ones(len(r))] + [r[:, i + 1] for i in range(len(covs))])
    return r[:, 0] - X @ np.linalg.lstsq(X, r[:, 0], rcond=None)[0]
def partial(a, x, covs): return float(np.corrcoef(rank_resid(a, "hours", covs), rank_resid(a, x, covs))[0, 1])
def boot(a, x, covs, B=2000, seed=2026):
    g = pd.factorize(a.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]; rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        pick = rng.integers(0, len(idx), len(idx)); bs.append(partial(a.iloc[np.concatenate([idx[i] for i in pick])], x, covs))
    return [float(v) for v in np.percentile(bs, [2.5, 97.5])]
out = {}
for p in ["moodle", "mariadb"]:
    st = pd.read_csv(f"{D}/history/{p}_history.csv")[["key", "assignee_T"]]
    df = pd.read_csv(f"{D}/features/{p}_features.csv").merge(st, on="key", how="left")
    df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str))
    sc = pd.concat([pd.read_json(f"{D}/confirmatory/exploratory_sample_scan_{p}.jsonl", lines=True), pd.read_json(f"{D}/confirmatory/holdout_scan_{p}.jsonl", lines=True)]).drop_duplicates("key")
    a = sc.merge(df[["key", "hours", "dev"]], on="key")
    a = a[(a.hours > 0) & (a.c1_files_at_parent > 0) & (a.ncloc_c1_prima > 0)].copy()
    a["removed"] = a.sqale_c1_prima - a.sqale_c1_dopo
    a["removed_pos"] = a.removed.clip(lower=0)
    r = {"n": int(len(a)), "share_debt_removed": float((a.removed > 0).mean()), "share_debt_added": float((a.removed < 0).mean()),
         "median_removed_min_when_positive": float(a.removed[a.removed > 0].median())}
    for x, covs in [("removed", ["ncloc_c1_prima"]), ("removed_pos", ["ncloc_c1_prima"]), ("removed", ["ncloc_c1_prima", "righe_vecchie_modificate"])]:
        lab = f"partial_rho(hours,{x}|{'+'.join(covs)})"
        r[lab] = {"rho": partial(a, x, covs), "CI95_dev_bootstrap": boot(a, x, covs)}
    r["spearman(hours,removed_pos) raw"] = float(stats.spearmanr(a.hours, a.removed_pos)[0])
    out[p] = r
json.dump(out, open(f"{OUT}/debt_removed.json", "w"), indent=1)
print(json.dumps(out, indent=1))
