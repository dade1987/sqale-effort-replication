# Confirmatory analysis of preregistration 2 (MariaDB, SonarSource C/C++ analyser on SonarQube Cloud, one new project per issue).
# Usage: python3 confermativo_v2.py <features.csv> <history.csv> <newsample_keys.txt> <new_scan.jsonl> <train_scan.jsonl> <out.json>
#   new_scan.jsonl: one record per new-sample issue (cloud_cxx_fresh.py output); train_scan.jsonl: the CFamily records of the first hold-out
#   (data/official_cxx/fresh_w*.jsonl + fresh_redo.jsonl, concatenated; 821 measured issues).
# H1-C: partial Spearman rho (hours, SQALE_files | NCLOC_files); H3-C: dMAE lines+SQALE vs lines only, models fitted on the training issues.
# 90% CIs: bootstrap over developers, B = 5000, seed 2026. Statistic, bootstrap and decision rules copied from the first registration (confermativo.py).
import sys, json, numpy as np, pandas as pd
featf, stf, keysf, newf, trainf, outf = sys.argv[1:7]
B, SEED, SESOI_RHO, MARGIN = 5000, 2026, 0.10, 0.02
rng = np.random.default_rng(SEED)

def rank_resid(a, y, covs):
    r = a[[y] + covs].rank().values; X = np.column_stack([np.ones(len(r))] + [r[:, i + 1] for i in range(len(covs))])
    return r[:, 0] - X @ np.linalg.lstsq(X, r[:, 0], rcond=None)[0]
def partial(a, x, covs, y="hours"):
    e1, e2 = rank_resid(a, y, covs), rank_resid(a, x, covs)
    return float(np.corrcoef(e1, e2)[0, 1])
def boot_groups(a, col="dev"):
    g = pd.factorize(a[col])[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]
    for _ in range(B):
        pick = rng.integers(0, len(idx), len(idx)); yield np.concatenate([idx[i] for i in pick])
def boot_twoway(a):
    # two-way cluster bootstrap (developer x component): resample developers and components independently, keep issues whose both are drawn,
    # with multiplicity = product of the two draw counts
    gd, gc = pd.factorize(a.dev)[0], pd.factorize(a.comp)[0]
    for _ in range(B):
        wd = np.bincount(rng.integers(0, gd.max() + 1, gd.max() + 1), minlength=gd.max() + 1)
        wc = np.bincount(rng.integers(0, gc.max() + 1, gc.max() + 1), minlength=gc.max() + 1)
        yield np.repeat(np.arange(len(a)), wd[gd] * wc[gc])
def verdict_rho(est, lo, hi):
    if lo > SESOI_RHO: return "supported, practically relevant (CI above 0.10)"
    if lo > -SESOI_RHO and hi < SESOI_RHO: return "practically negligible (CI inside +-0.10)"
    if lo > 0: return "positive but of uncertain size (CI above 0, not all above 0.10)"
    return "inconclusive"
def test_rho(a, x, covs, y="hours", boot=boot_groups):
    est = partial(a, x, covs, y); bs = np.array([partial(a.iloc[i], x, covs, y) for i in boot(a)])
    lo, hi = np.nanpercentile(bs, [5, 95]); p_pos = float(min(1, np.mean(bs <= 0) + 1 / B))
    return {"n": int(len(a)), "partial_rho": est, "CI90": [float(lo), float(hi)], "p_one_sided_rho_gt_0": p_pos, "verdict": verdict_rho(est, lo, hi)}
def test_h3(tr, te):
    X = lambda d, cols: np.column_stack([np.ones(len(d))] + [np.log1p(d[c].values) for c in cols])
    P = {lab: np.exp(X(te, cols) @ np.linalg.lstsq(X(tr, cols), np.log(tr.hours.values), rcond=None)[0]) for lab, cols in [("lines", ["ncloc"]), ("lines+SQALE", ["ncloc", "sqale"])]}
    y = te.hours.values; d = np.abs(y - P["lines+SQALE"]) - np.abs(y - P["lines"]); mae = float(np.mean(np.abs(y - P["lines"])))
    bs = np.array([d[i].mean() for i in boot_groups(te)]); lo, hi = np.percentile(bs, [5, 95])
    v = ("SQALE helps (CI below -2% of MAE)" if hi < -MARGIN * mae else
         "equivalent (CI inside +-2% of MAE)" if lo > -MARGIN * mae and hi < MARGIN * mae else "inconclusive")
    return {"n_train": int(len(tr)), "n_test": int(len(te)), "MAE_lines_only": mae, "dMAE": float(d.mean()), "CI90": [float(lo), float(hi)],
            "CI90_pct_MAE": [float(100 * lo / mae), float(100 * hi / mae)], "verdict": v}

