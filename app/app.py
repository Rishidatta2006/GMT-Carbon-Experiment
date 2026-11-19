#!/usr/bin/env python3
"""
Python Application Carbon Footprint Analyzer - Workload Simulator
Designed for Green Metrics Tool (GMT) ScenarioRunner Benchmarks.

Provides two deterministic workload profiles:
  - LOW:  Minimal CPU duty-cycle (light periodic hashing + sleep, ~5-15% CPU).
          Demonstrates base static energy consumption & idle power draw.
  - HIGH: Continuous cryptographic SHA-256 hash chaining (100% core load).
          Demonstrates active dynamic energy consumption under compute stress.

Both profiles execute for identical target durations to enable rigorous
scientific energy and carbon emission comparison under GMT.
"""

import argparse
import datetime
import hashlib
import json
import os
import signal
import sys
import time
import tracemalloc

# Attempt to import psutil for system-level memory metrics; gracefully fallback
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


# Global flag to support graceful shutdown on SIGINT / SIGTERM
TERMINATION_REQUESTED = False


def signal_handler(signum, frame):
    """Graceful termination handler for SIGINT and SIGTERM."""
    global TERMINATION_REQUESTED
    sig_name = signal.Signals(signum).name
    sys.stderr.write(f"\n[ALERT] Received termination signal: {sig_name}. Finishing current cycle...\n")
    TERMINATION_REQUESTED = True


