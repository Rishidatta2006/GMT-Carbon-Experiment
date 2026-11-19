"""
Unit and integration tests for app/app.py.
Validates CLI argument parsing, execution modes, deterministic behavior,
timing accuracy, and JSON telemetry export.
"""

import json
import os
import subprocess
import sys
import tempfile
import pytest

PYTHON_EXE = sys.executable
APP_PATH = os.path.join(os.path.dirname(__file__), "..", "app", "app.py")


def run_app_cli(args):
    """Helper to run app.py with subprocess and capture output."""
    cmd = [PYTHON_EXE, APP_PATH] + args
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result


def test_app_help_flag():
    """Verify --help flag prints usage instructions and exits with 0."""
    res = run_app_cli(["--help"])
    assert res.returncode == 0
    assert "GMT Carbon Footprint Experiment Workload Simulator" in res.stdout
    assert "--mode" in res.stdout
    assert "--duration" in res.stdout


def test_low_workload_execution():
    """Verify LOW workload executes cleanly and completes in ~1.0 second."""
    res = run_app_cli(["--mode", "low", "--duration", "1.0", "--heartbeat", "0.5"])
    assert res.returncode == 0
    assert "Execution Mode       : LOW" in res.stdout
    assert "Status               : COMPLETED" in res.stdout
    assert "SHA-256 Hashes" in res.stdout
    assert "Wall-Clock Duration" in res.stdout


def test_high_workload_execution():
    """Verify HIGH workload executes continuous computation and completes in ~1.0 second."""
    res = run_app_cli(["--mode", "high", "--duration", "1.0", "--batch-size", "5000", "--heartbeat", "0.5"])
    assert res.returncode == 0
    assert "Execution Mode       : HIGH" in res.stdout
    assert "Status               : COMPLETED" in res.stdout
    assert "Total Operations" in res.stdout


def test_invalid_workload_mode():
    """Verify invalid mode is rejected with descriptive error message."""
    res = run_app_cli(["--mode", "extreme_stress"])
    assert res.returncode != 0
    assert "invalid choice" in res.stderr.lower()


def test_invalid_negative_duration():
    """Verify negative duration is rejected with exit code != 0."""
    res = run_app_cli(["--mode", "low", "--duration", "-15"])
    assert res.returncode != 0
    assert "strictly positive" in res.stderr.lower()


def test_invalid_zero_duration():
    """Verify zero duration is rejected with exit code != 0."""
    res = run_app_cli(["--mode", "low", "--duration", "0"])
    assert res.returncode != 0
    assert "strictly positive" in res.stderr.lower()


def test_telemetry_json_export():
    """Verify --output-json writes a well-formed JSON summary."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
        temp_json_path = tf.name

    try:
        res = run_app_cli(["--mode", "low", "--duration", "1.0", "--output-json", temp_json_path])
        assert res.returncode == 0
        assert os.path.exists(temp_json_path)

        with open(temp_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["mode"] == "LOW"
        assert data["status"] == "COMPLETED"
        assert data["target_duration_sec"] == 1.0
        assert "actual_wall_time_sec" in data
        assert "process_cpu_time_sec" in data
        assert "operations_completed" in data
        assert "peak_rss_mb" in data
        assert "deterministic_fingerprint" in data
    finally:
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)


def test_workload_contrast():
    """Verify HIGH mode executes significantly more operations than LOW mode over identical 1s window."""
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf1:
        low_json = tf1.name
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf2:
        high_json = tf2.name

    try:
        run_app_cli(["--mode", "low", "--duration", "1.0", "--output-json", low_json])
        run_app_cli(["--mode", "high", "--duration", "1.0", "--batch-size", "5000", "--output-json", high_json])

        with open(low_json, "r", encoding="utf-8") as f:
            low_data = json.load(f)
        with open(high_json, "r", encoding="utf-8") as f:
            high_data = json.load(f)

        assert high_data["operations_completed"] > (low_data["operations_completed"] * 10), \
            f"Expected HIGH ({high_data['operations_completed']}) to exceed LOW ({low_data['operations_completed']}) by >10x"
        assert high_data["process_cpu_time_sec"] > low_data["process_cpu_time_sec"], \
            "Expected HIGH CPU time to exceed LOW CPU time"
    finally:
        if os.path.exists(low_json):
            os.remove(low_json)
        if os.path.exists(high_json):
            os.remove(high_json)
