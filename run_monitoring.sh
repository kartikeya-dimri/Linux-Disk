#!/bin/bash

# ==========================================
# Monitoring Wrapper (FINAL)
# ==========================================

WORKLOAD=$1
OUTPUT_DIR=$2

if [ -z "$WORKLOAD" ] || [ -z "$OUTPUT_DIR" ]; then
    echo "Usage: $0 <workload> <output_dir>"
    exit 1
fi

# Clean previous run
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR"

echo "[+] Starting monitoring..."

./disk_baseline_full.sh "$OUTPUT_DIR" &
MONITOR_PID=$!

sleep 5

echo "[+] Running workload..."
./run_workload.sh $WORKLOAD

sleep 5

kill $MONITOR_PID 2>/dev/null

echo "[+] Completed. Data in: $OUTPUT_DIR"