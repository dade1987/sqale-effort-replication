"""Official SonarQube Cloud C/C++ analyser (CFamily) on all analysable MariaDB hold-out issues: the 200 of Table 13 plus the
other 662. Re-analysing the same SonarQube Cloud project carried file measures over from earlier analyses (0 debt with a stale ncloc), and
turning the analysis cache off did not remove it. All 862 issues were therefore re-analysed, one fresh SonarQube Cloud project per issue
(data/official_cxx/fresh_w*.jsonl, fresh_redo.jsonl); only these records are used. The earlier records (cloud_w*, full_w*, nocache_w*) serve only
for the before/after comparison. Exploratory, analysis plan written before the new measurements (see README).
Primary: partial rho (hours, official SQALE | ncloc), frozen H1 code (developer-clustered bootstrap, B=5000, seed 2026, 90% CI).
Writes results/exploratory/official_cxx_full.json."""
import json, glob, os
import numpy as np, pandas as pd
from scipy.stats import spearmanr
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")]); exec(src[src.index("def rank_resid"):src.index("out = {")])
rng = np.random.default_rng(SEED)
R = [json.loads(l) for f in sorted(glob.glob(f"{H}/data/official_cxx/fresh_w*.jsonl")) + [f"{H}/data/official_cxx/fresh_redo.jsonl"] for l in open(f)]
cloud = pd.DataFrame([{k: v for k, v in r.items() if k != "per_file"} for r in R]).drop_duplicates("key", keep="last")
st = pd.read_csv(f"{H}/data/history/mariadb_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{H}/data/features/mariadb_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df = df[df.hours > 0]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_mariadb.jsonl", lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev"]], on="key")
pop = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy()                       # the 862 H1 issues
d = pop.merge(cloud, on="key", how="left")
err = d.get("error")
meas = d[(d.files_measured.fillna(0) > 0) & (err.isna() if err is not None else True)].copy()
lost = d[~d.key.isin(meas.key)]
allf = meas[meas.files_measured == meas.files_at_parent].copy()
s200 = set(open(f"{H}/data/official_cxx/sample200_keys.txt").read().split())
out = {"population_H1": int(len(pop)), "scanned": int(d.files_at_parent.notna().sum()), "with_measures": int(len(meas)),
       "lost": {"n": int(len(lost)), "median_hours_lost": float(lost.hours.median()) if len(lost) else None, "median_hours_measured": float(meas.hours.median()),
                "median_ncloc_lost": float(lost.ncloc.median()) if len(lost) else None, "median_ncloc_measured": float(meas.ncloc.median())},
       "median_stmt_parsed_pct": float(meas.stmt_parsed_pct.median())}
old = pd.DataFrame([{k: v for k, v in r.items() if k != "per_file"} for f in sorted(glob.glob(f"{H}/data/official_cxx/cloud_w*.jsonl")) + sorted(glob.glob(f"{H}/data/official_cxx/full_w*.jsonl")) + sorted(glob.glob(f"{H}/data/official_cxx/nocache_w*.jsonl")) for r in map(json.loads, open(f))]).drop_duplicates("key", keep="last")
cmp = old[["key", "sqale_min_official"]].merge(cloud[["key", "sqale_min_official"]], on="key", suffixes=("_before", "_fresh")).dropna()
cmp = cmp[cmp.key.isin(meas.key)]
out["carryover_fix"] = {"compared": int(len(cmp)), "identical": int((cmp.sqale_min_official_before == cmp.sqale_min_official_fresh).sum()),
                        "higher_fresh": int((cmp.sqale_min_official_fresh > cmp.sqale_min_official_before).sum()), "lower_fresh": int((cmp.sqale_min_official_fresh < cmp.sqale_min_official_before).sum()),
                        "zero_debt_share_before": float((cmp.sqale_min_official_before == 0).mean()), "zero_debt_share_fresh": float((cmp.sqale_min_official_fresh == 0).mean()),
                        "zero_debt_share_first200": float((meas[meas.key.isin(s200)].sqale_min_official == 0).mean()), "zero_debt_share_new662": float((meas[~meas.key.isin(s200)].sqale_min_official == 0).mean()),
                        "median_ratio_fresh_before": float((cmp.sqale_min_official_fresh / cmp.sqale_min_official_before).replace([np.inf], np.nan).dropna().median())}
out["primary"] = test_rho(meas, "sqale_min_official", ["ncloc"])
out["secondary_all_files_measured"] = test_rho(allf, "sqale_min_official", ["ncloc"])
out["sonarcxx_same_issues"] = test_rho(meas, "sqale_min", ["ncloc"])
out["first_200_same_code"] = test_rho(meas[meas.key.isin(s200)], "sqale_min_official", ["ncloc"])
out["new_662_same_code"] = test_rho(meas[~meas.key.isin(s200)], "sqale_min_official", ["ncloc"])
out["spearman_official_vs_ncloc"] = float(spearmanr(meas.sqale_min_official, meas.ncloc)[0])
out["spearman_official_vs_sonarcxx"] = float(spearmanr(meas.sqale_min_official, meas.sqale_min)[0])
out["spearman_sonarcxx_vs_ncloc"] = float(spearmanr(meas.sqale_min, meas.ncloc)[0])
# H3-style: log-linear lines only vs lines + official SQALE, 10-fold CV on the measured issues, 90% clustered CI, 2% margin
from sklearn.model_selection import KFold
y = np.log(meas.hours.values); X1 = np.log1p(meas.ncloc.values); X2 = np.log1p(meas.sqale_min_official.values)
P1, P2 = np.zeros(len(y)), np.zeros(len(y))
for a, b in KFold(10, shuffle=True, random_state=SEED).split(y):
    for P, cols in [(P1, [X1]), (P2, [X1, X2])]:
        A = np.column_stack([np.ones(len(a))] + [c[a] for c in cols]); Bm = np.column_stack([np.ones(len(b))] + [c[b] for c in cols])
        P[b] = np.exp(Bm @ np.linalg.lstsq(A, y[a], rcond=None)[0])
h = meas.hours.values; dd = np.abs(h - P2) - np.abs(h - P1); mae = float(np.mean(np.abs(h - P1)))
bs = np.array([dd[i].mean() for i in boot_groups(meas.reset_index(drop=True))]); lo, hi = np.percentile(bs, [5, 95])
out["h3_style"] = {"n": int(len(h)), "MAE_lines_only": mae, "dMAE": float(dd.mean()), "IC90": [float(lo), float(hi)], "IC90_pct_MAE": [float(100 * lo / mae), float(100 * hi / mae)],
                   "verdict": "equivalent (CI inside +-2% of MAE)" if lo > -0.02 * mae and hi < 0.02 * mae else ("helps (CI below -2%)" if hi < -0.02 * mae else "inconclusive")}
json.dump(out, open(f"{H}/results/exploratory/official_cxx_full.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
