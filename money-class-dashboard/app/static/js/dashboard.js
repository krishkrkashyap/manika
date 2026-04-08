// ═══════════════════════════════════════════════════════════════════════════
// Money Class Dashboard - Enhanced JavaScript with Charts
// ═══════════════════════════════════════════════════════════════════════════

// Chart instances
let mtmBarChart = null;
let positionsPieChart = null;
let scenarioLineChart = null;
let marginChart = null;

// ═══════════════════════════════════════════════════════════════════════════
// UTILITY FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function formatCurrency(value) {
    if (value === null || value === undefined) return '--';
    const absValue = Math.abs(value);
    if (absValue >= 10000000) return '₹' + (value / 10000000).toFixed(2) + 'Cr';
    if (absValue >= 100000) return '₹' + (value / 100000).toFixed(2) + 'L';
    return '₹' + value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatNumber(value) {
    if (value === null || value === undefined) return '--';
    return value.toLocaleString('en-IN');
}

function getMTMColor(value) {
    if (value > 0) return '#22C55E';
    if (value < 0) return '#EF4444';
    return '#94A3B8';
}

// ═══════════════════════════════════════════════════════════════════════════
// TAB NAVIGATION
// ═══════════════════════════════════════════════════════════════════════════

function switchTab(tabName) {
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
    });
    event.target.closest('.nav-item').classList.add('active');
    
    // Show correct content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
        content.classList.remove('active');
    });
    const tabContent = document.getElementById('tab-' + tabName);
    if (tabContent) {
        tabContent.classList.remove('hidden');
        tabContent.classList.add('active');
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// WEBSOCKET CONNECTION
// ═══════════════════════════════════════════════════════════════════════════

let ws = null;
let reconnectAttempts = 0;
const maxReconnectAttempts = 10;

// Stock scenario state
let currentStockScenario = 'all';
let allStockScenarios = {};
let availableStocks = [];

function connectWebSocket() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
    
    console.log('Connecting to WebSocket:', wsUrl);
    
    ws = new WebSocket(wsUrl);
    
    ws.onopen = function() {
        console.log('WebSocket connected');
        reconnectAttempts = 0;
        document.getElementById('wsDot').classList.remove('disconnected');
        document.getElementById('wsDot').style.background = '#22C55E';
        document.getElementById('wsDot').style.boxShadow = '0 0 10px #22C55E';
        document.getElementById('wsStatus').textContent = 'Live';
        document.getElementById('wsSettingsStatus').textContent = 'Connected';
    };
    
    ws.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'update') {
                updateDashboard(data);
            }
        } catch (e) {
            console.error('Error parsing message:', e);
        }
    };
    
    ws.onclose = function() {
        console.log('WebSocket disconnected');
        document.getElementById('wsDot').classList.add('disconnected');
        document.getElementById('wsDot').style.background = '#EF4444';
        document.getElementById('wsDot').style.boxShadow = '0 0 10px #EF4444';
        document.getElementById('wsStatus').textContent = 'Disconnected';
        document.getElementById('wsSettingsStatus').textContent = 'Disconnected';
        
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`Reconnecting... Attempt ${reconnectAttempts}`);
            setTimeout(connectWebSocket, 3000);
        }
    };
    
    ws.onerror = function(error) {
        console.error('WebSocket error:', error);
    };
}

// ═══════════════════════════════════════════════════════════════════════════
// CHART INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

