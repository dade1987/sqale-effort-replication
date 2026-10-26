"""Exploratory checks requested by the v2 reviews (not preregistered).
(a) timing: work logged before the first fix commit; (b) analysable vs excluded issues;
(c) matched nonlinear test: LightGBM on size only vs size + SQALE (+ density, interaction via trees);
(d) uncertainty for Table 10 (size classes). Usage: python3 revision_checks.py -> revision_checks.json"""
import json, numpy as np, pandas as pd, lightgbm as lgb
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; D = f"{ROOT}/data"
rng = np.random.default_rng(2026); B = 2000
FEAT = {p: f"{D}/features/{p}_features.csv" for p in ["moodle", "mariadb", "percona"]}
OLD = {"moodle": f"{D}/confirmatory/exploratory_sample_scan_moodle.jsonl", "mariadb": f"{D}/confirmatory/exploratory_sample_scan_mariadb.jsonl", "percona": f"{D}/sqale/percona_sqale.jsonl"}
HO = {p: f"{D}/confirmatory/holdout_scan_{p}.jsonl" for p in ["moodle", "mariadb"]}
T0 = {"moodle": "2023-01-01", "mariadb": "2023-01-01", "percona": "2021-01-01"}
def load(p):
    st = pd.read_csv(f"{D}/history/{p}_history.csv")[["key", "assignee_T"]]
    df = pd.read_csv(FEAT[p]).merge(st, on="key", how="left")
    df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
    df = df[df.hours > 0].sort_values(["fix_date", "key"]).reset_index(drop=True)
    # developer's number of issues fixed before this one
    df["dev_prior_n"] = df.groupby("dev").cumcount()
    return df
def cboot(vals, grp, stat):
    g = pd.Series(np.arange(len(vals))).groupby(np.asarray(grp)).apply(list).tolist(); out = []
    for _ in range(B):
        idx = np.concatenate([g[i] for i in rng.integers(0, len(g), len(g))]); out.append(stat(idx))
    return [float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))]
