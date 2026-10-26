#!/bin/sh
# Re-runs the official C/C++ analyser on the 200 sampled MariaDB hold-out issues, with two workers.
# Set MARIADB_REPO, SONAR_SCANNER, SONAR_ORG and SONAR_TOKEN first (see official_cxx_scan.py).
cd "$(dirname "$0")"; K=../data/official_cxx/sample200_keys.txt
for w in 0 1; do python3 official_cxx_scan.py $K $w 2 cloud_w$w.jsonl > cloud_w$w.log 2>&1 & done
wait