st = pd.read_csv(stf)[["key", "assignee_T", "hours_assignee"]]
df = pd.read_csv(featf, usecols=["key", "hours", "fix_author", "components"]).merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df["comp"] = df.components.fillna("?").astype(str).str.split(";").str[0].replace({"": "?"})
df = df[df.hours > 0]
def load(f):
    R = [json.loads(l) for l in open(f)]
    s = pd.DataFrame([{k: v for k, v in r.items() if k != "per_file"} for r in R]).drop_duplicates("key", keep="last")
    s = s.rename(columns={"sqale_min_official": "sqale", "ncloc_official": "ncloc"})
    if "error" not in s: s["error"] = None
    return s
keys = open(keysf).read().split()
new, train = load(newf), load(trainf)
measured = lambda s: s[s.error.isna() & (s.files_measured.fillna(0) > 0) & (s.ncloc.fillna(0) > 0)]
pop = df[df.key.isin(keys)].merge(new, on="key", how="left")
elig = pop[(pop.files_at_parent.fillna(0) > 0) | pop.error.notna()]               # C/C++ code file at par, or scan failed (counted as missing)
a = elig[elig.key.isin(measured(new).key)].reset_index(drop=True)                  # analysed: NCLOC_files > 0 from the same analysis
miss = elig[~elig.key.isin(a.key)]
tr = df.merge(measured(train), on="key").reset_index(drop=True)
out = {"parameters": {"B": B, "seed": SEED, "SESOI_rho": SESOI_RHO, "margin_dMAE": MARGIN},
       "counts": {"keys": len(keys), "hours_gt_0": int(len(pop)), "scanned": int(pop.files_at_parent.notna().sum()), "eligible_cxx_at_parent_or_failed": int(len(elig)),
                  "analysed": int(len(a)), "missing": int(len(miss)), "median_hours_analysed": float(a.hours.median()) if len(a) else None,
                  "median_hours_missing": float(miss.hours.median()) if len(miss) else None, "train_issues": int(len(tr))},
       "analyser_versions": sorted({str(v) for v in new.get("analyser_version", pd.Series(dtype=str)).dropna()})}
out["H1-C"] = test_rho(a, "sqale", ["ncloc"])
out["H3-C"] = test_h3(tr, a)
# secondary analyses (not confirmatory)
both = pd.concat([a, tr[~tr.key.isin(a.key)]], ignore_index=True)
out["secondary"] = {
    "H1-C_pooled_with_first_holdout": test_rho(both, "sqale", ["ncloc"]),
    "H3-C_pooled_with_first_holdout_cv10": None,
    "H1-C_twoway_dev_component": test_rho(a, "sqale", ["ncloc"], boot=boot_twoway),
    "H1-C_all_files_measured": test_rho(a[a.files_measured == a.files_at_parent].reset_index(drop=True), "sqale", ["ncloc"]),
    "H1-C_assignee_hours": test_rho(a[a.hours_assignee.fillna(0) > 0].reset_index(drop=True), "sqale", ["ncloc"], y="hours_assignee")}
# pooled H3-C: 10-fold cross-validation on the pooled issues (no separate training set exists)
from sklearn.model_selection import KFold
y = np.log(both.hours.values); P1, P2 = np.zeros(len(y)), np.zeros(len(y))
for i, j in KFold(10, shuffle=True, random_state=SEED).split(y):
    for P, cols in [(P1, ["ncloc"]), (P2, ["ncloc", "sqale"])]:
        A = np.column_stack([np.ones(len(i))] + [np.log1p(both[c].values[i]) for c in cols]); Bm = np.column_stack([np.ones(len(j))] + [np.log1p(both[c].values[j]) for c in cols])
        P[j] = np.exp(Bm @ np.linalg.lstsq(A, y[i], rcond=None)[0])
h = both.hours.values; d = np.abs(h - P2) - np.abs(h - P1); mae = float(np.mean(np.abs(h - P1)))
bs = np.array([d[i].mean() for i in boot_groups(both)]); lo, hi = np.percentile(bs, [5, 95])
out["secondary"]["H3-C_pooled_with_first_holdout_cv10"] = {"n": int(len(h)), "MAE_lines_only": mae, "dMAE": float(d.mean()), "CI90": [float(lo), float(hi)],
    "verdict": "SQALE helps (CI below -2% of MAE)" if hi < -MARGIN * mae else "equivalent (CI inside +-2% of MAE)" if lo > -MARGIN * mae and hi < MARGIN * mae else "inconclusive"}
json.dump(out, open(outf, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
