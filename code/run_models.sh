#!/bin/sh
# Re-runs the main and exploratory analyses from the distributed data (run from this folder).
D=../data
for p in moodle mariadb percona; do
  if [ $p = percona ]; then export VALID_START=2020-01-01 TEST_START=2021-01-01; else export VALID_START=2021-01-01 TEST_START=2023-01-01; fi
  python3 model.py $D/features/${p}_features.csv $D/history/${p}_history.csv $p $D/sqale/${p}_sqale.jsonl > log_$p.txt 2>&1
  python3 exploratory.py $D/features/${p}_features.csv $D/history/${p}_history.csv $p $D/sqale/${p}_sqale.jsonl $D/extra/$p > log_exploratory_$p.txt 2>&1
done
python3 transfer.py $D/ > log_transfer.txt 2>&1
