# Percona: file paths carry the repository as prefix. For each issue we keep the main repository
# (the one with most touched files, excluding vendored code under vendor/) and keep only its files, without prefix.
import gzip, json, collections, sys
import sys
src = sys.argv[1]   # data/links/percona_links.jsonl.gz
per = collections.defaultdict(list); stat = collections.Counter()
for l in gzip.open(src, "rt"):
    d = json.loads(l)
    fs = [f for f in d["files"] if "/vendor/" not in "/" + f]
    if not fs: stat["solo_vendor"] += 1; continue
    c = collections.Counter(f.split("/", 1)[0] for f in fs)
    repo = c.most_common(1)[0][0]
    d["n_repos"] = len(c); stat["multi_repo"] += len(c) > 1
    d["files"] = [f.split("/", 1)[1] for f in fs if f.startswith(repo + "/")]
    d["repo"] = repo; per[repo].append(d)
for r, ds in per.items():
    with gzip.open(f"ds_{r}.jsonl.gz", "wt") as f:
        for d in ds: f.write(json.dumps(d) + "\n")
print({r: len(v) for r, v in sorted(per.items(), key=lambda x: -len(x[1]))}, dict(stat))
