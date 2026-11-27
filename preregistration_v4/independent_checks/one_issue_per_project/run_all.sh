#!/bin/bash
chmod o+x /home/user /home/user/sonar_fresh
curl -s localhost:9000/api/system/status | grep -q '"UP"' || su claude -s /bin/bash -c "cd /home/user/sonar_fresh/sonarqube-26.9.0.129388 && bash bin/linux-x86-64/sonar.sh start"
until curl -s localhost:9000/api/system/status | grep -q '"UP"'; do sleep 5; done
cd /home/user/v4single
pids=()
for w in 0 1 2; do python3 worker.py $w 3 > worker_$w.log 2>&1 & pids+=($!); done
if [ ! -f /home/user/v4run/indep_20seeds.json ]; then
  (cd /home/user/sqale-effort-replication && python3 /mnt/project-files/ricerca2/preregistrazione_v4/verifica_indipendente/independent_v4.py . preregistration_v4/results/moodle_scan_v4.jsonl /home/user/v4run/indep_20seeds.json 5000 $(seq 101 120) > /home/user/v4run/indep_20seeds.log 2>&1) &
  pids+=($!)
fi
wait "${pids[@]}"
echo ALLDONE $(date -u) >> /home/user/v4single/status.txt
