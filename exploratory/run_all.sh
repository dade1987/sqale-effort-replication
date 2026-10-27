#!/bin/sh
# Re-runs every exploratory analysis of the EMSE paper (outputs in ../results/exploratory/).
# The official C/C++ scan itself is not re-run here (it needs a SonarQube Cloud account; see official_cxx_run.sh).
set -e
cd "$(dirname "$0")"
python3 by_issue_type.py
python3 debt_removed.py
python3 size_collinearity.py
python3 confirmatory_secondary.py
python3 official_cxx_compare.py
python3 official_cxx_models.py
python3 revision_checks.py
python3 size_classes_cutpoints.py
python3 other_quality_measures.py
for p in percona moodle mariadb; do
  if [ $p = percona ]; then export VALID_START=2020-01-01 TEST_START=2021-01-01; else export VALID_START=2021-01-01 TEST_START=2023-01-01; fi
  python3 other_algorithms.py ../data/features/${p}_features.csv ../data/history/${p}_history.csv $p ../data/predictions/${p}_predictions.csv
done
python3 figure1_partial_rho.py en
python3 figure1_partial_rho.py it
