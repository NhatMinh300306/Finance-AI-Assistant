/**
 * FinMate — Chart.js visualisations.
 * Creates and updates modern dark-themed financial charts.
 */

const Charts = {
  // Chart instances
  categoryChart: null,
  incomeExpenseChart: null,
  spendingTrendChart: null,
  analyticsCategoryChart: null,
  analyticsMonthlyChart: null,

  // Theme color palette
  colors: {
    purple: '#8b5cf6',
    indigo: '#6366f1',
    emerald: '#34d399',
    rose: '#f87171',
    amber: '#fbbf24',
    sky: '#38bdf8',
    pink: '#ec4899',
    teal: '#2dd4bf',
    orange: '#fb923c',
    blue: '#60a5fa',
  },

  getCategoryColorPalette() {
    return [
      '#6366f1', '#34d399', '#f87171', '#fbbf24', '#38bdf8',
      '#ec4899', '#8b5cf6', '#2dd4bf', '#fb923c', '#a855f7',
      '#4ade80', '#f43f5e', '#94a3b8'
    ];
  },

  getDefaultOptions() {
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: '#8b95b0',
            font: { family: "'Inter', sans-serif", size: 12 },
            padding: 14,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: '#1a2035',
          titleColor: '#f0f2f8',
          bodyColor: '#8b95b0',
          borderColor: 'rgba(99, 102, 241, 0.25)',
          borderWidth: 1,
          padding: 12,
          boxPadding: 6,
          usePointStyle: true,
          callbacks: {
            label(context) {
              const label = context.dataset.label || context.label || '';
              const value = context.parsed.y !== undefined ? context.parsed.y : context.parsed;
              return ` ${label}: ¥${Number(value).toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
            }
          }
        }
      }
    };
  },

  /**
   * Render or update Category Expense Doughnut Chart
   */
  renderCategoryChart(canvasId, categories) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.categoryChart && canvasId === 'chart-categories') {
      this.categoryChart.destroy();
    }
    if (this.analyticsCategoryChart && canvasId === 'analytics-chart-categories') {
      this.analyticsCategoryChart.destroy();
    }

    if (!categories || categories.length === 0) {
      categories = [{ category: 'No Data', total: 0 }];
    }

    const labels = categories.map(c => c.category);
    const data = categories.map(c => c.total);
    const colors = this.getCategoryColorPalette().slice(0, categories.length);

    const chartConfig = {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: colors,
          borderColor: '#111827',
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '70%',
        plugins: {
          legend: {
            position: 'right',
            labels: {
              color: '#8b95b0',
              font: { family: "'Inter', sans-serif", size: 12 },
              padding: 10,
              usePointStyle: true,
              boxWidth: 8
            }
          },
          tooltip: {
            backgroundColor: '#1a2035',
            titleColor: '#f0f2f8',
            bodyColor: '#8b95b0',
            borderColor: 'rgba(99, 102, 241, 0.25)',
            borderWidth: 1,
            padding: 12,
            callbacks: {
              label(context) {
                const val = context.raw || 0;
                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                return ` ¥${Number(val).toLocaleString('en-US', { minimumFractionDigits: 2 })} (${pct}%)`;
              }
            }
          }
        }
      }
    };

    const newChart = new Chart(ctx, chartConfig);
    if (canvasId === 'chart-categories') this.categoryChart = newChart;
    if (canvasId === 'analytics-chart-categories') this.analyticsCategoryChart = newChart;
  },

  /**
   * Render Income vs Expense Bar Chart
   */
  renderIncomeExpenseChart(canvasId, monthlyData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.incomeExpenseChart) {
      this.incomeExpenseChart.destroy();
    }

    const labels = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.month)
      : ['No Data'];
    const incomeData = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.total_income)
      : [0];
    const expenseData = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.total_expense)
      : [0];

    const options = this.getDefaultOptions();
    options.scales = {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#8b95b0', font: { family: "'Inter', sans-serif" } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#8b95b0',
          font: { family: "'Inter', sans-serif" },
          callback: (value) => '¥' + Number(value).toLocaleString()
        }
      }
    };

    this.incomeExpenseChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Income',
            data: incomeData,
            backgroundColor: 'rgba(52, 211, 153, 0.8)',
            borderColor: '#34d399',
            borderWidth: 1,
            borderRadius: 6,
          },
          {
            label: 'Expenses',
            data: expenseData,
            backgroundColor: 'rgba(248, 113, 113, 0.8)',
            borderColor: '#f87171',
            borderWidth: 1,
            borderRadius: 6,
          }
        ]
      },
      options
    });
  },

  /**
   * Render Spending Trend Line Chart
   */
  renderSpendingTrendChart(canvasId, trendData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.spendingTrendChart) {
      this.spendingTrendChart.destroy();
    }

    const labels = (trendData && trendData.length > 0)
      ? trendData.map(t => t.date.slice(5)) // MM-DD
      : [];
    const amounts = (trendData && trendData.length > 0)
      ? trendData.map(t => t.amount)
      : [];

    const options = this.getDefaultOptions();
    options.scales = {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#8b95b0', maxTicksLimit: 10, font: { family: "'Inter', sans-serif" } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#8b95b0',
          font: { family: "'Inter', sans-serif" },
          callback: (value) => '¥' + Number(value).toLocaleString()
        }
      }
    };

    this.spendingTrendChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Daily Spending',
          data: amounts,
          fill: true,
          backgroundColor: 'rgba(99, 102, 241, 0.12)',
          borderColor: '#6366f1',
          borderWidth: 2,
          tension: 0.35,
          pointBackgroundColor: '#818cf8',
          pointRadius: 3,
          pointHoverRadius: 6,
        }]
      },
      options
    });
  },

  /**
   * Render Monthly Comparison on Analytics Page
   */
  renderMonthlyAnalyticsChart(canvasId, monthlyData) {
    const ctx = document.getElementById(canvasId);
    if (!ctx) return;

    if (this.analyticsMonthlyChart) {
      this.analyticsMonthlyChart.destroy();
    }

    const labels = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.month)
      : ['No Data'];
    const incomeData = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.total_income)
      : [0];
    const expenseData = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.total_expense)
      : [0];
    const savingsData = (monthlyData && monthlyData.length > 0)
      ? monthlyData.map(m => m.net_savings)
      : [0];

    const options = this.getDefaultOptions();
    options.scales = {
      x: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: { color: '#8b95b0', font: { family: "'Inter', sans-serif" } }
      },
      y: {
        grid: { color: 'rgba(255, 255, 255, 0.04)' },
        ticks: {
          color: '#8b95b0',
          callback: (value) => '¥' + Number(value).toLocaleString()
        }
      }
    };

    this.analyticsMonthlyChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Income',
            data: incomeData,
            backgroundColor: 'rgba(52, 211, 153, 0.75)',
            borderColor: '#34d399',
            borderWidth: 1,
            borderRadius: 4
          },
          {
            label: 'Expenses',
            data: expenseData,
            backgroundColor: 'rgba(248, 113, 113, 0.75)',
            borderColor: '#f87171',
            borderWidth: 1,
            borderRadius: 4
          },
          {
            type: 'line',
            label: 'Net Savings',
            data: savingsData,
            borderColor: '#60a5fa',
            backgroundColor: '#60a5fa',
            borderWidth: 2,
            tension: 0.3,
            pointRadius: 4
          }
        ]
      },
      options
    });
  }
};
