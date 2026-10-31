#!/bin/sh
# Re-runs the official C/C++ analyser on all 862 MariaDB hold-out issues of H1, one new SonarQube Cloud project per issue, three workers.
# Set MARIADB_REPO, SONAR_SCANNER, SONAR_ORG and SONAR_TOKEN first (see official_cxx_scan.py). Then run official_cxx_full.py,
# official_cxx_compare.py and official_cxx_models.py on the fresh_w*.jsonl files.
cd "$(dirname "$0")"; K=../data/official_cxx/fresh_keys.txt
for w in 0 1 2; do python3 official_cxx_scan.py $K $w 3 fresh_w$w.jsonl > fresh_w$w.log 2>&1 & done
wait
