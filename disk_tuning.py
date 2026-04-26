#!/usr/bin/env python3

import json

DEVICE = input("Enter disk device (e.g., sda, nvme0n1): ").strip()
FEATURE_FILE = input("Enter feature JSON path: ").strip()

with open(FEATURE_FILE) as f:
    features = json.load(f)

print("\n===== Tuning Decision =====\n")

commands = []
reasons = []

queue = features.get("avg_queue", 0)
req_size = features.get("avg_req_size", 0)
psi = features.get("psi_some_avg10", 0)

# -----------------------------------
# Workload Detection (Simple)
# -----------------------------------

if req_size > 128:
    workload = "sequential"
elif req_size < 32:
    workload = "random"
else:
    workload = "mixed"

print(f"Detected Workload: {workload}")
print(f"Avg Request Size: {req_size:.2f} KB")
print(f"Queue Depth: {queue:.2f}")

# -----------------------------------
# Scheduler Decision (Simple & Stable)
# -----------------------------------

if queue > 50:
    scheduler = "mq-deadline"
    reasons.append("High queue depth → scheduling needed")
else:
    scheduler = "none"
    reasons.append("Low queue → minimize scheduler overhead")

commands.append(f"echo {scheduler} | sudo tee /sys/block/{DEVICE}/queue/scheduler")

# -----------------------------------
# Read-Ahead Decision (Simple)
# -----------------------------------

if workload == "sequential":
    readahead = 1024
    reasons.append("Sequential workload → increase read-ahead")

else:
    readahead = 128
    reasons.append("Random/mixed workload → keep read-ahead low")

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