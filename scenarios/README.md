# Green Metrics Tool (GMT) Scenarios Specification

This directory contains the formal `usage_scenario.yml` specifications for the **Green Metrics Tool (GMT) ScenarioRunner**.

## Scenario Files Overview

| Scenario File | Target Workload | Description | Use Case |
|---|---|---|---|
| `usage_scenario.yml` | Configurable (LOW or HIGH) | Uses GMT native `__GMT_VAR_*__` variable replacement. Defaults to `low`. | Root auto-detection & CLI variable injection |
| `usage_scenario_low.yml` | Dedicated LOW | 5s stabilization pause followed by 30s controlled low duty-cycle execution. | Web UI submission on `metrics.green-coding.io` |
| `usage_scenario_high.yml` | Dedicated HIGH | 5s stabilization pause followed by 30s saturated SHA-256 CPU execution. | Web UI submission on `metrics.green-coding.io` |
| `usage_scenario_comparison.yml` | Sequential Dual | Executes LOW, 10s cooldown, and HIGH in a single run. | Phase-level comparative breakdown |

---

## Anatomy of the Scenario Configuration

The Green Metrics Tool uses an extended subset of the Docker Compose specification combined with a flow lifecycle orchestrator:

```yaml
---
name: "Scenario Name"
author: "Author Name <email@example.com>"
description: "Human-readable scenario description"

# Optional GMT variables block
variables:
  __GMT_VAR_MODE__: "low"
  __GMT_VAR_DURATION__: "30"

# Infrastructure & Container specification
services:
  app-runner:
    build:
      context: ..
      dockerfile: Dockerfile
    entrypoint: ["tail", "-f", "/dev/null"]

# Runtime interaction sequence
flow:
  - name: "Phase Name"
    container: app-runner
    commands:
      - type: console
        command: python app/app.py --mode low --duration 30
        note: "Phase explanation"
```

### Key Architectural Concepts

1. **Docker Build Context Resolution for Nested Scenarios:**
   When GMT executes a scenario located in a subdirectory (e.g. `scenarios/usage_scenario_low.yml`), GMT resolves relative paths in `build` relative to the scenario file's directory. By specifying:
   ```yaml
   build:
     context: ..
     dockerfile: Dockerfile
   ```
   The build context is shifted up to the repository root. This ensures that the container builder locates the root `Dockerfile` and all referenced source files (`app/requirements.txt` and `app/app.py`) correctly.

2. **`services` & Keep-Alive Mechanism:**
   GMT orchestrates containers in distinct phases: `CHECKOUT`, `BUILD`, `BOOT`, `RUNTIME`, and `TEARDOWN`. During the `BOOT` phase, the container is started, and metric providers (RAPL, cgroups, perf counters) attach to the container PID/cgroup namespace. If a container exits immediately after running its CMD, GMT aborts the run. Overriding `entrypoint: ["tail", "-f", "/dev/null"]` guarantees the container remains alive, ready to execute interactive flow commands.

3. **`flow` & Phase Metrics:**
   Every entry in `flow` represents an isolated benchmark phase. GMT's metric providers record metrics continually, tagging metric samples with the active flow step. This enables phase-level energy breakdown (e.g., differentiating baseline idle power from active computation).

4. **`type: console` Execution:**
   GMT uses `docker exec` under strict POSIX shell parameters (`-o errexit -o nounset -o pipefail`) to execute commands inside the designated container.

5. **Variables (`__GMT_VAR_*__`):**
   Variables allow runtime parameter injection without modifying the file. The GMT runner replaces matching tokens prior to execution.

---

## Executing Scenarios Locally via GMT CLI

If running GMT locally on an Intel/AMD Linux machine with root/sudo access:

```bash
# 1. Run LOW Workload
python3 runner.py --uri /path/to/GMT-Carbon-Experiment \
  --filename scenarios/usage_scenario_low.yml

# 2. Run HIGH Workload
python3 runner.py --uri /path/to/GMT-Carbon-Experiment \
  --filename scenarios/usage_scenario_high.yml

# 3. Parameterized run using variables
python3 runner.py --uri /path/to/GMT-Carbon-Experiment \
  --variable "MODE=high" \
  --variable "DURATION=30"
```

For remote execution on `metrics.green-coding.io`, see [`docs/demonstration_guide.md`](../docs/demonstration_guide.md).
