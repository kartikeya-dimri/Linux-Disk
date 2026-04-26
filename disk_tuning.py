#!/usr/bin/env python3

import json

DEVICE = input("Enter disk device (e.g., sda, nvme0n1): ").strip()
FEATURE_FILE = input("Enter feature JSON path: ").strip()

with open(FEATURE_FILE) as f:
    features = json.load(f)

print("\n===== Intelligent Tuning Decision =====\n")

commands = []
reasons = []

queue = features.get("avg_queue", 0)
req_size = features.get("avg_req_size", 0)
util = features.get("avg_util", 0)
write_ratio = features.get("write_ratio", 0.0)

# -----------------------------------
# Workload Detection (IMPROVED)
# -----------------------------------
# Step 1: I/O pattern from request size
if req_size > 128:
    io_pattern = "sequential"
elif req_size < 32:
    io_pattern = "random"
else:
    io_pattern = "mixed"

# Step 2: Detect mixed read/write from write_ratio
# write_ratio > 0.15 means significant writes mixed with reads
if io_pattern != "sequential" and write_ratio > 0.15:
    workload = "mixed"
elif io_pattern == "sequential":
    workload = "sequential"
else:
    workload = "random"

print(f"Detected Workload: {workload}")
print(f"Avg Request Size: {req_size:.2f} KB")
print(f"Queue Depth: {queue:.2f}")
print(f"Write Ratio: {write_ratio:.2f}")

# -----------------------------------
# Scheduler Decision (FIXED)
# -----------------------------------
# Priority: workload type FIRST, then queue depth.
# Sequential I/O is already ordered — no benefit from
# scheduler reordering, regardless of queue depth.

if workload == "sequential":
    scheduler = "none"
    reasons.append("Sequential I/O → no reordering needed, remove scheduler overhead")

elif workload == "random":
    scheduler = "mq-deadline"
    reasons.append("Random I/O → mq-deadline improves request ordering")

elif workload == "mixed":
    scheduler = "mq-deadline"
    reasons.append("Mixed I/O → mq-deadline provides read/write fairness")

else:
    scheduler = "mq-deadline"
    reasons.append("Safe default")

commands.append(f"echo {scheduler} | sudo tee /sys/block/{DEVICE}/queue/scheduler")

# -----------------------------------
# Read-Ahead Decision (FIXED)
# -----------------------------------
# Mixed workloads need moderate read-ahead because
# they still have a read-heavy component that benefits
# from prefetching, unlike pure random.

if workload == "sequential":
    readahead = 2048
    reasons.append("Sequential workload → maximize read-ahead for prefetching")

elif workload == "mixed":
    readahead = 512
    reasons.append("Mixed workload → moderate read-ahead (reads benefit, but writes don't)")

else:
    readahead = 128
    reasons.append("Random workload → keep read-ahead low (prefetching wastes I/O)")

commands.append(f"sudo blockdev --setra {readahead} /dev/{DEVICE}")

# -----------------------------------
# OUTPUT
# -----------------------------------

print("\nSelected Scheduler:", scheduler)
print("Read-Ahead:", readahead)

print("\nReasoning:")
for r in reasons:
    print("-", r)

print("\n===== Recommended Commands =====\n")
for cmd in commands:
    print(cmd)

print("\nNOTE: Apply manually. Changes are temporary.")