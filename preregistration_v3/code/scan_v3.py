# SQALE debt (SonarQube Community Build 26.9, default "Sonar way" profiles, SonarSource analysers for Java, JavaScript and TypeScript)
# of the code files touched by each issue's linked commits in its main repository, at the parent of the earliest linked commit.
# Same procedure as code/sqale_scan.py of the replication package (one SonarQube project per lot; each issue is a folder <key>/
# holding its files at the parent), with Java analysed without bytecode (sonar.java.binaries = an empty folder).
# Usage: python3 scan_v3.py <repos_dir> <repo_prefix> <links.jsonl> <keys.txt> <lot> <n_lots> <out.jsonl>
# Environment: SONAR_TOKEN, SONAR_SCANNER, WORK_DIR, PK_PREFIX
import json, subprocess, sys, os, shutil, collections, urllib.request, base64
rdir, rpre, linksf, keysf, lot, nlot, out = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], int(sys.argv[5]), int(sys.argv[6]), sys.argv[7]
TOK = os.environ["SONAR_TOKEN"]; SCAN = os.environ.get("SONAR_SCANNER", "sonar-scanner")
SUF = (".java", ".js", ".jsx", ".mjs", ".ts", ".tsx")
SKIP = ("/node_modules/", "/vendor/", "/bower_components/", "/dist/", "/build/", "/target/")
def is_code(f):
    g = "/" + f.lower()
    return g.endswith(SUF) and not g.endswith((".min.js", ".bundle.js")) and not any(s in g for s in SKIP)
sel = open(keysf).read().split()
ds = {json.loads(l)["key"]: json.loads(l) for l in open(linksf)}
ds = [ds[k] for i, k in enumerate(sel) if i % nlot == lot and k in ds]
work = os.path.join(os.environ.get("WORK_DIR", "sqale_work_v3"), f"lot{lot}"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
os.makedirs(os.path.join(work, "_empty_binaries"))
meta = {}
for d in ds:
    repo = os.path.join(rdir, rpre + d["repo"] if not os.path.isdir(os.path.join(rdir, d["repo"])) else d["repo"])
    G = lambda *a, **k: subprocess.run(["git", "-C", repo, *a], capture_output=True, **k)
    times = []
    for c in d["commits"]:
        r = G("show", "-s", "--format=%ct %P", c, text=True).stdout.split()
        if len(r) >= 2: times.append((int(r[0]), r[1]))
    if not times: meta[d["key"]] = {"error": "no commit with parent"}; continue
    par = min(times)[1]
    files = [f for f in d["files"] if is_code(f)]
    present = []
    if files:
        ls = G("ls-tree", par, "--", *files, text=True).stdout
        present = [ln.split("\t", 1)[1] for ln in ls.splitlines() if " blob " in ln]
    meta[d["key"]] = {"parent": par, "code_files_touched": len(files), "code_files_at_parent": len(present)}
    if present:
        tar = G("archive", par, "--", *present).stdout
        dst = os.path.join(work, d["key"]); os.makedirs(dst); subprocess.run(["tar", "-x", "-C", dst], input=tar)
pk = os.environ.get("PK_PREFIX", "v3_") + "lot" + str(lot)
env = dict(os.environ, SONAR_SCANNER_OPTS="-Xmx3g")
r = subprocess.run([SCAN, f"-Dsonar.projectKey={pk}", "-Dsonar.sources=.", "-Dsonar.host.url=http://localhost:9000", f"-Dsonar.token={TOK}",
                    "-Dsonar.scm.disabled=true", "-Dsonar.cpd.exclusions=**/*", "-Dsonar.java.binaries=_empty_binaries", "-Dsonar.exclusions=_empty_binaries/**",
                    "-Dsonar.qualitygate.wait=true", "-Dsonar.qualitygate.timeout=7200"], cwd=work, env=env, capture_output=True, text=True)
open(f"scan_{pk}.log", "w").write(r.stdout + r.stderr)
if "QUALITY GATE STATUS" not in r.stdout + r.stderr: sys.exit("SonarQube analysis failed: see scan_" + pk + ".log")
def api(path):
    q = urllib.request.Request("http://localhost:9000" + path, headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
    return json.load(urllib.request.urlopen(q))
per = collections.defaultdict(lambda: {"sqale_min": 0, "smells": 0, "ncloc": 0, "files_measured": 0}); p = 1
while True:
    j = api(f"/api/measures/component_tree?component={pk}&qualifiers=FIL&metricKeys=sqale_index,code_smells,ncloc&ps=500&p={p}")
    for c in j["components"]:
        k = c["path"].split("/")[0]; m = {x["metric"]: float(x["value"]) for x in c["measures"]}
        per[k]["sqale_min"] += m.get("sqale_index", 0); per[k]["smells"] += m.get("code_smells", 0); per[k]["ncloc"] += m.get("ncloc", 0); per[k]["files_measured"] += 1
    if p * 500 >= j["paging"]["total"]: break
    p += 1
with open(out, "w") as f:
    for k, m in meta.items():
        f.write(json.dumps({"key": k, **m, **per.get(k, {"sqale_min": 0, "smells": 0, "ncloc": 0, "files_measured": 0})}) + "\n")
shutil.rmtree(work, ignore_errors=True)
print(out, len(meta), file=sys.stderr)
