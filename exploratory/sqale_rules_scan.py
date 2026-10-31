# Rule efforts are taken from CODE_SMELL issues (types=CODE_SMELL): sqale_index sums exactly these, including code smells whose impact is SECURITY.
# Per-rule SQALE debt of the touched code files at the parent of the first fix commit (hold-out issues), for the
# exploratory analysis F. Same file set, analysers and settings as preregistration/sqale_lines.py ("prima" side only).
# Usage: python3 sqale_rules_scan.py <repo> <dataset.jsonl.gz> <lot> <n_lots> <out.jsonl>   (env KEYS, CXX_MODE, PK_PREFIX)
import json, gzip, subprocess, sys, os, shutil, collections, urllib.request, urllib.parse, base64, re
repo, dsf, lot, nlot, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
H = os.path.dirname(os.path.abspath(__file__)) + "/.."
src = open(f"{H}/preregistration/sqale_lines.py").read()
exec(src[src.index("TOK = "):src.index("ds = [json.loads")])          # TOK, SCAN, G, CXX, CSUF, is_code, AUTH, api, effort_min (frozen code)
exec(src[src.index("def extract("):src.index("for d in ds:")])            # extract
exec(src[src.index("def scan("):src.index("def smells(")])                # scan (frozen analyser settings)
ds = [json.loads(l) for l in gzip.open(dsf, "rt")]
sel = set(open(os.environ["KEYS"]).read().split())
ds = [d for d in ds if d["key"] in sel]
ds = [d for i, d in enumerate(ds) if i % nlot == lot]
done = {json.loads(l)["key"] for l in open(out)} if os.path.exists(out) else set()
ds = [d for d in ds if d["key"] not in done]
if not ds: sys.exit(0)
base = os.path.abspath(os.environ.get("WORK_DIR", "sqale_work") + f"/rules{lot}"); shutil.rmtree(base, ignore_errors=True); work = os.path.join(base, "prima"); os.makedirs(work)
meta = {}
for d in ds:
    times = []
    for c in d["commits"]:
        r = G("show", "-s", "--format=%ct %P", c, text=True).stdout.split()
        if len(r) >= 2: times.append((int(r[0]), r[1], c))
    if not times: continue
    _, par, c1 = min(times)
    files = [f for f in d["files"] if is_code(f)]
    meta[d["key"]] = extract(par, files, os.path.join(work, d["key"])) if files else []
pk = os.environ.get("PK_PREFIX", "rules_") + ("cxx_" if CXX else "") + str(lot)
F = scan(work, pk) if any(os.scandir(work)) else {}
def issues(ckey):
    res, p = [], 1
    while True:
        j = api("/api/issues/search?" + urllib.parse.urlencode({"components": ckey, "types": "CODE_SMELL", "issueStatuses": "OPEN,CONFIRMED", "ps": 500, "p": p}))
        res += [(i.get("rule"), effort_min(i.get("effort") or i.get("debt"))) for i in j["issues"]]
        if p * 500 >= j["paging"]["total"] or p >= 20: break
        p += 1
    return res
with open(out, "a") as f:
    for k, fs in meta.items():
        by_rule, n = collections.Counter(), collections.Counter()
        for x in fs:
            if f"{k}/{x}" not in F: continue
            for rule, eff in issues(F[f"{k}/{x}"][0]): by_rule[rule] += eff; n[rule] += 1
        rec = {"key": k, "code_files_at_parent": len(fs), "files_measured": sum(f"{k}/{x}" in F for x in fs),
               "sqale_min": sum(F.get(f"{k}/{x}", (None, {}))[1].get("sqale_index", 0) for x in fs),
               "ncloc": sum(F.get(f"{k}/{x}", (None, {}))[1].get("ncloc", 0) for x in fs),
               "effort_by_rule": dict(by_rule), "count_by_rule": dict(n)}
        f.write(json.dumps(rec) + "\n")
shutil.rmtree(base, ignore_errors=True)
try: api(f"/api/projects/delete?project={pk}", "POST")
except Exception: pass
