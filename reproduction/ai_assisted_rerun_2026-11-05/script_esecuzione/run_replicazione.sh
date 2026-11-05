#!/usr/bin/env bash
set -u
ROOT=/mnt/data/riproduzione_sqale
W=$(echo "$ROOT"/lavoro/*)
C="$ROOT/consegna"
cd "$W" || exit 77
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
run_step() {
  local id="$1" name="$2" limit="$3"
  shift 3
  echo "INIZIO $id $(date -u +'%Y-%m-%dT%H:%M:%SZ') $name" | tee -a "$ROOT/progresso.txt"
  local start end ec
  start=$(date +%s)
  timeout -s TERM -k 5 "$limit" "$@" > "$C/$name.txt" 2>&1
  ec=$?
  end=$(date +%s)
  echo "$ec" > "$C/${id}_exit.txt"
  echo "FINE $id $(date -u +'%Y-%m-%dT%H:%M:%SZ') EXIT=$ec DURATA=$((end-start))s" | tee -a "$ROOT/progresso.txt"
}
run_step 05 05_test1 1000 python3.13 -u preregistration/run_confirmatory.py
run_step 06 06_test2 1000 python3.13 -u preregistration_v2/confermativo_v2.py data/features/mariadb_features.csv data/history/mariadb_history.csv preregistration_v2/newsample_keys_mariadb.txt preregistration_v2/risultati/new_scan_mariadb_v2.jsonl preregistration_v2/risultati/train_scan_mariadb_fresh.jsonl out_v2.json
cd preregistration_v3
run_step 07 07_test3 1400 python3.13 -u code/confermativo_v3.py ../out_v3.json mosip:data/features_v3_mosip.csv:scan/scan_mosip.jsonl openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl
run_step 07b 07_test3_mosip_regola_protocollo 1400 python3.13 -u code/confermativo_v3.py ../out_v3_strict.json mosip:data/features_v3_mosip.csv:results/sensitivity_strict_rerun_rule/scan_mosip_without_lots48_56.jsonl openlmis:data/features_v3_openlmis.csv:scan/scan_openlmis.jsonl openmrs:data/features_v3_openmrs.csv:scan/scan_openmrs.jsonl
cd ..
run_step 08 08_modelli 2000 sh -c 'cd code && sh run_models.sh'
cp code/log_*.txt "$C/" 2>/dev/null || true
run_step 09 09_esplorative 2000 sh exploratory/run_all.sh
run_step 10 10_collegamenti 120 python3.13 -u link_validation/manual_check/analyze_manual_check.py
run_step 11 11_confronto 120 python3.13 "$ROOT/confronta.py" "$ROOT/originale/$(basename "$W")" . \
  code/results_moodle.json=results/results_moodle.json \
  code/results_mariadb.json=results/results_mariadb.json \
  code/results_percona.json=results/results_percona.json \
  code/results_transfer.json=results/results_transfer.json \
  code/results_exploratory_moodle.json=results/results_exploratory_moodle.json \
  code/results_exploratory_mariadb.json=results/results_exploratory_mariadb.json \
  code/results_exploratory_percona.json=results/results_exploratory_percona.json \
  out_v2.json=preregistration_v2/risultati/risultati_confermativo_v2.json \
  out_v3.json=preregistration_v3/results/results_v3.json \
  out_v3_strict.json=preregistration_v3/results/sensitivity_strict_rerun_rule/results_strict.json
printf '%s\n' 'PROCEDURA_TERMINATA' >> "$ROOT/progresso.txt"
