# Analisi confermativa preregistrata (protocollo del 24/10/2026) sul campione mai analizzato (holdout).
# Uso: python3 confermativo.py <feat.csv> <storia.csv> <nome> <holdout_scan.jsonl> <sqale_vecchio.jsonl>
# H1: rho parziale (ore, SQALE file toccati | ncloc); H2: rho parziale (ore, SQALE righe modificate | righe vecchie modificate, ncloc file c1);
# H3: dMAE righe+SQALE vs solo righe, modelli stimati sulle issue pre-2023 del vecchio campione. IC 90% bootstrap a grappoli per sviluppatore.
import sys, json, numpy as np, pandas as pd
featf, stf, name, hof, oldf = sys.argv[1:6]
B, SEED, SESOI_RHO, MARGIN = 5000, 2026, 0.10, 0.02
st = pd.read_csv(stf)[["key", "assignee_T"]]
df = pd.read_csv(featf).merge(st, on="key", how="left")
df["dev"] = df.assignee_T.fillna("git:" + df.fix_author.fillna("").astype(str)).replace({"git:": "?", "": "?"})
df = df[df.hours > 0]
ho = pd.read_json(hof, lines=True).drop_duplicates("key").merge(df[["key", "hours", "dev", "fix_date"]], on="key")
old = pd.read_json(oldf, lines=True).drop_duplicates("key").merge(df[["key", "hours", "fix_date"]], on="key")
rng = np.random.default_rng(SEED)

def rank_resid(a, y, covs):
    r = a[[y] + covs].rank().values; X = np.column_stack([np.ones(len(r))] + [r[:, i + 1] for i in range(len(covs))])
    return r[:, 0] - X @ np.linalg.lstsq(X, r[:, 0], rcond=None)[0]
def partial(a, x, covs):
    e1, e2 = rank_resid(a, "hours", covs), rank_resid(a, x, covs)
    return float(np.corrcoef(e1, e2)[0, 1])
def boot_groups(a):
    g = pd.factorize(a.dev)[0]; idx = [np.where(g == i)[0] for i in range(g.max() + 1)]
    for _ in range(B):
        pick = rng.integers(0, len(idx), len(idx)); yield np.concatenate([idx[i] for i in pick])
def verdict_rho(est, lo, hi):
    if lo > SESOI_RHO: return "supportata: effetto rilevante (IC sopra 0,10)"
    if lo > -SESOI_RHO and hi < SESOI_RHO: return "trascurabile in pratica (IC dentro +-0,10)"
    if lo > 0: return "positiva ma di entita' incerta (IC sopra 0, non tutto sopra 0,10)"
    return "inconcludente"
def test_rho(a, x, covs):
    est = partial(a, x, covs); bs = np.array([partial(a.iloc[i], x, covs) for i in boot_groups(a)])
    lo, hi = np.percentile(bs, [5, 95]); p_pos = float(min(1, np.mean(bs <= 0) + 1 / B))
    return {"n": int(len(a)), "rho_parziale": est, "IC90": [float(lo), float(hi)], "p_unilaterale_rho_gt_0": p_pos, "esito": verdict_rho(est, lo, hi)}

out = {"progetto": name, "parametri": {"B": B, "seme": SEED, "SESOI_rho": SESOI_RHO, "margine_dMAE": MARGIN}}
a1 = ho[(ho.code_files_at_parent > 0) & (ho.ncloc > 0)].copy()
out["H1"] = test_rho(a1, "sqale_min", ["ncloc"])
a2 = ho[(ho.c1_files_at_parent > 0) & (ho.righe_vecchie_modificate > 0) & (ho.ncloc_c1_prima > 0)].copy()
out["H2"] = test_rho(a2, "sqale_righe_modificate", ["righe_vecchie_modificate", "ncloc_c1_prima"])
# H3
tr = old[(old.fix_date < "2023-01-01") & (old.code_files_at_parent > 0) & (old.ncloc > 0)]
X = lambda d, cols: np.column_stack([np.ones(len(d))] + [np.log1p(d[c].values) for c in cols])
P = {lab: np.exp(X(a1, cols) @ np.linalg.lstsq(X(tr, cols), np.log(tr.hours.values), rcond=None)[0]) for lab, cols in [("righe", ["ncloc"]), ("righe+SQALE", ["ncloc", "sqale_min"])]}
y = a1.hours.values; d = np.abs(y - P["righe+SQALE"]) - np.abs(y - P["righe"]); mae = float(np.mean(np.abs(y - P["righe"])))
bs = np.array([d[i].mean() for i in boot_groups(a1)]); lo, hi = np.percentile(bs, [5, 95])
v = ("SQALE aiuta in modo rilevante (IC sotto -2% del MAE)" if hi < -MARGIN * mae else
     "equivalente: nessun aiuto rilevante (IC dentro +-2% del MAE)" if lo > -MARGIN * mae and hi < MARGIN * mae else "inconcludente")
out["H3"] = {"n_train": int(len(tr)), "n_test": int(len(a1)), "MAE_solo_righe": mae, "dMAE": float(d.mean()), "IC90": [float(lo), float(hi)],
             "IC90_percento_MAE": [float(100 * lo / mae), float(100 * hi / mae)], "esito": v}
# Holm sui test rho > 0 (H1, H2) dentro il progetto; tra progetti si applica nel riepilogo
json.dump(out, open(f"confermativo_{name}.json", "w"), indent=1)
print(json.dumps(out, indent=1))
