# Faculty Demonstration & Academic Viva Guide

**Project:** Python Application Carbon Footprint Analyzer Using Green Metrics Tool (GMT)  
**Academic Presentation & Evaluation Guide**

---

## 1. Demonstration Strategy & Time Allocation (10-Minute Walkthrough)

| Phase | Time | Key Focus | What to Show |
|---|---|---|---|
| **Phase 1: Problem & Objectives** | 2 min | Sustainable Computing Principles & Project Scope | Problem statement, GSF SCI equation, static vs dynamic power |
| **Phase 2: Live Workload Execution** | 3 min | Terminal Execution & Telemetry Verification | Run LOW and HIGH workloads side-by-side in terminal |
| **Phase 3: GMT Scenario Architecture** | 2 min | Green Metrics Tool ScenarioRunner Contract | Inspect `usage_scenario.yml`, Dockerfile, keep-alive entrypoint |
| **Phase 4: Dashboard & Sustainability Insights** | 3 min | Visual Analytics, CSV Import, Academic Q&A | Open `dashboard/index.html`, review KPI deltas, discuss optimization |

---

## 2. Step-by-Step Live Demonstration Script

### Step 1: Automated Verification Test Run
Open your terminal in the project root and execute the automated test runner:

```bash
python tests/run_tests.py
```

**Talking Points for Faculty:**
> *"Before demonstrating individual components, I am running our automated validation suite comprising 34 unit, scenario, and schema tests. This confirms that all CLI arguments, duration counters, deterministic fingerprints, and GMT ScenarioRunner YAML files conform strictly to official Green Coding specifications."*

---

### Step 2: Live Python Workload Execution

#### A. Execute LOW Workload (Controlled Duty-Cycle)
Run a 10-second or 30-second low workload in the terminal:

```bash
python app/app.py --mode low --duration 10
```

**What the faculty sees:**
* Heartbeat logging every 5 seconds.
* CPU utilization remains low (~0.5% – 5%).
* Wall-clock duration matches exactly 10.00 seconds.

**Key Explanation:**
> *"In LOW mode, the application simulates a realistic lightweight microservice. It executes a 100ms duty cycle: 10ms of light activity followed by 90ms of sleep. Notice that even though CPU activity is minimal, software in this state still commands physical hardware, incurring static baseline energy."*

#### B. Execute HIGH Workload (Cryptographic SHA-256 Stress)
Run a 10-second or 30-second high workload in the terminal:

```bash
python app/app.py --mode high --duration 10
```

**What the faculty sees:**
* CPU utilization surges to ~99% – 100%.
* Computes ~3.7 million SHA-256 hashes in 10 seconds (~370,000 hashes/second).
* Wall-clock duration is strictly controlled to 10.00 seconds.

**Key Explanation:**
> *"In HIGH mode, the application saturates the processor core with chained cryptographic hashing without yielding CPU time. Both workloads ran for the exact same duration, allowing us to isolate computational intensity as the sole independent variable."*

---

### Step 3: Architecture & GMT Integration Walkthrough

Show the faculty the following files in your IDE:

1. **[`Dockerfile`](../Dockerfile):**
   * Explain the multi-layer caching (`COPY requirements.txt` before code).
   * Point out the security hardening: `USER gmtuser` (non-root).
   * Point out `CMD ["tail", "-f", "/dev/null"]`:
     > *"GMT ScenarioRunner manages containers across distinct lifecycle phases: BOOT, RUNTIME, and TEARDOWN. If a container exits immediately after boot, GMT aborts metric collection. The keep-alive command keeps the container alive so GMT can attach RAPL and cgroup monitors and execute our workload via `flow`."*
2. **[`scenarios/usage_scenario_low.yml`](../scenarios/usage_scenario_low.yml) and [`scenarios/usage_scenario_high.yml`](../scenarios/usage_scenario_high.yml):**
   * Point out the 5-second stabilization sleep before execution:
     > *"This stabilization phase ensures that transient CPU frequency spikes from container spin-up dissipate before we sample energy."*

---

### Step 4: Remote Measurement on Official GMT Service

