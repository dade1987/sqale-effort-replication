# Exploratory: H1 on a proxy — for each analysed MOSIP issue of the repository, sum the CURRENT-version measures of the touched
# Java files that still exist at the same path, once without and once with bytecode; run the frozen H1 script on both.
# The proxy is not the registered measure (it uses today's files); it only shows whether adding bytecode changes the association.
import json, sys, subprocess
P = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti"
d = json.load(open(sys.argv[1])); prefix = sys.argv[2]; repo = sys.argv[3]; tag = sys.argv[4]
links = {json.loads(l)["key"]: json.loads(l) for l in open(sys.argv[5])}
an = [json.loads(l) for l in open(sys.argv[6])]
an = [x for x in an if x["files_measured"] > 0 and x["ncloc"] > 0 and links[x["key"]]["repo"] == repo]
for which in ("nobin", "bin"):
    F0 = d["files_" + which]; F = {}; rows = []
    for f, v in F0.items():
        i = f.find("/java/");  F.setdefault(f[i:] if i >= 0 else f, v)   # match by package path: modules were moved over time
    for x in an:
        fs = [f[f.find("/java/"):] for f in links[x["key"]]["files"] if f.endswith(".java") and "/java/" in f]
        fs = sorted(set(f for f in fs if f in F))
        if fs: rows.append({"key": x["key"], "sqale_min": sum(F[f].get("sqale_index", 0) for f in fs), "ncloc": sum(F[f].get("ncloc", 0) for f in fs), "files_measured": len(fs), "code_files_touched": len(fs), "code_files_at_parent": len(fs)})
    p = f"proxy_{tag}_{which}.jsonl"; open(p, "w").writelines(json.dumps(r) + "\n" for r in rows)
    subprocess.run(["python3", P + "/code/confermativo_v3.py", f"proxy_{tag}_{which}_res.json", f"{sys.argv[7]}:{sys.argv[8]}:{p}"], capture_output=True, check=True)
    r = json.load(open(f"proxy_{tag}_{which}_res.json"))[sys.argv[7]]
    print(which, len(rows), r["counts"]["analysed"], round(r["H1"]["partial_rho"], 3), [round(v, 3) for v in r["H1"]["CI90"]])
