# Confirmatory analysis of preregistration 4: Moodle issues never measured before, two-way clustering as the primary interval.
# Usage: python3 confermativo_v4.py <package_root> <moodle_scan.jsonl> <out.json>
#   <package_root>: the replication package (data/features, data/history, data/links, preregistration_v4/newsample_keys_moodle.txt).
#   moodle_scan.jsonl: records of the frozen preregistration/sqale_lines.py (key, code_files_at_parent, sqale_min, ncloc, and the H2 fields; or key, error).
# Primary: H1-2W, partial Spearman rho(hours, SQALE_files | NCLOC_files), 90% CI from a two-way (developer x first Jira component) pigeonhole
# bootstrap, B = 5000, seed 2026 (reseeded for every test). Statistic, SESOI and decision rules as in the first registration (preregistration/confermativo.py).
import sys, json, gzip, collections, numpy as np, pandas as pd
R, MSF, OUTF = sys.argv[1:4]
B, SEED, SESOI, MARGIN, MAXFILES = 5000, 2026, 0.10, 0.02, 2000

# ---------- statistic (copied from the first registration) ----------
def rank_resid(a, y, covs):
    r = a[[y] + covs].rank().values; X = np.column_stack([np.ones(len(r))] + [r[:, i + 1] for i in range(len(covs))])
    return r[:, 0] - X @ np.linalg.lstsq(X, r[:, 0], rcond=None)[0]
def partial(a, x, covs=("ncloc",), y="hours"):
    covs = list(covs)
    e1, e2 = rank_resid(a, y, covs), rank_resid(a, x, covs)
    return float(np.corrcoef(e1, e2)[0, 1])

# ---------- intervals ----------
def boot_twoway(a, rng):
    gd, gc = pd.factorize(a.dev)[0], pd.factorize(a.comp)[0]
    for _ in range(B):
        wd = np.bincount(rng.integers(0, gd.max() + 1, gd.max() + 1), minlength=gd.max() + 1)
        wc = np.bincount(rng.integers(0, gc.max() + 1, gc.max() + 1), minlength=gc.max() + 1)
        yield np.repeat(np.arange(len(a)), wd[gd] * wc[gc])
def boot_dev(a, rng):
    g = pd.factorize(a.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]
    for _ in range(B):
        yield np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))])
def verdict(lo, hi):
    if lo > SESOI: return "supported, practically relevant (CI above 0.10)"
    if lo > -SESOI and hi < SESOI: return "practically negligible (CI inside +-0.10)"
    if lo > 0: return "positive but of uncertain size (CI above 0, not all above 0.10)"
    return "inconclusive"
def test(a, x="sqale", covs=("ncloc",), y="hours", boot=boot_twoway):
    rng = np.random.default_rng(SEED)
    est = partial(a, x, covs, y); bs = np.array([partial(a.iloc[i], x, covs, y) for i in boot(a, rng)])
    lo, hi = np.nanpercentile(bs, [5, 95])
    p_pos = float(min(1, np.mean(bs <= 0) + 1 / B))
    p_lo, p_hi = float(min(1, np.mean(bs <= -SESOI) + 1 / B)), float(min(1, np.mean(bs >= SESOI) + 1 / B))
    return {"n": int(len(a)), "n_dev": int(a.dev.nunique()), "n_comp": int(a.comp.nunique()), "partial_rho": est, "CI90": [float(lo), float(hi)],
            "p_one_sided_rho_gt_0": p_pos, "p_tost_lower": p_lo, "p_tost_upper": p_hi, "p_tost": max(p_lo, p_hi), "verdict": verdict(lo, hi)}
def cgm(a, x="sqale"):
    # secondary: analytic two-way cluster-robust SE (Cameron, Gelbach and Miller 2011) of the partial rho, via its influence function
    e1, e2 = rank_resid(a, "hours", ["ncloc"]), rank_resid(a, x, ["ncloc"]); e1 = (e1 - e1.mean()) / e1.std(); e2 = (e2 - e2.mean()) / e2.std()
    r = float(np.mean(e1 * e2)); psi = e1 * e2 - r * (e1 ** 2 + e2 ** 2) / 2; n = len(psi)
    V = lambda g: float(pd.Series(psi).groupby(g).sum().pow(2).sum()) / n ** 2
    v = V(a.dev.values) + V(a.comp.values) - V((a.dev + "|" + a.comp).values); se = float(np.sqrt(max(v, 0)))
    return {"partial_rho": r, "se_twoway": se, "CI90": [r - 1.645 * se, r + 1.645 * se], "verdict": verdict(r - 1.645 * se, r + 1.645 * se)}

# ---------- data ----------
def is_code(f):   # same rule as preregistration/sqale_lines.py for Moodle
    f = f.lower(); return f.endswith((".php", ".js", ".mjs")) and not f.endswith(".min.js") and "/build/" not in f and "/yui/" not in f
st = pd.read_csv(f"{R}/data/history/moodle_history.csv")[["key", "assignee_T", "hours_assignee"]]
df = pd.read_csv(f"{R}/data/features/moodle_features.csv", usecols=["key", "hours", "fix_author", "components", "fix_date", "h_commits_1y"]).merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df["comp"] = df.components.fillna("?").astype(str).str.split(";").str[0].replace({"": "?"})
df = df[df.hours > 0]
keys = open(f"{R}/preregistration_v4/newsample_keys_moodle.txt").read().split(); K = set(keys)
L = {d["key"]: d["files"] for d in map(json.loads, gzip.open(f"{R}/data/links/moodle_links.jsonl.gz", "rt")) if d["key"] in K}
def module(files):   # most frequent of the first two directory levels of the touched code files (ties: alphabetical)
    c = collections.Counter("/".join(f.split("/")[:2]) if f.count("/") >= 2 else f.split("/")[0] for f in files if is_code(f))
    return sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] if c else "?"
