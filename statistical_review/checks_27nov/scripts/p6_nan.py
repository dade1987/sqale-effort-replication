# Executes a frozen script unchanged, counting non-finite bootstrap replicates seen by np.nanpercentile / np.percentile.
import sys, runpy, numpy as np, json
log = []
for name in ("nanpercentile", "percentile"):
    orig = getattr(np, name)
    def wrap(x, *a, _o=orig, _n=name, **k):
        arr = np.asarray(x, dtype=float)
        if arr.ndim == 1 and arr.size >= 1000: log.append({"fn": _n, "n": int(arr.size), "nonfinite": int((~np.isfinite(arr)).sum())})
        return _o(x, *a, **k)
    setattr(np, name, wrap)
out = sys.argv[1]; sys.argv = sys.argv[2:]
import contextlib, io
with contextlib.redirect_stdout(io.StringIO()): runpy.run_path(sys.argv[0], run_name="__main__")
json.dump(log, open(out, "w"), indent=0); print(out, len(log), "calls;", sum(l["nonfinite"] for l in log), "non-finite replicates")
