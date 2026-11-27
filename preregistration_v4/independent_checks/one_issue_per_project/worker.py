import sys, os, json, subprocess, datetime
w, nw, limit = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]) if len(sys.argv) > 3 else 10**9
D = "/home/user/v4single"; keys = open(f"{D}/keys_single.txt").read().split()
mine = [k for i, k in enumerate(keys) if i % nw == w][:limit]
out = f"{D}/single_w{w}.jsonl"
done = {json.loads(l)["key"] for l in open(out)} if os.path.exists(out) else set()
for k in mine:
    if k in done: continue
    kf, of = f"{D}/tmp/{k}.keys", f"{D}/tmp/{k}.jsonl"; os.makedirs(f"{D}/tmp", exist_ok=True)
    open(kf, "w").write(k + "\n")
    for attempt in (1, 2):
        r = subprocess.run(["python3", f"{D}/sqale_lines_single.py", "/home/user/repos/moodle", "/mnt/project-files/ricerca2/dati/moodle_ore_commit_v3.jsonl.gz", "0", "1", of],
                           env=dict(os.environ, KEYS=kf, PK_PREFIX=f"s_{k}_", WORKBASE=f"/home/user/sqale_work/single_w{w}", SKIP_DOPO="1", DELETE_PROJECT="1"),
                           cwd=f"{D}/tmp", capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(of) and os.path.getsize(of) > 0: break
    rec = json.loads(open(of).readline()) if os.path.exists(of) and os.path.getsize(of) > 0 else {"key": k, "error": r.stderr[-300:]}
    rec["utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"); rec["attempt"] = attempt
    with open(out, "a") as f: f.write(json.dumps(rec) + "\n")
    for p in (kf, of):
        try: os.remove(p)
        except OSError: pass
