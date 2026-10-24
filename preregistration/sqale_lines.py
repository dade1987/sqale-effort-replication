# Debito SQALE prima e dopo il primo commit di correzione, e debito sulle sole righe modificate da quel commit.
# Per ogni issue: c1 = primo commit collegato (per data), par = suo padre.
#   prima:  tutti i file di codice toccati dalla issue, al commit par (come sqale.py: misura principale);
#   righe:  code smell di manutenibilita' sui file di c1, a par, la cui riga cade su una riga vecchia modificata da c1;
#   dopo:   i file di codice di c1, al commit c1 (debito tolto = prima - dopo sugli stessi file di c1).
# Uso: python3 sqale_lines.py <repo> <dataset_v3.jsonl.gz> <lotto> <n_lotti> <out.jsonl>   (env KEYS, CXX_MODE, PK_PREFIX, DELETE_PROJECT)
import json, gzip, subprocess, sys, os, shutil, collections, urllib.request, urllib.parse, base64, re
repo, dsf, lot, nlot, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
TOK = json.load(open("/home/user/sonar/token.json"))["token"]
SCAN = "/home/user/sonar/sonar-scanner-8.2.0.6438-linux-x64/bin/sonar-scanner"
G = lambda *a, **k: subprocess.run(["git", "-C", repo, *a], capture_output=True, **k)
CXX = os.environ.get("CXX_MODE") == "1"
CSUF = (".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".hxx", ".ic", ".inl")
def is_code(f):
    f = f.lower()
    if CXX: return f.endswith(CSUF)
    return f.endswith((".php", ".js", ".mjs")) and not f.endswith(".min.js") and "/build/" not in f and "/yui/" not in f
AUTH = {"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()}
def api(path, method="GET"):
    return json.load(urllib.request.urlopen(urllib.request.Request("http://localhost:9000" + path, method=method, headers=AUTH)))
def effort_min(s):
    if not s: return 0
    d = dict((u, int(v)) for v, u in re.findall(r"(\d+)(d|h|min)", s))
    return d.get("d", 0) * 480 + d.get("h", 0) * 60 + d.get("min", 0)

ds = [json.loads(l) for l in gzip.open(dsf, "rt")]
sel = set(open(os.environ["KEYS"]).read().split()) if os.environ.get("KEYS") else None
ds = [d for d in ds if sel is None or d["key"] in sel]
ds = [d for i, d in enumerate(ds) if i % nlot == lot]
base = f"/home/user/sqale_work/lines{lot}"; shutil.rmtree(base, ignore_errors=True)
W = {s: os.path.join(base, s) for s in ("prima", "dopo")}
for w in W.values(): os.makedirs(w)
meta = {}
def extract(commit, files, dst):
    ls = G("ls-tree", commit, "--", *files, text=True).stdout
    present = [ln.split("\t", 1)[1] for ln in ls.splitlines() if " blob " in ln]
    if present:
        os.makedirs(dst); subprocess.run(["tar", "-x", "-C", dst], input=G("archive", commit, "--", *present).stdout)
    return present
for d in ds:
    times = []
    for c in d["commits"]:
        r = G("show", "-s", "--format=%ct %P", c, text=True).stdout.split()
        if len(r) >= 2: times.append((int(r[0]), r[1], c))
    if not times: continue
    _, par, c1 = min(times)
    files = [f for f in d["files"] if is_code(f)]
    c1files = [f for f in G("show", "--no-renames", "--name-only", "--format=", c1, text=True).stdout.split("\n") if f and is_code(f)]
    m = {"union_at_parent": extract(par, files, os.path.join(W["prima"], d["key"])) if files else [], "c1_files": c1files}
    m["c1_at_c1"] = extract(c1, c1files, os.path.join(W["dopo"], d["key"])) if c1files else []
    lines = collections.defaultdict(set)   # righe vecchie (al padre) toccate da c1, per file
    for f in c1files:
        for a, b in re.findall(r"^@@ -(\d+)(?:,(\d+))? \+", G("diff", "-U0", "--no-renames", par, c1, "--", f, text=True, errors="replace").stdout, re.M):
            a, b = int(a), (1 if b == "" else int(b))
            lines[f].update(range(a, a + b) if b > 0 else [max(a, 1)])   # inserimento puro: la riga dopo cui si inserisce
    m["changed_old_lines"] = {f: sorted(v) for f, v in lines.items()}
    meta[d["key"]] = m

def scan(work, pk):
    extra = []
    if CXX:
        import glob
        from concurrent.futures import ThreadPoolExecutor
        srcs = [p for p in glob.glob(work + "/**/*", recursive=True) if p.lower().endswith(CSUF) and os.path.isfile(p)]
        def cpp(p):
            r = subprocess.run(["timeout", "60", "cppcheck", "-q", "--max-configs=1", "--enable=style,performance,portability,warning",
                                "--inline-suppr", "--language=c++", "--xml", "--xml-version=2", os.path.relpath(p, work)], cwd=work, capture_output=True, text=True, errors="replace")
            return re.findall(r"<error .*?</error>|<error [^>]*/>", r.stderr, re.S)
        with ThreadPoolExecutor(4) as ex: errs = [e for es in ex.map(cpp, srcs) for e in es]
        open(os.path.join(work, "cppcheck.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<results version="2">\n<cppcheck version="2.13.0"/>\n<errors>\n' + "\n".join(errs) + "\n</errors>\n</results>\n")
        extra = ["-Dsonar.cxx.cppcheck.reportPaths=cppcheck.xml", "-Dsonar.cxx.file.suffixes=" + ",".join(CSUF), "-Dsonar.inclusions=**/*" + ",**/*".join(CSUF)]
    r = subprocess.run([SCAN, f"-Dsonar.projectKey={pk}", "-Dsonar.sources=.", "-Dsonar.host.url=http://localhost:9000", f"-Dsonar.token={TOK}",
                        "-Dsonar.scm.disabled=true", "-Dsonar.cpd.exclusions=**/*", "-Dsonar.qualitygate.wait=true", "-Dsonar.qualitygate.timeout=7200"] + extra,
                       cwd=work, env=dict(os.environ, SONAR_SCANNER_OPTS="-Xmx3g"), capture_output=True, text=True)
    open(f"scan_{pk}.log", "w").write(r.stdout + r.stderr)
    if "QUALITY GATE STATUS" not in r.stdout + r.stderr: sys.exit("analisi SonarQube fallita: vedi scan_" + pk + ".log")
    files, p = {}, 1   # percorso "KEY/percorso" -> (chiave componente, misure)
    while True:
        j = api(f"/api/measures/component_tree?component={pk}&qualifiers=FIL&metricKeys=sqale_index,code_smells,ncloc&ps=500&p={p}")
        for c in j["components"]: files[c["path"]] = (c["key"], {x["metric"]: float(x["value"]) for x in c["measures"]})
        if p * 500 >= j["paging"]["total"]: break
        p += 1
    return files
def smells(ckey):
    res, p = [], 1
    while True:
        j = api("/api/issues/search?" + urllib.parse.urlencode({"components": ckey, "impactSoftwareQualities": "MAINTAINABILITY", "issueStatuses": "OPEN,CONFIRMED", "ps": 500, "p": p}))
        res += [(i.get("line"), effort_min(i.get("effort") or i.get("debt")), i.get("rule")) for i in j["issues"]]
        if p * 500 >= j["paging"]["total"] or p >= 20: break
        p += 1
    return res
pre = os.environ.get("PK_PREFIX", "") + ("linescxx_" if CXX else "lines_")
F = {s: (scan(W[s], pre + s + str(lot)) if any(os.scandir(W[s])) else {}) for s in W}
with open(out, "w") as f:
    for k, m in meta.items():
        get = lambda s, fs, met: sum(F[s].get(f"{k}/{x}", (None, {}))[1].get(met, 0) for x in fs)
        rec = {"key": k, "code_files_at_parent": len(m["union_at_parent"]), "sqale_min": get("prima", m["union_at_parent"], "sqale_index"),
               "ncloc": get("prima", m["union_at_parent"], "ncloc"), "c1_code_files": len(m["c1_files"]),
               "c1_files_at_parent": sum(1 for x in m["c1_files"] if f"{k}/{x}" in F["prima"]),
               "sqale_c1_prima": get("prima", m["c1_files"], "sqale_index"), "ncloc_c1_prima": get("prima", m["c1_files"], "ncloc"),
               "sqale_c1_dopo": get("dopo", m["c1_at_c1"], "sqale_index"), "ncloc_c1_dopo": get("dopo", m["c1_at_c1"], "ncloc"),
               "righe_vecchie_modificate": sum(len(v) for x, v in m["changed_old_lines"].items() if f"{k}/{x}" in F["prima"])}
        sc, n_on, eff_all = 0, 0, 0
        for x in m["c1_files"]:
            if f"{k}/{x}" not in F["prima"]: continue
            ch = set(m["changed_old_lines"].get(x, []))
            for line, eff, rule in smells(F["prima"][f"{k}/{x}"][0]):
                eff_all += eff
                if line in ch: sc += eff; n_on += 1
        rec.update({"sqale_righe_modificate": sc, "smell_su_righe_modificate": n_on, "sqale_c1_da_issues": eff_all})
        f.write(json.dumps(rec) + "\n")
shutil.rmtree(base, ignore_errors=True)
if os.environ.get("DELETE_PROJECT") == "1":
    for s in W:
        try: api(f"/api/projects/delete?project={pre + s + str(lot)}", "POST")
        except Exception: pass
print(out, len(meta), file=sys.stderr)
