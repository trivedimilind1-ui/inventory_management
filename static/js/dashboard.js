/**
 * SMARTSTOCK - Dashboard Visual Analytics (Chart.js)
 */

document.addEventListener('DOMContentLoaded', function() {
  fetch('/api/dashboard/charts')
    .then(response => {
      if (!response.ok) throw new Error('Failed to load chart data');
      return response.json();
    })
    .then(data => {
      initSevenDaysChart(data.seven_days);
      initCategoryChart(data.categories);
      initTopProductsChart(data.top_products);
      initStockStatusChart(data.stock_status);
      initMonthlyRevenueChart(data.monthly_revenue);
    })
    .catch(err => {
      console.error('Error loading dashboard charts:', err);
    });
});

// Chart 1: 7-Day Sales Trend
function initSevenDaysChart(data) {
  const ctx = document.getElementById('chartSevenDays');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: [
        {
          label: 'Revenue (₹)',
          data: data.revenue,
          borderColor: '#4f46e5',
          backgroundColor: 'rgba(79, 70, 229, 0.1)',
          fill: true,
          tension: 0.35,
          borderWidth: 2.5,
          pointBackgroundColor: '#4f46e5',
          pointRadius: 4,
          yAxisID: 'y'
        },
        {
          label: 'Orders Count',
          data: data.orders,
          borderColor: '#10b981',
          borderDash: [4, 4],
          tension: 0.3,
          borderWidth: 2,
          pointRadius: 3,
          yAxisID: 'y1'
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12, font: { weight: 600 } } },
        tooltip: {
          callbacks: {
            label: function(context) {
              if (context.datasetIndex === 0) {
                return ` Revenue: ₹${context.raw.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`;
              }
              return ` Orders: ${context.raw}`;
            }
          }
        }
      },
      scales: {
        y: {
          type: 'linear',
          display: true,
          position: 'left',
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: {
            callback: value => '₹' + value.toLocaleString('en-IN')
          }
        },
        y1: {
          type: 'linear',
          display: true,
          position: 'right',
          grid: { drawOnChartArea: false },
          ticks: { precision: 0 }
        },
        x: {
          grid: { display: false }
        }
      }
    }
  });
}

// Chart 2: Category Distribution
function initCategoryChart(data) {
  const ctx = document.getElementById('chartCategories');
  if (!ctx) return;

  const colors = [
    '#4f46e5', '#7c3aed', '#06b6d4', '#10b981', '#f59e0b',
    '#ef4444', '#ec4899', '#8b5cf6', '#14b8a6', '#64748b'
  ];

  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.counts,
        backgroundColor: colors.slice(0, data.labels.length),
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'right', labels: { boxWidth: 10, font: { size: 11 } } }
      },
      cutout: '68%'
    }
  });
}

// Chart 3: Top 5 Selling Products
function initTopProductsChart(data) {
  const ctx = document.getElementById('chartTopProducts');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Units Sold',
        data: data.quantities,
        backgroundColor: 'rgba(79, 70, 229, 0.85)',
        borderRadius: 6,
        hoverBackgroundColor: '#4338ca'
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            afterLabel: function(context) {
              const val = data.values[context.dataIndex];
              return `Value: ₹${val.toLocaleString('en-IN')}`;
            }
          }
        }
      },
      scales: {
        x: {
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { precision: 0 }
        },
        y: {
          grid: { display: false }
        }
      }
    }
  });
}

// Chart 4: Stock Availability
function initStockStatusChart(data) {
  const ctx = document.getElementById('chartStockStatus');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: data.labels,
      datasets: [{
        data: data.counts,
        backgroundColor: ['#10b981', '#f59e0b', '#ef4444'],
        borderWidth: 2,
        borderColor: '#ffffff'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { boxWidth: 12 } }
      }
    }
  });
}

// Chart 5: Monthly Revenue Bar Chart
function initMonthlyRevenueChart(data) {
  const ctx = document.getElementById('chartMonthlyRevenue');
  if (!ctx) return;

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.labels,
      datasets: [{
        label: 'Monthly Revenue (₹)',
        data: data.revenue,
        backgroundColor: '#7c3aed',
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
          ticks: {
            callback: value => '₹' + value.toLocaleString('en-IN')
          }
        },
        x: { grid: { display: false } }
      }
    }
  });
}
