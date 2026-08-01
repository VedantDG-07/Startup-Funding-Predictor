/**
 * StartupIQ – Dashboard JS (static/js/dashboard.js)
 * Fetches all BI REST endpoints and renders Plotly.js charts + dynamic tables.
 */

document.addEventListener('DOMContentLoaded', () => {

    // --- Date Header ---
    const dateEl = document.getElementById('currentDate');
    if (dateEl) {
        const opts = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateEl.textContent = new Date().toLocaleDateString('en-US', opts);
    }

    // --- Stagger card entrance animation ---
    const cards = document.querySelectorAll('.dashboard-container .card');
    cards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(18px)';
        card.style.transition = 'opacity 0.45s ease, transform 0.45s ease';
        setTimeout(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
            setTimeout(() => { card.style.transition = ''; }, 450);
        }, i * 45);
    });

    // =========================================================
    // UTILITIES
    // =========================================================

    function fmtMoney(val) {
        if (!val || val === 0) return '$0';
        if (val >= 1e9) return '$' + (val / 1e9).toFixed(2) + 'B';
        if (val >= 1e6) return '$' + (val / 1e6).toFixed(2) + 'M';
        if (val >= 1e3) return '$' + (val / 1e3).toFixed(1) + 'K';
        return '$' + parseFloat(val).toFixed(0);
    }

    function statusBadge(status) {
        const map = {
            'operating': 'success',
            'acquired':  'primary',
            'closed':    'danger',
            'ipo':       'warning'
        };
        const cls = map[status] || 'secondary';
        return `<span class="badge bg-${cls}-subtle text-${cls} border border-${cls}-subtle text-capitalize">${status}</span>`;
    }

    const PLOTLY_LAYOUT = {
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor:  'rgba(0,0,0,0)',
        font: { family: 'Inter, sans-serif', size: 12, color: '#555' },
        margin: { t: 20, r: 10, b: 40, l: 50 },
        showlegend: true
    };

    const PLOTLY_CFG = { responsive: true, displayModeBar: false };

    const PALETTE = [
        '#6366f1','#22d3ee','#f59e0b','#10b981',
        '#f43f5e','#a78bfa','#34d399','#fb923c'
    ];

    // =========================================================
    // 1. KPI SCORECARDS
    // =========================================================
    fetch('/api/kpis')
        .then(r => r.json())
        .then(({ data }) => {
            const setKpi = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };
            setKpi('kpi-total-startups', data.total_startups ?? '--');
            setKpi('kpi-total-funding',  fmtMoney(data.grand_total_funding_usd));
            setKpi('kpi-success-rate',   (data.success_rate_percent ?? 0) + '%');
            setKpi('kpi-failure-rate',   (data.failure_rate_percent ?? 0) + '%');
        })
        .catch(err => console.error('[KPI Error]', err));

    // =========================================================
    // 2. INDUSTRY FUNDING – Horizontal Bar Chart
    // =========================================================
    fetch('/api/charts/industry')
        .then(r => r.json())
        .then(({ data }) => {
            if (!data || !data.length) return;
            const sorted = [...data].sort((a, b) => b.total_funding_usd - a.total_funding_usd);
            Plotly.newPlot('chart-industry', [{
                type: 'bar',
                orientation: 'h',
                x: sorted.map(d => d.total_funding_usd),
                y: sorted.map(d => d.industry),
                marker: { color: PALETTE },
                text: sorted.map(d => fmtMoney(d.total_funding_usd)),
                textposition: 'outside',
                hovertemplate: '<b>%{y}</b><br>Funding: $%{x:,.0f}<extra></extra>'
            }], {
                ...PLOTLY_LAYOUT,
                xaxis: { title: 'Total Funding (USD)', tickformat: '$.2s' },
                yaxis: { automargin: true },
                margin: { t: 20, r: 80, b: 50, l: 130 }
            }, PLOTLY_CFG);
        })
        .catch(err => console.error('[Industry Chart Error]', err));

    // =========================================================
    // 3. FUNDING STAGE DISTRIBUTION – Donut / Pie Chart
    // =========================================================
    fetch('/api/charts/funding_stages')
        .then(r => r.json())
        .then(({ data }) => {
            if (!data || !data.length) return;
            Plotly.newPlot('chart-stages', [{
                type: 'pie',
                hole: 0.46,
                labels: data.map(d => d.round_type.replace(/_/g, ' ').toUpperCase()),
                values: data.map(d => d.total_amount_raised),
                marker: { colors: PALETTE },
                textinfo: 'label+percent',
                hovertemplate: '<b>%{label}</b><br>Total: $%{value:,.0f}<br>Share: %{percent}<extra></extra>'
            }], {
                ...PLOTLY_LAYOUT,
                margin: { t: 20, r: 20, b: 20, l: 20 },
                legend: { orientation: 'v', x: 1.02, y: 0.5 }
            }, PLOTLY_CFG);
        })
        .catch(err => console.error('[Stage Chart Error]', err));

    // =========================================================
    // 4. K-MEANS CLUSTERS – Grouped Bar Chart
    // =========================================================
    fetch('/api/charts/clustering')
        .then(r => r.json())
        .then(({ data }) => {
            if (!data || !data.clusters || !data.clusters.length) return;
            const clusters = data.clusters;
            Plotly.newPlot('chart-clusters', [
                {
                    name: 'Avg Funding ($)',
                    type: 'bar',
                    x: clusters.map(c => c.cluster_label),
                    y: clusters.map(c => c.avg_funding_usd),
                    marker: { color: '#6366f1' },
                    hovertemplate: '<b>%{x}</b><br>Avg Funding: $%{y:,.0f}<extra></extra>'
                },
                {
                    name: 'Avg Failure Risk',
                    type: 'bar',
                    x: clusters.map(c => c.cluster_label),
                    y: clusters.map(c => (c.avg_failure_risk * 100).toFixed(1)),
                    yaxis: 'y2',
                    marker: { color: '#f43f5e' },
                    hovertemplate: '<b>%{x}</b><br>Failure Risk: %{y}%<extra></extra>'
                }
            ], {
                ...PLOTLY_LAYOUT,
                barmode: 'group',
                xaxis: { tickangle: -15 },
                yaxis: { title: 'Avg Funding (USD)', tickformat: '$.2s' },
                yaxis2: { title: 'Failure Risk (%)', overlaying: 'y', side: 'right', range: [0, 100] },
                legend: { orientation: 'h', y: -0.25 },
                margin: { t: 20, r: 60, b: 80, l: 60 }
            }, PLOTLY_CFG);
        })
        .catch(err => console.error('[Cluster Chart Error]', err));

    // =========================================================
    // 5. NLP SENTIMENT – Donut Chart
    // =========================================================
    fetch('/api/charts/text_mining')
        .then(r => r.json())
        .then(({ data }) => {
            if (!data || !data.sentiment_distribution || !data.sentiment_distribution.length) return;
            const sd = data.sentiment_distribution;
            const colorMap = { positive: '#10b981', neutral: '#f59e0b', negative: '#f43f5e' };
            Plotly.newPlot('chart-sentiment', [{
                type: 'pie',
                hole: 0.50,
                labels: sd.map(d => d.sentiment_label),
                values: sd.map(d => d.count),
                marker: { colors: sd.map(d => colorMap[d.sentiment_label] || '#6366f1') },
                textinfo: 'label+percent',
                hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>Share: %{percent}<extra></extra>'
            }], {
                ...PLOTLY_LAYOUT,
                margin: { t: 20, r: 20, b: 20, l: 20 },
                legend: { orientation: 'h', x: 0.15, y: -0.15 }
            }, PLOTLY_CFG);
        })
        .catch(err => console.error('[Sentiment Chart Error]', err));

    // =========================================================
    // 6. TOP INVESTORS TABLE
    // =========================================================
    fetch('/api/charts/investors')
        .then(r => r.json())
        .then(({ data }) => {
            const tbody = document.querySelector('#table-investors tbody');
            if (!tbody || !data || !data.length) return;
            tbody.innerHTML = data.slice(0, 10).map(inv => `
                <tr>
                    <td class="fw-medium">${inv.investor_name}</td>
                    <td><span class="badge bg-secondary-subtle text-secondary text-capitalize">${inv.investor_type}</span></td>
                    <td>${inv.country || '—'}</td>
                    <td><span class="badge bg-primary-subtle text-primary">${inv.portfolio_startups_count}</span></td>
                    <td class="fw-medium text-success">${fmtMoney(inv.total_capital_deployed)}</td>
                </tr>
            `).join('');
        })
        .catch(err => console.error('[Investor Table Error]', err));

    // =========================================================
    // 7. STARTUPS PORTFOLIO TABLE
    // =========================================================
    fetch('/api/startups')
        .then(r => r.json())
        .then(({ data }) => {
            const tbody = document.querySelector('#table-startups tbody');
            if (!tbody || !data || !data.length) return;
            tbody.innerHTML = data.slice(0, 20).map(s => `
                <tr>
                    <td class="fw-medium">${s.name}</td>
                    <td><small class="text-muted">${s.industry}</small></td>
                    <td>${statusBadge(s.operating_status)}</td>
                    <td class="text-success fw-medium">${fmtMoney(s.total_funding_usd)}</td>
                    <td><small class="text-primary">${s.cluster_label || '—'}</small></td>
                </tr>
            `).join('');
        })
        .catch(err => console.error('[Startups Table Error]', err));

});
