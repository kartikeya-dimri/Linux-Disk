#!/bin/bash

WORKLOAD=$1
DEVICE="sda"

if [ -z "$WORKLOAD" ]; then
    echo "Usage: $0 {rand|seq|mix}"
    exit 1
fi

echo "=================================="
echo " CONTROLLED DISK EXPERIMENT"
echo "=================================="

# ----------------------------------
# FUNCTION: RESET SYSTEM
# ----------------------------------
reset_system() {
    echo "[+] Resetting system..."
    sudo sync
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
    sleep 5
}

# ----------------------------------
# BASELINE RUN
# ----------------------------------
echo ""
echo "===== BASELINE RUN ====="

reset_system

echo "[+] Setting baseline config..."

if [ "$WORKLOAD" == "rand" ]; then
    echo "[+] Applying BAD baseline for RANDOM workload"
    echo none | sudo tee /sys/block/$DEVICE/queue/scheduler > /dev/null
    sudo blockdev --setra 1024 /dev/$DEVICE

elif [ "$WORKLOAD" == "seq" ]; then
    echo "[+] Applying BAD baseline for SEQUENTIAL workload"
    echo none | sudo tee /sys/block/$DEVICE/queue/scheduler > /dev/null
    sudo blockdev --setra 128 /dev/$DEVICE

elif [ "$WORKLOAD" == "mix" ]; then
    echo "[+] Applying BAD baseline for MIXED workload"
    echo none | sudo tee /sys/block/$DEVICE/queue/scheduler > /dev/null
    sudo blockdev --setra 1024 /dev/$DEVICE
fi

echo "[+] Verifying baseline..."
cat /sys/block/$DEVICE/queue/scheduler
sudo blockdev --getra /dev/$DEVICE

echo "[+] Running baseline workload..."
./run_monitoring.sh $WORKLOAD run_before

echo "[+] Extracting baseline features..."
echo run_before | python3 disk_features_full.py

echo ""
echo "===== BASELINE COMPLETE ====="

# ----------------------------------
# RESET BEFORE TUNING
# ----------------------------------
echo ""
echo "[+] Resetting before tuning..."
reset_system

# ----------------------------------
# TUNING RECOMMENDATION
# ----------------------------------
echo ""
echo "===== TUNING RECOMMENDATION ====="

echo -e "$DEVICE\nrun_before/disk_features_full.json" | python3 disk_tuning.py

echo ""
echo ">>> Apply the above tuning manually"
echo ">>> Then VERIFY using:"
echo "    cat /sys/block/$DEVICE/queue/scheduler"
echo "    sudo blockdev --getra /dev/$DEVICE"
echo ""
echo "Press ENTER once tuning is applied correctly"
read

# ----------------------------------
# TUNED RUN
# ----------------------------------
echo ""
echo "===== TUNED RUN ====="

echo "[+] Running tuned workload..."
./run_monitoring.sh $WORKLOAD run_after

echo "[+] Extracting tuned features..."
echo run_after | python3 disk_features_full.py

echo ""
echo "===== TUNED RUN COMPLETE ====="

# ----------------------------------
# ANALYSIS
# ----------------------------------
echo ""
echo "===== GENERATING PLOTS ====="

echo -e "run_before\nrun_after" | python3 disk_plots.py

echo ""
echo "=================================="
echo " EXPERIMENT COMPLETE"
echo "=================================="
echo "Results:"
echo " - Baseline: run_before"
echo " - Tuned   : run_after"
echo " - Plots   : comparison_plots/"