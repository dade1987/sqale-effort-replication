# Exploratory (not preregistered): are the issues whose historical snapshot compiled different from those that did not?
# Compares year, hours, NCLOC, SQALE, files, type, developer, module, repository; reruns the frozen H1/H3 script on
# the registered measure for all attempted / compiled / not compiled issues (selection check on the registered association).
import json, sys, subprocess, numpy as np, pandas as pd
from scipy import stats
out = sys.argv[1]
B = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti"; CONF = B + "/code/confermativo_v3.py"
res = {}
def smd(a, b):
    return float((a.mean() - b.mean()) / np.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2))
for p in ("openmrs", "openlmis"):
    recs = [json.loads(l) for l in open(f"/home/user/hb/full_{p}.jsonl")]
    reg = {json.loads(l)["key"]: json.loads(l) for l in open(f"{B}/risultati/scan_{p}.jsonl")}
    f = pd.read_csv(f"/home/user/np/v3/features_v3_{p}.csv").set_index("key")
    rows = []
    for r in recs:
        k = r["key"]; ok = bool(r.get("bin")) and "error" not in r["bin"] and "error" not in r["nobin"]
        rows.append(dict(key=k, compiled=ok, build_ok=r["build_ok"], year=int(r["parent_date"][:4]), hours=f.loc[k, "hours"],
                         ncloc=reg[k]["ncloc"], sqale=reg[k]["sqale_min"], files=reg[k]["files_measured"], java_files=r["java_files_at_parent"],
                         type=f.loc[k, "type"], dev=f.loc[k, "dev"], module=f.loc[k, "module"], repo=r["repo"],
                         fail=None if ok else (r.get("build_log_tail", "") or "")[-300:]))
    d = pd.DataFrame(rows); d.to_csv(f"{out}/issues_{p}.csv", index=False)
    c, n = d[d.compiled], d[~d.compiled]
    R = {"attempted": len(d), "compiled": len(c), "not_compiled": len(n), "build_ok_but_not_measured": int((d.build_ok & ~d.compiled).sum()), "numeric": {}}
    for v in ("year", "hours", "ncloc", "sqale", "files", "java_files"):
        x, y = c[v].astype(float), n[v].astype(float)
        lx, ly = (np.log1p(x), np.log1p(y)) if v != "year" else (x, y)
        R["numeric"][v] = {"median_compiled": float(x.median()), "median_not": float(y.median()), "mean_compiled": float(x.mean()), "mean_not": float(y.mean()),
                           "smd" + ("" if v == "year" else "_log1p"): round(smd(lx, ly), 3), "mannwhitney_p": float(stats.mannwhitneyu(x, y).pvalue)}
    R["compile_rate_by_year"] = {int(y): [int(g.compiled.sum()), int(len(g))] for y, g in d.groupby("year")}
    R["compile_rate_by_type"] = {t: [int(g.compiled.sum()), int(len(g))] for t, g in d.groupby("type")}
    R["compile_rate_by_repo"] = {t: [int(g.compiled.sum()), int(len(g))] for t, g in d.groupby("repo")}
    ct = pd.crosstab(d.type, d.compiled); R["type_chi2_p"] = float(stats.chi2_contingency(ct)[1])
    for g in ("dev", "module"):
        sc, sn = set(c[g]), set(n[g])
        R[g] = {"distinct_compiled": len(sc), "distinct_not": len(sn), "distinct_all": len(sc | sn),
                "share_not_compiled_issues_whose_" + g + "_appears_among_compiled": round(float(n[g].isin(sc).mean()), 3)}
    dv = d.groupby("dev").compiled.agg(["sum", "count"]); top = dv.sort_values("count", ascending=False).head(10)
    R["dev"]["top10_compile_rate"] = [[int(a), int(b)] for a, b in zip(top["sum"], top["count"])]
    res[p] = R
    # selection check: frozen H1/H3 on the REGISTERED measure, three subsets
    for name, keys in (("all_attempted", d.key), ("compiled", c.key), ("not_compiled", n.key)):
        f.reset_index()[lambda z: z.key.isin(set(keys))].to_csv(f"{out}/feat_{p}_{name}.csv", index=False)
        with open(f"{out}/scan_{p}_{name}.jsonl", "w") as fh:
            for k in keys: fh.write(json.dumps(reg[k]) + "\n")
for name in ("all_attempted", "compiled", "not_compiled"):
    sp = [f"{p}:{out}/feat_{p}_{name}.csv:{out}/scan_{p}_{name}.jsonl" for p in ("openmrs", "openlmis")]
    subprocess.run(["python3", CONF, f"{out}/results_registered_{name}.json"] + sp, check=True, capture_output=True)
    J = json.load(open(f"{out}/results_registered_{name}.json"))
    for p in ("openmrs", "openlmis"):
        res[p].setdefault("H1_registered_measure", {})[name] = {"n": J[p]["H1"]["n"], "rho": round(J[p]["H1"]["partial_rho"], 3), "CI90_dev": [round(x, 3) for x in J[p]["H1"]["CI90"]],
            "CI90_twoway": [round(x, 3) for x in J[p]["H1_twoway_dev_module"]["CI90"]], "H3_CI90_pct_MAE": [round(x, 2) for x in J[p]["H3"]["CI90_pct_MAE"]]}
json.dump(res, open(f"{out}/summary_selection.json", "w"), indent=1); print(json.dumps(res, indent=1))
