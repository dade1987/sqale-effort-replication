# Confirmatory analysis of preregistration 3 (MOSIP, OpenLMIS, OpenMRS; SonarQube Community Build 26.9, SonarSource Java/JS/TS analysers).
# Usage: python3 confermativo_v3.py <out.json> <project>:<features.csv>:<scan.jsonl> [...]   (one argument per project)
# Statistic, bootstrap and decision rules as in the first two registrations, plus familywise equivalence (TOST + Holm) and a
# dependence-robust reading (two-way developer x module bootstrap), both fixed here before any measurement.
import sys, json, numpy as np, pandas as pd
B, SEED, S, M = 5000, 2026, 0.10, 0.02
outf, specs = sys.argv[1], [a.split(":") for a in sys.argv[2:]]
def rank_resid(a, y, covs):
    r = a[[y] + covs].rank().values; X = np.column_stack([np.ones(len(r))] + [r[:, i + 1] for i in range(len(covs))])
    return r[:, 0] - X @ np.linalg.lstsq(X, r[:, 0], rcond=None)[0]
def partial(a, x="sqale", covs=("ncloc",), y="hours"):
    covs = list(covs); return float(np.corrcoef(rank_resid(a, y, covs), rank_resid(a, x, covs))[0, 1])
def boot_dev(a, rng):
    g = pd.factorize(a.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]
    for _ in range(B): yield np.concatenate([idx[i] for i in rng.integers(0, len(idx), len(idx))])
def boot_twoway(a, rng):
    gd, gm = pd.factorize(a.dev)[0], pd.factorize(a.module)[0]
    for _ in range(B):
        wd = np.bincount(rng.integers(0, gd.max() + 1, gd.max() + 1), minlength=gd.max() + 1)
        wm = np.bincount(rng.integers(0, gm.max() + 1, gm.max() + 1), minlength=gm.max() + 1)
        yield np.repeat(np.arange(len(a)), wd[gd] * wm[gm])
def verdict(lo, hi):
    if lo > S: return "supported, practically relevant (CI above 0.10)"
    if lo > -S and hi < S: return "practically negligible (CI inside +-0.10)"
    if lo > 0: return "positive but of uncertain size (CI above 0, not all above 0.10)"
    return "inconclusive"
def h1(a, boot, rng):
    bs = np.array([partial(a.iloc[i]) for i in boot(a, rng)]); lo, hi = np.nanpercentile(bs, [5, 95])
    return {"n": int(len(a)), "partial_rho": partial(a), "CI90": [float(lo), float(hi)], "verdict": verdict(lo, hi),
            "p_one_sided_rho_gt_0": float(min(1, np.mean(bs <= 0) + 1 / B)),
            "p_TOST": float(max(min(1, np.mean(bs <= -S) + 1 / B), min(1, np.mean(bs >= S) + 1 / B))), "boot_se": float(np.nanstd(bs))}
def h3(a, rng):
    a = a.sort_values(["resolved", "key"]).reset_index(drop=True); cut = len(a) // 2; tr, te = a.iloc[:cut], a.iloc[cut:].reset_index(drop=True)
    X = lambda d, cols: np.column_stack([np.ones(len(d))] + [np.log1p(d[c].values) for c in cols])
    P = {lab: np.exp(X(te, cols) @ np.linalg.lstsq(X(tr, cols), np.log(tr.hours.values), rcond=None)[0]) for lab, cols in [("l", ["ncloc"]), ("ls", ["ncloc", "sqale"])]}
    y = te.hours.values; d = np.abs(y - P["ls"]) - np.abs(y - P["l"]); mae = float(np.mean(np.abs(y - P["l"])))
    bs = np.array([d[i].mean() for i in boot_dev(te, rng)]); lo, hi = np.percentile(bs, [5, 95])
    v = "SQALE helps (CI below -2% of MAE)" if hi < -M * mae else "equivalent (CI inside +-2% of MAE)" if lo > -M * mae and hi < M * mae else "inconclusive"
    return {"n_train": int(cut), "n_test": int(len(te)), "train_until": str(tr.resolved.iloc[-1]), "MAE_lines_only": mae, "dMAE": float(d.mean()),
            "CI90": [float(lo), float(hi)], "CI90_pct_MAE": [float(100 * lo / mae), float(100 * hi / mae)], "verdict": v}
