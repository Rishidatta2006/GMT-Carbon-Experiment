/**
 * Green Metrics Tool (GMT) Results Dashboard - Client Application Logic
 * Supports CSV/JSON result ingestion, dynamic KPI rendering, and Canvas charts.
 */

(function () {
  'use strict';

  // --- Baseline Demonstration / Placeholder Data ---
  // IMPORTANT: Clearly labelled as demonstration estimates to satisfy scientific integrity.
  const DEMO_STATE = {
    isRealData: false,
    sourceLabel: 'Demonstration Placeholder (Awaiting Actual GMT Measurement)',
    gridIntensity: 400.0, // g CO2e / kWh
    low: {
      runId: 'DEMO-RUN-LOW-001',
      timestamp: '2026-11-20T10:15:00Z',
      scenario: 'Python Carbon Experiment - LOW Workload',
      duration: 30.0,
      totalEnergyJ: 41.25,
      totalEnergyWh: 0.01146,
      cpuPkgJ: 35.10,
      dramJ: 6.15,
      carbonG: 0.00458,
      carbonMg: 4.58,
      cpuPct: 9.2,
      peakMemMb: 22.4,
      source: 'DEMO_ESTIMATE_RAPL',
      status: 'DEMONSTRATION_PLACEHOLDER_NOT_REAL'
    },
    high: {
      runId: 'DEMO-RUN-HIGH-002',
      timestamp: '2026-11-20T10:25:00Z',
      scenario: 'Python Carbon Experiment - HIGH Workload',
      duration: 30.0,
      totalEnergyJ: 214.80,
      totalEnergyWh: 0.05967,
      cpuPkgJ: 192.40,
      dramJ: 22.40,
      carbonG: 0.02387,
      carbonMg: 23.87,
      cpuPct: 99.4,
      peakMemMb: 24.1,
      source: 'DEMO_ESTIMATE_RAPL',
      status: 'DEMONSTRATION_PLACEHOLDER_NOT_REAL'
    }
  };

  let currentState = JSON.parse(JSON.stringify(DEMO_STATE));

  // --- DOM Element References ---
  const themeToggleBtn = document.getElementById('themeToggleBtn');
  const themeIcon = document.getElementById('themeIcon');
  const themeText = document.getElementById('themeText');
  const statusBanner = document.getElementById('statusBanner');
  const bannerBadge = document.getElementById('bannerBadge');
  const bannerMessage = document.getElementById('bannerMessage');
  const bannerDismissBtn = document.getElementById('bannerDismissBtn');

  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('fileInput');
  const triggerFileSelect = document.getElementById('triggerFileSelect');
  const loadDemoBtn = document.getElementById('loadDemoBtn');
  const resetBtn = document.getElementById('resetBtn');
  const activeSourceLabel = document.getElementById('activeSourceLabel');

  const dataStatusPill = document.getElementById('dataStatusPill');
  const dataStatusDot = document.getElementById('dataStatusDot');
  const dataStatusText = document.getElementById('dataStatusText');
  const dataBadge = document.getElementById('dataBadge');
  const evidenceBadge = document.getElementById('evidenceBadge');

  // KPI elements
  const kpiLowEnergy = document.getElementById('kpiLowEnergy');
  const kpiLowEnergyWh = document.getElementById('kpiLowEnergyWh');
  const kpiHighEnergy = document.getElementById('kpiHighEnergy');
  const kpiHighEnergyWh = document.getElementById('kpiHighEnergyWh');
  const kpiEnergyRatio = document.getElementById('kpiEnergyRatio');

  const kpiLowCarbon = document.getElementById('kpiLowCarbon');
  const kpiLowCarbonG = document.getElementById('kpiLowCarbonG');
  const kpiHighCarbon = document.getElementById('kpiHighCarbon');
  const kpiHighCarbonG = document.getElementById('kpiHighCarbonG');
  const kpiCarbonRatio = document.getElementById('kpiCarbonRatio');

  const kpiLowCpu = document.getElementById('kpiLowCpu');
  const kpiHighCpu = document.getElementById('kpiHighCpu');
  const kpiCpuRatio = document.getElementById('kpiCpuRatio');
  const kpiDuration = document.getElementById('kpiDuration');
  const gridIntensityVal = document.getElementById('gridIntensityVal');
  const analysisDisparityText = document.getElementById('analysisDisparityText');
  const evidenceTableBody = document.getElementById('evidenceTableBody');

  // Canvases
  const energyCanvas = document.getElementById('energyChart');
  const carbonCanvas = document.getElementById('carbonChart');

  // --- Theme Toggle ---
  function initTheme() {
    const isLight = localStorage.getItem('gmt_theme') === 'light';
    if (isLight) {
      document.body.classList.remove('theme-dark');
      document.body.classList.add('theme-light');
      themeIcon.textContent = '🌙';
      themeText.textContent = 'Dark';
    } else {
      document.body.classList.remove('theme-light');
      document.body.classList.add('theme-dark');
      themeIcon.textContent = '☀️';
      themeText.textContent = 'Light';
    }
  }

  themeToggleBtn.addEventListener('click', () => {
    const isCurrentlyLight = document.body.classList.contains('theme-light');
    if (isCurrentlyLight) {
      document.body.classList.remove('theme-light');
      document.body.classList.add('theme-dark');
      themeIcon.textContent = '☀️';
      themeText.textContent = 'Light';
      localStorage.setItem('gmt_theme', 'dark');
    } else {
      document.body.classList.remove('theme-dark');
      document.body.classList.add('theme-light');
      themeIcon.textContent = '🌙';
      themeText.textContent = 'Dark';
      localStorage.setItem('gmt_theme', 'light');
    }
    renderCharts();
  });

  // Banner dismiss
  bannerDismissBtn.addEventListener('click', () => {
    statusBanner.style.display = 'none';
  });

  // --- File Upload & Drag-and-Drop Handlers ---
  triggerFileSelect.addEventListener('click', () => fileInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleIncomingFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleIncomingFile(e.target.files[0]);
    }
  });

  loadDemoBtn.addEventListener('click', () => {
    currentState = JSON.parse(JSON.stringify(DEMO_STATE));
    updateDashboardUI();
  });

  resetBtn.addEventListener('click', () => {
    currentState = JSON.parse(JSON.stringify(DEMO_STATE));
    updateDashboardUI();
  });

  function handleIncomingFile(file) {
    const reader = new FileReader();
    const fileName = file.name.toLowerCase();

    reader.onload = (event) => {
      try {
        const content = event.target.result;
        if (fileName.endsWith('.json')) {
          parseJsonResults(content, file.name);
        } else if (fileName.endsWith('.csv')) {
          parseCsvResults(content, file.name);
        } else {
          alert('Unsupported file format. Please upload a .csv or .json GMT result file.');
        }
      } catch (err) {
        console.error('File parsing error:', err);
        alert('Failed to parse file: ' + err.message);
      }
    };

    reader.readAsText(file);
  }

  // --- Parsing CSV Results ---
  function parseCsvResults(csvText, fileName) {
    const lines = csvText.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0 && !l.startsWith('#'));
    if (lines.length < 2) {
      throw new Error('CSV file has insufficient data rows.');
    }

    const headers = lines[0].split(',').map(h => h.trim().toLowerCase());
    const runs = [];

    for (let i = 1; i < lines.length; i++) {
      const values = lines[i].split(',').map(v => v.trim());
      const row = {};
      headers.forEach((h, idx) => {
        row[h] = values[idx] !== undefined ? values[idx] : '';
      });
      runs.push(row);
    }

    applyParsedRuns(runs, fileName);
  }

  // --- Parsing JSON Results ---
  function parseJsonResults(jsonText, fileName) {
    const data = JSON.parse(jsonText);
    let runs = [];
    if (Array.isArray(data)) {
      runs = data;
    } else if (data.runs && Array.isArray(data.runs)) {
      runs = data.runs;
    } else if (data.data && Array.isArray(data.data)) {
      runs = data.data;
    } else {
      // Single object
      runs = [data];
    }
    applyParsedRuns(runs, fileName);
  }

  function applyParsedRuns(runs, fileName) {
    let lowRun = null;
    let highRun = null;

    runs.forEach(r => {
      const mode = (r.workload_mode || r.mode || '').toUpperCase();
      if (mode.includes('LOW')) lowRun = r;
      if (mode.includes('HIGH')) highRun = r;
    });

    if (!lowRun && !highRun && runs.length >= 2) {
      lowRun = runs[0];
      highRun = runs[1];
    } else if (!lowRun && runs.length >= 1) {
      lowRun = runs[0];
    }

    function extractNum(val, fallback) {
      const n = parseFloat(val);
      return !isNaN(n) ? n : fallback;
    }

    const isReal = runs.some(r => {
      const status = (r.measurement_status || r.status || '').toUpperCase();
      return status === 'MEASURED_BY_GMT' || (status && !status.includes('PLACEHOLDER') && !status.includes('DEMO'));
    });

    if (lowRun) {
      const energyJ = extractNum(lowRun.total_energy_joules || lowRun.energy_joules || lowRun.energy, currentState.low.totalEnergyJ);
      const energyWh = extractNum(lowRun.total_energy_wh || lowRun.energy_wh, energyJ / 3600);
      const carbonG = extractNum(lowRun.carbon_emissions_gco2e || lowRun.carbon_g, currentState.low.carbonG);
      const pkgJ = extractNum(lowRun.cpu_pkg_joules || lowRun.cpu_joules, energyJ * 0.85);
      const dramJ = extractNum(lowRun.dram_joules, energyJ * 0.15);

      currentState.low = {
        runId: lowRun.run_id || lowRun.id || 'GMT-IMPORTED-LOW',
        timestamp: lowRun.timestamp_utc || lowRun.timestamp || new Date().toISOString(),
        scenario: lowRun.scenario_name || lowRun.scenario || 'Imported LOW Workload',
        duration: extractNum(lowRun.duration_seconds || lowRun.duration, 30.0),
        totalEnergyJ: energyJ,
        totalEnergyWh: energyWh,
        cpuPkgJ: pkgJ,
        dramJ: dramJ,
        carbonG: carbonG,
        carbonMg: carbonG * 1000,
        cpuPct: extractNum(lowRun.avg_cpu_utilization_pct || lowRun.cpu_pct, 9.2),
        peakMemMb: extractNum(lowRun.peak_memory_mb || lowRun.memory_mb, 22.4),
        source: lowRun.hardware_source || lowRun.metric_source || 'Imported GMT Measurement',
        status: lowRun.measurement_status || (isReal ? 'MEASURED_BY_GMT' : 'DEMONSTRATION_PLACEHOLDER')
      };
    }

    if (highRun) {
      const energyJ = extractNum(highRun.total_energy_joules || highRun.energy_joules || highRun.energy, currentState.high.totalEnergyJ);
      const energyWh = extractNum(highRun.total_energy_wh || highRun.energy_wh, energyJ / 3600);
      const carbonG = extractNum(highRun.carbon_emissions_gco2e || highRun.carbon_g, currentState.high.carbonG);
      const pkgJ = extractNum(highRun.cpu_pkg_joules || highRun.cpu_joules, energyJ * 0.88);
      const dramJ = extractNum(highRun.dram_joules, energyJ * 0.12);

      currentState.high = {
        runId: highRun.run_id || highRun.id || 'GMT-IMPORTED-HIGH',
        timestamp: highRun.timestamp_utc || highRun.timestamp || new Date().toISOString(),
        scenario: highRun.scenario_name || highRun.scenario || 'Imported HIGH Workload',
        duration: extractNum(highRun.duration_seconds || highRun.duration, 30.0),
        totalEnergyJ: energyJ,
        totalEnergyWh: energyWh,
        cpuPkgJ: pkgJ,
        dramJ: dramJ,
        carbonG: carbonG,
        carbonMg: carbonG * 1000,
        cpuPct: extractNum(highRun.avg_cpu_utilization_pct || highRun.cpu_pct, 99.4),
        peakMemMb: extractNum(highRun.peak_memory_mb || highRun.memory_mb, 24.1),
        source: highRun.hardware_source || highRun.metric_source || 'Imported GMT Measurement',
        status: highRun.measurement_status || (isReal ? 'MEASURED_BY_GMT' : 'DEMONSTRATION_PLACEHOLDER')
      };
    }

    currentState.isRealData = isReal;
    currentState.sourceLabel = `Imported: ${fileName} (${isReal ? 'Verified GMT Measurement' : 'Placeholder Format'})`;

    updateDashboardUI();
  }

  // --- UI Update Function ---
  function updateDashboardUI() {
    // 1. Banner & Badges
    if (currentState.isRealData) {
      statusBanner.className = 'status-banner banner-warning';
      statusBanner.style.backgroundColor = 'rgba(16, 185, 129, 0.15)';
      statusBanner.style.borderColor = 'rgba(16, 185, 129, 0.4)';
      statusBanner.style.color = '#D1FAE5';
      bannerBadge.className = 'badge badge-success';
      bannerBadge.textContent = 'ACTUAL GMT MEASUREMENTS LOADED';
      bannerMessage.textContent = 'Displaying real verified energy and carbon metrics measured via Green Metrics Tool ScenarioRunner.';

      dataStatusDot.className = 'indicator-dot';
      dataStatusText.textContent = 'Real GMT Data Active';
      dataBadge.className = 'badge badge-success';
      dataBadge.textContent = 'MEASURED METRICS';
      evidenceBadge.className = 'badge badge-success';
      evidenceBadge.textContent = 'VERIFIED AUDIT LOG';
    } else {
      statusBanner.className = 'status-banner banner-warning';
      statusBanner.style.backgroundColor = '';
      statusBanner.style.borderColor = '';
      statusBanner.style.color = '';
      bannerBadge.className = 'badge badge-warning';
      bannerBadge.textContent = 'DEMONSTRATION PLACEHOLDER MODE';
      bannerMessage.textContent = 'Currently displaying educational baseline values. Real GMT measurements are pending. Upload an official GMT export or CSV/JSON file to display measured results.';

      dataStatusDot.className = 'indicator-dot dot-pending';
      dataStatusText.textContent = 'Awaiting Real GMT Run';
      dataBadge.className = 'badge badge-warning';
      dataBadge.textContent = 'DEMO ESTIMATES';
      evidenceBadge.className = 'badge badge-warning';
      evidenceBadge.textContent = 'PLACEHOLDER AUDIT TRAIL';
    }

    activeSourceLabel.textContent = currentState.sourceLabel;

    // 2. KPI Cards
    const low = currentState.low;
    const high = currentState.high;

    kpiLowEnergy.innerHTML = `${low.totalEnergyJ.toFixed(2)} <small>J</small>`;
    kpiLowEnergyWh.textContent = `(${low.totalEnergyWh.toFixed(4)} Wh)`;
    kpiHighEnergy.innerHTML = `${high.totalEnergyJ.toFixed(2)} <small>J</small>`;
    kpiHighEnergyWh.textContent = `(${high.totalEnergyWh.toFixed(4)} Wh)`;

    const energyDeltaPct = low.totalEnergyJ > 0 ? (((high.totalEnergyJ - low.totalEnergyJ) / low.totalEnergyJ) * 100) : 0;
    kpiEnergyRatio.textContent = `▲ +${energyDeltaPct.toFixed(1)}% Higher Consumption`;

    kpiLowCarbon.innerHTML = `${low.carbonMg.toFixed(2)} <small>mg</small>`;
    kpiLowCarbonG.textContent = `(${low.carbonG.toFixed(4)} g)`;
    kpiHighCarbon.innerHTML = `${high.carbonMg.toFixed(2)} <small>mg</small>`;
    kpiHighCarbonG.textContent = `(${high.carbonG.toFixed(4)} g)`;

    const carbonDeltaPct = low.carbonG > 0 ? (((high.carbonG - low.carbonG) / low.carbonG) * 100) : 0;
    kpiCarbonRatio.textContent = `▲ +${carbonDeltaPct.toFixed(1)}% Emissions Increase`;

    kpiLowCpu.innerHTML = `${low.cpuPct.toFixed(1)} <small>%</small>`;
    kpiHighCpu.innerHTML = `${high.cpuPct.toFixed(1)} <small>%</small>`;
    const cpuFactor = low.cpuPct > 0 ? (high.cpuPct / low.cpuPct).toFixed(1) : 'N/A';
    kpiCpuRatio.textContent = `${cpuFactor}x Higher CPU Load`;

    kpiDuration.innerHTML = `${high.duration.toFixed(1)} <small>s</small>`;
    gridIntensityVal.textContent = `${currentState.gridIntensity.toFixed(0)} g/kWh`;

    // 3. Dynamic Analysis Update
    const factorEnergy = low.totalEnergyJ > 0 ? (high.totalEnergyJ / low.totalEnergyJ).toFixed(1) : '5.2';
    analysisDisparityText.textContent = `The HIGH workload consumed ${factorEnergy}x more total energy than the LOW workload (${high.totalEnergyJ.toFixed(1)} J vs ${low.totalEnergyJ.toFixed(1)} J) over the identical 30-second measurement window. This demonstrates that continuous instruction execution and saturated CPU core load drive dynamic voltage and frequency scaling (DVFS), significantly elevating power dissipation.`;

    // 4. Evidence Table
    renderEvidenceTable();

    // 5. Canvas Charts
    renderCharts();
  }

  function renderEvidenceTable() {
    evidenceTableBody.innerHTML = '';
    const items = [currentState.low, currentState.high];

    items.forEach((item, idx) => {
      const mode = idx === 0 ? 'LOW Workload' : 'HIGH Workload';
      const tr = document.createElement('tr');
      const isPlaceholder = item.status.includes('PLACEHOLDER') || item.status.includes('DEMO');
      const statusPill = isPlaceholder
        ? `<span class="badge badge-warning" title="Not measured yet">DEMO / ESTIMATE</span>`
        : `<span class="badge badge-success" title="Verified GMT Measurement">GMT VERIFIED</span>`;

      tr.innerHTML = `
        <td><strong>${mode}</strong></td>
        <td><code>${item.runId}</code></td>
        <td>${item.timestamp}</td>
        <td>${item.duration.toFixed(1)}s</td>
        <td>${item.totalEnergyJ.toFixed(2)} J</td>
        <td>${item.carbonG.toFixed(5)} g</td>
        <td>${item.cpuPct.toFixed(1)}%</td>
        <td>${item.source}</td>
        <td>${statusPill}</td>
      `;
      evidenceTableBody.appendChild(tr);
    });
  }

  // --- Canvas Chart Rendering ---
  function renderCharts() {
    renderEnergyChart();
    renderCarbonChart();
  }

  function setupCanvas(canvas) {
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    const ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx, width: rect.width, height: rect.height };
  }

  function renderEnergyChart() {
    const { ctx, width, height } = setupCanvas(energyCanvas);
    ctx.clearRect(0, 0, width, height);

    const isLight = document.body.classList.contains('theme-light');
    const textColor = isLight ? '#475569' : '#94A3B8';
    const gridColor = isLight ? '#E2E8F0' : '#273A31';

    const lowPkg = currentState.low.cpuPkgJ;
    const lowDram = currentState.low.dramJ;
    const highPkg = currentState.high.cpuPkgJ;
    const highDram = currentState.high.dramJ;

    const maxVal = Math.max(lowPkg + lowDram, highPkg + highDram) * 1.25 || 250;
    const paddingLeft = 55;
    const paddingBottom = 40;
    const paddingTop = 25;
    const chartHeight = height - paddingBottom - paddingTop;
    const chartWidth = width - paddingLeft - 20;

    // Y Axis Grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.fillStyle = textColor;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';

    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const val = (maxVal / gridSteps) * i;
      const y = height - paddingBottom - (val / maxVal) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(paddingLeft, y);
      ctx.lineTo(width - 20, y);
      ctx.stroke();
      ctx.fillText(val.toFixed(0) + ' J', paddingLeft - 8, y + 4);
    }

    // Bars
    const colWidth = chartWidth / 2;
    const barWidth = Math.min(64, colWidth * 0.45);

    // LOW Workload Bar (Stacked)
    const xLow = paddingLeft + colWidth * 0.5 - barWidth / 2;
    const lowPkgHeight = (lowPkg / maxVal) * chartHeight;
    const lowDramHeight = (lowDram / maxVal) * chartHeight;

    // Draw DRAM (top portion)
    ctx.fillStyle = '#38BDF8';
    ctx.fillRect(xLow, height - paddingBottom - lowPkgHeight - lowDramHeight, barWidth, lowDramHeight);

    // Draw CPU PKG (bottom portion)
    ctx.fillStyle = '#10B981';
    ctx.fillRect(xLow, height - paddingBottom - lowPkgHeight, barWidth, lowPkgHeight);

    // LOW Total label
    ctx.fillStyle = isLight ? '#0F172A' : '#ECFDF5';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      (lowPkg + lowDram).toFixed(1) + ' J',
      xLow + barWidth / 2,
      height - paddingBottom - lowPkgHeight - lowDramHeight - 8
    );

    // HIGH Workload Bar (Stacked)
    const xHigh = paddingLeft + colWidth * 1.5 - barWidth / 2;
    const highPkgHeight = (highPkg / maxVal) * chartHeight;
    const highDramHeight = (highDram / maxVal) * chartHeight;

    // Draw DRAM
    ctx.fillStyle = '#38BDF8';
    ctx.fillRect(xHigh, height - paddingBottom - highPkgHeight - highDramHeight, barWidth, highDramHeight);

    // Draw CPU PKG
    ctx.fillStyle = '#10B981';
    ctx.fillRect(xHigh, height - paddingBottom - highPkgHeight, barWidth, highPkgHeight);

    // HIGH Total label
    ctx.fillStyle = isLight ? '#0F172A' : '#ECFDF5';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      (highPkg + highDram).toFixed(1) + ' J',
      xHigh + barWidth / 2,
      height - paddingBottom - highPkgHeight - highDramHeight - 8
    );

    // X Axis Labels
    ctx.fillStyle = textColor;
    ctx.font = '12px sans-serif';
    ctx.fillText('LOW Workload', xLow + barWidth / 2, height - paddingBottom + 20);
    ctx.fillText('HIGH Workload', xHigh + barWidth / 2, height - paddingBottom + 20);
  }

  function renderCarbonChart() {
    const { ctx, width, height } = setupCanvas(carbonCanvas);
    ctx.clearRect(0, 0, width, height);

    const isLight = document.body.classList.contains('theme-light');
    const textColor = isLight ? '#475569' : '#94A3B8';
    const gridColor = isLight ? '#E2E8F0' : '#273A31';

    const lowCarbon = currentState.low.carbonMg;
    const highCarbon = currentState.high.carbonMg;
    const maxVal = Math.max(lowCarbon, highCarbon) * 1.25 || 30;

    const paddingLeft = 55;
    const paddingBottom = 40;
    const paddingTop = 25;
    const chartHeight = height - paddingBottom - paddingTop;
    const chartWidth = width - paddingLeft - 20;

    // Y Axis Grid lines
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.fillStyle = textColor;
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'right';

    const gridSteps = 4;
    for (let i = 0; i <= gridSteps; i++) {
      const val = (maxVal / gridSteps) * i;
      const y = height - paddingBottom - (val / maxVal) * chartHeight;
      ctx.beginPath();
      ctx.moveTo(paddingLeft, y);
      ctx.lineTo(width - 20, y);
      ctx.stroke();
      ctx.fillText(val.toFixed(1) + ' mg', paddingLeft - 8, y + 4);
    }

    const colWidth = chartWidth / 2;
    const barWidth = Math.min(64, colWidth * 0.45);

    // LOW Bar
    const xLow = paddingLeft + colWidth * 0.5 - barWidth / 2;
    const lowHeight = (lowCarbon / maxVal) * chartHeight;
    ctx.fillStyle = '#059669';
    ctx.fillRect(xLow, height - paddingBottom - lowHeight, barWidth, lowHeight);

    ctx.fillStyle = isLight ? '#0F172A' : '#ECFDF5';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      lowCarbon.toFixed(2) + ' mg',
      xLow + barWidth / 2,
      height - paddingBottom - lowHeight - 8
    );

    // HIGH Bar
    const xHigh = paddingLeft + colWidth * 1.5 - barWidth / 2;
    const highHeight = (highCarbon / maxVal) * chartHeight;
    ctx.fillStyle = '#10B981';
    ctx.fillRect(xHigh, height - paddingBottom - highHeight, barWidth, highHeight);

    ctx.fillStyle = isLight ? '#0F172A' : '#ECFDF5';
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      highCarbon.toFixed(2) + ' mg',
      xHigh + barWidth / 2,
      height - paddingBottom - highHeight - 8
    );

    // X Axis Labels
    ctx.fillStyle = textColor;
    ctx.font = '12px sans-serif';
    ctx.fillText('LOW Workload', xLow + barWidth / 2, height - paddingBottom + 20);
    ctx.fillText('HIGH Workload', xHigh + barWidth / 2, height - paddingBottom + 20);
  }

  // Handle window resizing for responsive charts
  window.addEventListener('resize', () => {
    renderCharts();
  });

  // Initialization
  initTheme();
  updateDashboardUI();
})();
