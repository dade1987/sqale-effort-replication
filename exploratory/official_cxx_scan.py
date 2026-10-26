# Official SonarQube Cloud C/C++ analyser (CFamily) on MariaDB hold-out issues, with the real build configuration.
# Per issue: checkout parent of the first fix commit, cmake configure (compile_commands.json), generate parser/error headers,
# analyse the touched C/C++ files (headers through a translation unit that includes them), read SQALE per touched file.
# Usage: python3 official_cxx_scan.py <keys.txt> <worker> <n_workers> <out.jsonl>
# Needs: a MariaDB/server clone (MARIADB_REPO), sonar-scanner (SONAR_SCANNER), a SonarQube Cloud organisation (SONAR_ORG)
# and a token with analysis rights, passed to the scanner and the API as SONAR_TOKEN. The paper used organisation "dade1987".
import json, gzip, subprocess, sys, os, shutil, re, time, urllib.request
keysf, wk, nw, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
REPO = os.environ.get("MARIADB_REPO", "mariadb-server"); DS = f"{ROOT}/data/links/mariadb_links.jsonl.gz"
SCAN = os.environ.get("SONAR_SCANNER", "sonar-scanner")
ORG = os.environ.get("SONAR_ORG", "dade1987"); PK = f"{ORG}_mdb_cloud_w{wk}"
CSUF = (".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".hxx", ".ic", ".inl"); TU = (".c", ".cc", ".cpp", ".cxx")
WT = os.path.abspath(f"worktree_w{wk}")
G = lambda *a, cwd=REPO, **k: subprocess.run(["git", "-C", cwd, *a], capture_output=True, **k)
def api(path, method="GET", data=None):
    req = urllib.request.Request("https://sonarcloud.io" + path, method=method, data=data)
    if os.environ.get("SONAR_TOKEN"): req.add_header("Authorization", "Bearer " + os.environ["SONAR_TOKEN"])
    return json.load(urllib.request.urlopen(req, timeout=120))
try: api("/api/projects/create", "POST", f"organization={ORG}&project={PK}&name={PK}&visibility=public".encode())
except Exception: pass
keys = open(keysf).read().split(); keys = keys[wk::nw]
done = {r["key"] for r in map(json.loads, open(out)) if "error" not in r} if os.path.exists(out) else set()
ds = {d["key"]: d for d in (json.loads(l) for l in gzip.open(DS, "rt")) if d["key"] in set(keys)}
if not os.path.exists(WT): G("worktree", "add", "-f", "--detach", WT, "HEAD")
for k in keys:
    if k in done or k not in ds: continue
    t0 = time.time(); d = ds[k]; rec = {"key": k}
    times = []
    for c in d["commits"]:
        r = G("show", "-s", "--format=%ct %P", c, text=True).stdout.split()
        if len(r) >= 2: times.append((int(r[0]), r[1], c))
    par = min(times)[1]
    files = [f for f in d["files"] if f.lower().endswith(CSUF)]
    present = [ln.split("\t", 1)[1] for ln in G("ls-tree", par, "--", *files, text=True).stdout.splitlines() if " blob " in ln] if files else []
    rec["files_at_parent"] = len(present)
    if present:
        G("checkout", "-f", "--detach", par, cwd=WT); G("clean", "-fdxq", cwd=WT)
        r = subprocess.run(["cmake", "-S", ".", "-B", "bld", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DPLUGIN_ROCKSDB=NO", "-DPLUGIN_MROONGA=NO", "-DPLUGIN_SPIDER=NO",
                            "-DPLUGIN_TOKUDB=NO", "-DPLUGIN_CONNECT=NO", "-DPLUGIN_COLUMNSTORE=NO", "-DWITH_SSL=system", "-DWITH_UNIT_TESTS=OFF"], cwd=WT, capture_output=True, text=True)
        ccf = os.path.join(WT, "bld", "compile_commands.json")
        if not os.path.exists(ccf) and "SSL" in r.stdout + r.stderr:
            shutil.rmtree(os.path.join(WT, "bld"), ignore_errors=True)
            r = subprocess.run(["cmake", "-S", ".", "-B", "bld", "-DCMAKE_EXPORT_COMPILE_COMMANDS=ON", "-DPLUGIN_ROCKSDB=NO", "-DPLUGIN_MROONGA=NO", "-DPLUGIN_SPIDER=NO",
                                "-DPLUGIN_TOKUDB=NO", "-DPLUGIN_CONNECT=NO", "-DPLUGIN_COLUMNSTORE=NO", "-DWITH_SSL=bundled", "-DWITH_UNIT_TESTS=OFF"], cwd=WT, capture_output=True, text=True)
            rec["ssl"] = "bundled"
        if not os.path.exists(ccf):
            rec["error"] = "cmake: " + (r.stdout + r.stderr)[-300:]
        else:
            for tgt in ("GenError", "GenServerSource"): subprocess.run(["make", "-C", "bld", "-j2", tgt], cwd=WT, capture_output=True)
            cc = json.load(open(ccf)); byfile = {}
            for c in cc:
                rel = os.path.relpath(os.path.join(c["directory"], c["file"]), WT)
                if not rel.startswith("bld/"): byfile.setdefault(rel, c)
            sel, sources = [], set()
            for f in present:
                if f in byfile: sel.append(byfile[f]); sources.add(f)
            for h in [f for f in present if not f.lower().endswith(TU)]:
                base = os.path.basename(h); pat = re.compile(r'#\s*include\s*[<"]([^>"]*/)?' + re.escape(base) + r'[>"]')
                if any(pat.search(open(os.path.join(WT, s), errors="replace").read()) for s in sources if os.path.exists(os.path.join(WT, s))):
                    sources.add(h); continue
                cands = sorted(byfile, key=lambda s: (os.path.dirname(s) != os.path.dirname(h), len(s)))
                for s in cands:
                    try:
                        if pat.search(open(os.path.join(WT, s), errors="replace").read()): sel.append(byfile[s]); sources.add(s); sources.add(h); rec.setdefault("helper_tus", []).append(s); break
                    except OSError: pass
            rec["files_in_build"] = len([f for f in present if f in sources])
            if sel:
                json.dump(sel, open(os.path.join(WT, "cc_sel.json"), "w"))
                r = subprocess.run([SCAN, "-Dsonar.host.url=https://sonarcloud.io", f"-Dsonar.organization={ORG}", f"-Dsonar.projectKey={PK}", "-Dsonar.token=" + os.environ.get("SONAR_TOKEN", ""),
                                    "-Dsonar.sources=" + ",".join(sorted(sources)), "-Dsonar.cfamily.compile-commands=cc_sel.json", "-Dsonar.scm.disabled=true",
                                    "-Dsonar.cpd.exclusions=**/*", "-Dsonar.qualitygate.wait=true", "-Dsonar.qualitygate.timeout=1200"], cwd=WT, capture_output=True, text=True)
                log = r.stdout + r.stderr
                m = re.search(r"([\d.]+)% of statements were parsed successfully", log); rec["stmt_parsed_pct"] = float(m.group(1)) if m else None
                if "QUALITY GATE STATUS" not in log: rec["error"] = "scan: " + log[-300:]
                else:
                    meas, p = {}, 1
                    while True:
                        j = api(f"/api/measures/component_tree?component={PK}&qualifiers=FIL&metricKeys=sqale_index,code_smells,ncloc&ps=500&p={p}")
                        for c in j["components"]: meas[c["path"]] = {x["metric"]: float(x["value"]) for x in c["measures"]}
                        if p * 500 >= j["paging"]["total"]: break
                        p += 1
                    got = [f for f in present if f in meas]
                    rec.update({"files_measured": len(got), "sqale_min_official": sum(meas[f].get("sqale_index", 0) for f in got),
                                "ncloc_official": sum(meas[f].get("ncloc", 0) for f in got), "smells_official": sum(meas[f].get("code_smells", 0) for f in got),
                                "per_file": {f: meas[f] for f in got}})
    rec["seconds"] = round(time.time() - t0)
    with open(out, "a") as fo: fo.write(json.dumps(rec) + "\n")
    print(k, rec.get("files_measured"), rec.get("sqale_min_official"), rec.get("error", "")[:80], rec["seconds"], flush=True)
