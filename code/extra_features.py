# Features for the exploratory analyses (defined after the main results, reported separately).
#  - text embeddings (title + current description) with BAAI/bge-small-en-v1.5 (fastembed, ONNX, CPU)
#  - past effort on the same files: log-hours of earlier issues, RESOLVED before the first commit, that touched
#    at least one of the same files (scenario M1), and on the same component at creation (scenario M0)
# Usage: python3 extra_features.py <features.csv> <history.csv> <descriptions.jsonl> <links.jsonl.gz ...> -- <out_prefix>
import sys, json, gzip, bisect, numpy as np, pandas as pd
i = sys.argv.index("--"); feat, storia, descr = sys.argv[1:4]; dss = sys.argv[4:i]; out = sys.argv[i + 1]
df = pd.read_csv(feat).merge(pd.read_csv(storia)[["key", "summary", "components_open"]], on="key", how="left")
df = df[df.hours > 0].reset_index(drop=True)
D = {j["key"]: j["description"] for j in map(json.loads, open(descr))}
files = {}
for f in dss:
    for l in gzip.open(f, "rt"):
        j = json.loads(l)
        files.setdefault(j["key"], set()).update(x for x in j["files"] if "/vendor/" not in "/" + x)
# past effort: for each file, list of (resolved, log-hours) of the issues that touched it
y = np.log(df.hours.values)
by_file, by_comp = {}, {}
for k, r, v, c in zip(df.key, df.resolved, y, df.components_open.fillna("")):
    for x in files.get(k, ()): by_file.setdefault(x, []).append((r, v))
    c1 = c.split("|")[0]
    if c1: by_comp.setdefault(c1, []).append((r, v))
for d in (by_file, by_comp):
    for x in d: d[x].sort()
fp_n, fp_med, cp_n, cp_med = [], [], [], []
for k, T, c in zip(df.key, df.fix_date, df.components_open.fillna("")):
    past = []
    for x in files.get(k, ()):
        v = by_file.get(x, []); j = bisect.bisect_left(v, (T,)); past += [w for _, w in v[max(0, j - 20):j]]
    fp_n.append(len(past)); fp_med.append(np.median(past) if past else np.nan)
    v = by_comp.get(c.split("|")[0], []) if c else []; j = bisect.bisect_left(v, (T,)); p2 = [w for _, w in v[max(0, j - 50):j]]
    cp_n.append(j); cp_med.append(np.median(p2) if p2 else np.nan)
pd.DataFrame({"key": df.key, "file_prior_n": fp_n, "file_prior_med": fp_med, "comp_prior_n": cp_n, "comp_prior_med": cp_med,
              "descr_len": [len(D.get(k, "")) for k in df.key]}).to_csv(out + "_extra.csv", index=False)
from fastembed import TextEmbedding
m = TextEmbedding("BAAI/bge-small-en-v1.5")
txt = [(s if isinstance(s, str) else "") + "\n" + D.get(k, "")[:2000] for k, s in zip(df.key, df.summary)]
E = np.array(list(m.embed(txt, batch_size=64)), dtype=np.float32)
np.save(out + "_emb.npy", E); df[["key"]].to_csv(out + "_emb_keys.csv", index=False)
print(out, E.shape, np.mean(np.isnan(fp_med)), np.mean(np.isnan(cp_med)))
