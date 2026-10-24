# Draws the SQALE samples for Moodle and MariaDB: 1,000 issues resolved before 2023 and 1,000 from 2023 (seed 2026).
# Usage: python3 sample_sqale.py <links.jsonl.gz> <out_keys.txt>   (Percona: all issues are analysed)
import gzip, json, random, sys
ds = [json.loads(l) for l in gzip.open(sys.argv[1], "rt")]
tr = [d["key"] for d in ds if d["resolved"] < "2023"]; te = [d["key"] for d in ds if d["resolved"] >= "2023"]
random.seed(2026); s = random.sample(tr, 1000) + random.sample(te, 1000)
open(sys.argv[2], "w").write("\n".join(s))
