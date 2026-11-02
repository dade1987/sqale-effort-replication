#!/bin/bash
# Preregistration 2 scan of the new MariaDB sample. DO NOT RUN before the OSF registration is confirmed.
# Step 1: bash run_v2.sh first10   -> 10 issues, one worker, then hand quality check (no hours).
# Step 2: bash run_v2.sh rest      -> all 1,730 keys, three workers (resumes; keys already done are skipped; failures re-run once in a new project).
cd /home/user/model/cloudcxx
[ -d /usr/include/eigen3 ] || apt-get install -y libeigen3-dev >/dev/null 2>&1 || (apt-get update >/dev/null 2>&1 && apt-get install -y libeigen3-dev >/dev/null 2>&1)
K=/mnt/project-files/ricerca2/preregistrazione_v2/newsample_keys_mariadb.txt
for w in 0 1 2; do rm -rf "/home/user/model/cloudcxx/wtv2_$w"; done
git -C /home/user/repos/mariadb worktree prune
if [ "$1" = first10 ]; then
  python3 cloud_cxx_v2.py v2_first10_keys.txt 0 1 v2_w0.jsonl >> v2_w0.log 2>&1
elif [ "$1" = rest ]; then
  for w in 0 1 2; do nohup python3 cloud_cxx_v2.py $K $w 3 v2_w$w.jsonl >> v2_w$w.log 2>&1 & done
fi
