import sys, os, json, subprocess, datetime, urllib.request, base64
# one SonarQube project per issue, frozen scan_v3.py unchanged
w, nw, limit, proj, rpre = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5]
P = "/home/user/sqale-effort-replication/preregistration_v3"; D = f"/home/user/audit/v3/{proj}"; os.makedirs(f"{D}/tmp", exist_ok=True)
TOK = json.load(open("/home/user/sonar/token.json"))["token"]
keys = open(f"{D}/keys.txt").read().split()
mine = [k for i, k in enumerate(keys) if i % nw == w][:limit]
out = f"{D}/single_w{w}.jsonl"
import glob
done = {json.loads(l)["key"] for p in glob.glob(f"{D}/single_w*.jsonl") for l in open(p)}
links = f"{D}/links.jsonl"
def delete(pk):
    try:
        q = urllib.request.Request("http://localhost:9000/api/projects/delete?project=" + pk, method="POST",
                                   headers={"Authorization": "Basic " + base64.b64encode((TOK + ":").encode()).decode()})
        urllib.request.urlopen(q)
    except Exception: pass
for k in mine:
    if k in done: continue
    kf, of = f"{D}/tmp/{k}.keys", f"{D}/tmp/{k}.jsonl"; open(kf, "w").write(k + "\n")
    pre = f"s_{k}_"
    for attempt in (1, 2):
        r = subprocess.run(["python3", f"{P}/code/scan_v3.py", f"/home/user/repos3/{proj}", rpre, links, kf, "0", "1", of],
                           env=dict(os.environ, SONAR_TOKEN=TOK, SONAR_SCANNER="/home/user/sonar/sonar-scanner-8.2.0.6438-linux-x64/bin/sonar-scanner",
                                    WORK_DIR=f"/home/user/sqale_work/v3_{proj}_w{w}", PK_PREFIX=pre), cwd=f"{D}/tmp", capture_output=True, text=True)
        delete(pre + "lot0")
        if r.returncode == 0 and os.path.exists(of) and os.path.getsize(of) > 0: break
    rec = json.loads(open(of).readline()) if os.path.exists(of) and os.path.getsize(of) > 0 else {"key": k, "error": r.stderr[-300:]}
    rec["utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"); rec["attempt"] = attempt
    with open(out, "a") as f: f.write(json.dumps(rec) + "\n")
    for p in (kf, of, f"{D}/tmp/scan_{pre}lot0.log"):
        try: os.remove(p)
        except OSError: pass
