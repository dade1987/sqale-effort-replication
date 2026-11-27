import sys, os, json, subprocess, datetime
w, nw, limit = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
D = sys.argv[4]; keys = open(f"{D}/keys.txt").read().split(); REPO, DS = sys.argv[5], sys.argv[6]
mine = [k for i, k in enumerate(keys) if i % nw == w][:limit]
out = f"{D}/single_w{w}.jsonl"
done = {json.loads(l)["key"] for l in open(out)} if os.path.exists(out) else set()
for k in mine:
    if k in done: continue
    kf, of = f"{D}/tmp/{k}.keys", f"{D}/tmp/{k}.jsonl"; os.makedirs(f"{D}/tmp", exist_ok=True)
    open(kf, "w").write(k + "\n")
    for attempt in (1, 2):
        r = subprocess.run(["python3", "/home/user/v4single/sqale_lines_single.py", REPO, DS, "0", "1", of],
                           env=dict(os.environ, KEYS=kf, PK_PREFIX=f"s_{k}_", WORKBASE=f"/home/user/sqale_work/"+os.path.basename(D)+f"_w{w}", SKIP_DOPO="1", DELETE_PROJECT="1"),
                           cwd=f"{D}/tmp", capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(of) and os.path.getsize(of) > 0: break
    rec = json.loads(open(of).readline()) if os.path.exists(of) and os.path.getsize(of) > 0 else {"key": k, "error": r.stderr[-300:]}
    rec["utc"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"); rec["attempt"] = attempt
    with open(out, "a") as f: f.write(json.dumps(rec) + "\n")
    for p in (kf, of):
        try: os.remove(p)
        except OSError: pass