def holm(p):
    ks = sorted(p, key=p.get); out, run = {}, 0
    for i, k in enumerate(ks): run = max(run, min(1, (len(ks) - i) * p[k])); out[k] = run
    return out
out = {"parameters": {"B": B, "seed": SEED, "SESOI_rho": S, "margin_dMAE": M}}
for p, ff, sf in specs:
    f = pd.read_csv(ff); s = pd.DataFrame([json.loads(l) for l in open(sf)]).drop_duplicates("key", keep="last")
    s = s.rename(columns={"sqale_min": "sqale"}); s["error"] = s["error"] if "error" in s else None
    pop = f.merge(s, on="key", how="left")
    elig = pop[(pop.code_files_at_parent.fillna(0) > 0) | pop.error.notna()]
    a = elig[elig.error.isna() & (elig.files_measured.fillna(0) > 0) & (elig.ncloc.fillna(0) > 0)].reset_index(drop=True)
    miss = elig[~elig.key.isin(a.key)]
    R = {"counts": {"issues": int(len(f)), "scanned": int(pop.code_files_at_parent.notna().sum()), "eligible": int(len(elig)), "analysed": int(len(a)),
                    "missing": int(len(miss)), "median_hours_analysed": float(a.hours.median()), "median_hours_missing": float(miss.hours.median()) if len(miss) else None,
                    "developers": int(a.dev.nunique()), "modules": int(a.module.nunique())}}
    rng = np.random.default_rng(SEED)                  # per project, order: H1 developer, H1 two-way, H3
    R["H1"] = h1(a, boot_dev, rng); R["H1_twoway_dev_module"] = h1(a, boot_twoway, rng); R["H3"] = h3(a, rng)
    R["secondary"] = {"H1_bugs_only": h1(a[a.type == "Bug"].reset_index(drop=True), boot_dev, np.random.default_rng(SEED)) if (a.type == "Bug").sum() > 50 else None,
                      "H1_all_touched_code_files_measured": h1(a[a.files_measured == a.code_files_at_parent].reset_index(drop=True), boot_dev, np.random.default_rng(SEED))}
    out[p] = R
P = [p for p, _, _ in specs]
out["family"] = {"holm_one_sided_rho_gt_0": holm({p: out[p]["H1"]["p_one_sided_rho_gt_0"] for p in P}),
                 "holm_TOST": holm({p: out[p]["H1"]["p_TOST"] for p in P})}
out["family"]["all_equivalent_familywise"] = all(v < 0.05 for v in out["family"]["holm_TOST"].values())
out["family"]["all_negligible_under_twoway"] = all(out[p]["H1_twoway_dev_module"]["verdict"].startswith("practically negligible") for p in P)
z = np.array([np.arctanh(out[p]["H1"]["partial_rho"]) for p in P]); se = np.array([out[p]["H1"]["boot_se"] / (1 - out[p]["H1"]["partial_rho"] ** 2) for p in P])
w = 1 / se ** 2; zf = float((w * z).sum() / w.sum()); Q = float((w * (z - zf) ** 2).sum()); tau2 = max(0.0, (Q - (len(P) - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
wr = 1 / (se ** 2 + tau2); zr = float((wr * z).sum() / wr.sum()); ser = float(np.sqrt(1 / wr.sum()))
out["pooled_random_effects_secondary"] = {"rho": float(np.tanh(zr)), "CI90": [float(np.tanh(zr - 1.645 * ser)), float(np.tanh(zr + 1.645 * ser))], "tau2": tau2, "Q": Q}
json.dump(out, open(outf, "w"), indent=1, default=float); print(json.dumps(out, indent=1, default=float))
