# Preregistration 4 scan of the new Moodle sample. DO NOT RUN before the OSF registration is confirmed.
# Runs the frozen preregistration/sqale_lines.py (first registration, unchanged) in lots of 50 keys, as for the first Moodle hold-out, on the local
# SonarQube Community Build 26.9.0.129388 with the "Sonar way" profiles, and adds to every record: lot, lot_start_utc, lot_end_utc, attempt,
# sonarqube_version, scanner. If a lot fails, each of its keys is re-run once alone (the registered single retry); a key that still fails gets
# {"key", "error"}. Resumes: keys with a record are skipped.
# Usage: python3 run_v3.py <keys.txt> <out.jsonl> [first10]
import sys, os, json, subprocess, datetime, urllib.request, base64
keysf, outf = sys.argv[1], sys.argv[2]; FIRST10 = len(sys.argv) > 3 and sys.argv[3] == "first10"
S = "/home/user/sqale-effort-replication/preregistration/sqale_lines.py"
REPO, DS = "/home/user/repos/moodle", "/mnt/project-files/ricerca2/dati/moodle_ore_commit_v3.jsonl.gz"
TOK = json.load(open("/home/user/sonar/token.json"))["token"]
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
ver = urllib.request.urlopen(urllib.request.Request("http://localhost:9000/api/server/version",
      headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})).read().decode().strip()
keys = open(keysf).read().split()
if FIRST10: keys = keys[:10]
done = {json.loads(l)["key"] for l in open(outf)} if os.path.exists(outf) else set()
todo = [k for k in keys if k not in done]
def run(lot_keys, lot, attempt):
    kf, of = f"lot_{lot}_{attempt}.keys", f"lot_{lot}_{attempt}.jsonl"
    open(kf, "w").write("\n".join(lot_keys) + "\n"); t0 = now()
    r = subprocess.run(["python3", S, REPO, DS, "0", "1", of], env=dict(os.environ, KEYS=kf, PK_PREFIX=f"v4_{lot}_{attempt}_", DELETE_PROJECT="1"),
                       capture_output=True, text=True)
    open(f"lot_{lot}_{attempt}.log", "w").write(r.stdout + r.stderr); t1 = now()
    if r.returncode != 0 or not os.path.exists(of): return None
    recs = [json.loads(l) for l in open(of)]
    for x in recs: x.update({"lot": lot, "lot_start_utc": t0, "lot_end_utc": t1, "attempt": attempt, "sonarqube_version": ver, "scanner": "8.2.0.6438"})
    return recs
with open(outf, "a") as out:
    for j in range(0, len(todo), 50):
        lot_keys, lot = todo[j:j + 50], f"{j // 50:03d}"
        recs = run(lot_keys, lot, 1)
        if recs is None:
            recs = []
            for k in lot_keys:
                rk = run([k], f"{lot}_{k}", 2)
                recs += rk if rk else [{"key": k, "error": "scan failed twice", "lot": lot, "attempt": 2, "utc": now(), "sonarqube_version": ver}]
        got = {x["key"] for x in recs}
        recs += [{"key": k, "error": "no record from sqale_lines.py (no linked commit found)", "lot": lot, "utc": now(), "sonarqube_version": ver}
                 for k in lot_keys if k not in got]
        for x in recs: out.write(json.dumps(x) + "\n")
        out.flush(); print(lot, len(recs), now(), flush=True)
