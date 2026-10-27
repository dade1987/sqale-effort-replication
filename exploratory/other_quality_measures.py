"""Exploratory check (not preregistered): do code-quality and change-history measures that do not come from SonarQube
relate to logged hours beyond size? If none does, the 'interest' visible in issue hours is probably small in these projects;
if some do, interest exists but SQALE does not capture it.
Partial Spearman rho (hours, X | log lines of touched code, number of touched code files) on the test issues with code files,
95% developer-clustered bootstrap CI. Output: results/exploratory/other_quality_measures.json"""
import json, numpy as np, pandas as pd
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"; OUT = f"{ROOT}/results/exploratory"
B, rng = 2000, np.random.default_rng(2026)
T0 = {"moodle": "2023-01-01", "mariadb": "2023-01-01", "percona": "2021-01-01"}
X = {"complexity density (CCN per line)": "st_ccn_density", "max function complexity": "st_fccn_max", "max file complexity": "st_ccn_max",
     "commits in the last year": "h_commits_1y", "churn in the last year": "h_churn_1y", "distinct past authors": "h_authors",
     "prior commits (max)": "h_commits_max", "co-change partners": "cc_partners_sum", "strongly coupled files outside the change": "cc_strong_outside",
     "file age (max, days)": "h_age_max_d", "days since last change (min)": "h_last_min_d"}
COV = ["st_loc_sum", "n_code"]
def rres(a, col):
    r = a[[col] + COV].rank().values; M = np.column_stack([np.ones(len(r)), r[:, 1:]])
    return r[:, 0] - M @ np.linalg.lstsq(M, r[:, 0], rcond=None)[0]
def partial(a, x): return float(np.corrcoef(rres(a, "hours"), rres(a, x))[0, 1])
out = {}
for p in ["moodle", "mariadb", "percona"]:
    df = pd.read_csv(f"{D}/features/{p}_features.csv")
    a = df[(df.hours > 0) & (df.fix_date >= T0[p]) & (df.n_code > 0) & (df.st_loc_sum > 0)].reset_index(drop=True)
    a["dev"] = a.assignee.fillna("?")
    g = [ix for ix in a.groupby("dev").indices.values()]
    sq = pd.read_json(f"{D}/sqale/{p}_sqale.jsonl", lines=True).drop_duplicates("key")[["key", "sqale_min", "ncloc"]]
    res = {"n_test_issues": int(len(a))}
    boots = [np.concatenate([g[i] for i in rng.integers(0, len(g), len(g))]) for _ in range(B)]
    for lab, col in X.items():
        b = a.dropna(subset=[col]).reset_index(drop=True) if a[col].isna().any() else a
        est = partial(b, col)
        bs = [partial(a.iloc[i].dropna(subset=[col]), col) for i in boots[:500]] if b is not a else [partial(a.iloc[i], col) for i in boots]
        res[lab] = {"partial_rho": round(est, 3), "ci95": [round(float(v), 3) for v in np.percentile(bs, [2.5, 97.5])], "n": int(len(b))}
    s = a.merge(sq, on="key")
    s = s[s.ncloc > 0].reset_index(drop=True); s["sqale_density"] = s.sqale_min / s.ncloc
    gs = [ix for ix in s.groupby("dev").indices.values()]
    bss = [np.concatenate([gs[i] for i in rng.integers(0, len(gs), len(gs))]) for _ in range(B)]
    for lab, col in [("SQALE (reference)", "sqale_min"), ("SQALE density (reference)", "sqale_density")]:
        res[lab] = {"partial_rho": round(partial(s, col), 3), "ci95": [round(float(v), 3) for v in np.percentile([partial(s.iloc[i], col) for i in bss], [2.5, 97.5])], "n": int(len(s))}
    out[p] = res
    print(p, json.dumps(res, indent=0))
json.dump(out, open(f"{OUT}/other_quality_measures.json", "w"), indent=1)