function initCharts() {
    // MTM Bar Chart
    const mtmCtx = document.getElementById('mtmBarChart').getContext('2d');
    mtmBarChart = new Chart(mtmCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'MTM (₹)',
                data: [],
                backgroundColor: [],
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94A3B8' }
                },
                y: {
                    grid: { color: '#334155' },
                    ticks: { 
                        color: '#94A3B8',
                        callback: function(value) { return formatCurrency(value); }
                    }
                }
            }
        }
    });
    
    // Positions Pie Chart
    const pieCtx = document.getElementById('positionsPieChart').getContext('2d');
    positionsPieChart = new Chart(pieCtx, {
        type: 'doughnut',
        data: {
            labels: [],
            datasets: [{
                data: [],
                backgroundColor: [
                    '#F59E0B', '#8B5CF6', '#06B6D4', '#22C55E', '#EF4444',
                    '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#94A3B8', padding: 15 }
                }
            }
        }
    });
    
    // Scenario Line Chart
    const scenarioCtx = document.getElementById('scenarioLineChart').getContext('2d');
    scenarioLineChart = new Chart(scenarioCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'MTM (₹)',
                data: [],
                borderColor: '#F59E0B',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#F59E0B',
                pointBorderColor: '#fff',
                pointRadius: 6,
                pointHoverRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#334155' },
                    ticks: { color: '#94A3B8' }
                },
                y: {
                    grid: { color: '#334155' },
                    ticks: { 
                        color: '#94A3B8',
                        callback: function(value) { return formatCurrency(value); }
                    }
                }
            }
        }
    });
    
    // Margin Chart
    const marginCtx = document.getElementById('marginChart').getContext('2d');
    marginChart = new Chart(marginCtx, {
        type: 'bar',
        data: {
            labels: ['Futures', 'Options'],
            datasets: [{
                data: [0, 0],
                backgroundColor: ['#8B5CF6', '#06B6D4'],
                borderRadius: 6,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: {
                    grid: { color: '#334155' },
                    ticks: { 
                        color: '#94A3B8',
                        callback: function(value) { return formatCurrency(value); }
                    }
                },
                y: {
                    grid: { display: false },
                    ticks: { color: '#94A3B8' }
                }
            }
        }
    });
}

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD UPDATE FUNCTIONS
// ═══════════════════════════════════════════════════════════════════════════

function updateDashboard(data) {
    const now = new Date();
    document.getElementById('currentTime').textContent = now.toLocaleTimeString();
    document.getElementById('lastUpdateTime').textContent = now.toLocaleTimeString();
    
    const positions = data.positions || [];
    const mtm = data.mtm || {};
    const margin = data.margin || {};
    
    // Update KPI cards
    updateKPIs(positions, mtm, margin);
    
    // Update tables
    updatePositionsTable(positions);
    updateMarginTable(margin);
    
    // Update MTM tab
    updateMTMTable(mtm);
    
    // Update charts
    updateCharts(positions, mtm, margin);
    
    // Update scenarios
    updateScenarios(mtm);
    
    // Load alerts
    loadAlerts();
}

function updateKPIs(positions, mtm, margin) {
    // Total MTM
    const totalMtm = mtm.total_mtm || 0;
    const mtmEl = document.getElementById('totalMtm');
    mtmEl.textContent = formatCurrency(totalMtm);
    mtmEl.style.color = getMTMColor(totalMtm);
    
    // Position Value
    let positionValue = 0;
    positions.forEach(pos => {
        const ltp = pos.ltp || 0;
        const qty = Math.abs(pos.net_qty || 0);
        positionValue += ltp * qty;
    });
    document.getElementById('positionValue').textContent = formatCurrency(positionValue);
    
    // Total Margin
    const totalMargin = margin.total_margin || 0;
    document.getElementById('totalMargin').textContent = formatCurrency(totalMargin);
    
    // Position Count
    document.getElementById('positionCount').textContent = positions.length;
}

function updatePositionsTable(positions) {
    const tbody = document.getElementById('positionsTable');
    const allPosTable = document.getElementById('allPositionsTable');
    
    if (!positions || positions.length === 0) {
        const emptyRow = '<tr><td colspan="6" class="loading">No positions</td></tr>';
        if (tbody) tbody.innerHTML = emptyRow;
        if (allPosTable) allPosTable.innerHTML = emptyRow;
        return;
    }
    
    let html = '';
    positions.forEach(pos => {
        const m2m = pos.m2m || pos.mtm || 0;
        const colorClass = m2m >= 0 ? 'positive' : 'negative';
        const typeClass = pos.type === 'FUT' ? 'fut' : (pos.type === 'PE' ? 'pe' : 'ce');
        
        html += `
            <tr>
                <td>
                    <div class="stock-name">${pos.stock || '--'}</div>
                    <div class="stock-symbol">${pos.symbol || ''}</div>
                </td>
                <td><span class="type-badge ${typeClass}">${pos.type || '--'}</span></td>
                <td>${formatNumber(pos.net_qty || 0)}</td>
                <td>${formatCurrency(pos.ltp || 0)}</td>
                <td>${formatCurrency(pos.buy_avg || 0)}</td>
                <td class="mtm-value ${colorClass}">${formatCurrency(m2m)}</td>
            </tr>
        `;
    });
    
    if (tbody) tbody.innerHTML = html;
    if (allPosTable) allPosTable.innerHTML = html;
}

