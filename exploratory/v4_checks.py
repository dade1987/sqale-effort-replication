# Short exploratory checks requested after the third simulated review (not preregistered). Usage: python3 v4_checks.py <project>
# (a) H3 with the positive-control measures (commits and churn of the last year) in place of SQALE, frozen H3 code;
# (c) H1 with a two-way (developer x component) cluster bootstrap; (d) H1 adjusted for developer and component (fixed effects);
# (e) MariaDB and Moodle: M1/M0 vs Jira estimates on log error and within-2x, and with the assignee's own hours.
# Writes results/exploratory/v4_checks_<project>.json
import sys, json, os, numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
p = sys.argv[1]
src = open(f"{H}/preregistration/confermativo.py").read()
exec(src[src.index("B, SEED"):src.index("\nst = ")]); exec(src[src.index("def rank_resid"):src.index("out = {")])
st = pd.read_csv(f"{H}/data/history/{p}_history.csv")
df = pd.read_csv(f"{H}/data/features/{p}_features.csv").merge(st[["key", "assignee_T"]], on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df["comp"] = df.components.fillna("?").astype(str).str.split(";").str[0].replace({"": "?"})
df = df[df.hours > 0]
X1 = ["hours", "dev", "comp", "fix_date", "h_commits_1y", "h_churn_1y"]
ho = pd.read_json(f"{H}/data/confirmatory/holdout_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key"] + X1], on="key")
old = pd.read_json(f"{H}/data/confirmatory/exploratory_sample_scan_{p}.jsonl", lines=True).drop_duplicates("key").merge(df[["key"] + X1], on="key")
a1 = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy().reset_index(drop=True)
tr = old[(old.fix_date < "2023-01-01") & (old.code_files_at_parent > 0) & (old.ncloc > 0)]
out = {"project": p, "n_H1": int(len(a1))}
rng = np.random.default_rng(SEED)
# (a) frozen H3 code, measure substituted
def h3(x):
    X = lambda d, cols: np.column_stack([np.ones(len(d))] + [np.log1p(d[c].values) for c in cols])
    P = {lab: np.exp(X(a1, cols) @ np.linalg.lstsq(X(tr, cols), np.log(tr.hours.values), rcond=None)[0]) for lab, cols in [("lines", ["ncloc"]), ("lines+X", ["ncloc", x])]}
    y = a1.hours.values; d = np.abs(y - P["lines+X"]) - np.abs(y - P["lines"]); mae = float(np.mean(np.abs(y - P["lines"])))
    bs = np.array([d[i].mean() for i in boot_groups(a1)]); lo, hi = np.percentile(bs, [5, 95])
    v = ("X helps (CI below -2% of MAE)" if hi < -MARGIN * mae else "equivalent (CI inside +-2% of MAE)" if lo > -MARGIN * mae and hi < MARGIN * mae else "inconclusive")
    return {"n_train": int(len(tr)), "n_test": int(len(a1)), "MAE_lines_only": mae, "dMAE": float(d.mean()), "IC90": [float(lo), float(hi)],
            "IC90_pct_MAE": [float(100 * lo / mae), float(100 * hi / mae)], "verdict": v}
out["a_H3_positive_control"] = {"sqale_min (= H3)": h3("sqale_min"), "h_commits_1y": h3("h_commits_1y"), "h_churn_1y": h3("h_churn_1y")}
# (c) two-way cluster bootstrap: developers and components resampled independently, issue weight = product of the draw counts
def boot_twoway(a):
    gd, gc = pd.factorize(a.dev)[0], pd.factorize(a.comp)[0]
    for _ in range(B):
        wd = np.bincount(rng.integers(0, gd.max() + 1, gd.max() + 1), minlength=gd.max() + 1)
        wc = np.bincount(rng.integers(0, gc.max() + 1, gc.max() + 1), minlength=gc.max() + 1)
        yield np.repeat(np.arange(len(a)), wd[gd] * wc[gc])
