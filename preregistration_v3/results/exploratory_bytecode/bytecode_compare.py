# Exploratory (5 Nov 2026): does analysing Java WITHOUT compiled classes (as in the third registration) change SQALE?
# The historical snapshots of the sample no longer build (dependencies removed from public repositories, old toolchains),
# so we compare on a current, buildable version of each repository: the same Java files are analysed twice with
# SonarQube Community Build 26.9 (Sonar way): (A) sonar.java.binaries = empty folder, as registered; (B) with the compiled
# classes and the dependency jars. As in the registered scans, test files are analysed as code (no sonar.tests).
# Usage: python3 bytecode_compare.py <module_root> <name> <out.json>   (modules must already be built: target/classes, target/deps)
import sys, os, glob, json, subprocess, urllib.request, base64, collections
root, name, out = sys.argv[1], sys.argv[2], sys.argv[3]
mods = sys.argv[4].split(",") if len(sys.argv) > 4 else None   # optional: only these module folders (those that were built)
keep = lambda p: mods is None or os.path.relpath(p, root).split("/")[0] in mods
TOK = json.load(open("/home/user/sonar/token.json"))["token"]; SCAN = "/home/user/sonar/sonar-scanner-8.2.0.6438-linux-x64/bin/sonar-scanner"
srcs = sorted(set(d for d in glob.glob(root + "/**/src/main/java", recursive=True) + glob.glob(root + "/**/src/test/java", recursive=True) if "/target/" not in d and keep(d)))
bins = sorted(set(glob.glob(root + "/**/target/classes", recursive=True) + glob.glob(root + "/**/target/test-classes", recursive=True)))
libs = sorted(set(glob.glob(root + "/**/target/deps/*.jar", recursive=True)))
os.makedirs(root + "/_empty_binaries", exist_ok=True)
rel = lambda ps: ",".join(os.path.relpath(p, root) for p in ps)
def scan(pk, extra):
    r = subprocess.run([SCAN, f"-Dsonar.projectKey={pk}", f"-Dsonar.sources={rel(srcs)}", "-Dsonar.inclusions=**/*.java", "-Dsonar.host.url=http://localhost:9000",
                        f"-Dsonar.token={TOK}", "-Dsonar.scm.disabled=true", "-Dsonar.cpd.exclusions=**/*", "-Dsonar.qualitygate.wait=true",
                        "-Dsonar.qualitygate.timeout=7200", *extra], cwd=root, env=dict(os.environ, SONAR_SCANNER_OPTS="-Xmx3g"), capture_output=True, text=True)
    open(f"{out}.{pk}.log", "w").write(r.stdout + r.stderr)
    if "QUALITY GATE STATUS" not in r.stdout + r.stderr: sys.exit("scan failed " + pk)
def api(path):
    q = urllib.request.Request("http://localhost:9000" + path, headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
    return json.load(urllib.request.urlopen(q))
def files(pk):
    res, p = {}, 1
    while True:
        j = api(f"/api/measures/component_tree?component={pk}&qualifiers=FIL&metricKeys=sqale_index,code_smells,ncloc&ps=500&p={p}")
        for c in j["components"]: res[c["path"]] = {x["metric"]: float(x["value"]) for x in c["measures"]}
        if p * 500 >= j["paging"]["total"]: break
        p += 1
    return res
def rules(pk):
    c, p = collections.Counter(), 1
    while True:
        j = api(f"/api/issues/search?componentKeys={pk}&types=CODE_SMELL&ps=500&p={p}&facets=rules")
        for f in j.get("facets", []):
            if f["property"] == "rules": return {v["val"]: v["count"] for v in f["values"]}
        break
    return dict(c)
A, B = f"bc_{name}_nobin", f"bc_{name}_bin"
scan(A, ["-Dsonar.java.binaries=_empty_binaries", "-Dsonar.exclusions=_empty_binaries/**"])
scan(B, [f"-Dsonar.java.binaries={rel(bins)}", f"-Dsonar.java.libraries={rel(libs)}", f"-Dsonar.java.test.binaries={rel(bins)}"])
fa, fb = files(A), files(B)
json.dump({"name": name, "n_source_dirs": len(srcs), "n_binary_dirs": len(bins), "n_jars": len(libs),
           "files_nobin": fa, "files_bin": fb, "rules_nobin": rules(A), "rules_bin": rules(B)}, open(out, "w"), indent=0)
print(name, len(fa), len(fb), sum(v.get("sqale_index", 0) for v in fa.values()), sum(v.get("sqale_index", 0) for v in fb.values()))