function updateMarginTable(margin) {
    const tbody = document.getElementById('marginTable');
    if (!margin) {
        tbody.innerHTML = '<tr><td colspan="2" class="loading">No data</td></tr>';
        return;
    }
    
    tbody.innerHTML = `
        <tr>
            <td><strong>Futures</strong></td>
            <td class="mtm-value">${formatCurrency(margin.futures_margin || 0)}</td>
        </tr>
        <tr>
            <td><strong>Options</strong></td>
            <td class="mtm-value">${formatCurrency(margin.options_margin || 0)}</td>
        </tr>
        <tr style="background: var(--bg-primary);">
            <td><strong>Total</strong></td>
            <td class="mtm-value" style="color: var(--accent);">${formatCurrency(margin.total_margin || 0)}</td>
        </tr>
    `;
}

function updateCharts(positions, mtm, margin) {
    // MTM Bar Chart - MTM by Stock
    const stockMTM = {};
    positions.forEach(pos => {
        const stock = pos.stock || 'Unknown';
        const m2m = pos.m2m || pos.mtm || 0;
        stockMTM[stock] = (stockMTM[stock] || 0) + m2m;
    });
    
    const stocks = Object.keys(stockMTM);
    const mtmValues = Object.values(stockMTM);
    const mtmColors = mtmValues.map(v => v >= 0 ? '#22C55E' : '#EF4444');
    
    if (mtmBarChart) {
        mtmBarChart.data.labels = stocks;
        mtmBarChart.data.datasets[0].data = mtmValues;
        mtmBarChart.data.datasets[0].backgroundColor = mtmColors;
        mtmBarChart.update();
    }
    
    // Positions Pie Chart
    const positionValues = {};
    positions.forEach(pos => {
        const stock = pos.stock || 'Unknown';
        const value = (pos.ltp || 0) * Math.abs(pos.net_qty || 0);
        positionValues[stock] = (positionValues[stock] || 0) + value;
    });
    
    if (positionsPieChart) {
        positionsPieChart.data.labels = Object.keys(positionValues);
        positionsPieChart.data.datasets[0].data = Object.values(positionValues);
        positionsPieChart.update();
    }
    
    // Margin Chart
    if (marginChart) {
        marginChart.data.datasets[0].data = [
            margin.futures_margin || 0,
            margin.options_margin || 0
        ];
        marginChart.update();
    }
}

function updateScenarios(mtm) {
    const scenarios = mtm.scenarios || [];
    
    // Store per-stock scenarios
    allStockScenarios = mtm.stock_scenarios || {};
    availableStocks = mtm.stocks || [];
    
    // Populate stock selector
    const selector = document.getElementById('stockSelector');
    if (selector) {
        selector.innerHTML = '<option value="all">All Stocks</option>' + 
            availableStocks.map(s => `<option value="${s}">${s}</option>`).join('');
    }
    
    // Quick scenarios grid
    const quickScenarios = document.getElementById('quickScenarios');
    if (quickScenarios && scenarios.length > 0) {
        let html = '';
        scenarios.forEach(s => {
            const m2m = s.total_mtm || 0;
            const colorClass = m2m >= 0 ? 'positive' : 'negative';
            html += `
                <div class="scenario-card">
                    <div class="scenario-label">${s.percentage}</div>
                    <div class="scenario-value ${colorClass}">${formatCurrency(m2m)}</div>
                </div>
            `;
        });
        quickScenarios.innerHTML = html;
    }
    
    // Scenario Line Chart - show total or stock-specific
    if (currentStockScenario === 'all') {
        // Show total scenarios (existing behavior)
        if (scenarioLineChart && scenarios.length > 0) {
            scenarioLineChart.data.labels = scenarios.map(s => s.percentage);
            scenarioLineChart.data.datasets[0].data = scenarios.map(s => s.total_mtm || 0);
            scenarioLineChart.data.datasets[0].label = 'Total MTM (₹)';
            scenarioLineChart.update();
        }
    } else if (allStockScenarios[currentStockScenario]) {
        // Show stock-specific breakdown
        showStockScenarioChart(currentStockScenario, allStockScenarios[currentStockScenario]);
    }
    
    // Full scenario table
    const scenarioTable = document.getElementById('scenarioTable');
    if (scenarioTable && scenarios.length > 0) {
        let html = '';
        scenarios.forEach(s => {
            const m2m = s.total_mtm || 0;
            const colorClass = m2m >= 0 ? 'positive' : 'negative';
            const impact = m2m >= 0 ? 'Profit' : 'Loss';
            html += `
                <tr>
                    <td>${s.percentage}</td>
                    <td>${(s.pct_value * 100).toFixed(1)}%</td>
                    <td class="mtm-value ${colorClass}">${formatCurrency(m2m)}</td>
                    <td><span class="type-badge ${m2m >= 0 ? 'ce' : 'pe'}">${impact}</span></td>
                </tr>
            `;
        });
        scenarioTable.innerHTML = html;
    }
}

