"""
Tests validating results templates and sample data structure.
Ensures CSV and JSON test data conform to GMT metric schemas and clearly mark
demonstration placeholders vs real measurements.
"""

import csv
import json
import os
import pytest

RESULTS_DIR = os.path.join(os.path.dirname(__file__), "..", "results")


def test_results_template_csv_structure():
    """Verify results_template.csv headers match expected GMT export schema."""
    template_path = os.path.join(RESULTS_DIR, "results_template.csv")
    assert os.path.exists(template_path)

    with open(template_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)

    expected_cols = [
        "run_id", "timestamp_utc", "scenario_name", "workload_mode",
        "duration_seconds", "total_energy_joules", "total_energy_wh",
        "cpu_pkg_joules", "dram_joules", "carbon_emissions_gco2e",
        "grid_carbon_intensity_g_kwh", "avg_cpu_utilization_pct",
        "peak_memory_mb", "hardware_source", "measurement_status"
    ]
    for col in expected_cols:
        assert col in header, f"Missing expected column '{col}' in results_template.csv"


def test_sample_demonstration_csv_content():
    """Verify demonstration CSV is well-formed and clearly flagged as demonstration data."""
    sample_csv = os.path.join(RESULTS_DIR, "sample_gmt_demonstration_data.csv")
    assert os.path.exists(sample_csv)

    with open(sample_csv, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 2, "Expected at least 2 demonstration rows (LOW and HIGH)"
    modes = [r["workload_mode"].upper() for r in rows]
    assert "LOW" in modes and "HIGH" in modes

    for r in rows:
        assert "DEMO" in r["run_id"] or "DEMO" in r["measurement_status"], \
            "Demonstration row must be clearly identified as demonstration data"
        assert float(r["duration_seconds"]) > 0
        assert float(r["total_energy_joules"]) > 0
        assert float(r["carbon_emissions_gco2e"]) > 0


def test_sample_demonstration_json_content():
    """Verify demonstration JSON contains metadata warning and valid runs."""
    sample_json = os.path.join(RESULTS_DIR, "sample_gmt_demonstration_data.json")
    assert os.path.exists(sample_json)

    with open(sample_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "meta" in data
    assert "DEMONSTRATION PLACEHOLDER ONLY" in data["meta"]["notice"]
    assert "runs" in data and len(data["runs"]) >= 2
