# Verdict probabilities of the fourth registration (two-way developer x first-component interval) on the REAL new pools, before any scan.
# Uses only data already seen: hours, developers, components and a size proxy (st_loc_sum = lines of the touched code files at the parent,
# from git) of the pool issues; and, from issues ALREADY scanned, the size slope of log SQALE and the share of the debt residual that is
# shared within a Jira component (ICC). Synthetic debt = a + b*log1p(size) + sd*(sqrt(ICC)*u_component + sqrt(1-ICC)*e); for a target rho it is
# mixed with the rank residual of hours. Then the registered two-way bootstrap and decision rules. Usage: python3 power_pool.py <project> <target> <nsim> <B> [icc]
import sys, json, gzip, glob, numpy as np, pandas as pd
R = "/home/user/sqale-effort-replication"; p, T, NSIM, B = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
src = open(f"{R}/preregistration/confermativo.py").read(); exec(src[src.index("def rank_resid"):src.index("def boot_groups")])
st = pd.read_csv(f"{R}/data/history/{p}_history.csv")[["key", "assignee_T"]]
df = pd.read_csv(f"{R}/data/features/{p}_features.csv").merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df["comp"] = df.components.fillna("?").astype(str).str.split(";").str[0].replace({"": "?"}); df = df[df.hours > 0]
keys = set(open(f"/mnt/project-files/ricerca2/preregistrazione_v4/" + ("newsample_keys_moodle.txt" if p == "moodle" else "power_sim/pool_keys_mariadb.txt") + "").read().split())
P = df[df.key.isin(keys) & (df.st_loc_sum.fillna(0) > 0)].reset_index(drop=True)
if p == "moodle":
    S = pd.concat([pd.read_json(f"{R}/data/confirmatory/{f}_scan_moodle.jsonl", lines=True) for f in ["holdout", "exploratory_sample"]]).drop_duplicates("key")
    S = S[(S.code_files_at_parent > 0) & (S.ncloc > 0)][["key", "sqale_min", "ncloc"]]
else:
    S = pd.concat([pd.read_json(f"{R}/preregistration_v2/risultati/{f}.jsonl", lines=True) for f in ["new_scan_mariadb_v2", "train_scan_mariadb_fresh"]]).drop_duplicates("key", keep="last")
    S = S[S.get("error").isna() & (S.ncloc_official.fillna(0) > 0)].rename(columns={"sqale_min_official": "sqale_min", "ncloc_official": "ncloc"})[["key", "sqale_min", "ncloc"]]
S = S.merge(df[["key", "comp"]], on="key")
l, s = np.log1p(S.ncloc.values), np.log1p(S.sqale_min.values); X = np.column_stack([np.ones(len(l)), l]); beta = np.linalg.lstsq(X, s, rcond=None)[0]
res = s - X @ beta; g = pd.Series(res).groupby(S.comp.values)
k = g.size(); msb = (k * (g.mean() - res.mean()) ** 2).sum() / (len(k) - 1); msw = ((res - g.transform("mean").values) ** 2).sum() / (len(res) - len(k))
n0 = (len(res) - (k ** 2).sum() / len(res)) / (len(k) - 1); icc = float(max(0, (msb - msw) / (msb - msw + n0 * msw)))
icc_est = icc
if len(sys.argv) > 5: icc = float(sys.argv[5])   # sensitivity: override the ICC
rng = np.random.default_rng(20261124)
def boot_twoway(a):
    gd, gc = pd.factorize(a.dev)[0], pd.factorize(a.comp)[0]
    for _ in range(B):
        wd = np.bincount(rng.integers(0, gd.max() + 1, gd.max() + 1), minlength=gd.max() + 1)
        wc = np.bincount(rng.integers(0, gc.max() + 1, gc.max() + 1), minlength=gc.max() + 1)
        yield np.repeat(np.arange(len(a)), wd[gd] * wc[gc])
def verdict(lo, hi): return "supported" if lo > .10 else "negligible" if lo > -.10 and hi < .10 else "positive, uncertain size" if lo > 0 else "inconclusive"
keep = 0.95 if p == "mariadb" else 0.99   # expected scan success
counts, rhos, widths = {}, [], []
gc = pd.factorize(P.comp)[0]
for it in range(NSIM):
    a = P.sample(frac=keep, random_state=int(rng.integers(1e9))).reset_index(drop=True); a["ncloc"] = a.st_loc_sum
    gi = pd.factorize(a.comp)[0]; u = rng.standard_normal(gi.max() + 1)[gi]; e = rng.standard_normal(len(a))
    z = np.sqrt(icc) * u + np.sqrt(1 - icc) * e; z = (z - z.mean()) / z.std()
    if T:
        eh = rank_resid(a, "hours", ["ncloc"]); eh = (eh - eh.mean()) / eh.std(); z = T * eh + np.sqrt(1 - T ** 2) * z
    a["x"] = beta[0] + beta[1] * np.log1p(a.ncloc.values) + res.std() * z
    est = partial(a, "x", ["ncloc"]); bs = np.array([partial(a.iloc[i], "x", ["ncloc"]) for i in boot_twoway(a)])
    lo, hi = np.nanpercentile(bs, [5, 95]); v = verdict(lo, hi); counts[v] = counts.get(v, 0) + 1; rhos.append(est); widths.append(hi - lo)
out = {"project": p, "target_rho": T, "n_pool_with_code": int(len(P)), "n_sim_issues": int(round(len(P) * keep)), "n_dev": int(P.dev.nunique()), "n_comp": int(P.comp.nunique()),
       "icc_debt_residual_by_component": icc, "icc_estimated": icc_est, "n_scanned_for_icc": int(len(S)), "n_sim": NSIM, "B": B,
       "verdict_share": {v: c / NSIM for v, c in counts.items()}, "mean_rho": float(np.mean(rhos)), "sd_rho": float(np.std(rhos)), "mean_ci_width": float(np.mean(widths))}
json.dump(out, open(f"/mnt/project-files/ricerca2/preregistrazione_v4/power_sim/power_{p}_t{T}" + (f"_icc{icc}" if len(sys.argv) > 5 else "") + ".json", "w"), indent=1); print(json.dumps(out))