function updateStockScenario() {
    const selector = document.getElementById('stockSelector');
    if (!selector) return;
    
    currentStockScenario = selector.value;
    
    // Re-render the scenario chart with selected stock
    const scenarios = document.getElementById('stockSelector')?.value === 'all' 
        ? [] 
        : allStockScenarios[currentStockScenario];
    
    if (currentStockScenario === 'all') {
        // Fetch scenarios from mtm data
        fetchData('scenarios').then(data => {
            if (data && data.success) {
                if (scenarioLineChart && data.scenarios.length > 0) {
                    scenarioLineChart.data.labels = data.scenarios.map(s => s.percentage);
                    scenarioLineChart.data.datasets[0].data = data.scenarios.map(s => s.total_mtm || 0);
                    scenarioLineChart.data.datasets[0].label = 'Total MTM (₹)';
                    scenarioLineChart.data.datasets[0].borderColor = '#F59E0B';
                    scenarioLineChart.data.datasets[0].backgroundColor = 'rgba(245, 158, 11, 0.1)';
                    scenarioLineChart.update();
                }
            }
        });
    } else if (allStockScenarios[currentStockScenario]) {
        showStockScenarioChart(currentStockScenario, allStockScenarios[currentStockScenario]);
    }
}

function showStockScenarioChart(stock, scenarios) {
    // Show futures, options, total for selected stock
    const ctx = document.getElementById('scenarioLineChart');
    if (!ctx || !scenarioLineChart) return;
    
    // Update chart with 3 datasets: futures, options, total
    scenarioLineChart.data.labels = scenarios.map(s => s.percentage);
    
    // Update or add datasets
    if (scenarioLineChart.data.datasets.length === 1) {
        // Add additional datasets
        scenarioLineChart.data.datasets.push({
            label: 'Futures MTM (₹)',
            data: scenarios.map(s => s.futures_mtm || 0),
            borderColor: '#8B5CF6',
            backgroundColor: 'rgba(139, 92, 246, 0.1)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#8B5CF6',
            pointBorderColor: '#fff',
            pointRadius: 4,
            pointHoverRadius: 6
        });
        scenarioLineChart.data.datasets.push({
            label: 'Options MTM (₹)',
            data: scenarios.map(s => s.options_mtm || 0),
            borderColor: '#06B6D4',
            backgroundColor: 'rgba(6, 182, 212, 0.1)',
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#06B6D4',
            pointBorderColor: '#fff',
            pointRadius: 4,
            pointHoverRadius: 6
        });
    }
    
    // Update main dataset to be Total
    scenarioLineChart.data.datasets[0].label = 'Total MTM (₹)';
    scenarioLineChart.data.datasets[0].data = scenarios.map(s => s.total_mtm || 0);
    scenarioLineChart.data.datasets[0].borderColor = '#F59E0B';
    scenarioLineChart.data.datasets[0].backgroundColor = 'rgba(245, 158, 11, 0.1)';
    
    // Update futures and options datasets
    if (scenarioLineChart.data.datasets.length >= 3) {
        scenarioLineChart.data.datasets[1].data = scenarios.map(s => s.futures_mtm || 0);
        scenarioLineChart.data.datasets[2].data = scenarios.map(s => s.options_mtm || 0);
    }
    
    // Enable legend
    scenarioLineChart.options.plugins.legend = {
        display: true,
        position: 'bottom',
        labels: { color: '#94A3B8', padding: 15 }
    };
    
    scenarioLineChart.update();
}

