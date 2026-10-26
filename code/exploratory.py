# EXPLORATORY analyses (defined after the main results; reported separately and in full, including those that do not help).
# Protocol: each variant is chosen and compared on VALIDATION; the test is computed once, for all variants together.
# Variants: E1 text embeddings (title+description), E2 past effort on the same files/component, E3 SQALE as a feature,
#           E4 average of LightGBM and ATLM (weight chosen on validation), E6 similar past issues by text.
# Usage: python3 exploratory.py <features.csv> <history.csv> <name> <sqale.jsonl> <extra_prefix>
import sys, os
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "model.py")).read()
exec(src.split("models = {}")[0])          # data, split, TF-IDF text, baselines (same code as the main model)
pref = sys.argv[5]
ex = pd.read_csv(pref + "_extra.csv")
E = np.load(pref + "_emb.npy"); ek = pd.read_csv(pref + "_emb_keys.csv").key.values; erow = {k: i for i, k in enumerate(ek)}
sq = pd.read_json(sys.argv[4], lines=True).drop_duplicates("key").set_index("key")
def add(d):
    d = d.merge(ex, on="key", how="left")
    d["sqale_h"] = d.key.map(sq.sqale_min / 60); d["sqale_density"] = d.key.map(sq.sqale_min / sq.ncloc.replace(0, np.nan))
    return d
tr, va, te, trva = [add(d) for d in (tr, va, te, trva)]
def emb_model(fit):
    m = Ridge(alpha=10.0).fit(E[[erow[k] for k in fit.key]], fit.y)
    return lambda d: m.predict(E[[erow[k] for k in d.key]])
def emb_feature(fit, app):
    oof = np.zeros(len(fit))
    for a, b in KFold(5, shuffle=True, random_state=2026).split(fit): oof[b] = emb_model(fit.iloc[a])(fit.iloc[b])
    return oof, emb_model(fit)(app)
tr["emb_pred"], va["emb_pred"] = emb_feature(tr, va); trva["emb_pred"], te["emb_pred"] = emb_feature(trva, te)
def knn_emb(fit, app, k=20, self_=False):
    from sklearn.neighbors import NearestNeighbors
    Ef = E[[erow[x] for x in fit.key]]; Ea = E[[erow[x] for x in app.key]]
    nn = NearestNeighbors(n_neighbors=k + int(self_), metric="cosine").fit(Ef)
    idx = nn.kneighbors(Ea, return_distance=False)[:, int(self_):]
    return np.median(fit.y.values[idx], axis=1)
def knn_feature(fit, app):
    oof = np.zeros(len(fit))
    for a_, b_ in KFold(5, shuffle=True, random_state=2026).split(fit): oof[b_] = knn_emb(fit.iloc[a_], fit.iloc[b_])
    return oof, knn_emb(fit, app)
tr["simili"], va["simili"] = knn_feature(tr, va); trva["simili"], te["simili"] = knn_feature(trva, te)
SET["simili"] = ["simili"];
SET["emb"] = ["emb_pred"]; SET["storia_file"] = ["file_prior_n", "file_prior_med"]; SET["storia_comp"] = ["comp_prior_n", "comp_prior_med"]
SET["sqale"] = ["sqale_h", "sqale_density"]
VAR = {"M0": A, "M0+E1 embedding": A + ["emb"], "M0+E2 component history": A + ["storia_comp"], "M0+E1+E2": A + ["emb", "storia_comp"], "M0+E6 similar issues": A + ["simili"], "M0+E1+E2+E6": A + ["emb", "storia_comp", "simili"],
       "M1": B, "M1+E1 embedding": B + ["emb"], "M1+E2 file and component history": B + ["storia_file", "storia_comp"],
       "M1+E3 SQALE": B + ["sqale"], "M1+E6 similar issues": B + ["simili"], "M1+E1+E2+E3": B + ["emb", "storia_file", "storia_comp", "sqale"], "M1+E1+E2+E3+E6": B + ["emb", "storia_file", "storia_comp", "sqale", "simili"]}
out = {"valid": {}, "test": {}}
yv, yt = va.hours.values, te.hours.values
PV, PT = {}, {}
for lab, groups in VAR.items():
    m, cols = fit_gbm(tr, va, groups); PV[lab] = np.exp(m.predict(frame(va, cols, tr)))
    m2, _ = fit_gbm(trva, None, groups, rounds=max(50, m.best_iteration)); PT[lab] = np.exp(m2.predict(frame(te, cols, trva)))
# E4: weighted geometric mean of LightGBM and ATLM, weight chosen on validation
def atlm_fit(fit, app, groups):
    Xf = design(fit, fit, groups); Xa = design(app, fit, groups).reindex(columns=Xf.columns, fill_value=0)
    return np.exp(LinearRegression().fit(Xf, fit.y).predict(Xa))
for base, groups in [("M0", A), ("M1", B), ("M1+E1+E2+E3", B + ["emb", "storia_file", "storia_comp"])]:
    av, at = atlm_fit(tr, va, groups), atlm_fit(trva, te, groups)
    w = min(np.linspace(0, 1, 11), key=lambda w: np.mean(np.abs(np.log(yv) - (w * np.log(PV[base]) + (1 - w) * np.log(av)))))
    PV[f"{base} + E4 blend with ATLM (w={w:.1f})"] = np.exp(w * np.log(PV[base]) + (1 - w) * np.log(av))
    PT[f"{base} + E4 blend with ATLM (w={w:.1f})"] = np.exp(w * np.log(PT[base]) + (1 - w) * np.log(at))
