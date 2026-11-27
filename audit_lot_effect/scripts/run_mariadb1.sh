#!/bin/bash
chmod o+x /home/user /home/user/sonar_fresh
curl -s localhost:9000/api/system/status | grep -q '"UP"' || su claude -s /bin/bash -c "cd /home/user/sonar_fresh/sonarqube-26.9.0.129388 && bash bin/linux-x86-64/sonar.sh start"
until curl -s localhost:9000/api/system/status | grep -q '"UP"'; do sleep 5; done
cd /home/user/audit
L=${1:-1000000000}
export CXX_MODE=1
pids=()
for w in 0 1; do python3 worker.py $w 2 $L /home/user/audit/mariadb1 /home/user/repos/mariadb /mnt/project-files/ricerca2/dati/mariadb_ore_commit_v3.jsonl.gz > mariadb1/worker_$w.log 2>&1 & pids+=($!); done
wait "${pids[@]}"
echo DONE $L $(date -u) >> mariadb1/status.txt