// ═══════════════════════════════════════════════════════════════════════════
// MARGIN CALCULATOR
// ═══════════════════════════════════════════════════════════════════════════

function calculateMargin() {
    const qty = parseInt(document.getElementById('calcQty').value) || 0;
    const price = parseFloat(document.getElementById('calcPrice').value) || 0;
    const product = document.getElementById('calcProduct').value.toUpperCase();
    
    if (qty <= 0 || price <= 0) {
        document.getElementById('calcTotalValue').textContent = '₹0';
        document.getElementById('calcMarginReq').textContent = '₹0';
        document.getElementById('calcLeverage').textContent = '0x';
        return;
    }
    
    const totalValue = qty * price;
    let marginRate = 0.12; // Default 12%
    
    if (product === 'CNC') marginRate = 0;
    else if (product === 'NRML') marginRate = 0.12;
    else if (product === 'MIS') marginRate = 0.12;
    
    const margin = totalValue * marginRate;
    const leverage = margin > 0 ? (totalValue / margin).toFixed(2) : 0;
    
    document.getElementById('calcTotalValue').textContent = formatCurrency(totalValue);
    document.getElementById('calcMarginReq').textContent = formatCurrency(margin);
    document.getElementById('calcLeverage').textContent = leverage + 'x';
}

// ═══════════════════════════════════════════════════════════════════
// POSITIONS FILTER
// ═══════════════════════════════════════════════════════════════════

let currentPositionFilter = 'all';

async function filterPositions(filter) {
    currentPositionFilter = filter;
    
    // Update active button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.filter === filter) {
            btn.classList.add('active');
        }
    });
    
    // Fetch filtered positions
    try {
        const response = await fetch('/api/positions?filter=' + filter);
        const data = await response.json();
        
        if (data.success) {
            updatePositionsTable(data.positions);
        }
    } catch (error) {
        console.error('Error filtering positions:', error);
    }
}

function updatePositionsTable(positions) {
    const tbody = document.getElementById('positionsTableBody');
    if (!tbody) return;
    
    if (!positions || positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" class="loading">No positions found</td></tr>';
        return;
    }
    
    tbody.innerHTML = positions.map(pos => {
        const m2m = pos.m2m || pos.mtm || 0;
        const isProfit = m2m >= 0;
        const typeClass = pos.type === 'FUT' ? 'fut' : (pos.type === 'PE' ? 'pe' : 'ce');
        const buyQty = pos.buy_qty || pos.net_qty > 0 ? Math.abs(pos.net_qty) : '-';
        const sellQty = pos.sell_qty || pos.net_qty < 0 ? Math.abs(pos.net_qty) : '-';
        
        return `
            <tr>
                <td>
                    <div class="stock-name">${pos.stock || '--'}</div>
                </td>
                <td><div class="stock-symbol">${pos.symbol || '--'}</div></td>
                <td><span class="type-badge ${typeClass}">${pos.type || '--'}</span></td>
                <td>${pos.buy_qty || (pos.net_qty > 0 ? pos.net_qty : '-')}</td>
                <td>${pos.sell_qty || (pos.net_qty < 0 ? Math.abs(pos.net_qty) : '-')}</td>
                <td>${pos.net_qty || 0}</td>
                <td>${formatCurrency(pos.buy_avg || 0)}</td>
                <td>${formatCurrency(pos.sell_avg || 0)}</td>
                <td>${formatCurrency(pos.ltp || 0)}</td>
                <td class="mtm-value ${isProfit ? 'positive' : 'negative'}">${formatCurrency(m2m)}</td>
            </tr>
        `;
    }).join('');
}

// ═══════════════════════════════════════════════════════════════════
// MTM TAB - LAST/INTRA/EXP
// ═══════════════════════════════════════════════════════════════════

