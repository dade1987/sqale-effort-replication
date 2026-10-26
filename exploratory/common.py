# Shared metrics and paired tests, identical to those in code/model.py.
import numpy as np, pandas as pd
from scipy import stats
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

