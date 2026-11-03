# Exploratory (not preregistered), 3 Nov 2026: automatic estimate of commits the strict linking rule leaves out.
# For each sample issue, commits in its main repository (non-merge) whose subject or body mentions the key
# anywhere, but that the strict rule did not link (key not at the start, several keys, key only in the body).
import json, re, subprocess, sys, os, collections, gzip
proj, rdir, links_f, keys_f, out = sys.argv[1:6]
keys = set(open(keys_f).read().split())
L = {json.loads(l)["key"]: json.loads(l) for l in (gzip.open(links_f, "rt") if links_f.endswith(".gz") else open(links_f))}
L = {k: v for k, v in L.items() if k in keys}
rx = re.compile(r"(?<![A-Z0-9])([A-Z][A-Z0-9]+-[0-9]+)(?![0-9])")
byrepo = collections.defaultdict(set)
for k, v in L.items(): byrepo[v["repo"]].add(k)
extra = collections.defaultdict(set)
for repo, ks in byrepo.items():
    d = os.path.join(rdir, repo)
    if not os.path.isdir(d): d = os.path.join(rdir, proj + "-" + repo) if os.path.isdir(os.path.join(rdir, proj + "-" + repo)) else d
    p = subprocess.run(["git", "-C", d, "log", "--all", "--no-merges", "--format=%x1e%H%x09%s%n%b"], capture_output=True, text=True, errors="replace").stdout
    for block in p.split("\x1e")[1:]:
        h, _, rest = block.partition("\t")
        for k in set(rx.findall(rest)) & ks:
            if h not in L[k]["commits"]: extra[k].add(h)
n = len(L); m = sum(1 for k in L if extra[k])
res = {"project": proj, "issues": n, "issues_with_unlinked_mentioning_commits": m, "share": m / n,
       "unlinked_commits": sum(len(v) for v in extra.values()), "linked_commits": sum(len(v["commits"]) for v in L.values())}
json.dump({"summary": res, "per_issue": {k: sorted(v) for k, v in extra.items() if v}}, open(out, "w"), indent=1); print(res)