function updateMTMTable(mtmData) {
    const tbody = document.getElementById('mtmTableBody');
    if (!tbody || !mtmData) return;
    
    const positions = mtmData.positions || [];
    
    // Update KPI cards
    const lastEl = document.getElementById('lastMtmTotal');
    const intraEl = document.getElementById('intraMtmTotal');
    const expEl = document.getElementById('expMtmTotal');
    
    if (lastEl) {
        lastEl.textContent = formatCurrency(mtmData.last_total || 0);
        lastEl.style.color = getMTMColor(mtmData.last_total || 0);
    }
    if (intraEl) {
        intraEl.textContent = formatCurrency(mtmData.intra_total || 0);
        intraEl.style.color = getMTMColor(mtmData.intra_total || 0);
    }
    if (expEl) {
        expEl.textContent = formatCurrency(mtmData.exp_total || 0);
        expEl.style.color = getMTMColor(mtmData.exp_total || 0);
    }
    
    if (positions.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="loading">No positions</td></tr>';
        return;
    }
    
    tbody.innerHTML = positions.map(pos => {
        const lastColor = getMTMColor(pos.last_mtm || 0);
        const intraColor = getMTMColor(pos.intra_mtm || 0);
        const expColor = getMTMColor(pos.exp_mtm || 0);
        const typeClass = pos.type === 'FUT' ? 'fut' : (pos.type === 'PE' ? 'pe' : 'ce');
        
        return `
            <tr onclick="openStockDrilldown('${pos.stock}')" style="cursor: pointer;">
                <td><strong>${pos.stock || '--'}</strong></td>
                <td><div class="stock-symbol">${pos.symbol || '--'}</div></td>
                <td><span class="type-badge ${typeClass}">${pos.type || '--'}</span></td>
                <td>${formatNumber(pos.net_qty || 0)}</td>
                <td>${formatCurrency(pos.ltp || 0)}</td>
                <td style="color: ${lastColor}">${formatCurrency(pos.last_mtm || 0)}</td>
                <td style="color: ${intraColor}">${formatCurrency(pos.intra_mtm || 0)}</td>
                <td style="color: ${expColor}">${formatCurrency(pos.exp_mtm || 0)}</td>
            </tr>
        `;
    }).join('');
}

async function openStockDrilldown(stock) {
    const modal = document.getElementById('stockDrilldown');
    const nameEl = document.getElementById('drilldownStockName');
    const bodyEl = document.getElementById('drilldownBody');
    
    if (!modal || !bodyEl) return;
    
    nameEl.textContent = stock + ' - Detailed MTM';
    bodyEl.innerHTML = '<div class="loading">Loading...</div>';
    modal.classList.remove('hidden');
    
    try {
        const [mtmRes, optionsRes] = await Promise.all([
            fetch('/api/mtm/' + stock),
            fetch('/api/options/' + stock)
        ]);
        
        const mtmData = await mtmRes.json();
        const optionsData = await optionsRes.json();
        
        if (!mtmData.success) {
            bodyEl.innerHTML = '<p>No data found for ' + stock + '</p>';
            return;
        }
        
        const positions = mtmData.mtm.positions || [];
        const pePositions = optionsData.pe.positions || [];
        const cePositions = optionsData.ce.positions || [];
        const totalExp = optionsData.total_exp || 0;
        
        let html = '<div class="stock-kpi">';
        html += `<div class="kpi-card"><div class="kpi-label">LAST MTM</div><div class="kpi-value" style="color: ${getMTMColor(mtmData.mtm.last_total)}">${formatCurrency(mtmData.mtm.last_total)}</div></div>`;
        html += `<div class="kpi-card"><div class="kpi-label">INTRA MTM</div><div class="kpi-value" style="color: ${getMTMColor(mtmData.mtm.intra_total)}">${formatCurrency(mtmData.mtm.intra_total)}</div></div>`;
        html += `<div class="kpi-card"><div class="kpi-label">EXP MTM</div><div class="kpi-value" style="color: ${getMTMColor(mtmData.mtm.exp_total)}">${formatCurrency(mtmData.mtm.exp_total)}</div></div>`;
        html += '</div>';
        
        html += '<h4 style="margin: 16px 0 8px;">Positions</h4>';
        html += '<table class="data-table"><thead><tr><th>Symbol</th><th>Type</th><th>Net Qty</th><th>LTP</th><th>LAST</th><th>INTRA</th><th>EXP</th></tr></thead><tbody>';
        
        positions.forEach(pos => {
            html += `<tr>
                <td>${pos.symbol}</td>
                <td><span class="type-badge ${pos.type === 'FUT' ? 'fut' : (pos.type === 'PE' ? 'pe' : 'ce')}">${pos.type}</span></td>
                <td>${formatNumber(pos.net_qty)}</td>
                <td>${formatCurrency(pos.ltp)}</td>
                <td style="color: ${getMTMColor(pos.last_mtm)}">${formatCurrency(pos.last_mtm)}</td>
                <td style="color: ${getMTMColor(pos.intra_mtm)}">${formatCurrency(pos.intra_mtm)}</td>
                <td style="color: ${getMTMColor(pos.exp_mtm)}">${formatCurrency(pos.exp_mtm)}</td>
            </tr>`;
        });
        
        html += '</tbody></table>';
        
        html += '<h4 style="margin: 16px 0 8px;">Options Breakdown</h4>';
        html += '<div class="stock-kpi">';
        html += `<div class="kpi-card"><div class="kpi-label">PE MTM</div><div class="kpi-value" style="color: ${getMTMColor(optionsData.pe.exp_total)}">${formatCurrency(optionsData.pe.exp_total)}</div></div>`;
        html += `<div class="kpi-card"><div class="kpi-label">CE MTM</div><div class="kpi-value" style="color: ${getMTMColor(optionsData.ce.exp_total)}">${formatCurrency(optionsData.ce.exp_total)}</div></div>`;
        html += `<div class="kpi-card"><div class="kpi-label">TOTAL OPTIONS</div><div class="kpi-value" style="color: ${getMTMColor(totalExp)}">${formatCurrency(totalExp)}</div></div>`;
        html += '</div>';
        
        bodyEl.innerHTML = html;
    } catch (error) {
        bodyEl.innerHTML = '<p>Error loading data: ' + error.message + '</p>';
    }
}

