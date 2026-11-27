import json, numpy as np
from common_v4 import load, REG
g = load(REG); a = g["a"]; out = {}
for col in ("dev", "comp"):
    vc = a[col].value_counts(); hrs = a.groupby(col).hours.sum().reindex(vc.index); p = vc / vc.sum()
    out[col] = {"n_clusters": int(len(vc)), "top1_share_issues": float(p.iloc[:1].sum()), "top5_share_issues": float(p.iloc[:5].sum()), "top10_share_issues": float(p.iloc[:10].sum()),
                "top5_share_hours": float(hrs.iloc[:5].sum() / a.hours.sum()), "effective_n_clusters": float(1 / (p ** 2).sum()),
                "top5": [{"label_pseudonymised": f"{col}_{i+1}", "issues": int(vc.iloc[i]), "is_missing_label": vc.index[i] == "?"} for i in range(5)]}
    loo = []
    for i, lab in enumerate(vc.index[:5]):
        t = g["test"](a[a[col] != lab].reset_index(drop=True))
        loo.append({"left_out": f"{col}_{i+1}", "n": t["n"], "partial_rho": t["partial_rho"], "CI90": t["CI90"], "p_tost": t["p_tost"], "verdict": t["verdict"]})
    out[col]["leave_one_out"] = loo
json.dump(out, open("p3_clusters.json", "w"), indent=1)
for col in out:
    o = out[col]; print(col, o["n_clusters"], round(o["top1_share_issues"], 3), round(o["top5_share_issues"], 3), round(o["effective_n_clusters"], 1), [t["is_missing_label"] for t in o["top5"]])
    for l in o["leave_one_out"]: print("  ", l["left_out"], l["n"], round(l["partial_rho"], 4), [round(x, 4) for x in l["CI90"]], round(l["p_tost"], 4), l["verdict"][:22])
