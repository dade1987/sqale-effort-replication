# Per-issue features of the third registration, computed BEFORE any SQALE measurement of the sample (no SonarQube involved).
# Usage: python3 prepare_features_v3.py <issues.jsonl> <links.jsonl> <repos_dir> <out.csv> <keys_out.txt>
# developer: Jira assignee (account id); if none, the author e-mail of the earliest linked commit ("git:" prefix).
# module: main repository + the most frequent of the first two directory levels of the touched files, after dropping
# layout and namespace segments that carry no module information (STOP below).
import json, sys, os, subprocess, collections, csv, hashlib
issf, linksf, rdir, outf, keysf = sys.argv[1:6]
iss = {json.loads(l)["key"]: json.loads(l) for l in open(issf)}
STOP = {"src", "main", "java", "test", "tests", "webapp", "resources", "org", "com", "io", "net", "app", "js", "ts", "openlmis", "openmrs", "mosip"}
def strip(f):
    parts = f.split("/"); return "/".join([x for x in parts[:-1] if x.lower() not in STOP] + parts[-1:])
rows = []
for l in open(linksf):
    d = json.loads(l); i = iss[d["key"]]
    repo = d["repo"]; rp = os.path.join(rdir, repo)
    c1 = min(d["commits"], key=lambda c: subprocess.run(["git", "-C", rp, "show", "-s", "--format=%ct", c], capture_output=True, text=True).stdout.strip() or "9")
    mail = subprocess.run(["git", "-C", rp, "show", "-s", "--format=%ae", c1], capture_output=True, text=True).stdout.strip()
    a = (i.get("assignee") or {}).get("accountId")
    dev = a if a else "git:" + hashlib.sha256(mail.lower().encode()).hexdigest()[:12]
    dirs = collections.Counter("/".join(strip(f).split("/")[:2]) if "/" in strip(f) else "." for f in d["files"])
    module = repo + ":" + dirs.most_common(1)[0][0]
    comp = ((i.get("components") or [{}])[0] or {}).get("name", "?")
    rows.append({"key": d["key"], "hours": d["hours"], "resolved": d["resolved"], "created": d["created"], "dev": dev, "module": module,
                 "component": comp, "repo": repo, "type": d["type"]})
rows = [r for r in rows if r["hours"] > 0]
rows.sort(key=lambda r: r["key"])
with open(outf, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
open(keysf, "w").write("\n".join(r["key"] for r in rows) + "\n")
print(outf, len(rows), "devs", len({r["dev"] for r in rows}), "modules", len({r["module"] for r in rows}))
