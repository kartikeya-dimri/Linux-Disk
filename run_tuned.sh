#!/bin/bash

WORKLOAD=$1
OUTDIR="run_after"

if [ -z "$WORKLOAD" ]; then
    echo "Usage: $0 {rand|seq|mix}"
    exit 1
fi

echo "=================================="
echo " TUNED RUN"
echo "=================================="

./reset_system.sh

echo "[+] Generating tuning recommendation..."

echo -e "sda\nrun_before/disk_features_full.json" | python3 disk_tuning.py

echo ""
echo ">>> Apply the above tuning manually, then press ENTER"
read

echo "[+] Running tuned experiment..."

./run_monitoring.sh $WORKLOAD $OUTDIR

echo "[+] Extracting features..."
echo $OUTDIR | python3 disk_features_full.py

echo "=================================="
echo " Tuned run completed: $OUTDIR"
echo "=================================="