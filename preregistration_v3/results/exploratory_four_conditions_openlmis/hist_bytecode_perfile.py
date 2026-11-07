# Per-file rerun (7 Nov 2026) of the compiled issues, storing per-file measures so test files can be left out afterwards.
# Derived from the exploratory pilot (5 Nov 2026, not preregistered): can the historical snapshots (parent of the earliest linked commit)
# of the third test's Java issues be compiled, and how do SQALE/NCLOC of the touched Java files change with bytecode?
# Usage: python3 hist_bytecode_pilot.py <project> <n> <seed> <out.jsonl>
import json, os, sys, re, random, subprocess, shutil, time, urllib.request, base64, glob
proj, N, seed, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
B = "/mnt/project-files/ricerca2/preregistrazione_nuovi_progetti/risultati"
links = {json.loads(l)["key"]: json.loads(l) for l in open(f"/home/user/np/data/{proj}_links.jsonl")}
feat = set(l.split(",")[0] for l in open(f"/home/user/np/v3/features_v3_{proj}.csv").read().split("\n")[1:] if l)
scan = {json.loads(l)["key"]: json.loads(l) for l in open(f"{B}/scan_{proj}.jsonl")}
RD = {"mosip": "/home/user/repos/cand/mosip", "openlmis": "/home/user/repos/cand/OpenLMIS", "openmrs": "/home/user/repos/cand/openmrs"}[proj]
SKIP = ("/node_modules/", "/vendor/", "/bower_components/", "/dist/", "/build/", "/target/")
TOK = json.load(open("/home/user/sonar/token.json"))["token"]; SCAN = "/home/user/sonar/sonar-scanner-8.2.0.6438-linux-x64/bin/sonar-scanner"
JDK = {8: "/usr/lib/jvm/java-8-openjdk-amd64", 11: "/usr/lib/jvm/java-11-openjdk-amd64", 21: "/usr/lib/jvm/java-21-openjdk-amd64"}
def jfiles(k):
    d = links[k]; return [f for f in d["files"] if f.endswith(".java") and not any(s in "/" + f for s in SKIP)]
elig = sorted(k for k in feat if k in scan and scan[k]["files_measured"] > 0 and k in links and jfiles(k)
              and os.path.isdir(os.path.join(RD, links[k]["repo"])))
if os.environ.get("HB_MIN_RESOLVED"):   # MOSIP feasibility check: random sample among issues resolved on/after a date
    import csv
    res = {r["key"]: r["resolved"] for r in csv.DictReader(open(f"/home/user/np/v3/features_v3_{proj}.csv"))}
    sample = random.Random(seed).sample([k for k in elig if res[k][:10] >= os.environ["HB_MIN_RESOLVED"]], N)
else:
    sample = [json.loads(l)["key"] for l in open(os.environ["HB_KEYS_FROM"]) if json.loads(l).get("bin") and "error" not in json.loads(l)["bin"]][:N]