function closeDrilldown() {
    const modal = document.getElementById('stockDrilldown');
    if (modal) modal.classList.add('hidden');
}

// ═══════════════════════════════════════════════════════════════════
// TRADES TAB
// ═══════════════════════════════════════════════════════════════════

async function loadTrades() {
    const tbody = document.getElementById('tradesTableBody');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/trades');
        const data = await response.json();
        
        if (!data.success || !data.trades || data.trades.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="loading">No trades found</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.trades.map(trade => {
            const typeColor = trade.type === 'BUY' ? 'var(--green)' : 'var(--red)';
            return `
                <tr>
                    <td>${trade.time || '--'}</td>
                    <td><strong>${trade.symbol || '--'}</strong></td>
                    <td><span style="color: ${typeColor}; font-weight: 600;">${trade.type || '--'}</span></td>
                    <td>${formatNumber(trade.qty || 0)}</td>
                    <td>${formatCurrency(trade.price || 0)}</td>
                    <td>${formatCurrency(trade.value || 0)}</td>
                </tr>
            `;
        }).join('');
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" class="loading">Error loading trades</td></tr>';
    }
}

// ═══════════════════════════════════════════════════════════════════
// ALERTS TAB
// ═══════════════════════════════════════════════════════════════════

async function addAlert() {
    const stock = document.getElementById('alertStock').value;
    const type = document.getElementById('alertType').value;
    const threshold = parseFloat(document.getElementById('alertThreshold').value) || 5;
    
    try {
        const response = await fetch('/api/alerts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stock, type, threshold })
        });
        
        const data = await response.json();
        if (data.success) {
            loadAlerts();
        }
    } catch (error) {
        console.error('Error adding alert:', error);
    }
}

async function removeAlert(alertId) {
    try {
        await fetch('/api/alerts/' + alertId, { method: 'DELETE' });
        loadAlerts();
    } catch (error) {
        console.error('Error removing alert:', error);
    }
}