def parse_arguments(args=None):
    """
    Parse and validate command line arguments.
    """
    parser = argparse.ArgumentParser(
        description="GMT Carbon Footprint Experiment Workload Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python app/app.py --mode low --duration 30
  python app/app.py --mode high --duration 30
  python app/app.py --mode high --duration 15 --output-json results/run_high.json
        """
    )

    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["low", "high"],
        help="Computational workload mode: 'low' (controlled duty cycle) or 'high' (continuous CPU stress)."
    )

    parser.add_argument(
        "--duration",
        type=float,
        default=30.0,
        help="Execution duration in seconds (must be a positive number, default: 30.0)."
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10000,
        help="Number of operations per time check in HIGH mode (default: 10,000)."
    )

    parser.add_argument(
        "--heartbeat",
        type=float,
        default=5.0,
        help="Interval in seconds for printing heartbeat progress logs (default: 5.0)."
    )

    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to export run telemetry summary in JSON format."
    )

    parsed = parser.parse_args(args)

    # Input validation
    if parsed.duration <= 0:
        parser.error(f"--duration must be a strictly positive number (received: {parsed.duration})")

    if parsed.batch_size <= 0:
        parser.error(f"--batch-size must be a strictly positive integer (received: {parsed.batch_size})")

    if parsed.heartbeat <= 0:
        parser.error(f"--heartbeat must be a strictly positive number (received: {parsed.heartbeat})")

    return parsed


def get_current_memory_mb():
    """Retrieve current RSS memory in Megabytes."""
    if PSUTIL_AVAILABLE:
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / (1024 * 1024)
        except Exception:
            pass
    # Fallback to tracemalloc
    current, peak = tracemalloc.get_traced_memory()
    return current / (1024 * 1024)


def execute_low_workload(duration_sec, heartbeat_sec):
    """
    Execute LOW workload.
    Controlled duty-cycle:
      In each 100ms window:
        - 10ms of light SHA-256 computation (approx. 200 hashes)
        - 90ms of sleep
      This maintains low, stable CPU utilization (~5-15%) while keeping
      the process alive to demonstrate software base energy consumption.
    """
    seed = b"GMT-EXPERIMENT-LOW-WORKLOAD-SEED-2026-SUSTAINABLE-COMPUTING"
    current_hash = hashlib.sha256(seed).digest()

    start_perf = time.perf_counter()
    start_cpu = time.process_time()
    last_heartbeat = start_perf

    hashes_computed = 0
    cycles_completed = 0
    cycle_target_sec = 0.100  # 100 ms total cycle
    active_work_chunk = 200    # Hashes per cycle

    print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S UTC')}] "
          f"Starting LOW workload loop (Target Duration: {duration_sec:.1f}s, Cycle: 100ms duty-cycle)...")

    while not TERMINATION_REQUESTED:
        cycle_start = time.perf_counter()
        now = cycle_start
        elapsed = now - start_perf

        if elapsed >= duration_sec:
            break

        # Light computational block (active duty)
        for _ in range(active_work_chunk):
            current_hash = hashlib.sha256(current_hash).digest()
        hashes_computed += active_work_chunk
        cycles_completed += 1

        # Sleep for remainder of the 100ms cycle
        work_elapsed = time.perf_counter() - cycle_start
        sleep_time = cycle_target_sec - work_elapsed
        if sleep_time > 0:
            # Check we don't overshoot duration
            remaining_total = duration_sec - (time.perf_counter() - start_perf)
            actual_sleep = min(sleep_time, max(0.0, remaining_total))
            if actual_sleep > 0:
                time.sleep(actual_sleep)

        # Heartbeat logging
        current_time = time.perf_counter()
        if (current_time - last_heartbeat) >= heartbeat_sec:
            pct = min(100.0, (current_time - start_perf) / duration_sec * 100.0)
            mem_mb = get_current_memory_mb()
            print(f"  [Heartbeat] Elapsed: {current_time - start_perf:5.1f}s / {duration_sec:.1f}s ({pct:5.1f}%) | "
                  f"Hashes: {hashes_computed:8,d} | RAM: {mem_mb:5.2f} MB")
            last_heartbeat = current_time

    end_perf = time.perf_counter()
    end_cpu = time.process_time()

    return {
        "wall_time": end_perf - start_perf,
        "cpu_time": end_cpu - start_cpu,
        "operations": hashes_computed,
        "cycles": cycles_completed,
        "op_name": "SHA-256 Hashes",
        "final_hash_hex": current_hash.hex()[:16]
    }


def execute_high_workload(duration_sec, batch_size, heartbeat_sec):
    """
    Execute HIGH workload.
    Continuous, saturated CPU utilization:
      Performs tight chained SHA-256 hashing in batches without sleeping,
      keeping the executing core fully occupied at 100% capacity.
    """
    seed = b"GMT-EXPERIMENT-HIGH-WORKLOAD-SEED-2026-SUSTAINABLE-COMPUTING"
    current_hash = hashlib.sha256(seed).digest()

    start_perf = time.perf_counter()
    start_cpu = time.process_time()
    last_heartbeat = start_perf

    hashes_computed = 0
    batches_completed = 0

    print(f"[{datetime.datetime.now(datetime.timezone.utc).strftime('%H:%M:%S UTC')}] "
          f"Starting HIGH workload loop (Target Duration: {duration_sec:.1f}s, Batch: {batch_size:,d} hashes)...")

    while not TERMINATION_REQUESTED:
        # Tight compute batch without yielding CPU
        for _ in range(batch_size):
            current_hash = hashlib.sha256(current_hash).digest()

        hashes_computed += batch_size
        batches_completed += 1

        now = time.perf_counter()
        if (now - start_perf) >= duration_sec:
            break

        # Heartbeat logging
        if (now - last_heartbeat) >= heartbeat_sec:
            pct = min(100.0, (now - start_perf) / duration_sec * 100.0)
            mem_mb = get_current_memory_mb()
            rate = hashes_computed / (now - start_perf)
            print(f"  [Heartbeat] Elapsed: {now - start_perf:5.1f}s / {duration_sec:.1f}s ({pct:5.1f}%) | "
                  f"Hashes: {hashes_computed:10,d} ({rate:10.1f} h/s) | RAM: {mem_mb:5.2f} MB")
            last_heartbeat = now

    end_perf = time.perf_counter()
    end_cpu = time.process_time()

    return {
        "wall_time": end_perf - start_perf,
        "cpu_time": end_cpu - start_cpu,
        "operations": hashes_computed,
        "batches": batches_completed,
        "op_name": "SHA-256 Hashes",
        "final_hash_hex": current_hash.hex()[:16]
    }


def run_experiment(args):
    """Run workload experiment based on parsed command line arguments."""
    tracemalloc.start()

    # Register OS signals
    signal.signal(signal.SIGINT, signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, signal_handler)

    utc_start = datetime.datetime.now(datetime.timezone.utc)
    print("=" * 72)
    print("  GREEN METRICS TOOL (GMT) - PYTHON WORKLOAD SIMULATOR")
    print("  Sustainable Software Engineering Carbon Experiment")
    print("=" * 72)
    print(f"  Execution Mode       : {args.mode.upper()}")
    print(f"  Target Duration      : {args.duration:.2f} seconds")
    print(f"  Start Timestamp (UTC): {utc_start.isoformat()}")
    print(f"  PID                  : {os.getpid()}")
    print(f"  Python Version       : {sys.version.split()[0]}")
    print(f"  Platform             : {sys.platform}")
    print("-" * 72)

    if args.mode == "low":
        metrics = execute_low_workload(args.duration, args.heartbeat)
    else:
        metrics = execute_high_workload(args.duration, args.batch_size, args.heartbeat)

    utc_end = datetime.datetime.now(datetime.timezone.utc)
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    wall_time = metrics["wall_time"]
    cpu_time = metrics["cpu_time"]
    cpu_percent = (cpu_time / wall_time * 100.0) if wall_time > 0 else 0.0
    throughput = metrics["operations"] / wall_time if wall_time > 0 else 0.0
    peak_rss_mb = get_current_memory_mb()

    summary = {
        "experiment_name": "GMT-Python-Carbon-Footprint-Analyzer",
        "mode": args.mode.upper(),
        "target_duration_sec": args.duration,
        "actual_wall_time_sec": round(wall_time, 4),
        "process_cpu_time_sec": round(cpu_time, 4),
        "calculated_cpu_utilization_pct": round(cpu_percent, 2),
        "operations_completed": metrics["operations"],
        "throughput_ops_per_sec": round(throughput, 2),
        "peak_tracemalloc_mb": round(peak_mem / (1024 * 1024), 3),
        "peak_rss_mb": round(peak_rss_mb, 2),
        "deterministic_fingerprint": metrics["final_hash_hex"],
        "interrupted": TERMINATION_REQUESTED,
        "timestamp_start": utc_start.isoformat(),
        "timestamp_end": utc_end.isoformat(),
        "status": "COMPLETED" if not TERMINATION_REQUESTED else "INTERRUPTED"
    }

    print("-" * 72)
    print("  EXPERIMENT EXECUTION SUMMARY")
    print("-" * 72)
    print(f"  Status               : {summary['status']}")
    print(f"  Workload Profile     : {summary['mode']}")
    print(f"  Wall-Clock Duration  : {summary['actual_wall_time_sec']:.4f} s (Target: {args.duration:.2f} s)")
    print(f"  Process CPU Time     : {summary['process_cpu_time_sec']:.4f} s")
    print(f"  Process CPU Load     : {summary['calculated_cpu_utilization_pct']:.2f} %")
    print(f"  Total Operations     : {summary['operations_completed']:,d} {metrics['op_name']}")
    print(f"  Throughput Rate      : {summary['throughput_ops_per_sec']:,.2f} ops/s")
    print(f"  Peak Memory (RSS)    : {summary['peak_rss_mb']:.2f} MB")
    print(f"  Result Fingerprint   : {summary['deterministic_fingerprint']}")
    print("=" * 72)
    print("  [NOTE] Actual energy (Joules/Wh) and carbon emissions (g CO2e) are")
    print("         measured at the host/container level by Green Metrics Tool (GMT).")
    print("=" * 72)

    if args.output_json:
        try:
            out_dir = os.path.dirname(args.output_json)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump(summary, f, indent=2)
            print(f"[Telemetry] Saved run summary to: {args.output_json}")
        except Exception as e:
            sys.stderr.write(f"[WARNING] Could not save JSON telemetry to {args.output_json}: {e}\n")

    return summary


def main():
    args = parse_arguments()
    run_experiment(args)


if __name__ == "__main__":
    main()
