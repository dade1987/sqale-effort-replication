# Per-issue features: set of touched files, static metrics at the parent commit,
# Git history and co-change before the fix, Jira fields, patch size.
# Usage: python3 features.py <repo> <links.jsonl.gz> <jira.jsonl> <out.csv>
import itertools, datetime, json, gzip, subprocess, sys, collections, bisect, os, csv, math, statistics as st
from multiprocessing import Pool
import lizard

repo, dsf, jiraf, out = sys.argv[1:5]
G = lambda *a: subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, errors="replace").stdout

ds = [json.loads(l) for l in gzip.open(dsf, "rt")]
if os.environ.get("LIMIT"): ds = ds[:int(os.environ["LIMIT"])]
jira = {}
for l in open(jiraf):
    d = json.loads(l); jira[d["key"]] = d

# ---- 1. linked commits: date and parent (light pass)
need_c = {c for d in ds for c in d["commits"]}
meta = {}
for ln in G("log", "--all", "--no-merges", "--format=%H %ct %ae %P").splitlines():
    p = ln.split()
    if p[0] in need_c: meta[p[0]] = (int(p[1]), p[3] if len(p) > 3 else "", p[2].lower())
recs = []
for d in ds:
    cs = [c for c in d["commits"] if c in meta]
    if not cs: continue
    c0 = min(cs, key=lambda c: meta[c][0])
    recs.append((d, cs, c0, meta[c0][0], meta[c0][1]))

