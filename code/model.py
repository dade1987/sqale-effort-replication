# Per-issue effort models (version after the methodological review).
# Two prediction scenarios:
#   M0 "at start of work": Jira fields as at creation, the developer known at the start of work and their history, title text.
#   M1 "after file localisation": M0 + set of touched files and their metrics at the parent commit (the files are an oracle).
#   M2 ex post: M1 + patch size.
# Removed fix-dependent features: n_new, h_ownership, dev_fix_prior_n.
# Baselines: median, median per type, log-linear on number of files, text (TF-IDF + ridge), ATLM, analogy (k-NN).
# Statistics: developer-clustered bootstrap, Holm correction, Wilcoxon, paired A12, non-inferiority against experts.
# Usage: python3 model.py <features.csv> <history.csv> <name> [sqale.jsonl]
#      environment: VALID_START, TEST_START (split dates)
import sys, os, json, re, bisect, warnings, numpy as np, pandas as pd, lightgbm as lgb
from scipy import stats
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.model_selection import KFold
from sklearn.neighbors import NearestNeighbors
warnings.filterwarnings("ignore")
rng = np.random.default_rng(2026)
f, sf, name = sys.argv[1:4]
V0, T0 = os.environ.get("VALID_START", "2021-01-01"), os.environ.get("TEST_START", "2023-01-01")
df = pd.read_csv(f).merge(pd.read_csv(sf), on="key", how="left")
df = df[df.hours > 0].sort_values(["fix_date", "key"]).reset_index(drop=True)
# Jira fields reconstructed at creation; developer at the start of work (DEV_AT=commit: at the first commit)
df["type"] = df.type_open.fillna(df.type)
df["priority"] = df.priority_open
df["components"] = df.components_open.fillna("")
df["comp1"] = df.components.str.split("|").str[0].fillna("")
df["n_components"] = df.components.map(lambda s: len([c for c in s.split("|") if c]))
df["assignee"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace("git:", "")
df["dev_date"] = df.fix_date
# Developer, developer history and title at the start of work S (start_of_work.py): the default since the EMSE revision.
# DEV_AT=start: assignee at S, or the author of the first worklog only if that worklog is on day S; title as it was at S.
# DEV_AT=start_lenient: first-worklog author even when the worklog is after S, current title (sensitivity analysis).
# DEV_AT=commit: assignee at the first fix commit, current title (sensitivity analysis).
DEV_AT = os.environ.get("DEV_AT", "start")
if DEV_AT in ("start", "start_lenient"):
    sw = pd.read_csv(os.environ.get("START_FILE", sf.replace("_history.csv", "_start_of_work.csv")))[["key", "start_date", "assignee_S", "assignee_S_lenient", "title_at_start"]]
    df = df.merge(sw, on="key", how="left"); df["dev_date"] = df.start_date.fillna(df.fix_date)
    df["assignee"] = (df.assignee_S if DEV_AT == "start" else df.assignee_S_lenient).fillna("")
    if DEV_AT == "start": df["summary"] = df.title_at_start.fillna(df.summary)
df["summary"] = df.summary.fillna("")
df["y"] = np.log(df.hours)
df["year"] = df.fix_date.str[:4].astype(int)

def prior_dev(df, ycol="y"):
    """Developer history: only issues of the same assignee RESOLVED before dev_date (day of the first commit, or start of work with DEV_AT=start)."""
    by = {}
    for a, r, y in zip(df.assignee, df.resolved, df[ycol]):
        by.setdefault(a, []).append((r, y))
    for a in by: by[a].sort()
    n, med = [], []
    for a, T in zip(df.assignee, df.dev_date):
        if not a: n.append(0); med.append(np.nan); continue
        v = by[a]; i = bisect.bisect_left(v, (T,))
        past = [y for _, y in v[:i]][-50:]
        n.append(i); med.append(np.median(past) if past else np.nan)
    return n, med
df["dev_prior_n"], df["dev_prior_med"] = prior_dev(df)

SET = {"jira": ["type", "priority", "comp1", "n_components"],
       "developer": ["dev_prior_n", "dev_prior_med"],
       "text": ["text_pred"],
       "change_set": ["n_files", "n_dirs", "n_top", "n_test", "n_code"],
       "static": ["st_files", "st_loc_sum", "st_loc_max", "st_nfun_sum", "st_ccn_sum", "st_ccn_max", "st_fccn_max", "st_bytes_sum", "st_ccn_density"],
       "history": ["h_commits_sum", "h_commits_max", "h_commits_mean", "h_authors", "h_age_max_d", "h_age_min_d", "h_last_min_d", "h_commits_1y", "h_churn_1y"],
       "co_change": ["cc_partners_sum", "cc_partners_max", "cc_strong_outside", "cc_pair_frac", "cc_conf_in_mean"],
       "patch": ["p_commits", "p_added", "p_deleted"]}
A = ["jira", "developer", "text"]
FILE = ["change_set", "static", "history", "co_change"]
B = A + FILE
cats = ["type", "priority", "comp1"]

# ---- title text: TF-IDF + ridge on log-hours; out-of-fold for the training data
def text_model(tr):
    v = TfidfVectorizer(ngram_range=(1, 2), min_df=3, sublinear_tf=True, max_features=50000)
    X = v.fit_transform(tr.summary); m = Ridge(alpha=3.0).fit(X, tr.y)
    return lambda d: m.predict(v.transform(d.summary))
def text_feature(fit, apply_):
    """out-of-fold values (5 folds) for 'fit', and a model on all of 'fit' for 'apply_'"""
    oof = np.zeros(len(fit))
    for a, b in KFold(5, shuffle=True, random_state=2026).split(fit):
        oof[b] = text_model(fit.iloc[a])(fit.iloc[b])
    return oof, text_model(fit)(apply_)

def frame(d, cols, ref):
    X = d[cols].copy()
    for c in cats:
        if c in X:
            top = ref[c].value_counts(); top = top[top >= 20].index
            X[c] = pd.Categorical(X[c].where(X[c].isin(top), "altro"), categories=list(top) + ["altro"])
    return X
P = dict(objective="l1", learning_rate=0.03, num_leaves=31, min_data_in_leaf=40, feature_fraction=0.8,
         bagging_fraction=0.8, bagging_freq=1, lambda_l2=1.0, verbose=-1, seed=2026, num_threads=4, deterministic=True)
def fit_gbm(tr, va, groups, rounds=None):
    cols = [c for g in groups for c in SET[g]]
    dtr = lgb.Dataset(frame(tr, cols, tr), tr.y, categorical_feature=[c for c in cats if c in cols])
    if rounds is None:
        m = lgb.train(P, dtr, 3000, valid_sets=[lgb.Dataset(frame(va, cols, tr), va.y, reference=dtr)], callbacks=[lgb.early_stopping(100, verbose=False)])
    else:
        m = lgb.train(P, dtr, rounds)
    return m, cols

def metrics(y, p, ytr):
    ae = np.abs(y - p)
    r_ = np.random.default_rng(2026)   # local generator: result independent of call order
    rg = np.mean([np.mean(np.abs(y - r_.choice(ytr, len(y)))) for _ in range(1000)])
    return dict(n=len(y), MAE=ae.mean(), MdAE=np.median(ae), SA=1 - ae.mean() / rg,
                MdAE_log=np.median(np.abs(np.log(y) - np.log(p))), within2x=np.mean(np.abs(np.log(y / p)) <= np.log(2)),
                spearman=stats.spearmanr(y, p)[0] if np.std(p) > 0 else np.nan)

def _bs(y, pa, pb, groups, B=5000):
    """developer-clustered bootstrap replicates of the MAE difference a - b"""
    ea, eb = np.abs(y - pa), np.abs(y - pb); d = ea - eb
    g = pd.factorize(groups)[0]; G = g.max() + 1
    sums = np.bincount(g, d, G); cnt = np.bincount(g, None, G)
    draws = np.random.default_rng(2026).integers(0, G, (B, G))   # same seed for every comparison: reproducible in any order
    return d.mean(), sums[draws].sum(1) / cnt[draws].sum(1)
def cboot(y, pa, pb, groups, B=5000, q=(2.5, 97.5)):
    m, bs = _bs(y, pa, pb, groups, B)
    return m, np.percentile(bs, q[0]), np.percentile(bs, q[1])
def compare(y, pa, pb, groups):
    ea, eb = np.abs(y - pa), np.abs(y - pb)
    m, bs = _bs(y, pa, pb, groups)
    # two-sided p from the clustered bootstrap: primary test; Wilcoxon (independent issues) for comparison only
    p_boot = float(min(1.0, 2 * min(np.mean(bs >= 0), np.mean(bs <= 0)) + 1 / len(bs)))
    return dict(dMAE=m, lo=np.percentile(bs, 2.5), hi=np.percentile(bs, 97.5), p_boot=p_boot, p_wilcoxon=stats.wilcoxon(ea, eb).pvalue,
                A12_paired=float(np.mean(ea < eb) + 0.5 * np.mean(ea == eb)))
def holm(res, key="p_boot"):
    ks = sorted(res, key=lambda k: res[k][key]); m = len(ks); run = 0
    for i, k in enumerate(ks):
        run = max(run, min(1, (m - i) * res[k][key])); res[k]["p_holm"] = run
    return res

# ---- temporal split
tr = df[df.fix_date < V0].copy(); va = df[(df.fix_date >= V0) & (df.fix_date < T0)].copy(); te = df[df.fix_date >= T0].copy()
trva = pd.concat([tr, va]).copy()
res = {"project": name, "split_dates": {"valid_from": V0, "test_from": T0},
       "split": {k: [len(v), float(np.median(v.hours))] for k, v in dict(train=tr, valid=va, test=te).items()},
       "jira_history": {c: float(df[c].mean()) for c in ["type_changed", "prio_changed", "ass_changed", "est_changed"] if c in df},
       "assignee_missing": float((df.assignee == "").mean())}
# text: two versions (validation phase and final phase)
tr["text_pred"], va["text_pred"] = text_feature(tr, va)
trva["text_pred"], te["text_pred"] = text_feature(trva, te)
ytr = trva.hours.values; y = te.hours.values; grp = te.assignee.replace("", "?").values
pred = {}
pred["B0 median"] = np.full(len(te), np.median(ytr))
tm = trva.groupby("type").hours.median(); pred["B1 median per type"] = te.type.map(tm).fillna(np.median(ytr)).values
co = np.polyfit(np.log1p(trva.n_files), trva.y, 1); pred["B2 log-linear on number of files"] = np.exp(np.polyval(co, np.log1p(te.n_files)))
pred["B3 title text"] = np.exp(te.text_pred.values)

def design(d, ref, groups):
    """ATLM (Whigham et al. 2015): log of skewed numeric variables, categories as dummies"""
    cols = [c for g in groups for c in SET[g] if c not in cats and c != "text_pred"]
    X = pd.DataFrame(index=d.index)
    for c in cols:
        x = d[c].astype(float)
        X[c] = np.log1p(x.clip(lower=0)) if ref[c].skew() > 1 else x
    if "dev_prior_med" in X: X["dev_prior_med"] = X["dev_prior_med"].fillna(ref.y.median())
    X = X.fillna(0)
    for c in [c for c in cats if any(c in SET[g] for g in groups)]:
        top = ref[c].value_counts(); top = top[top >= 20].index
        X = X.join(pd.get_dummies(d[c].where(d[c].isin(top), "altro"), prefix=c, dtype=float))
    return X
def atlm(groups):
    Xt = design(trva, trva, groups); Xs = design(te, trva, groups).reindex(columns=Xt.columns, fill_value=0)
    return np.exp(LinearRegression().fit(Xt, trva.y).predict(Xs))
pred["B4 ATLM (feature M1)"] = atlm(B)
pred["B4a ATLM (feature M0)"] = atlm(["jira", "developer"])
# analogy: k-NN on standardised features, median hours of the neighbours; k chosen on validation
def knn(fit, app, k, groups=B):
    Xf = design(fit, fit, groups); Xa = design(app, fit, groups).reindex(columns=Xf.columns, fill_value=0)
    mu, sd = Xf.mean(), Xf.std().replace(0, 1)
    nn = NearestNeighbors(n_neighbors=k).fit(((Xf - mu) / sd).values)
    idx = nn.kneighbors(((Xa - mu) / sd).values, return_distance=False)
    return np.median(fit.hours.values[idx], axis=1)
kbest = min([3, 5, 10, 20, 40], key=lambda k: np.mean(np.abs(np.log(va.hours.values) - np.log(knn(tr, va, k)))))
pred[f"B5 analogy k-NN (k={kbest})"] = knn(trva, te, kbest)

models = {}
for lab, groups in {"M0 at start of work": A, "M1 after file localisation": B, "M2 ex post (+ patch)": B + ["patch"],
                    "M1 without developer": [g for g in B if g != "developer"],
                    "M0 without text": ["jira", "developer"]}.items():
    m, cols = fit_gbm(tr, va, groups)
    m2, _ = fit_gbm(trva, None, groups, rounds=max(50, m.best_iteration))
    pred[lab] = np.exp(m2.predict(frame(te, cols, trva))); models[lab] = (m2, cols, m.best_iteration)
for g in B:
    groups = [x for x in B if x != g]
    if g == "developer": continue
    m, cols = fit_gbm(tr, va, groups); m2, _ = fit_gbm(trva, None, groups, rounds=max(50, m.best_iteration))
    pred[f"M1 without {g}"] = np.exp(m2.predict(frame(te, cols, trva)))
res["test"] = {k: metrics(y, p, ytr) for k, p in pred.items()}
M0, M1 = "M0 at start of work", "M1 after file localisation"
cmp = {}
for k in pred:
    if k.startswith("B"): cmp[f"M1 vs {k}"] = compare(y, pred[M1], pred[k], grp)
for k in ["B0 median", "B1 median per type", "B3 title text", "B4a ATLM (feature M0)"]:
    cmp[f"M0 vs {k}"] = compare(y, pred[M0], pred[k], grp)
cmp["M1 vs M0"] = compare(y, pred[M1], pred[M0], grp)
cmp["M2 vs M1"] = compare(y, pred["M2 ex post (+ patch)"], pred[M1], grp)
res["comparisons"] = holm(cmp)
if T0 < "2023-01-01":
    s23 = (te.fix_date >= "2023-01-01").values
    if s23.sum() >= 30: res["test_from_2023"] = {k: metrics(y[s23], p[s23], ytr) for k, p in pred.items() if k[:2] in ("B0", "M0", "M1", "M2")}

# ---- expert estimate: Original Estimate versions; non-inferiority with a margin of 10% of the expert MAE
if "est_first_date" in te:
    pro = (te.est_first_date.fillna("9999") <= te.fix_date) & (te.est_first_date.fillna("9999") <= te.first_worklog.fillna("9999"))
    te["est_first_pro_h"] = te.est_first_h.where(pro)
for lab, col in [("first estimate", "est_first_h"), ("first estimate before work", "est_first_pro_h"), ("final estimate", "expert_estimate_h")]:
    if col not in te: continue
    e = (te[col].fillna(0) > 0).values
    if e.sum() < 30: continue
    ye, pe = y[e], te[col].values[e]; g = grp[e]
    out = {"expert": metrics(ye, pe, ytr)}
    for mlab in [M0, M1]:
        pm = pred[mlab][e]; mae_e = np.abs(ye - pe).mean(); margin = 0.10 * mae_e
        d, lo90, hi90 = cboot(ye, pm, pe, g, q=(5, 95))
        _, lo, hi = cboot(ye, pm, pe, g)
        _, lob, hib = cboot(ye, pm, pe, g, q=(0.833, 99.167))   # Bonferroni over the 6 non-inferiority tests (3 estimates x 2 models)
        out[mlab] = dict(metrics(ye, pm, ytr), dMAE=d, CI95=[lo, hi], CI90=[lo90, hi90], margin_h=margin,
                         non_inferior=bool(hi90 < margin), non_inferior_bonferroni=bool(hib < margin), CI_one_sided_bonferroni=hib, equivalent_TOST=bool(hi90 < margin and lo90 > -margin),
                         p_wilcoxon=stats.wilcoxon(np.abs(ye - pm), np.abs(ye - pe)).pvalue)
    res[f"expert ({lab})"] = out
res["share_estimate_changed"] = float(df.est_changed[df.expert_estimate_h.fillna(0) > 0].mean()) if "est_changed" in df else None

# ---- SQALE on the analysed sample
if len(sys.argv) > 4 and os.path.exists(sys.argv[4]):
    sq = pd.read_json(sys.argv[4], lines=True).drop_duplicates("key").set_index("key")
    d2 = df.join(sq[["sqale_min", "smells", "ncloc", "code_files_at_parent"]], on="key", how="inner")
    d2 = d2[d2.code_files_at_parent > 0]
    s_tr = d2[d2.fix_date < T0]; s_te = d2[d2.fix_date >= T0]
    c = np.polyfit(np.log1p(s_tr.sqale_min), s_tr.y, 1)
    S = {}
    pm1 = pd.Series(pred[M1], index=te.key); pnd = pd.Series(pred["M1 without developer"], index=te.key); pm0 = pd.Series(pred[M0], index=te.key)
    REF = re.compile(r"refactor|clean ?up|code smell|technical debt|tech debt|tidy|deprecat|unused|simplif|dead code|lint|codestyle|coding style|code style|warning", re.I)
    for sub, mask in [("all", np.ones(len(s_te), bool)), ("refactoring and clean-up", s_te.summary.str.contains(REF).values)]:
        st_ = s_te[mask]; ys = st_.hours.values
        if len(st_) < 20: S[sub] = {"n": int(len(st_))}; continue
        p_raw = np.maximum(st_.sqale_min.values / 60, 1 / 60); p_cal = np.exp(np.polyval(c, np.log1p(st_.sqale_min.values)))
        m1 = pm1.reindex(st_.key).values; mnd = pnd.reindex(st_.key).values; m0 = pm0.reindex(st_.key).values; g = st_.assignee.replace("", "?").values
        S[sub] = {"n": int(len(st_)), "SQALE raw": metrics(ys, p_raw, ytr), "SQALE recalibrated": metrics(ys, p_cal, ytr),
                  "M1": metrics(ys, m1, ytr), "M1 without developer": metrics(ys, mnd, ytr), "M0": metrics(ys, m0, ytr), "M0 vs SQALE recalibrated": compare(ys, m0, p_cal, g),
                  "M1 vs SQALE recalibrated": compare(ys, m1, p_cal, g), "M1 without developer vs SQALE recalibrated": compare(ys, mnd, p_cal, g)}
    for sub in S:
        cmp_ = {k: v for k, v in S[sub].items() if isinstance(v, dict) and "p_wilcoxon" in v}
        if cmp_: holm(cmp_)   # Holm over the SQALE comparisons within each subset
    # SQALE beyond size: partial Spearman correlation (controlling for lines of code) and incremental validity
    def pcor(d):
        r = d[["hours", "sqale_min", "ncloc"]].rank()
        res_ = lambda a, b: r[a] - np.polyval(np.polyfit(r[b], r[a], 1), r[b])
        return float(stats.pearsonr(res_("hours", "ncloc"), res_("sqale_min", "ncloc"))[0])
    dd = d2[d2.ncloc > 0]
    X = lambda d, cols: np.column_stack([np.ones(len(d))] + [np.log1p(d[c].values) for c in cols])
    oltre = {"partial_spearman_all": pcor(dd), "partial_spearman_test": pcor(dd[dd.fix_date >= T0]),
             "spearman_hours_density": float(stats.spearmanr(dd.hours, dd.sqale_min / dd.ncloc)[0]),
             "spearman_hours_per_line_density": float(stats.spearmanr(dd.hours / dd.ncloc, dd.sqale_min / dd.ncloc)[0])}
    a_tr, a_te = dd[dd.fix_date < T0], dd[dd.fix_date >= T0]; ga = a_te.assignee.replace("", "?").values
    P_ = {}
    for lab, cols in [("lines only", ["ncloc"]), ("SQALE only", ["sqale_min"]), ("lines + SQALE", ["ncloc", "sqale_min"])]:
        beta = np.linalg.lstsq(X(a_tr, cols), a_tr.y.values, rcond=None)[0]
        P_[lab] = np.exp(X(a_te, cols) @ beta); oltre[lab] = metrics(a_te.hours.values, P_[lab], ytr)
        if lab == "lines + SQALE": oltre["coef_log_sqale"] = float(beta[-1])
    oltre["lines + SQALE vs lines only"] = compare(a_te.hours.values, P_["lines + SQALE"], P_["lines only"], ga)
    oltre["n_test"] = int(len(a_te))
    S["beyond_size"] = oltre
    S["n_train_calibration"] = int(len(s_tr))
    S["spearman_hours_sqale"] = float(stats.spearmanr(d2.hours, d2.sqale_min)[0]); S["spearman_hours_ncloc"] = float(stats.spearmanr(d2.hours, d2.ncloc)[0])
    S["median_sqale_hours"] = float(np.median(d2.sqale_min / 60)); S["median_hours"] = float(np.median(d2.hours))
    S["share_refactoring_in_sample"] = float(d2.summary.str.contains(REF).mean())
    res["sqale"] = S

# ---- target sensitivity
sens = {}
def refit(dtr, dva, dte, groups=B):
    for d in (dtr, dva, dte): pass
    m, cols = fit_gbm(dtr, dva, groups); m2, _ = fit_gbm(pd.concat([dtr, dva]), None, groups, rounds=max(50, m.best_iteration))
    return np.exp(m2.predict(frame(dte, cols, pd.concat([dtr, dva]))))
# (a) assignee hours only
if "hours_assignee" in df:
    da = df[df.hours_assignee > 0].copy(); da["y"] = np.log(da.hours_assignee); da["hours"] = da.hours_assignee
    da["dev_prior_n"], da["dev_prior_med"] = prior_dev(da)
    a_tr, a_va, a_te = da[da.fix_date < V0].copy(), da[(da.fix_date >= V0) & (da.fix_date < T0)].copy(), da[da.fix_date >= T0].copy()
    a_tr["text_pred"], a_va["text_pred"] = text_feature(a_tr, a_va); a_trva = pd.concat([a_tr, a_va]).copy(); a_trva["text_pred"], a_te["text_pred"] = text_feature(a_trva, a_te)
    pa = refit(a_tr, a_va, a_te)
    sens["assignee hours only"] = {"share_issues": float(len(da) / len(df)), "median_assignee_share_of_hours": float((df.hours_assignee / df.hours).median()),
                                          "M1": metrics(a_te.hours.values, pa, a_trva.hours.values),
                                          "B0": metrics(a_te.hours.values, np.full(len(a_te), a_trva.hours.median()), a_trva.hours.values)}
# (b) without issues under 15 minutes or above the 99th percentile (threshold from training)
q99 = trva.hours.quantile(0.99)
keep = lambda d: d[(d.hours >= 0.25) & (d.hours <= q99)].copy()
b_tr, b_va, b_te = keep(tr), keep(va), keep(te)
pb = refit(b_tr, b_va, b_te); yb = b_te.hours.values; ybt = pd.concat([b_tr, b_va]).hours.values
sens["without extremes (<0.25 h, >p99)"] = {"p99_threshold_h": float(q99), "M1": metrics(yb, pb, ybt), "B0": metrics(yb, np.full(len(b_te), np.median(ybt)), ybt)}
res["sensitivity"] = sens

# ---- error analysis (M1 and M0 against B0, absolute log error)
te["e_M1"] = np.abs(np.log(y) - np.log(pred[M1])); te["e_M0"] = np.abs(np.log(y) - np.log(pred[M0])); te["e_B0"] = np.abs(np.log(y) - np.log(pred["B0 median"]))
te["hours_decile"] = pd.qcut(te.hours.rank(method="first"), 10, labels=False) + 1
te["experience"] = pd.cut(te.dev_prior_n, [-1, 0, 9, 49, 1e9], labels=["0 issues", "1-9", "10-49", "50+"])
te["file"] = pd.cut(te.n_files, [0, 1, 3, 10, 1e9], labels=["1", "2-3", "4-10", ">10"])
EA = {}
for col in ["hours_decile", "type", "experience", "file"]:
    g = te.groupby(col, observed=True)
    EA[col] = {str(k): dict(n=int(len(v)), MdAE_log_M1=float(v.e_M1.median()), MdAE_log_M0=float(v.e_M0.median()), MdAE_log_B0=float(v.e_B0.median()),
                           underestimate_M1=float(np.mean(pred[M1][v.index.map(te.index.get_loc)] < v.hours)))
               for k, v in g if len(v) >= 20}
res["error_analysis"] = EA
worst = te.assign(p=pred[M1]).assign(r=lambda d: np.log(d.hours / d.p)).reindex(columns=["key", "hours", "p", "r", "type", "n_files", "summary"])
res["worst_cases"] = {"underestimates": worst.nlargest(10, "r").round(2).to_dict("records"), "overestimates": worst.nsmallest(10, "r").round(2).to_dict("records")}

# ---- feature importance and rolling origin (M1)
m2, cols, bi = models[M1]
imp = pd.Series(m2.feature_importance("gain"), index=cols); res["importance_M1"] = (imp / imp.sum()).sort_values(ascending=False).round(4).head(15).to_dict()
m2, cols, bi0 = models[M0]
imp = pd.Series(m2.feature_importance("gain"), index=cols); res["importance_M0"] = (imp / imp.sum()).sort_values(ascending=False).round(4).to_dict()
roll = {}
for Y in range(2015, 2027):
    a = df[df.year < Y].copy(); b = df[df.year == Y].copy()
    if len(a) < 1000 or len(b) < 100: continue
    a["text_pred"], b["text_pred"] = text_feature(a, b)
    out = {"n": len(b)}
    for lab, groups, r_ in [("M1", B, bi), ("M0", A, bi0)]:
        m, cols = fit_gbm(a, None, groups, rounds=max(50, r_))
        out[lab] = metrics(b.hours.values, np.exp(m.predict(frame(b, cols, a))), a.hours.values)["SA"]
    out["B0_MdAE_log"] = float(np.median(np.abs(b.y - np.median(a.y))))
    roll[Y] = out
res["rolling_origin_SA"] = roll
json.dump(res, open(f"results_{name}.json", "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
te.assign(**{k: v for k, v in pred.items()})[["key", "fix_date", "hours", "assignee", "type"] + list(pred)].to_csv(f"predictions_{name}.csv", index=False)
print(pd.DataFrame(res["test"]).T.round(3).to_string())
print(json.dumps({k: res[k] for k in ["comparisons", "split", "jira_history"]}, indent=1, default=float)[:5000])
