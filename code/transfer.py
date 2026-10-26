# Cross-project transfer: train on two projects, test on the third (same test period as the within-project model).
# Only features comparable across projects: harmonised type, file set, static, history, co-change (no developer,
# no priority or components, which have different scales). Compared with the median and with the within-project model.
# Usage: python3 transfer.py <data_dir>
import json, numpy as np, pandas as pd, lightgbm as lgb
from scipy import stats
rng = np.random.default_rng(2026)
import sys
M = sys.argv[1] if len(sys.argv) > 1 else "../data/"
PROG = {"moodle": (M + "features/moodle_features.csv", M + "history/moodle_history.csv", "2021-01-01", "2023-01-01"),
        "mariadb": (M + "features/mariadb_features.csv", M + "history/mariadb_history.csv", "2021-01-01", "2023-01-01"),
        "percona": (M + "features/percona_features.csv", M + "history/percona_history.csv", "2020-01-01", "2021-01-01")}
NUM = ["n_files", "n_dirs", "n_top", "n_test", "n_code", "st_files", "st_loc_sum", "st_loc_max", "st_nfun_sum", "st_ccn_sum", "st_ccn_max",
       "st_fccn_max", "st_bytes_sum", "st_ccn_density", "h_commits_sum", "h_commits_max", "h_commits_mean", "h_authors", "h_age_max_d",
       "h_age_min_d", "h_last_min_d", "h_commits_1y", "h_churn_1y", "cc_partners_sum", "cc_partners_max", "cc_strong_outside", "cc_pair_frac", "cc_conf_in_mean"]
def tipo(t):
    t = str(t).lower()
    if "bug" in t: return "bug"
    if "feature" in t or "epic" in t or "story" in t: return "feature"
    if "improvement" in t or "enhancement" in t: return "improvement"
    return "altro"
D = {}
for p, (f, s, v0, t0) in PROG.items():
    d = pd.read_csv(f).merge(pd.read_csv(s)[["key", "type_open"]], on="key", how="left")
    d = d[d.hours > 0].copy(); d["tipo"] = pd.Categorical(d.type_open.fillna(d.type).map(tipo), ["bug", "feature", "improvement", "altro"])
    d["y"] = np.log(d.hours); d["test"] = d.fix_date >= t0; d["train_interno"] = d.fix_date < t0
    D[p] = d
P = dict(objective="l1", learning_rate=0.03, num_leaves=31, min_data_in_leaf=40, feature_fraction=0.8, bagging_fraction=0.8,
         bagging_freq=1, lambda_l2=1.0, verbose=-1, seed=2026, num_threads=4, deterministic=True)
X = lambda d: d[NUM + ["tipo"]]
def sa(y, p, yref):
    rg = np.mean([np.mean(np.abs(y - rng.choice(yref, len(y)))) for _ in range(1000)])
    return 1 - np.mean(np.abs(y - p)) / rg
def fit(tr, rounds=600):
    return lgb.train(P, lgb.Dataset(X(tr), tr.y, categorical_feature=["tipo"]), rounds)
res = {}
for tgt in D:
    te = D[tgt][D[tgt].test]; own = D[tgt][D[tgt].train_interno]
    src = pd.concat([D[p] for p in D if p != tgt])
    # number of trees chosen within the source projects: each source validates the other
    a, b = [D[p] for p in D if p != tgt]
    best = min(range(100, 1501, 100), key=lambda r: np.mean(np.abs(b.y - fit(a, r).predict(X(b)))) + np.mean(np.abs(a.y - fit(b, r).predict(X(a)))))
    y, yo = te.hours.values, own.hours.values
    pr = {"B0 project median": np.full(len(te), np.median(yo)),
          "B0 median of the other projects": np.full(len(te), np.median(src.hours)),
          "transferred (other two projects)": np.exp(fit(src, best).predict(X(te))),
          "within project (same features)": np.exp(fit(own, best).predict(X(te))),
          "transferred + project median": np.exp(fit(src, best).predict(X(te)) - np.median(src.y) + np.median(own.y))}
    res[tgt] = {"n_test": len(te), "trees": best, **{k: dict(SA=sa(y, p, yo), MAE=float(np.mean(np.abs(y - p))),
                MdAE_log=float(np.median(np.abs(np.log(y / p)))), within2x=float(np.mean(np.abs(np.log(y / p)) <= np.log(2))),
                spearman=float(stats.spearmanr(y, p)[0]) if np.std(p) > 0 else None) for k, p in pr.items()}}
    print(tgt, best); print(pd.DataFrame({k: v for k, v in res[tgt].items() if isinstance(v, dict)}).T.round(3).to_string())
json.dump(res, open("results_transfer.json", "w"), indent=1, default=float)
