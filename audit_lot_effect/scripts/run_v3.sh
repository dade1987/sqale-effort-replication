#!/bin/bash
chmod o+x /home/user /home/user/sonar_fresh
curl -s localhost:9000/api/system/status | grep -q '"UP"' || su claude -s /bin/bash -c "cd /home/user/sonar_fresh/sonarqube-26.9.0.129388 && bash bin/linux-x86-64/sonar.sh start"
until curl -s localhost:9000/api/system/status | grep -q '"UP"'; do sleep 5; done
cd /home/user/audit
pids=()
for w in 0 1 2; do
python3 worker_v3.py $w 3 1000000000 mosip "" > v3/mosip/worker_$w.log 2>&1 & pids+=($!)
python3 worker_v3.py $w 3 1000000000 openlmis "openlmis-" > v3/openlmis/worker_$w.log 2>&1 & pids+=($!)
python3 worker_v3.py $w 3 1000000000 openmrs "" > v3/openmrs/worker_$w.log 2>&1 & pids+=($!)
done
wait "${pids[@]}"
echo DONE $(date -u) >> v3/status.txt
