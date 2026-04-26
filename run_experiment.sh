#!/bin/bash

WORKLOAD=$1
DEVICE="sda"

if [ -z "$WORKLOAD" ]; then
    echo "Usage: $0 {rand|seq|mix}"
    exit 1
fi

echo "===== BASELINE RUN ====="

./reset_system.sh

# BAD baseline
echo none | sudo tee /sys/block/$DEVICE/queue/scheduler > /dev/null
sudo blockdev --setra 128 /dev/$DEVICE

./run_monitoring.sh $WORKLOAD run_before

echo run_before | python3 disk_features_full.py

# Safety check
if [ ! -f "run_before/disk_features_full.json" ]; then
    echo "[ERROR] Feature extraction failed"
    exit 1
fi

echo "===== TUNING ====="

echo -e "$DEVICE\nrun_before/disk_features_full.json" | python3 disk_tuning.py

echo "Apply tuning manually and press ENTER"
read

echo "===== TUNED RUN ====="

./reset_system.sh

./run_monitoring.sh $WORKLOAD run_after

echo run_after | python3 disk_features_full.py

echo -e "run_before\nrun_after" | python3 disk_plots.py

echo "DONE"