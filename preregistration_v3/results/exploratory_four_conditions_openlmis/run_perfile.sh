cd /home/user/hb
for i in $(seq 1 30); do
  HB_KEYS_FROM=full_$1.jsonl python3 hist_bytecode_perfile.py $1 $2 20261105 perfile_$1.jsonl >> perfile_$1.log 2>&1 && break
  sleep 60
done
echo ALLDONE >> perfile_$1.log
