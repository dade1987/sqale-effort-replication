#!/bin/bash
chmod o+x /home/user /home/user/sonar_fresh
curl -s localhost:9000/api/system/status | grep -q '"UP"' || su claude -s /bin/bash -c "cd /home/user/sonar_fresh/sonarqube-26.9.0.129388 && bash bin/linux-x86-64/sonar.sh start"
until curl -s localhost:9000/api/system/status | grep -q '"UP"'; do sleep 5; done
cd /home/user/audit
L=${1:-1000000000}
pids=()
for w in 0 1 2; do python3 worker.py $w 3 $L /home/user/audit/moodle1 /home/user/repos/moodle /mnt/project-files/ricerca2/dati/moodle_ore_commit_v3.jsonl.gz > moodle1/worker_$w.log 2>&1 & pids+=($!); done
wait "${pids[@]}"
echo DONE $L $(date -u) >> moodle1/status.txt
