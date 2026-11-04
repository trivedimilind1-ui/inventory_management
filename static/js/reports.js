/**
 * SMARTSTOCK - Reports & Analytics Visualizations
 */

document.addEventListener('DOMContentLoaded', function() {
  const params = new URLSearchParams(window.location.search);
  const period = params.get('period') || 'month';
  const startDate = params.get('start_date') || '';
  const endDate = params.get('end_date') || '';

  const queryUrl = `/reports/api/chart-data?period=${encodeURIComponent(period)}&start_date=${encodeURIComponent(startDate)}&end_date=${encodeURIComponent(endDate)}`;

  fetch(queryUrl)
    .then(res => res.json())
    .then(data => {
      initReportTrendChart(data.trend);
      initReportCategoryChart(data.categories);
    })
    .catch(err => {
      console.error('Error loading report charts:', err);
    });
});

function initReportTrendChart(trend) {
  const ctx = document.getElementById('reportTrendChart');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: trend.labels,
      datasets: [
        {
          label: 'Revenue (₹)',
          data: trend.revenue,
          borderColor: '#4f46e5',
          backgroundColor: 'rgba(79, 70, 229, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        },
        {
          label: 'Gross Profit (₹)',
          data: trend.profit,
          borderColor: '#10b981',
          backgroundColor: 'rgba(16, 185, 129, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top' },
        tooltip: {
          callbacks: {
            label: context => ` ${context.dataset.label}: ₹${context.raw.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
          }
        }
      },
      scales: {
        y: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { callback: val => '₹' + val.toLocaleString('en-IN') }
        },
        x: { grid: { display: false } }
      }
    }
  });
}

function initReportCategoryChart(categories) {
  const ctx = document.getElementById('reportCategoryChart');
  if (!ctx) return;

  const colors = [
    '#4f46e5', '#7c3aed', '#06b6d4', '#10b981', '#f59e0b',
    '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6', '#64748b'
  ];

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: categories.labels,
      datasets: [{
        label: 'Revenue by Category (₹)',
        data: categories.revenue,
        backgroundColor: colors.slice(0, categories.labels.length),
        borderRadius: 6
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: context => ` Revenue: ₹${context.raw.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`
          }
        }
      },
      scales: {
        y: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { callback: val => '₹' + val.toLocaleString('en-IN') }
        },
        x: { grid: { display: false } }
      }
    }
  });
}
