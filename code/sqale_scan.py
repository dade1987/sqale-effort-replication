# SQALE technical debt (SonarQube Community Build 26.9, "Sonar way" profile) of the touched files,
# measured at the parent of the first fix commit. One SonarQube project per batch of issues:
# each issue is a folder <key>/ holding its files at the parent commit.
# Usage: python3 sqale_scan.py <repo> <links.jsonl.gz> <batch> <n_batches> <out.jsonl>
# Environment: SONAR_TOKEN, SONAR_SCANNER (path of sonar-scanner), WORK_DIR (scratch folder), KEYS (file with sampled keys)
import json, gzip, subprocess, sys, os, shutil, collections, urllib.request, base64
repo, dsf, lot, nlot, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
TOK = os.environ["SONAR_TOKEN"]
SCAN = os.environ.get("SONAR_SCANNER", "sonar-scanner")
G = lambda *a, **k: subprocess.run(["git", "-C", repo, *a], capture_output=True, **k)
CXX = os.environ.get("CXX_MODE") == "1"   # MariaDB: sonar-cxx plugin + cppcheck report, profile "TD-CXX" (sonarqube/td_cxx_profile.xml)
MULTI = os.environ.get("MULTI_MODE") == "1"   # Percona: C/C++ (sonar-cxx + cppcheck), Go, Python, JS/TS, Java in the same project
if MULTI: CXX = True
CSUF = (".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".hxx", ".ic", ".inl")
def is_code(f):
    f = f.lower()
    if MULTI: return (f.endswith(CSUF + (".go", ".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".php")) and not f.endswith(".min.js")
                      and not f.endswith(".pb.go") and "/vendor/" not in "/" + f and "node_modules/" not in f)
    if CXX: return f.endswith(CSUF)
    return f.endswith((".php", ".js", ".mjs")) and not f.endswith(".min.js") and "/build/" not in f and "/yui/" not in f
ds = [json.loads(l) for l in gzip.open(dsf, "rt")]
sel = set(open(os.environ["KEYS"]).read().split()) if os.environ.get("KEYS") else None
ds = [d for d in ds if sel is None or d["key"] in sel]
ds = [d for i, d in enumerate(ds) if i % nlot == lot]
work = os.path.join(os.environ.get("WORK_DIR", "sqale_work"), f"lot{lot}"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
meta = {}
for d in ds:
    times = []
    for c in d["commits"]:
        r = G("show", "-s", "--format=%ct %P", c, text=True).stdout.split()
        if len(r) >= 2: times.append((int(r[0]), r[1]))
    if not times: continue
    par = min(times)[1]
    files = [f for f in d["files"] if is_code(f)]
    if not files: meta[d["key"]] = []; continue
    ls = G("ls-tree", par, "--", *files, text=True).stdout
    present = [ln.split("\t", 1)[1] for ln in ls.splitlines() if " blob " in ln]
    meta[d["key"]] = present
    if present:
        tar = G("archive", par, "--", *present).stdout
        dst = os.path.join(work, d["key"]); os.makedirs(dst)
        subprocess.run(["tar", "-x", "-C", dst], input=tar)
pk = os.environ.get("PK_PREFIX", "") + ("sqalecxx_lot" if CXX else "sqale_lot") + str(lot)
extra = []
if CXX:
    # cppcheck one file at a time with a 60 s limit (some MariaDB files block it for hours); results are merged into one XML
    import glob, re
    from concurrent.futures import ThreadPoolExecutor
    srcs = [p for p in glob.glob(work + "/**/*", recursive=True) if p.lower().endswith(CSUF) and os.path.isfile(p)]
    def cpp(p):
        try:
            r = subprocess.run(["timeout", "60", "cppcheck", "-q", "--max-configs=1", "--enable=style,performance,portability,warning",
                                "--inline-suppr", "--language=c++", "--xml", "--xml-version=2", os.path.relpath(p, work)], cwd=work, capture_output=True, text=True, errors="replace")
            return re.findall(r"<error .*?</error>|<error [^>]*/>", r.stderr, re.S), r.returncode == 124
        except Exception: return [], True
    with ThreadPoolExecutor(4) as ex: res = list(ex.map(cpp, srcs))
    errs = [e for es, _ in res for e in es]; tout = sum(t for _, t in res)
    print("cppcheck file", len(srcs), "interrotti per tempo", tout, file=sys.stderr)
    open(os.path.join(work, "cppcheck.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<results version="2">\n<cppcheck version="2.13.0"/>\n<errors>\n' + "\n".join(errs) + "\n</errors>\n</results>\n")
    meta_tout = tout
    extra = ["-Dsonar.cxx.cppcheck.reportPaths=cppcheck.xml", "-Dsonar.cxx.file.suffixes=" + ",".join(CSUF),
             "-Dsonar.inclusions=**/*" + ",**/*".join(CSUF)] if not MULTI else ["-Dsonar.cxx.cppcheck.reportPaths=cppcheck.xml", "-Dsonar.cxx.file.suffixes=" + ",".join(CSUF)]
env = dict(os.environ, SONAR_SCANNER_OPTS="-Xmx3g")
r = subprocess.run([SCAN, f"-Dsonar.projectKey={pk}", f"-Dsonar.sources=.", "-Dsonar.host.url=http://localhost:9000",
                    f"-Dsonar.token={TOK}", "-Dsonar.scm.disabled=true", "-Dsonar.cpd.exclusions=**/*",
                    "-Dsonar.qualitygate.wait=true", "-Dsonar.qualitygate.timeout=7200"] + extra, cwd=work, env=env, capture_output=True, text=True)
open(f"scan_{pk}.log", "w").write(r.stdout + r.stderr); print(r.stdout[-1500:], file=sys.stderr)
if "QUALITY GATE STATUS" not in r.stdout + r.stderr: sys.exit("analisi SonarQube fallita: vedi scan_" + pk + ".log")
def api(path):
    q = urllib.request.Request("http://localhost:9000" + path, headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
    return json.load(urllib.request.urlopen(q))
per = collections.defaultdict(lambda: {"sqale_min": 0, "smells": 0, "ncloc": 0, "files": 0})
p = 1
while True:
    j = api(f"/api/measures/component_tree?component={pk}&qualifiers=FIL&metricKeys=sqale_index,code_smells,ncloc&ps=500&p={p}")
    for c in j["components"]:
        k = c["path"].split("/")[0]; m = {x["metric"]: float(x["value"]) for x in c["measures"]}
        per[k]["sqale_min"] += m.get("sqale_index", 0); per[k]["smells"] += m.get("code_smells", 0)
        per[k]["ncloc"] += m.get("ncloc", 0); per[k]["files"] += 1
    if p * 500 >= j["paging"]["total"]: break
    p += 1
with open(out, "w") as f:
    for k, files in meta.items():
        f.write(json.dumps({"key": k, "lot_cppcheck_timeouts": globals().get("meta_tout"), "code_files_at_parent": len(files), **per.get(k, {"sqale_min": 0, "smells": 0, "ncloc": 0, "files": 0})}) + "\n")
shutil.rmtree(work, ignore_errors=True)
if os.environ.get("DELETE_PROJECT") == "1":   # frees space in the SonarQube database: the results are already in the output file
    q = urllib.request.Request(f"http://localhost:9000/api/projects/delete?project={pk}", method="POST", headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
    urllib.request.urlopen(q)
print(out, len(meta), file=sys.stderr)