print(proj, "eligible", len(elig), "sample", sample, file=sys.stderr, flush=True)
def api(path, post=False):
    q = urllib.request.Request("http://localhost:9000" + path, method="POST" if post else "GET",
                               headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
    r = urllib.request.urlopen(q); return json.load(r) if not post else None
def measure(pk, root, incl, bins, libs, empty):
    args = [SCAN, f"-Dsonar.projectKey={pk}", "-Dsonar.sources=.", "-Dsonar.host.url=http://localhost:9000", f"-Dsonar.token={TOK}",
            "-Dsonar.scm.disabled=true", "-Dsonar.cpd.exclusions=**/*", "-Dsonar.inclusions=" + ",".join(incl),
            "-Dsonar.java.binaries=" + (",".join(bins) if bins else empty), "-Dsonar.qualitygate.wait=true", "-Dsonar.qualitygate.timeout=3600"]
    if libs: args.append("-Dsonar.java.libraries=" + ",".join(libs))
    r = subprocess.run(args, cwd=root, capture_output=True, text=True, env=dict(os.environ, SONAR_SCANNER_OPTS="-Xmx3g", JAVA_HOME=JDK[21]))
    if "QUALITY GATE STATUS" not in r.stdout + r.stderr: return {"error": (r.stdout + r.stderr)[-400:]}
    tot = {"sqale_min": 0.0, "ncloc": 0.0, "files_measured": 0}; p = 1
    while True:
        j = api(f"/api/measures/component_tree?component={pk}&qualifiers=FIL&metricKeys=sqale_index,ncloc&ps=500&p={p}")
        for c in j["components"]:
            m = {x["metric"]: float(x["value"]) for x in c["measures"]}
            tot["sqale_min"] += m.get("sqale_index", 0); tot["ncloc"] += m.get("ncloc", 0); tot["files_measured"] += 1; tot.setdefault("files", []).append({"path": c["path"], "sqale_min": m.get("sqale_index", 0), "ncloc": m.get("ncloc", 0)})
        if p * 500 >= j["paging"]["total"]: break
        p += 1
    api(f"/api/projects/delete?project={pk}", post=True); return tot
def sonar_up():
    for i in range(60):
        try:
            if "UP" in urllib.request.urlopen("http://localhost:9000/api/system/status", timeout=10).read().decode(): return True
        except Exception: pass
        if i == 0:
            S = "/home/user/sonar/sonarqube-26.9.0.129388"
            subprocess.run(["rm", "-f", S + "/bin/linux-x86-64/SonarQube.pid"]); subprocess.run(["su", "sonar", "-s", "/bin/bash", "-c", S + "/bin/linux-x86-64/sonar.sh start"], cwd=S)
        time.sleep(10)
    return False
def jdk_guess(txt):
    m = re.search(r"<(?:maven\.compiler\.(?:source|release)|java\.version|source)>\s*(1\.)?(\d+)", txt)
    v = int(m.group(2)) if m else 8
    return [8 if v <= 8 else 11 if v <= 11 else 21]

def olmis_snapshots(R, date):
    # rebuild org.openlmis -SNAPSHOT libraries as they were at the parent's date and install them in mavenLocal
    txt = open(os.path.join(R, "build.gradle"), errors="ignore").read(); done_ = []
    for art, ver in set(re.findall(r"org\.openlmis:([A-Za-z0-9_-]+):([0-9.]+-SNAPSHOT)", txt)):
        rn = art.replace("openlmis-", ""); src = os.path.join("/home/user/repos/cand/OpenLMIS", rn)
        if not os.path.isdir(src): done_.append({"lib": art, "ok": False, "why": "no repo"}); continue
        c = subprocess.run(["git", "-C", src, "rev-list", "-1", "--before=" + date, "HEAD"], capture_output=True, text=True).stdout.strip()
        D = f"/home/user/hb/w/_lib_{rn}"; shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
        subprocess.run(["tar", "-x", "-C", D], input=subprocess.run(["git", "-C", src, "archive", c], capture_output=True).stdout)
        gv = re.search(r"serviceVersion=(\S+)", open(os.path.join(D, "gradle.properties"), errors="ignore").read() if os.path.exists(os.path.join(D, "gradle.properties")) else "")
        ok_ = False
        for gg in (["/opt/gradle-3.5.1/bin/gradle"], ["/opt/gradle/bin/gradle"]):
            try:
                r = subprocess.run(gg + ["-q", "--no-daemon", "-I", "/home/user/hb/gcs_init_lib.gradle", "install"], cwd=D, capture_output=True, text=True, timeout=1500,
                                   env=dict(os.environ, JAVA_HOME=JDK[8], PATH=JDK[8] + "/bin:" + os.environ["PATH"]))
                ok_ = r.returncode == 0
            except subprocess.TimeoutExpired: ok_ = False
            if ok_: break
        done_.append({"lib": art, "version": ver, "commit": c, "lib_version": gv.group(1) if gv else None, "ok": ok_}); shutil.rmtree(D, ignore_errors=True)
    return done_

def own_version(pom):
    s = re.sub(r"<parent>.*?</parent>", "", pom, flags=re.S); s = re.sub(r"<dependencies>.*", "", s, flags=re.S)
    m = re.search(r"<version>([^<$]+)</version>", s)
    if m: return m.group(1).strip()
    m = re.search(r"<parent>.*?<version>([^<]+)</version>", pom, flags=re.S); return m.group(1).strip() if m else None
def mosip_install_missing(repo, date, log, tried):
    # install an io.mosip artifact that is no longer public by building it from the same repository at the latest commit
    # (not after the parent's date) where that module declared exactly the missing version
    miss = re.findall(r"(io\.mosip[\w.]*):([\w.-]+):(?:jar|pom):([\w.-]+)", log)
    for g, a, v in miss:
        if (a, v) in tried: continue
        tried.add((a, v))
        cands = subprocess.run(["git", "-C", repo, "log", "--before=" + date, "--format=%H", "-n", "400", "--", "*pom.xml"], capture_output=True, text=True).stdout.split()
        for c in cands:
            hits = subprocess.run(["git", "-C", repo, "grep", "-l", f"<artifactId>{a}</artifactId>", c, "--", "*pom.xml"], capture_output=True, text=True).stdout.split()
            for h in hits:
                path = h.split(":", 1)[1]; pom = subprocess.run(["git", "-C", repo, "show", f"{c}:{path}"], capture_output=True, text=True).stdout
                body = re.sub(r"<parent>.*?</parent>", "", pom, flags=re.S)
                if re.search(rf"<artifactId>{re.escape(a)}</artifactId>", body.split("<dependencies>")[0]) and own_version(pom) == v:
                    D = "/home/user/hb/w/_mosiplib"; shutil.rmtree(D, ignore_errors=True); os.makedirs(D)
                    subprocess.run(["tar", "-x", "-C", D], input=subprocess.run(["git", "-C", repo, "archive", c], capture_output=True).stdout)
                    mod = os.path.dirname(path); top = mod.split("/")[0] if "/" in mod else mod
                    for jv in (8, 11):
                        r = subprocess.run(["/opt/maven/bin/mvn", "-B", "-q", "-s", "/home/user/hb/settings_central.xml", "-Dmaven.test.skip=true", "-DskipTests",
                                            "-Dmaven.javadoc.skip=true", "-Dgpg.skip", "-Dmaven.gitcommitid.skip=true", "-Denforcer.skip=true", "-Djacoco.skip=true",
                                            "install"] + (["-pl", mod, "-am"] if mod else ["-N"]), cwd=D, capture_output=True, text=True, timeout=1500,
                                           env=dict(os.environ, JAVA_HOME=JDK[jv], PATH=JDK[jv] + "/bin:" + os.environ["PATH"]))
                        if r.returncode == 0: break
                    shutil.rmtree(D, ignore_errors=True)
                    return {"artifact": f"{a}:{v}", "commit": c, "path": path, "ok": r.returncode == 0}
        return {"artifact": f"{a}:{v}", "ok": False, "why": "version not found in repository history"}
    return None
done = set()
if os.path.exists(out): done = {json.loads(l)["key"] for l in open(out)}
for k in sample:
    if k in done: continue
    if not sonar_up(): sys.exit("SonarQube down")
    d = links[k]; repo = os.path.join(RD, d["repo"]); par = scan[k]["parent"]; rec = {"key": k, "project": proj, "repo": d["repo"], "parent": par}
    W = f"/home/user/hb/w/{k}"; shutil.rmtree(W, ignore_errors=True); os.makedirs(W)
    tar = subprocess.run(["git", "-C", repo, "archive", par], capture_output=True).stdout; subprocess.run(["tar", "-x", "-C", W], input=tar)
    rec["parent_date"] = subprocess.run(["git", "-C", repo, "show", "-s", "--format=%cI", par], capture_output=True, text=True).stdout.strip()
    jf = [f for f in jfiles(k) if os.path.isfile(os.path.join(W, f))]; rec["java_files_at_parent"] = len(jf)
    # module = nearest ancestor with a build file; build root = topmost ancestor with one
    def anc(f):
        p = os.path.dirname(f); res = []
        while True:
            if any(os.path.exists(os.path.join(W, p, b)) for b in ("pom.xml", "build.gradle")): res.append(p)
            if p in ("", "/"): break
            p = os.path.dirname(p)
        return res
    mods = sorted({anc(f)[0] for f in jf if anc(f)}); roots = sorted({anc(f)[-1] for f in jf if anc(f)})
    rec["modules"] = mods; rec["build_roots"] = roots
    t0 = time.time(); ok = False; log = ""; bins = []; libs = []
    for root in roots:
        R = os.path.join(W, root)
        if os.path.exists(os.path.join(R, "pom.xml")):
            pl = ",".join(os.path.relpath(os.path.join(W, m), R) or "." for m in mods if (m + "/").startswith(root + "/" if root else ""))
            for jv in dict.fromkeys(jdk_guess(open(os.path.join(R, "pom.xml"), errors="ignore").read()) + [8, 11, 21]):
                cmd = ["/opt/maven/bin/mvn", "-B", "-q", "-s", "/home/user/hb/settings_" + ("openmrs" if proj == "openmrs" else "central") + ".xml", "-DskipTests", "-Dmaven.javadoc.skip=true", "-Dgpg.skip", "-Djacoco.skip=true",
                       "-Dmaven.gitcommitid.skip=true", "-Dcheckstyle.skip", "-Denforcer.skip=true", "-Dspotbugs.skip", "-Dlicense.skip=true",
                       "-Drat.skip=true", "-Dpmd.skip=true", "-Dfrontend.skip=true", "-Dskip.npm", "-Dskip.yarn",
                       "-U", "package", "dependency:build-classpath", "-Dmdep.outputFile=hb_cp.txt", "-Dmdep.includeScope=test"]
                if pl and pl != ".": cmd += ["-pl", pl, "-am"]
                try:
                    r = subprocess.run(cmd, cwd=R, capture_output=True, text=True, timeout=1500, env=dict(os.environ, JAVA_HOME=JDK[jv], PATH=JDK[jv] + "/bin:" + os.environ["PATH"]))
                    log = "\n".join(x for x in (r.stdout + r.stderr).splitlines() if "JAVA_TOOL_OPTIONS" not in x and ("ERROR" in x or "FAIL" in x or "rror" in x))[:3000]; ok = r.returncode == 0
                except subprocess.TimeoutExpired: log = "timeout"; ok = False
                rec.setdefault("attempts", []).append({"root": root, "jdk": jv, "ok": ok})
                if ok: rec["jdk"] = jv; break
            if not ok and proj == "mosip":
                tried = set()
                for it in range(8):
                    res = mosip_install_missing(repo, rec["parent_date"], log, tried)
                    if not res or not res["ok"]: 
                        if res: rec.setdefault("rebuilt_libs", []).append(res)
                        break
                    rec.setdefault("rebuilt_libs", []).append(res)
                    for jv in (8, 11):
                        r = subprocess.run(cmd, cwd=R, capture_output=True, text=True, timeout=1500, env=dict(os.environ, JAVA_HOME=JDK[jv], PATH=JDK[jv] + "/bin:" + os.environ["PATH"]))
                        log = "\n".join(x for x in (r.stdout + r.stderr).splitlines() if "JAVA_TOOL_OPTIONS" not in x and ("ERROR" in x or "FAIL" in x or "rror" in x))[:3000]; ok = r.returncode == 0
                        rec["attempts"].append({"root": root, "jdk": jv, "ok": ok, "after_rebuild": it + 1})
                        if ok: rec["jdk"] = jv; break
                    if ok: break
        elif os.path.exists(os.path.join(R, "build.gradle")):
            rec["olmis_libs"] = olmis_snapshots(R, rec["parent_date"]) if proj == "openlmis" else []
            init = os.path.join(W, "hb_init.gradle")
            open(init, "w").write("allprojects { afterEvaluate { p -> if (p.plugins.hasPlugin('java')) { p.tasks.create('hbCp') { doLast { new File(p.projectDir, 'hb_cp.txt').text = p.sourceSets.test.compileClasspath.files.join(':') } } } } }\n")
            gw = os.path.join(R, "gradlew"); gl = ([[gw]] if os.path.exists(gw) else []) + [["/opt/gradle-3.5.1/bin/gradle"], ["/opt/gradle-4.10.3/bin/gradle"], ["/opt/gradle-6.9.4/bin/gradle"]]
            if os.path.exists(gw): os.chmod(gw, 0o755)
            for g, jv in [(g, jv) for g in gl for jv in (8, 11)]:
                try:
                    r = subprocess.run(g + ["-q", "--no-daemon", "-I", "/home/user/hb/gcs_init.gradle", "-I", init, "compileJava", "compileTestJava", "hbCp", "-x", "test"], cwd=R, capture_output=True, text=True, timeout=1500,
                                       env=dict(os.environ, JAVA_HOME=JDK[jv], PATH=JDK[jv] + "/bin:" + os.environ["PATH"]))
                    log = "\n".join(x for x in (r.stdout + r.stderr).splitlines() if "JAVA_TOOL_OPTIONS" not in x and ("ERROR" in x or "FAIL" in x or "rror" in x))[:3000]; ok = r.returncode == 0
                except subprocess.TimeoutExpired: log = "timeout"; ok = False
                rec.setdefault("attempts", []).append({"root": root, "jdk": jv, "ok": ok, "tool": g[0]})
                if ok: rec["jdk"] = jv; break
        if not ok: break
    rec["build_ok"] = ok; rec["build_secs"] = round(time.time() - t0)
    if not ok: rec["build_log_tail"] = log[-800:]
    else:
        for m in mods:
            for sub in ("target/classes", "target/test-classes", "build/classes/java/main", "build/classes/java/test", "build/classes/main", "build/classes/test"):
                p = os.path.join(W, m, sub)
                if os.path.isdir(p): bins.append(p)
            cp = os.path.join(W, m, "hb_cp.txt")
            if os.path.exists(cp): libs += [x for x in open(cp).read().strip().split(":") if x.endswith(".jar")]
        libs = sorted(set(libs)); rec["n_bin_dirs"] = len(bins); rec["n_jars"] = len(libs)
        cls = 0
        for f in jf:
            base = os.path.basename(f)[:-5] + ".class"
            if any(glob.glob(os.path.join(b, "**", base), recursive=True) for b in bins): cls += 1
        rec["touched_with_class"] = cls
    os.makedirs(os.path.join(W, "_empty_binaries"), exist_ok=True)
    rec["registered"] = {x: scan[k][x] for x in ("sqale_min", "ncloc", "files_measured")}
    rec["nobin"] = measure(f"hb_{k}_nobin", W, jf, [], [], "_empty_binaries")
    if ok and bins: rec["bin"] = measure(f"hb_{k}_bin", W, jf, bins, libs, "_empty_binaries")
    if "error" in rec["nobin"] or ("bin" in rec and "error" in rec["bin"]):
        sys.exit("measurement failed for " + k + ": stop (record not written) " + json.dumps({"nobin": rec["nobin"].get("error", "")[-300:], "bin": (rec.get("bin") or {}).get("error", "")[-300:]}))
    open(out, "a").write(json.dumps(rec) + "\n"); print(json.dumps({x: rec.get(x) for x in ("key", "build_ok", "build_secs", "jdk", "registered", "nobin", "bin")}), file=sys.stderr, flush=True)
    shutil.rmtree(W, ignore_errors=True)