est = partial(a1, "sqale_min", ["ncloc"]); bs = np.array([partial(a1.iloc[i], "sqale_min", ["ncloc"]) for i in boot_twoway(a1)])
lo, hi = np.nanpercentile(bs, [5, 95])
out["c_H1_twoway_dev_component"] = {"n": int(len(a1)), "n_dev": int(a1.dev.nunique()), "n_comp": int(a1.comp.nunique()), "rho_parziale": est, "IC90": [float(lo), float(hi)], "esito": verdict_rho(est, lo, hi)}
# (d) H1 with developer and component fixed effects: ranks residualised on rank(ncloc) + dummies (levels with < 5 issues pooled)
def lump(s): c = s.value_counts(); return s.where(s.map(c) >= 5, "other")
def partial_fe(a):
    D = pd.get_dummies(pd.concat([lump(a.dev).rename("d"), lump(a.comp).rename("c")], axis=1), drop_first=True).values.astype(float)
    r = a[["hours", "sqale_min", "ncloc"]].rank().values; X = np.column_stack([np.ones(len(a)), r[:, 2], D])
    e = [r[:, j] - X @ np.linalg.lstsq(X, r[:, j], rcond=None)[0] for j in (0, 1)]
    return float(np.corrcoef(*e)[0, 1])
est = partial_fe(a1); bs = np.array([partial_fe(a1.iloc[i].reset_index(drop=True)) for i in boot_groups(a1)]); lo, hi = np.percentile(bs, [5, 95])
out["d_H1_dev_component_fixed_effects"] = {"n": int(len(a1)), "rho_parziale": est, "IC90": [float(lo), float(hi)], "esito": verdict_rho(est, lo, hi),
                                           "note": "developer-clustered bootstrap, B = 5000; developers and components with < 5 issues pooled into 'other'"}
# (e) learned models vs Jira estimates: log error and within-2x, total hours and assignee-only hours
pr = pd.read_csv(f"{H}/data/predictions/{p}_predictions.csv")
M1 = [c for c in pr.columns if c.startswith("M1 after")][0]; M0 = [c for c in pr.columns if c.startswith("M0 at")][0]
te = pr[["key", "hours", "assignee", M1, M0]].merge(df[["key", "expert_estimate_h", "fix_date"]], on="key").merge(
    st[["key", "est_first_h", "est_first_date", "first_worklog", "hours_assignee"]], on="key", how="left")
pro = (te.est_first_date.fillna("9999") <= te.fix_date) & (te.est_first_date.fillna("9999") <= te.first_worklog.fillna("9999"))
te["est_first_pro_h"] = te.est_first_h.where(pro); te["g"] = te.assignee.fillna("unknown")
def paired(y, pm, pe, g):
    le = lambda q, t: np.abs(np.log(q / t)); w2 = lambda q, t: ((q / t <= 2) & (q / t >= .5)).astype(float)
    res = {"n": int(len(y)), "MdAE_log_model": float(np.median(le(pm, y))), "MdAE_log_expert": float(np.median(le(pe, y))),
           "within2x_model": float(w2(pm, y).mean()), "within2x_expert": float(w2(pe, y).mean())}
    gi = pd.factorize(g)[0]; idx = [np.where(gi == i)[0] for i in range(gi.max() + 1)]; r = np.random.default_rng(SEED); bl, bw = [], []
    for _ in range(B):
        s = np.concatenate([idx[i] for i in r.integers(0, len(idx), len(idx))])
        bl.append(np.median(le(pm[s], y[s])) - np.median(le(pe[s], y[s]))); bw.append(w2(pm[s], y[s]).mean() - w2(pe[s], y[s]).mean())
    res["dMdAE_log_model_minus_expert"] = float(res["MdAE_log_model"] - res["MdAE_log_expert"]); res["dMdAE_log_CI90"] = [float(v) for v in np.percentile(bl, [5, 95])]
    res["dWithin2x_model_minus_expert"] = float(res["within2x_model"] - res["within2x_expert"]); res["dWithin2x_CI90"] = [float(v) for v in np.percentile(bw, [5, 95])]
    return res
E = {}
for lab, col in [("first estimate", "est_first_h"), ("first estimate before work", "est_first_pro_h"), ("final estimate", "expert_estimate_h")]:
    for ylab, ycol in [("total hours", "hours"), ("assignee-only hours", "hours_assignee")]:
        e = te[(te[col].fillna(0) > 0) & (te[ycol].fillna(0) > 0)]
        if len(e) < 30: continue
        for mlab, mcol in [("M1", M1), ("M0", M0)]:
            E[f"{mlab} vs {lab}, {ylab}"] = paired(e[ycol].values, e[mcol].values, e[col].values, e.g.values)
out["e_models_vs_experts"] = E
json.dump(out, open(f"{H}/results/exploratory/v4_checks_{p}.json", "w"), indent=1, default=float)
print(json.dumps(out, indent=1, default=float))