df["module"] = df.key.map(lambda k: module(L.get(k, [])))
s = pd.DataFrame([{k: v for k, v in r.items() if k != "per_file"} for r in map(json.loads, open(MSF))]).drop_duplicates("key", keep="last")
if "error" not in s: s["error"] = None
s = s.rename(columns={"sqale_min": "sqale"})
pop = df[df.key.isin(K)]
big = pop[pop.key.map(lambda k: len(L.get(k, []))) > MAXFILES]
pop = pop[~pop.key.isin(big.key)].merge(s, on="key", how="left")
elig = pop[(pop.code_files_at_parent.fillna(0) > 0) | pop.error.notna()]
ok = elig.error.isna() & (elig.ncloc.fillna(0) > 0) & elig.sqale.notna()
a = elig[ok].reset_index(drop=True); miss = elig[~ok]
out = {"parameters": {"B": B, "seed": SEED, "SESOI_rho": SESOI, "margin_dMAE": MARGIN, "max_files": MAXFILES},
       "counts": {"keys": len(keys), "hours_gt_0": int(len(df[df.key.isin(K)])), "excluded_over_max_files": int(len(big)), "with_record": int(pop.key.isin(s.key).sum()),
                  "eligible_code_at_parent_or_failed": int(len(elig)), "analysed": int(len(a)), "missing": int(len(miss)),
                  "median_hours_analysed": float(a.hours.median()) if len(a) else None, "median_hours_missing": float(miss.hours.median()) if len(miss) else None},
       "sonarqube_versions": sorted({str(v) for v in s.get("sonarqube_version", pd.Series(dtype=str)).dropna()})}
# ---------- primary ----------
out["H1-2W"] = test(a)
t1 = out["H1-2W"]
out["conclusion_rule"] = ("negligible: practically negligible beyond size under developer x component clustering" if t1["verdict"].startswith("practically negligible") else
                          "supported: a practically relevant positive association beyond size" if t1["verdict"].startswith("supported") else
                          "positive: above zero, size uncertain" if t1["verdict"].startswith("positive") else "inconclusive")
# registered positive control: commits to the touched files in the previous year, same statistic and interval
out["positive_control_h_commits_1y"] = test(a.dropna(subset=["h_commits_1y"]).reset_index(drop=True), x="h_commits_1y")
# ---------- registered secondary analyses (not confirmatory) ----------
S = out["secondary"] = {}
am = a.assign(comp=a.module)                                     # developer x code module
S["H1 two-way developer x code module"] = test(am)
S["H1 developer-only bootstrap (first registration)"] = test(a, boot=boot_dev)
S["H1 CGM analytic two-way (developer x component)"] = cgm(a)
S["H1 assignee hours only"] = test(a[a.hours_assignee.fillna(0) > 0].reset_index(drop=True), y="hours_assignee")
S["H1 resolved from 2023 (period of the first hold-out)"] = test(a[a.fix_date >= "2023-01-01"].reset_index(drop=True))
if {"sqale_righe_modificate", "righe_vecchie_modificate", "ncloc_c1_prima", "c1_files_at_parent"} <= set(a.columns):
    a2 = a[(a.c1_files_at_parent.fillna(0) > 0) & (a.righe_vecchie_modificate.fillna(0) > 0) & (a.ncloc_c1_prima.fillna(0) > 0)].reset_index(drop=True)
    S["H2 two-way developer x component"] = test(a2, x="sqale_righe_modificate", covs=("righe_vecchie_modificate", "ncloc_c1_prima"))
# H3 by 10-fold cross-validation (no separate training set): dMAE lines+SQALE vs lines only, two-way bootstrap of the mean difference
from sklearn.model_selection import KFold
y = np.log(a.hours.values); P1, P2 = np.zeros(len(y)), np.zeros(len(y))
for i, j in KFold(10, shuffle=True, random_state=SEED).split(y):
    for Pp, cols in [(P1, ["ncloc"]), (P2, ["ncloc", "sqale"])]:
        M = lambda idx: np.column_stack([np.ones(len(idx))] + [np.log1p(a[c].values[idx].astype(float)) for c in cols])
        Pp[j] = np.exp(M(j) @ np.linalg.lstsq(M(i), y[i], rcond=None)[0])
h = a.hours.values; d = np.abs(h - P2) - np.abs(h - P1); mae = float(np.mean(np.abs(h - P1))); rng = np.random.default_rng(SEED)
bs = np.array([d[i].mean() for i in boot_twoway(a, rng)]); lo, hi = np.percentile(bs, [5, 95])
S["H3 cv10, two-way developer x component"] = {"n": int(len(h)), "MAE_lines_only": mae, "dMAE": float(d.mean()), "CI90": [float(lo), float(hi)],
    "CI90_pct_MAE": [float(100 * lo / mae), float(100 * hi / mae)],
    "verdict": "SQALE helps (CI below -2% of MAE)" if hi < -MARGIN * mae else "equivalent (CI inside +-2% of MAE)" if lo > -MARGIN * mae and hi < MARGIN * mae else "inconclusive"}
json.dump(out, open(OUTF, "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
