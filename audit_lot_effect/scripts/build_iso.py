import json, glob, sys
proj, D = sys.argv[1], sys.argv[2]
C = "/home/user/sqale-effort-replication/data/confirmatory/"
iso = {}
for p in glob.glob(f"/home/user/audit/{D}/single_w*.jsonl"):
    for l in open(p):
        r = json.loads(l)
        if "error" not in r: iso[r["key"]] = r
for name in (f"holdout_scan_{proj}.jsonl", f"exploratory_sample_scan_{proj}.jsonl"):
    n = rep = miss = 0
    with open(f"/home/user/audit/recalc/iso/{name}", "w") as f:
        for l in open(C + name):
            r = json.loads(l); n += 1
            if r["key"] in iso:
                s = iso[r["key"]]; new = dict(r)
                for k in ("sqale_min", "ncloc", "code_files_at_parent", "sqale_c1_prima", "ncloc_c1_prima", "righe_vecchie_modificate", "sqale_righe_modificate", "smell_su_righe_modificate", "c1_files_at_parent", "c1_code_files"):
                    if k in r and k in s: new[k] = s[k]
                r = new; rep += 1
            elif r.get("code_files_at_parent", 0) > 0 and "error" not in r: miss += 1
            f.write(json.dumps(r) + "\n")
    print(name, "records", n, "replaced", rep, "code>0 not rescanned", miss)
