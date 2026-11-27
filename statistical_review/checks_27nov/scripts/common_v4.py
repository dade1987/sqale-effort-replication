# Loads the frozen fourth-registration script up to its analyses, unchanged, so data preparation is identical.
import sys
R = "/home/user/sqale-effort-replication"
def load(scan):
    src = open(f"{R}/preregistration_v4/confermativo_v4.py").read().split("# ---------- primary ----------")[0]
    g = {"__name__": "frozen"}; old = sys.argv; sys.argv = ["x", R, scan, "/dev/null"]
    try: exec(src, g)
    finally: sys.argv = old
    return g
REG = f"{R}/preregistration_v4/results/moodle_scan_v4.jsonl"
ISO = f"{R}/preregistration_v4/independent_checks/one_issue_per_project/single_all.jsonl"
