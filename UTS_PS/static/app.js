let stockChartInstance = null;
let flowChartInstance = null;

const sliders = [
    'months',
    'safety_stock_factor',
    'lead_time_supplier',
    'demand_shock_percent',
    'shock_start_month',
    'adjustment_time'
];

document.addEventListener('DOMContentLoaded', () => {
    sliders.forEach(id => {
        const input = document.getElementById(id);
        const display = document.getElementById(`val_${id}`);
        input.addEventListener('input', (e) => {
            display.textContent = e.target.value;
            fetchAndRenderSimulation();
        });
    });

    fetchAndRenderSimulation();
});

async function fetchAndRenderSimulation() {
    const params = new URLSearchParams({
        months: document.getElementById('months').value,
        safety_stock_factor: document.getElementById('safety_stock_factor').value,
        lead_time_supplier: document.getElementById('lead_time_supplier').value,
        demand_shock_percent: document.getElementById('demand_shock_percent').value,
        shock_start_month: document.getElementById('shock_start_month').value,
        adjustment_time: document.getElementById('adjustment_time').value
    });

    try {
        const response = await fetch(`/api/simulate?${params.toString()}`);
        const data = await response.json();

        updateMetrics(data);
        renderStockChart(data.simulation);
        renderFlowChart(data.simulation);
    } catch (err) {
        console.error("Gagal mengambil data simulasi:", err);
    }
}

function updateMetrics(data) {
    document.getElementById('baseRetailSales').textContent = data.baseline.retail_sales.toLocaleString();
    document.getElementById('baseWarehouseSales').textContent = data.baseline.warehouse_sales.toLocaleString();

    const totalStockout = data.simulation.retail_stockout.reduce((a, b) => a + b, 0);
    document.getElementById('totalRetailStockout').textContent = Math.round(totalStockout).toLocaleString();

    const statusText = document.getElementById('statusText');
    if (data.baseline.data_loaded_from_csv) {
        statusText.textContent = "Data sales.csv Berhasil Dimuat";
        statusText.style.color = "#008744";
    } else {
        statusText.textContent = "Menggunakan Baseline Fallback (CSV Tidak Ditemukan)";
        statusText.style.color = "#ffa700";
    }
}

function renderStockChart(simData) {
    const ctx = document.getElementById('stockChart').getContext('2d');
    if (stockChartInstance) stockChartInstance.destroy();

    stockChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: simData.month.map(m => `Bulan ${m}`),
            datasets: [
                {
                    label: 'Stok Gudang (Warehouse Stock)',
                    data: simData.warehouse_stock,
                    borderColor: '#0057e7',
                    backgroundColor: 'rgba(0, 87, 231, 0.1)',
                    fill: true,
                    tension: 0.2
                },
                {
                    label: 'Stok Toko Ritel (Retail Stock)',
                    data: simData.retail_stock,
                    borderColor: '#008744',
                    backgroundColor: 'rgba(0, 135, 68, 0.1)',
                    fill: true,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f8fafc' } } }
        }
    });
}

function renderFlowChart(simData) {
    const ctx = document.getElementById('flowChart').getContext('2d');
    if (flowChartInstance) flowChartInstance.destroy();

    flowChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: simData.month.map(m => `Bulan ${m}`),
            datasets: [
                {
                    label: 'Retail Sales Actual',
                    data: simData.retail_sales,
                    borderColor: '#008744',
                    borderDash: [],
                    tension: 0.2
                },
                {
                    label: 'Retail Demand (Target)',
                    data: simData.retail_demand,
                    borderColor: '#ffa700',
                    borderDash: [5, 5],
                    tension: 0.2
                },
                {
                    label: 'Retail Transfers Outflow',
                    data: simData.retail_transfers,
                    borderColor: '#0057e7',
                    tension: 0.2
                },
                {
                    label: 'Retail Stockout (Kehabisan Stok)',
                    data: simData.retail_stockout,
                    borderColor: '#d62d20',
                    backgroundColor: 'rgba(214, 45, 32, 0.2)',
                    fill: true,
                    tension: 0.2
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } },
                x: { grid: { color: '#334155' }, ticks: { color: '#94a3b8' } }
            },
            plugins: { legend: { labels: { color: '#f8fafc' } } }
        }
    });
}