# ---- 2. static metrics (lizard) on the blobs at the parent commit, cached on disk per blob
CODE = (".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".hh", ".ic", ".inl", ".php", ".js", ".mjs", ".java", ".py", ".yy", ".y")
def is_code(f):
    f = f.lower()
    return f.endswith(CODE) and not f.endswith(".min.js") and "/build/" not in f and "/yui/" not in f
def liz(arg):
    sha, path = arg
    src = subprocess.run(["git", "-C", repo, "cat-file", "blob", sha], capture_output=True).stdout
    if len(src) > 500_000: return sha, None
    txt = src.decode("utf-8", "replace")
    loc = sum(1 for l in txt.splitlines() if l.strip())
    try:
        r = lizard.analyze_file.analyze_source_code(path if not path.endswith((".yy", ".y", ".ic", ".inl")) else path + ".c", txt)
        fn = r.function_list
        return sha, (loc, r.nloc, len(fn), sum(x.cyclomatic_complexity for x in fn), max([x.cyclomatic_complexity for x in fn] or [0]), len(src))
    except Exception:
        return sha, (loc, loc, 0, 0, 0, len(src))
need = {}
blobmap = {}
for d, cs, c0, T, par in recs:
    if not par: continue
    out_ = G("ls-tree", par, "--", *d["files"]) if len(d["files"]) < 400 else ""
    m = {}
    for ln in out_.splitlines():
        mt, path = ln.split("\t", 1); t, sha = mt.split()[1:3]
        if t == "blob": m[path] = sha
        if t == "blob" and is_code(path): need[sha] = path
    blobmap[d["key"]] = m
cache = out + ".lizard.json"
stat = json.load(open(cache)) if os.path.exists(cache) else {}
todo = [(k, v) for k, v in need.items() if k not in stat]
print("blob da analizzare", len(need), "nuovi", len(todo), file=sys.stderr)
with Pool(4, maxtasksperchild=500) as pool:
    for n, (sha, v) in enumerate(pool.imap_unordered(liz, todo, chunksize=20)):
        stat[sha] = v
        if n % 5000 == 0: print("lizard", n, file=sys.stderr, flush=True)
json.dump(stat, open(cache, "w"))

# ---- 3. full history in streaming; cherry-picks deduplicated by (author, author date, subject)
pid = {}; paths = []
def P_(f):
    i = pid.get(f)
    if i is None: i = pid[f] = len(paths); paths.append(f)
    return i
proc = subprocess.Popen(["git", "-C", repo, "log", "--all", "--no-merges", "--no-renames", "--numstat", "--reverse", "--date-order",
                         "--format=%x1e%H%x09%ct%x09%at%x09%ae%x09%s"], stdout=subprocess.PIPE, text=True, errors="replace")
from array import array
needf = {f for d in ds for f in d['files']}
seen = set(); cfiles = []; fhist = collections.defaultdict(list); patch = {}; canon_of = {}
cur = None
def flush(cur):
    if cur is None: return
    h, ct, ae, k, fl = cur
    if h in need_c: patch[h] = (k, sum(a for _, a, _ in fl), sum(x for _, _, x in fl))
    if k in seen: return
    seen.add(k); i = len(cfiles)
    cfiles.append((ct, ae, array('i', [f for f, _, _ in fl])))
    for f, a, x in fl:
        if paths[f] in needf: fhist[f].append((ct, i, a + x))   # history only for the files that are needed
for ln in proc.stdout:
    if ln.startswith("\x1e"):
        flush(cur)
        p = ln[1:].rstrip("\n").split("\t", 4)
        if len(p) < 5: cur = None; continue
        h, ct, at, ae, subj = p
        cur = (h, int(ct), ae.lower(), hash((ae.lower(), at, subj)), [])
    elif cur is not None:
        q = ln.rstrip("\n").split("\t")
        if len(q) == 3:
            cur[4].append((P_(q[2]), int(q[0]) if q[0] != "-" else 0, int(q[1]) if q[1] != "-" else 0))
flush(cur)
print("commit unici", len(cfiles), "file", len(paths), "rss MB", int(open("/proc/self/statm").read().split()[1]) * 4096 // 2**20, file=sys.stderr, flush=True)
for f in fhist: fhist[f].sort()
ftimes = {f: [x[0] for x in v] for f, v in fhist.items()}
MAXCC = 50   # commits with more than 50 files (branch merges, mass renames) do not count for co-change
def prior(f, T):
    f = pid.get(f)
    if f is None: return []
    v = fhist.get(f, []); return v[:bisect.bisect_left(ftimes.get(f, []), T)]
def fix_author(c0): return meta[c0][2]

# ---- 4. per-issue features
def ag(v, f):
    return f(v) if v else 0
rows = []
for d, cs, c0, T, par in recs:
    k = d["key"]; F = d["files"]; j = jira.get(k, {})
    bm = blobmap.get(k, {})
    old = [f for f in F if f in bm]
    r = {"key": k, "hours": d["hours"], "resolved": d["resolved"][:10], "created": (j.get("created") or "")[:10],
         "fix_date": datetime.datetime.fromtimestamp(T, datetime.UTC).strftime("%Y-%m-%d"),
         "type": d["type"], "priority": (j.get("priority") or {}).get("name"),
         "components": "|".join(d["components"]), "n_components": len(d["components"]),
         "assignee": ((j.get("assignee") or {}).get("name") or (j.get("assignee") or {}).get("accountId") or ""),
         "expert_estimate_h": (j.get("timeoriginalestimate") or 0) / 3600 or None,
         "fix_author": fix_author(c0)}
    # file set
    dirs = {os.path.dirname(f) for f in F}; tops = {f.split("/")[0] for f in F}
    r.update(n_files=len(F), n_dirs=len(dirs), n_top=len(tops), n_new=len(F) - len(old),
             n_test=sum(("test" in f.lower()) for f in F), n_code=sum(is_code(f) for f in F))
    # static metrics at the parent (existing code files only)
    S = [stat[bm[f]] for f in old if is_code(f) and stat.get(bm[f])]
    r.update(st_files=len(S), st_loc_sum=sum(s[0] for s in S), st_loc_max=ag([s[0] for s in S], max),
             st_nfun_sum=sum(s[2] for s in S), st_ccn_sum=sum(s[3] for s in S), st_ccn_max=ag([s[3] for s in S], max),
             st_fccn_max=ag([s[4] for s in S], max), st_bytes_sum=sum(s[5] for s in S),
             st_ccn_density=(sum(s[3] for s in S) / max(1, sum(s[1] for s in S))))
    # history before T
    P = {f: prior(f, T) for f in F}
    ncom = [len(v) for v in P.values()]
    yr = T - 365 * 86400
    allidx = {i for v in P.values() for _, i, _ in v}
    authors = {cfiles[i][1] for i in allidx}
    own = sum(1 for i in allidx if cfiles[i][1] == r["fix_author"])
    r.update(h_commits_sum=sum(ncom), h_commits_max=ag(ncom, max), h_commits_mean=ag(ncom, st.mean),
             h_authors=len(authors), h_ownership=own / len(allidx) if allidx else 0,
             h_age_max_d=ag([(T - v[0][0]) / 86400 for v in P.values() if v], max),
             h_age_min_d=ag([(T - v[0][0]) / 86400 for v in P.values() if v], min),
             h_last_min_d=ag([(T - v[-1][0]) / 86400 for v in P.values() if v], min),
             h_commits_1y=sum(1 for v in P.values() for t, _, _ in v if t >= yr),
             h_churn_1y=sum(c for v in P.values() for t, _, c in v if t >= yr))
    # co-change before T (commits with <= MAXCC files)
    partners = {}
    for f, v in (P.items() if len(F) <= 500 else []):   # above 500 files (mass renames, imported libraries) no co-change
        cnt = collections.Counter(); fi = pid.get(f)
        n = 0
        for _, i, _ in v:
            fs = cfiles[i][2]
            if len(fs) > MAXCC: continue
            n += 1
            for g in fs:
                if g != fi: cnt[g] += 1
        partners[f] = (n, cnt)
    # note: the keys of cnt are path ids
    Fs = {pid.get(f) for f in F} - {None}
    np_ = [len(c) for n, c in partners.values()]
    strong_out = sum(1 for f, (n, c) in partners.items() for g, x in c.items() if n >= 3 and x / n >= 0.5 and g not in Fs)
    pairs = list(itertools.islice(((a, b) for ii, a in enumerate(F) for b in F[ii + 1:]), 2000))
    co = [] if len(F) > 500 else [1 if partners[a][1].get(pid.get(b), 0) > 0 else 0 for a, b in pairs]
    conf_in = [max([c.get(g, 0) / n for g in Fs if g != pid.get(f)] or [0]) for f, (n, c) in partners.items() if n > 0]
    r.update(cc_partners_sum=sum(np_), cc_partners_max=ag(np_, max), cc_strong_outside=strong_out,
             cc_pair_frac=ag(co, st.mean) if co else 0, cc_conf_in_mean=ag(conf_in, st.mean))
    # patch (known only when the work is finished)
    uc = {}   # cherry-picks on several branches count once
    for c in cs:
        if c in patch: uc[patch[c][0]] = patch[c]
    r.update(p_commits=len(uc), p_added=sum(v[1] for v in uc.values()), p_deleted=sum(v[2] for v in uc.values()))
    rows.append(r)
    if len(rows) % 500 == 0: print("issue", len(rows), "rss MB", int(open("/proc/self/statm").read().split()[1]) * 4096 // 2**20, file=sys.stderr, flush=True)
del_keys = []
with open(out, "w", newline="") as fo:
    w = csv.DictWriter(fo, [c for c in rows[0] if c not in del_keys], extrasaction="ignore"); w.writeheader(); w.writerows(rows)
print(out, len(rows), file=sys.stderr)
