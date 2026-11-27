import json, numpy as np, pandas as pd
from common_v4 import load, REG, ISO
out = {}
for tag, f in (("registered", REG), ("isolated", ISO)):
    g = load(f); a = g["a"]
    e1, e2 = g["rank_resid"](a, "hours", ["ncloc"]), g["rank_resid"](a, "sqale", ["ncloc"]); e1 = (e1 - e1.mean()) / e1.std(); e2 = (e2 - e2.mean()) / e2.std()
    r = float(np.mean(e1 * e2)); psi = e1 * e2 - r * (e1 ** 2 + e2 ** 2) / 2; n = len(psi)
    V = lambda gr: float(pd.Series(psi).groupby(gr).sum().pow(2).sum()) / n ** 2
    vd, vc, vi = V(a.dev.values), V(a.comp.values), V((a.dev + "|" + a.comp).values); v = vd + vc - vi
    out[tag] = {"rho": r, "V_dev": vd, "V_comp": vc, "V_intersection": vi, "V_total": v, "negative_truncated": v < 0, "se": float(np.sqrt(max(v, 0))),
                "CI90": [r - 1.645 * np.sqrt(max(v, 0)), r + 1.645 * np.sqrt(max(v, 0))], "se_dev_only": float(np.sqrt(vd)), "se_comp_only": float(np.sqrt(vc))}
json.dump(out, open("p7_cgm.json", "w"), indent=1); print(json.dumps(out, indent=1))
