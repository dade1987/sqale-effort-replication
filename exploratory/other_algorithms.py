"""Exploratory check (not preregistered): other learning algorithms on the same features, splits and target as M0/M1.
Random forest, XGBoost, CatBoost and a small neural network (MLP), against the paper's LightGBM M0/M1 and the median.
Every algorithm tried is reported. Usage: python3 other_algorithms.py <features.csv> <history.csv> <name> <predictions.csv>
environment: VALID_START, TEST_START"""
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
# Jira fields reconstructed at creation, and the developer at the start of work
df["type"] = df.type_open.fillna(df.type)
df["priority"] = df.priority_open
df["components"] = df.components_open.fillna("")
df["comp1"] = df.components.str.split("|").str[0].fillna("")
df["n_components"] = df.components.map(lambda s: len([c for c in s.split("|") if c]))
df["assignee"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace("git:", "")
df["dev_date"] = df.fix_date
# As in code/model.py. Developer, developer history and title at the start of work S (start_of_work.py): the default since the EMSE revision.
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
    """Developer history: only issues of the same assignee RESOLVED before dev_date."""
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
    """out-of-fold values (5 folds) for fit, and a model on all of fit for apply_"""
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
                A12_appaiato=float(np.mean(ea < eb) + 0.5 * np.mean(ea == eb)))
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
from sklearn.ensemble import RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
import xgboost as xgb, catboost as cb
paper = pd.read_csv(sys.argv[4]).set_index("key")
M0, M1 = [c for c in paper.columns if c.startswith("M0 at")][0], [c for c in paper.columns if c.startswith("M1 after")][0]
def X_of(d, ref, groups):
    X = design(d, ref, groups)
    if "text" in groups: X["text_pred"] = d.text_pred.values
    return X
pred = {"B0 median": np.full(len(te), np.median(ytr)), "LightGBM M0 (paper)": paper.loc[te.key, M0].values, "LightGBM M1 (paper)": paper.loc[te.key, M1].values}
for scen, groups in [("M0", A), ("M1", B)]:
    Xtr, Xva = X_of(tr, tr, groups), None
    Xva = X_of(va, tr, groups).reindex(columns=Xtr.columns, fill_value=0)
    Xf = X_of(trva, trva, groups); Xte = X_of(te, trva, groups).reindex(columns=Xf.columns, fill_value=0)
    # random forest (mean of log-hours per leaf), fixed settings
    rf = RandomForestRegressor(n_estimators=500, min_samples_leaf=20, max_features=0.5, n_jobs=4, random_state=2026).fit(Xf, trva.y)
    pred[f"Random forest {scen}"] = np.exp(rf.predict(Xte))
    # XGBoost with absolute-error loss; rounds by early stopping on validation, then refit on train+validation
    prm = dict(objective="reg:absoluteerror", learning_rate=0.03, max_depth=6, min_child_weight=40, subsample=0.8, colsample_bytree=0.8, reg_lambda=1.0, seed=2026, nthread=4)
    b = xgb.train(prm, xgb.DMatrix(Xtr, tr.y), 3000, evals=[(xgb.DMatrix(Xva, va.y), "va")], early_stopping_rounds=100, verbose_eval=False)
    b2 = xgb.train(prm, xgb.DMatrix(Xf, trva.y), max(50, b.best_iteration + 1))
    pred[f"XGBoost {scen}"] = np.exp(b2.predict(xgb.DMatrix(Xte)))
    # CatBoost with MAE loss and native categorical features
    cols = [c for g in groups for c in SET[g]]; cc = [c for c in cats if c in cols]
    prep = lambda d: d[cols].assign(**{c: d[c].fillna("").astype(str) for c in cc})
    m = cb.CatBoostRegressor(loss_function="MAE", iterations=3000, learning_rate=0.05, depth=6, random_seed=2026, verbose=False, thread_count=4, od_type="Iter", od_wait=100)
    m.fit(prep(tr), tr.y, cat_features=cc, eval_set=(prep(va), va.y))
    m2 = cb.CatBoostRegressor(loss_function="MAE", iterations=max(50, m.get_best_iteration() + 1), learning_rate=0.05, depth=6, random_seed=2026, verbose=False, thread_count=4)
    m2.fit(prep(trva), trva.y, cat_features=cc)
    pred[f"CatBoost {scen}"] = np.exp(m2.predict(prep(te)))
    # small neural network on the standardised ATLM design (squared loss on log-hours), early stopping on an internal split
    sc = StandardScaler().fit(Xf)
    nn = MLPRegressor(hidden_layer_sizes=(64, 32), alpha=1e-3, learning_rate_init=1e-3, max_iter=500, early_stopping=True, validation_fraction=0.15, random_state=2026).fit(sc.transform(Xf), trva.y)
    pred[f"Neural network {scen}"] = np.exp(nn.predict(sc.transform(Xte)))
res = {"project": name, "n_test": int(len(te)), "test": {k: metrics(y, p, ytr) for k, p in pred.items()}}
cmp = {}
for k in pred:
    for scen, ref in [("M0", "LightGBM M0 (paper)"), ("M1", "LightGBM M1 (paper)")]:
        if k.endswith(" " + scen) and not k.startswith("LightGBM"): cmp[f"{k} vs {ref}"] = compare(y, pred[k], pred[ref], grp)
res["vs_lightgbm"] = holm(cmp)
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results", "exploratory", f"other_algorithms_{name}.json"), "w"), indent=1, default=float)
print(pd.DataFrame(res["test"]).T[["MAE", "MdAE", "SA", "spearman"]].round(3).to_string())
print(pd.DataFrame(res["vs_lightgbm"]).T[["dMAE", "lo", "hi", "p_boot", "p_holm", "p_wilcoxon"]].round(3).to_string())