async function loadAlerts() {
    const tbody = document.getElementById('alertsTableBody');
    const triggeredDiv = document.getElementById('triggeredAlerts');
    if (!tbody) return;
    
    try {
        const response = await fetch('/api/alerts');
        const data = await response.json();
        
        if (!data.success || !data.alerts || data.alerts.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="loading">No alerts set</td></tr>';
            if (triggeredDiv) triggeredDiv.innerHTML = '';
            return;
        }
        
        tbody.innerHTML = data.alerts.map(alert => {
            const statusClass = alert.triggered ? 'positive' : 'negative';
            const statusText = alert.triggered ? 'TRIGGERED' : 'Active';
            return `
                <tr>
                    <td><strong>${alert.stock}</strong></td>
                    <td>${alert.type === 'price_drop' ? 'Price Drop' : 'Price Rise'}</td>
                    <td>${alert.threshold}%</td>
                    <td><span class="type-badge ${statusClass}">${statusText}</span></td>
                    <td><button class="alert-delete-btn" onclick="removeAlert(${alert.id})">Delete</button></td>
                </tr>
            `;
        }).join('');
        
        // Show triggered alerts
        if (triggeredDiv) {
            const triggered = data.alerts.filter(a => a.triggered);
            if (triggered.length > 0) {
                triggeredDiv.innerHTML = triggered.map(a => `
                    <div class="alert-item triggered">
                        <div>
                            <strong>${a.stock}</strong> - ${a.type === 'price_drop' ? 'Price Drop' : 'Price Rise'} ${a.threshold}%
                            ${a.current_change ? ` (Current: ${a.current_change}%)` : ''}
                        </div>
                        <button class="alert-delete-btn" onclick="removeAlert(${a.id})">Dismiss</button>
                    </div>
                `).join('');
            } else {
                triggeredDiv.innerHTML = '<p style="color: var(--text-muted);">No triggered alerts</p>';
            }
        }
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="5" class="loading">Error loading alerts</td></tr>';
    }
}

async function checkAlerts() {
    try {
        await fetch('/api/alerts/check');
        loadAlerts();
    } catch (error) {
        console.error('Error checking alerts:', error);
    }
}

// ═══════════════════════════════════════════════════════════════════
// REST API FALLBACK
// ═══════════════════════════════════════════════════════════════════════════

async function fetchData(endpoint) {
    try {
        const response = await fetch('/api/' + endpoint);
        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error fetching data:', error);
        return null;
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// INITIALIZATION
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Initialize charts
    initCharts();
    
    // Connect WebSocket
    connectWebSocket();
    
    // Fallback: fetch via REST if WebSocket fails
    setTimeout(async () => {
        if (!ws || ws.readyState !== WebSocket.OPEN) {
            console.log('WebSocket not connected, fetching via REST...');
            
            // Fetch all data
            const mtmData = await fetchData('mtm');
            const marginData = await fetchData('margin');
            const scenarioData = await fetchData('scenarios');
            const tradesData = await fetchData('trades');
            
            if (mtmData && mtmData.success) {
                // Merge scenarios into mtm data
                const mtmWithScenarios = {
                    ...mtmData.mtm,
                    scenarios: scenarioData?.scenarios || [],
                    stock_scenarios: scenarioData?.stock_scenarios || {},
                    stocks: scenarioData?.stocks || []
                };
                updateDashboard({
                    positions: mtmData.mtm.positions || [],
                    mtm: mtmWithScenarios,
                    margin: marginData?.margin || {},
                    quotes: {}
                });
                
                // Update MTM tab
                updateMTMTable(mtmData.mtm);
                
                // Update trades tab
                if (tradesData && tradesData.success) {
                    const tbody = document.getElementById('tradesTableBody');
                    if (tbody && tradesData.trades) {
                        tbody.innerHTML = tradesData.trades.map(trade => {
                            const typeColor = trade.type === 'BUY' ? 'var(--green)' : 'var(--red)';
                            return `
                                <tr>
                                    <td>${trade.time || '--'}</td>
                                    <td><strong>${trade.symbol || '--'}</strong></td>
                                    <td><span style="color: ${typeColor}; font-weight: 600;">${trade.type || '--'}</span></td>
                                    <td>${formatNumber(trade.qty || 0)}</td>
                                    <td>${formatCurrency(trade.price || 0)}</td>
                                    <td>${formatCurrency(trade.value || 0)}</td>
                                </tr>
                            `;
                        }).join('');
                    }
                }
                
                // Load alerts
                loadAlerts();
            }
        }
    }, 5000);
    
    // Periodically check alerts
    setInterval(checkAlerts, 30000);
});