yvt = tr.hours.values
for k in PV:
    out["valid"][k] = metrics(yv, PV[k], yvt); out["test"][k] = metrics(yt, PT[k], ytr)
best0 = min([k for k in PV if k.startswith("M0")], key=lambda k: out["valid"][k]["MdAE_log"])
best1 = min([k for k in PV if k.startswith("M1")], key=lambda k: out["valid"][k]["MdAE_log"])
out["chosen_on_validation"] = {"M0": best0, "M1": best1}
out["test_comparisons"] = holm({f"{best0} vs M0": compare(yt, PT[best0], PT["M0"], grp), f"{best1} vs M1": compare(yt, PT[best1], PT["M1"], grp)})
# comparison with recalibrated SQALE on the same subset as the main model
d2 = df.join(sq[["sqale_min", "code_files_at_parent"]], on="key", how="inner"); d2 = d2[d2.code_files_at_parent > 0]
c = np.polyfit(np.log1p(d2[d2.fix_date < T0].sqale_min), d2[d2.fix_date < T0].y, 1)
mask = te.key.isin(d2.key).values & te.sqale_h.notna().values
pc = np.exp(np.polyval(c, np.log1p(te.sqale_h.values[mask] * 60)))
out["sqale_subset"] = {"n": int(mask.sum()), "SQALE recalibrated": metrics(yt[mask], pc, ytr),
                             **{k: dict(metrics(yt[mask], PT[k][mask], ytr), vs_SQALE=compare(yt[mask], PT[k][mask], pc, grp[mask])) for k in ["M0", "M1", best0, best1]}}
PT["E6 similar issues only"] = np.exp(te.simili.values); out["test"]["E6 similar issues only"] = metrics(yt, PT["E6 similar issues only"], ytr)
# classes fixed a priori: small <=4 h, medium 4-16 h, large >16 h
from sklearn.metrics import accuracy_score, f1_score, cohen_kappa_score, confusion_matrix
cl = lambda h: np.digitize(h, [4, 16], right=True)
ct = cl(yt); C = {}
maj = np.bincount(cl(ytr)).argmax()
cand = {"most frequent class": np.full(len(yt), maj), "M0": cl(PT["M0"]), "M1": cl(PT["M1"]), best0: cl(PT[best0]), best1: cl(PT[best1])}
for k, p in cand.items():
    C[k] = dict(accuracy=accuracy_score(ct, p), F1_macro=f1_score(ct, p, average="macro"), weighted_kappa=cohen_kappa_score(ct, p, weights="quadratic"),
                two_class_error=float(np.mean(np.abs(ct - p) == 2)))
C["SQALE recalibrated (subset)"] = dict(n=int(mask.sum()), accuracy=accuracy_score(ct[mask], cl(pc)), F1_macro=f1_score(ct[mask], cl(pc), average="macro"),
                                            weighted_kappa=cohen_kappa_score(ct[mask], cl(pc), weights="quadratic"))
C["most frequent class (same subset)"] = dict(accuracy=float(np.mean(ct[mask] == maj)), F1_macro=f1_score(ct[mask], np.full(mask.sum(), maj), average="macro"), weighted_kappa=0.0)
C["M0 (same subset)"] = dict(accuracy=accuracy_score(ct[mask], cl(PT["M0"][mask])), F1_macro=f1_score(ct[mask], cl(PT["M0"][mask]), average="macro"), weighted_kappa=cohen_kappa_score(ct[mask], cl(PT["M0"][mask]), weights="quadratic"))
C["M1 (same subset)"] = dict(accuracy=accuracy_score(ct[mask], cl(PT["M1"][mask])), F1_macro=f1_score(ct[mask], cl(PT["M1"][mask]), average="macro"),
                                     weighted_kappa=cohen_kappa_score(ct[mask], cl(PT["M1"][mask]), weights="quadratic"))
C["actual_shares"] = np.bincount(ct, minlength=3) / len(ct)
out["classes"] = C
# cleaning rule R1: only issues where the assignee logged at least 50% of the hours
if "hours_assignee" in df:
    keep = lambda d: d[(d.hours_assignee.fillna(0) / d.hours) >= 0.5].copy()
    r_tr, r_va, r_te = keep(tr), keep(va), keep(te)
    m, cols = fit_gbm(r_tr, r_va, B); m2, _ = fit_gbm(pd.concat([r_tr, r_va]), None, B, rounds=max(50, m.best_iteration))
    pr = np.exp(m2.predict(frame(r_te, cols, pd.concat([r_tr, r_va])))); yr = r_te.hours.values; yrt = pd.concat([r_tr, r_va]).hours.values
    out["cleaning R1 (assignee >= 50% of hours)"] = {"share_test_kept": len(r_te) / len(te), "M1": metrics(yr, pr, yrt), "B0": metrics(yr, np.full(len(yr), np.median(yrt)), yrt)}
json.dump(out, open(f"results_exploratory_{name}.json", "w"), indent=1, default=lambda o: float(o) if isinstance(o, (np.floating, np.integer)) else str(o))
print(pd.DataFrame({k: {"SA_valid": out["valid"][k]["SA"], "MdAElog_valid": out["valid"][k]["MdAE_log"], "SA_test": out["test"][k]["SA"],
                        "MAE_test": out["test"][k]["MAE"], "MdAElog_test": out["test"][k]["MdAE_log"]} for k in PV}).T.round(3).to_string())
print(json.dumps({k: out[k] for k in ["chosen_on_validation", "test_comparisons"]}, indent=1, default=float))
