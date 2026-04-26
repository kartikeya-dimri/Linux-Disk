#!/usr/bin/env python3

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
import re

before_dir = input("Enter BEFORE directory path: ").strip()
after_dir = input("Enter AFTER directory path: ").strip()

os.makedirs("comparison_plots", exist_ok=True)

# -----------------------------------------
# Parse iostat
# -----------------------------------------
def parse_iostat(file_path):
    data = []
    headers = []

    with open(file_path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            if line.startswith("Device"):
                headers = re.split(r"\s+", line)
                continue

            if headers:
                values = re.split(r"\s+", line)
                if len(values) == len(headers):
                    data.append(dict(zip(headers, values)))

    df = pd.DataFrame(data)

    # Convert numeric columns
    for col in df.columns:
        if col != "Device":
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Keep only main disk
    df = df[df["Device"] == "sda"]

    # Drop Device column
    df = df.drop(columns=["Device"])

    return df.reset_index(drop=True)

# -----------------------------------------
# Parse PSI
# -----------------------------------------
def parse_psi(file_path):
    values = []

    with open(file_path) as f:
        lines = f.readlines()

    for i in range(0, len(lines), 2):
        if i + 1 < len(lines):
            line = lines[i+1]
            if "some avg10" in line:
                val = float(line.split("avg10=")[1].split()[0])
                values.append(val)

    return pd.DataFrame({"psi": values})

# -----------------------------------------
# Load data
# -----------------------------------------
before = parse_iostat(os.path.join(before_dir, "iostat_clean.log"))
after = parse_iostat(os.path.join(after_dir, "iostat_clean.log"))

# -----------------------------------------
# Helper plot (time-series)
# -----------------------------------------
def plot_ts(column, title, filename):
    plt.figure()

    if column in before.columns:
        plt.plot(before[column], label="Before")
    if column in after.columns:
        plt.plot(after[column], label="After")

    plt.title(title)
    plt.xlabel("Time")
    plt.ylabel(column)
    plt.legend()
    plt.savefig(f"comparison_plots/{filename}")
    plt.close()

# -----------------------------------------
# Basic Time-Series Plots
# -----------------------------------------
plot_ts("r_await", "Read Latency (ms)", "latency_ts.png")
plot_ts("%util", "Disk Utilization (%)", "utilization.png")
plot_ts("aqu-sz", "Queue Depth", "queue.png")
plot_ts("r/s", "IOPS", "iops.png")

if "rMB/s" in before.columns:
    plot_ts("rMB/s", "Throughput (MB/s)", "throughput.png")

# -----------------------------------------
# Latency Distribution (IMPORTANT)
# -----------------------------------------
if "r_await" in before.columns:
    plt.figure()

    plt.hist(before["r_await"].dropna(), bins=40, alpha=0.5, label="Before")
    plt.hist(after["r_await"].dropna(), bins=40, alpha=0.5, label="After")

    plt.title("Latency Distribution")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Frequency")
    plt.legend()

    plt.savefig("comparison_plots/latency_distribution.png")
    plt.close()

# -----------------------------------------
# Percentile Plot (MOST IMPORTANT)
# -----------------------------------------
def percentiles(data):
    return [
        np.percentile(data, 50),
        np.percentile(data, 95),
        np.percentile(data, 99)
    ]

before_lat = before["r_await"].dropna()
after_lat = after["r_await"].dropna()

labels = ["P50", "P95", "P99"]

b_vals = percentiles(before_lat)
a_vals = percentiles(after_lat)

x = np.arange(len(labels))

plt.figure()
plt.bar(x - 0.2, b_vals, width=0.4, label="Before")
plt.bar(x + 0.2, a_vals, width=0.4, label="After")

plt.xticks(x, labels)
plt.ylabel("Latency (ms)")
plt.title("Latency Percentiles")
plt.legend()

plt.savefig("comparison_plots/latency_percentiles.png")
plt.close()

# -----------------------------------------
# PSI Plot (CRITICAL)
# -----------------------------------------
psi_before_file = os.path.join(before_dir, "psi_io.log")
psi_after_file = os.path.join(after_dir, "psi_io.log")

if os.path.exists(psi_before_file) and os.path.exists(psi_after_file):
    before_psi = parse_psi(psi_before_file)
    after_psi = parse_psi(psi_after_file)

    plt.figure()
    plt.plot(before_psi["psi"], label="Before")
    plt.plot(after_psi["psi"], label="After")

    plt.title("I/O Pressure (PSI avg10)")
    plt.xlabel("Time")
    plt.ylabel("PSI")
    plt.legend()

    plt.savefig("comparison_plots/psi.png")
    plt.close()

# -----------------------------------------
print("\n[+] plots saved in comparison_plots/")