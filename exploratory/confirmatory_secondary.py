# Secondary (non-confirmatory) analyses listed in Section 8 of the preregistered protocol.
# Reuses the definitions of the frozen confermativo.py; 90% CIs, developer-clustered bootstrap (B=2000 here to save time).
import json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
B = 2000
def rank_resid(a, y, covs):
    r = a[[y] + covs].rank().values; X = np.column_stack([np.ones(len(r))] + [r[:, i + 1] for i in range(len(covs))])
    return r[:, 0] - X @ np.linalg.lstsq(X, r[:, 0], rcond=None)[0]
def partial(a, x, covs, y="hours"): return float(np.corrcoef(rank_resid(a, y, covs), rank_resid(a, x, covs))[0, 1])
def groups(a, by):
    g = pd.factorize(a[by])[0]; return [np.where(g == i)[0] for i in range(g.max() + 1)]
def ci(a, f, by="dev", seed=2026):
    idx = groups(a, by); rng = np.random.default_rng(seed); bs = []
    for _ in range(B):
        pick = rng.integers(0, len(idx), len(idx)); bs.append(f(a.iloc[np.concatenate([idx[i] for i in pick])]))
    return [float(v) for v in np.percentile(bs, [5, 95])]
def h3(tr, te, y="hours"):
    X = lambda d, cols: np.column_stack([np.ones(len(d))] + [np.log1p(d[c].values) for c in cols])
    P = {k: np.exp(X(te, c) @ np.linalg.lstsq(X(tr, c), np.log(tr[y].values), rcond=None)[0]) for k, c in [("l", ["ncloc"]), ("s", ["ncloc", "sqale_min"])]}
    return P
out = {}
for p in ["moodle", "mariadb"]:
    st = pd.read_csv(f"{D}/history/{p}_history.csv")[["key", "assignee_T", "hours_assignee"]]
    df = pd.read_csv(f"{D}/features/{p}_features.csv").merge(st, on="key", how="left")
    df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
    df["month"] = df.fix_date.str[:7]; df = df[df.hours > 0]
    ho = pd.read_json(f"{D}/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev", "fix_date", "type", "hours_assignee", "month"]], on="key")
    old = pd.read_json(f"{D}/confirmatory/exploratory_sample_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev", "fix_date", "type", "hours_assignee", "month"]], on="key")
    a1 = lambda d: d[(d.code_files_at_parent > 0) & (d.ncloc > 0)].copy()
    a2 = lambda d: d[(d.c1_files_at_parent > 0) & (d.righe_vecchie_modificate > 0) & (d.ncloc_c1_prima > 0)].copy()
    tr = old[(old.fix_date < "2023-01-01") & (old.code_files_at_parent > 0) & (old.ncloc > 0)]
    R = {}
    # removed debt vs hours | LINES_changed
    d = a2(ho); d["removed"] = d.sqale_c1_prima - d.sqale_c1_dopo
    R["removed_debt|lines_changed"] = {"n": len(d), "rho": partial(d, "removed", ["righe_vecchie_modificate"]), "CI90": ci(d, lambda x: partial(x, "removed", ["righe_vecchie_modificate"]))}
    # SQALE density vs hours
    d = a1(ho); d["density"] = d.sqale_min / d.ncloc
    R["density"] = {"n": len(d), "rho": float(d[["hours", "density"]].corr("spearman").iloc[0, 1]), "CI90": ci(d, lambda x: float(x[["hours", "density"]].corr("spearman").iloc[0, 1]))}
    # assignee-only hours
    for lab, sub in [("assignee_hours", lambda d: d[d.hours_assignee > 0].assign(hours=lambda z: z.hours_assignee)), ("bugs_only", lambda d: d[d.type == "Bug"])]:
        d1, d2 = sub(a1(ho)), sub(a2(ho))
        r = {"H1": {"n": len(d1), "rho": partial(d1, "sqale_min", ["ncloc"]), "CI90": ci(d1, lambda x: partial(x, "sqale_min", ["ncloc"]))},
             "H2": {"n": len(d2), "rho": partial(d2, "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"]), "CI90": ci(d2, lambda x: partial(x, "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"]))}}
        trs = sub(tr); P = h3(trs, d1); dd = np.abs(d1.hours.values - P["s"]) - np.abs(d1.hours.values - P["l"]); mae = float(np.mean(np.abs(d1.hours.values - P["l"])))
        r["H3"] = {"n": len(d1), "dMAE": float(dd.mean()), "pct_of_MAE": float(100 * dd.mean() / mae)}
        R[lab] = r
    # month-block bootstrap
    d1, d2 = a1(ho), a2(ho)
    R["month_block_CI90"] = {"H1": ci(d1, lambda x: partial(x, "sqale_min", ["ncloc"]), by="month"),
                             "H2": ci(d2, lambda x: partial(x, "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"]), by="month")}
    # earlier sample
    d1, d2 = a1(old), a2(old)
    R["earlier_sample"] = {"H1": {"n": len(d1), "rho": partial(d1, "sqale_min", ["ncloc"]), "CI90": ci(d1, lambda x: partial(x, "sqale_min", ["ncloc"]))},
                           "H2": {"n": len(d2), "rho": partial(d2, "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"]), "CI90": ci(d2, lambda x: partial(x, "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"]))}}
    out[p] = R
json.dump(out, open(f"{ROOT}/results/confirmatory/secondary_results.json", "w"), indent=1, default=int)
print(json.dumps(out, indent=1, default=int))