res = {}
for p in ["moodle", "mariadb", "percona"]:
    df = load(p); r = {}
    # (a) timing
    # per-issue worklog timing derived from the (not distributed) raw worklogs: data/extra/<project>_worklog_timing.csv
    wt = pd.read_csv(f"{D}/extra/{p}_worklog_timing.csv").merge(df[df.fix_date >= T0[p]][["key", "fix_date"]], on="key")
    gap = (pd.to_datetime(wt.fix_date) - pd.to_datetime(wt.first_worklog_date)).dt.days.values
    sb = np.where(wt.hours_logged > 0, wt.hours_before_first_fix_commit_day / wt.hours_logged, 0); any_before = wt.hours_before_first_fix_commit_day.values > 0
    r["timing_test_issues"] = {"n": int(len(gap)), "median_days_first_worklog_to_first_commit": float(np.median(gap)),
        "share_issues_with_hours_logged_before_first_commit_day": float(np.mean(any_before)),
        "median_share_of_hours_before_first_commit_day": float(np.median(sb)), "mean_share_of_hours_before_first_commit_day": float(np.mean(sb)),
        "share_issues_more_than_half_hours_before": float(np.mean(sb > 0.5))}
    # (b) analysable vs excluded
    def profile(d):
        return {"n": int(len(d)), "median_hours": float(d.hours.median()), "share_bug": float((d.type == "Bug").mean()),
                "median_files": float(d.n_files.median()), "median_dev_prior_issues": float(d.dev_prior_n.median())}
    old = pd.read_json(OLD[p], lines=True).drop_duplicates("key").merge(df, on="key")
    ot = old[old.fix_date >= T0[p]]
    r["selection_exploratory_test"] = {"analysable": profile(ot[ot.code_files_at_parent > 0]), "excluded": profile(ot[~(ot.code_files_at_parent > 0)])}
    if p in HO:
        ho = pd.read_json(HO[p], lines=True).drop_duplicates("key").merge(df, on="key")
        ok = (ho.code_files_at_parent > 0) & (ho.ncloc > 0)
        r["selection_holdout"] = {"analysable_H1": profile(ho[ok]), "excluded": profile(ho[~ok])}
    # (c) matched nonlinear comparison
    tr = old[(old.fix_date < T0[p]) & (old.code_files_at_parent > 0) & (old.ncloc > 0)].copy()
    evals = {"exploratory_test": ot[(ot.code_files_at_parent > 0) & (ot.ncloc > 0)].copy()}
    if p in HO: evals["holdout"] = ho[ok].copy()
    for d in [tr] + list(evals.values()):
        d["log_ncloc"] = np.log1p(d.ncloc); d["log_files"] = np.log1p(d.code_files_at_parent); d["log_sqale"] = np.log1p(d.sqale_min)
        d["density"] = d.sqale_min / d.ncloc
    S = ["log_ncloc", "log_files"]; S2 = S + ["log_sqale", "density"]
    prm = dict(objective="l1", learning_rate=0.03, num_leaves=15, min_data_in_leaf=40, feature_fraction=1.0, bagging_fraction=0.8, bagging_freq=1, seed=2026, verbose=-1, num_threads=4, deterministic=True)
    models = {}
    for lab, cols in [("size", S), ("size+SQALE", S2)]:
        cv = lgb.cv(prm, lgb.Dataset(tr[cols], np.log(tr.hours)), 2000, nfold=5, stratified=False, seed=2026, callbacks=[lgb.early_stopping(100, verbose=False)])
        nb = len(next(iter(cv.values())))
        models[lab] = lgb.train(prm, lgb.Dataset(tr[cols], np.log(tr.hours)), nb); models[lab + "_rounds"] = nb
    r["nonlinear"] = {"n_train": int(len(tr)), "rounds": {k: models[k + "_rounds"] for k in ["size", "size+SQALE"]}}
    for nm, ev in evals.items():
        y = ev.hours.values; a = np.exp(models["size+SQALE"].predict(ev[S2])); b = np.exp(models["size"].predict(ev[S]))
        e = np.abs(y - a) - np.abs(y - b); mae = float(np.mean(np.abs(y - b)))
        ci = cboot(e, ev.dev.values, lambda i: e[i].mean())
        r["nonlinear"][nm] = {"n": int(len(ev)), "MAE_size": mae, "MAE_size_sqale": float(np.mean(np.abs(y - a))), "dMAE": float(e.mean()), "ci95": ci,
                              "pct": float(e.mean() / mae * 100), "ci95_pct": [c / mae * 100 for c in ci]}
    # (d) Table 10 uncertainty: accuracy and weighted kappa of recalibrated SQALE vs most frequent class
    from sklearn.metrics import cohen_kappa_score
    ev = evals["exploratory_test"]; c = np.polyfit(np.log1p(tr.sqale_min), np.log(tr.hours), 1)
    cal = np.exp(np.polyval(c, np.log1p(ev.sqale_min.values)))
    cls = lambda h: np.digitize(h, [4, 16], right=True)   # as in exploratory.py
    yc, pc = cls(ev.hours.values), cls(cal); mf = np.bincount(cls(df[df.fix_date < T0[p]].hours.values)).argmax()   # majority class of the full training period
    acc_d = (pc == yc).astype(float) - (yc == mf).astype(float)
    r["size_classes"] = {"n": int(len(ev)), "acc_sqale": float((pc == yc).mean()), "acc_most_frequent": float((yc == mf).mean()),
        "acc_diff": float(acc_d.mean()), "acc_diff_ci95": cboot(acc_d, ev.dev.values, lambda i: acc_d[i].mean()),
        "kappa_w": float(cohen_kappa_score(yc, pc, weights="quadratic")),
        "kappa_w_ci95": cboot(acc_d, ev.dev.values, lambda i: cohen_kappa_score(yc[i], pc[i], weights="quadratic") if len(set(pc[i])) > 1 or len(set(yc[i])) > 1 else 0.0)}
    res[p] = r
    print(p, json.dumps(r, indent=0)[:1800])
json.dump(res, open(f"{ROOT}/results/exploratory/revision_checks.json", "w"), indent=1)