Explain how the repository connects to the official Green Metrics Tool cluster (`metrics.green-coding.io`):

1. **Step 1:** Push the project to a public GitHub repository.
2. **Step 2:** Navigate to `https://metrics.green-coding.io/` and select **Request Measurement**.
3. **Step 3:** Enter the repository URL (e.g. `https://github.com/your-username/GMT-Carbon-Experiment`).
4. **Step 4:** Submit Run 1: Filename `scenarios/usage_scenario_low.yml`.
5. **Step 5:** Submit Run 2: Filename `scenarios/usage_scenario_high.yml`.
6. **Step 6:** The GMT measurement node executes the run on dedicated hardware, measures RAPL registers and cgroups, and outputs the exact Joules and carbon footprint.

---

### Step 5: Dashboard Demonstration

Open `dashboard/index.html` in your web browser (or serve via `python -m http.server 8000` and visit `http://localhost:8000/dashboard/`):

1. **Point out the Status Banner:**
   * Notice the amber banner: `DEMONSTRATION PLACEHOLDER MODE`.
   * *"To maintain absolute scientific integrity, our dashboard never fakes real measurements. It clearly labels unmeasured estimates until actual GMT output files are ingested."*
2. **Demonstrate File Ingestion:**
   * Click **Browse File** or drag & drop [`results/sample_gmt_demonstration_data.csv`](../results/sample_gmt_demonstration_data.csv).
   * Show how the KPIs, stacked energy chart (CPU PKG vs DRAM), carbon emissions chart, and audit trail update instantly.
3. **Toggle Light/Dark Theme:**
   * Click the theme button in the top right to show responsive, accessible styling.

---

## 3. Anticipated Faculty Questions & Model Answers

### Q1: "Why can't we just measure energy using software CPU percentage?"
> **Model Answer:**  
> *"CPU percentage measures time spent by the scheduler executing threads, not physical power dissipation. Power consists of static leakage power ($P_{\text{static}}$) and dynamic switching power ($P_{\text{dynamic}} \propto C \cdot V^2 \cdot f$). Under high load, Dynamic Voltage and Frequency Scaling (DVFS) increases both frequency and voltage. Because voltage is squared, power draw increases non-linearly. Software CPU percent cannot detect frequency scaling, voltage changes, or DRAM controller power. That is why hardware-level interfaces like Intel RAPL and physical power meters used by GMT are necessary."*

### Q2: "What is the relationship between Energy (Joules) and Carbon ($\text{g CO}_2\text{e}$)?"
> **Model Answer:**  
> *"Energy (Joules or Watt-hours) is an intrinsic physical quantity of the hardware. Carbon emissions ($\text{g CO}_2\text{e}$) are calculated using the Green Software Foundation SCI equation: $\text{Emissions} = \text{Energy (kWh)} \times I$, where $I$ is the regional grid carbon intensity in $\text{g CO}_2\text{e}/\text{kWh}$. An application running in a region powered by coal will emit 20 to 40 times more carbon than the exact same application running on a renewable or nuclear grid, even though both consume the exact same Joules."*

### Q3: "Why did you use SHA-256 for the HIGH workload instead of an infinite while loop?"
> **Model Answer:**  
> *"A simple `while True: pass` loop can be heavily optimized by branch predictors and compiler loop unrolling, creating artificial instruction cache patterns. Chaining SHA-256 cryptographic hashes requires continuous ALU arithmetic, bitwise shifts, and memory reads from byte buffers, creating a deterministic, reproducible, compute-bound workload that reliably exercises the CPU cores."*

### Q4: "What is the Green Metrics Tool's advantage over running `psutil` or `top`?"
> **Model Answer:**  
> *"Tools like `psutil` or `top` only sample process CPU time and memory from the `/proc` filesystem. GMT is a full-lifecycle benchmarking framework: it orchestrates containers, reads CPU MSRs (Model Specific Registers) for Intel/AMD RAPL, interfaces with Linux cgroups v2, records network I/O, integrates with Electricity Maps for real-time grid carbon factors, and provides an audited, reproducible measurement record conforming to ISO/IEC 21031."*
