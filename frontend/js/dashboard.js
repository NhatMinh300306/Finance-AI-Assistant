/**
 * FinMate — Main Dashboard & Application Controller.
 * Manages navigation, modals, transactions CRUD, filters, and analytics views.
 */

// Toast notification helper
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  const icon = type === 'success' ? '✅' : type === 'error' ? '❌' : type === 'warning' ? '⚠️' : 'ℹ️';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;

  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(20px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Global navigation helper
function navigateTo(pageName) {
  const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
  navItems.forEach(item => {
    if (item.dataset.page === pageName) {
      item.classList.add('active');
    } else {
      item.classList.remove('active');
    }
  });

  const sections = document.querySelectorAll('.page-section');
  sections.forEach(sec => {
    sec.classList.remove('active');
  });

  const targetSection = document.getElementById(`page-${pageName}`);
  if (targetSection) {
    targetSection.classList.add('active');
  }

  // Update header title
  const titleMap = {
    dashboard: 'Dashboard',
    transactions: 'Transactions',
    analytics: 'Analytics & Insights',
    chat: 'AI Personal Assistant',
    settings: 'Settings'
  };
  const titleEl = document.getElementById('page-title');
  if (titleEl) {
    titleEl.textContent = titleMap[pageName] || 'Dashboard';
  }

  // Close mobile sidebar if open
  const sidebar = document.getElementById('sidebar');
  if (sidebar) sidebar.classList.remove('open');

  // Trigger page-specific data loading
  if (pageName === 'transactions') {
    Dashboard.loadAllTransactions();
  } else if (pageName === 'analytics') {
    Dashboard.loadAnalytics();
  } else if (pageName === 'dashboard') {
    Dashboard.loadDashboard();
  }
}

const Dashboard = {
  currentPage: 1,
  pageSize: 15,
  currentCategoryFilter: '',
  currentTypeFilter: '',

  init() {
    this.setupNavigation();
    this.setupModal();
    this.setupFilters();
    this.loadDashboard();
  },

  // Setup sidebar navigation and mobile toggle
  setupNavigation() {
    const navItems = document.querySelectorAll('.sidebar-nav .nav-item');
    navItems.forEach(item => {
      item.addEventListener('click', () => {
        const page = item.dataset.page;
        if (page) navigateTo(page);
      });
    });

    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    if (menuToggle && sidebar) {
      menuToggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
      });
    }
  },

  // Setup transaction modal (Add & Edit)
  setupModal() {
    const modal = document.getElementById('transaction-modal');
    const openBtn = document.getElementById('btn-add-transaction');
    const closeBtn = document.getElementById('modal-close');
    const cancelBtn = document.getElementById('modal-cancel');
    const form = document.getElementById('transaction-form');

    const openModal = () => {
      form.reset();
      document.getElementById('form-txn-id').value = '';
      document.getElementById('modal-title').textContent = 'Add Transaction';
      document.getElementById('modal-submit').textContent = 'Add Transaction';
      // Default to today's date in local format
      const today = new Date().toISOString().split('T')[0];
      document.getElementById('form-date').value = today;
      modal.classList.add('active');
    };

    const closeModal = () => {
      modal.classList.remove('active');
    };

    if (openBtn) openBtn.addEventListener('click', openModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    if (cancelBtn) cancelBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    // Handle form submit
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const txnId = document.getElementById('form-txn-id').value;
        const amount = parseFloat(document.getElementById('form-amount').value);
        const transaction_type = document.getElementById('form-type').value;
        const category = document.getElementById('form-category').value;
        const description = document.getElementById('form-description').value.trim();
        const dateVal = document.getElementById('form-date').value;

        if (isNaN(amount) || amount <= 0) {
          showToast('Please enter a valid positive amount', 'error');
          return;
        }

        const payload = {
          amount,
          transaction_type,
          category,
          description: description || null,
        };

        if (dateVal) {
          payload.transaction_date = new Date(dateVal).toISOString();
        }

        try {
          if (txnId) {
            await Api.updateTransaction(txnId, payload);
            showToast('Transaction updated successfully', 'success');
          } else {
            await Api.createTransaction(payload);
            showToast('Transaction added successfully', 'success');
          }
          closeModal();
          this.refreshData();
        } catch (error) {
          showToast(`Error: ${error.message}`, 'error');
        }
      });
    }
  },

  // Setup filters for transactions page
  setupFilters() {
    const catFilter = document.getElementById('filter-category');
    const typeFilter = document.getElementById('filter-type');

    if (catFilter) {
      catFilter.addEventListener('change', (e) => {
        this.currentCategoryFilter = e.target.value;
        this.currentPage = 1;
        this.loadAllTransactions();
      });
    }

    if (typeFilter) {
      typeFilter.addEventListener('change', (e) => {
        this.currentTypeFilter = e.target.value;
        this.currentPage = 1;
        this.loadAllTransactions();
      });
    }
  },

  // Format currency helper
  formatCurrency(num) {
    return '¥' + Number(num || 0).toLocaleString('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  },

  // Refresh all application views
  refreshData() {
    this.loadDashboard();
    const activeSection = document.querySelector('.page-section.active');
    if (activeSection && activeSection.id === 'page-transactions') {
      this.loadAllTransactions();
    } else if (activeSection && activeSection.id === 'page-analytics') {
      this.loadAnalytics();
    }
  },

  // Load Dashboard page data
  async loadDashboard() {
    try {
      // 1. Fetch Analytics Summary
      const summaryData = await Api.getAnalyticsSummary();
      const summary = summaryData.summary;

      const balanceEl = document.getElementById('card-balance');
      const incomeEl = document.getElementById('card-income');
      const expenseEl = document.getElementById('card-expense');
      const savingsEl = document.getElementById('card-savings');

      if (balanceEl) balanceEl.textContent = this.formatCurrency(summary.balance);
      if (incomeEl) incomeEl.textContent = this.formatCurrency(summary.total_income);
      if (expenseEl) expenseEl.textContent = this.formatCurrency(summary.total_expense);

      // Compute savings from monthly trend
      const monthly = summaryData.monthly_trend || [];
      const currentMonth = monthly.length > 0 ? monthly[monthly.length - 1] : null;
      const savings = currentMonth ? currentMonth.net_savings : (summary.total_income - summary.total_expense);
      if (savingsEl) {
        savingsEl.textContent = this.formatCurrency(savings);
        savingsEl.className = 'card-value ' + (savings >= 0 ? 'positive' : 'negative');
      }

      // 2. Render Charts
      if (typeof Charts !== 'undefined') {
        Charts.renderCategoryChart('chart-categories', summaryData.category_breakdown);
        Charts.renderIncomeExpenseChart('chart-income-expense', summaryData.monthly_trend);

        // Fetch daily trend
        try {
          const trend = await Api.getAnalyticsTrend(30);
          Charts.renderSpendingTrendChart('chart-spending-trend', trend);
        } catch (e) {
          console.warn('Failed to load spending trend:', e);
        }
      }

      // 3. Load Recent Transactions
      this.loadRecentTransactions();
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      showToast('Could not load dashboard data: ' + error.message, 'error');
    }
  },

  // Load Recent Transactions (top 8)
  async loadRecentTransactions() {
    const container = document.getElementById('recent-transactions-body');
    if (!container) return;

    try {
      const data = await Api.getTransactions({ page: 1, page_size: 8 });
      if (!data.transactions || data.transactions.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">💳</div>
            <p>No transactions yet. Click "+ Add Transaction" or tell FinMate AI to record one!</p>
          </div>
        `;
        return;
      }

      container.innerHTML = this.buildTransactionTableHtml(data.transactions);
      this.bindTransactionActions(container);
    } catch (error) {
      container.innerHTML = `<div class="empty-state"><p>Error loading transactions: ${error.message}</p></div>`;
    }
  },

  // Load All Transactions (Paginated)
  async loadAllTransactions() {
    const container = document.getElementById('all-transactions-body');
    const paginationContainer = document.getElementById('transactions-pagination');
    if (!container) return;

    container.innerHTML = '<div class="loading-state"><div class="spinner"></div></div>';

    try {
      const params = {
        page: this.currentPage,
        page_size: this.pageSize
      };
      if (this.currentCategoryFilter) params.category = this.currentCategoryFilter;
      if (this.currentTypeFilter) params.transaction_type = this.currentTypeFilter;

      const data = await Api.getTransactions(params);

      if (!data.transactions || data.transactions.length === 0) {
        container.innerHTML = `
          <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <p>No transactions matching the selected filters.</p>
          </div>
        `;
        if (paginationContainer) paginationContainer.innerHTML = '';
        return;
      }

      container.innerHTML = this.buildTransactionTableHtml(data.transactions);
      this.bindTransactionActions(container);

      // Render pagination
      if (paginationContainer) {
        const totalPages = Math.ceil(data.total / this.pageSize);
        let pagHtml = '';

        if (totalPages > 1) {
          pagHtml += `
            <button class="btn btn-secondary btn-sm" ${this.currentPage <= 1 ? 'disabled' : ''} onclick="Dashboard.goToPage(${this.currentPage - 1})">
              ← Prev
            </button>
            <span style="font-size:0.85rem;color:var(--text-secondary);align-self:center;">
              Page ${this.currentPage} of ${totalPages} (${data.total} total)
            </span>
            <button class="btn btn-secondary btn-sm" ${this.currentPage >= totalPages ? 'disabled' : ''} onclick="Dashboard.goToPage(${this.currentPage + 1})">
              Next →
            </button>
          `;
        }
        paginationContainer.innerHTML = pagHtml;
      }
    } catch (error) {
      container.innerHTML = `<div class="empty-state"><p>Error: ${error.message}</p></div>`;
    }
  },

  goToPage(page) {
    this.currentPage = page;
    this.loadAllTransactions();
  },

  // Build HTML table for transactions
  buildTransactionTableHtml(transactions) {
    let rows = transactions.map(t => {
      const isIncome = t.transaction_type === 'income';
      const formattedDate = new Date(t.transaction_date).toLocaleDateString(undefined, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
      const sign = isIncome ? '+' : '-';

      return `
        <tr data-id="${t.id}">
          <td style="color:var(--text-secondary);font-size:0.8rem;white-space:nowrap;">${formattedDate}</td>
          <td style="font-weight:500;">${t.description || '—'}</td>
          <td><span class="txn-category">${t.category}</span></td>
          <td><span class="txn-type ${t.transaction_type}">${t.transaction_type}</span></td>
          <td class="txn-amount ${t.transaction_type}">${sign}¥${Number(t.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
          <td>
            <div class="txn-actions">
              <button class="edit-btn" title="Edit transaction" data-id="${t.id}">✎</button>
              <button class="delete delete-btn" title="Delete transaction" data-id="${t.id}">✕</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    return `
      <table class="transaction-table">
        <thead>
          <tr>
            <th>Date</th>
            <th>Description</th>
            <th>Category</th>
            <th>Type</th>
            <th>Amount</th>
            <th style="width:80px;">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${rows}
        </tbody>
      </table>
    `;
  },

  // Bind Edit and Delete events on transaction rows
  bindTransactionActions(container) {
    const editButtons = container.querySelectorAll('.edit-btn');
    const deleteButtons = container.querySelectorAll('.delete-btn');

    editButtons.forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        try {
          const txn = await Api.getTransaction(id);
          document.getElementById('form-txn-id').value = txn.id;
          document.getElementById('form-amount').value = txn.amount;
          document.getElementById('form-type').value = txn.transaction_type;
          document.getElementById('form-category').value = txn.category;
          document.getElementById('form-description').value = txn.description || '';
          if (txn.transaction_date) {
            document.getElementById('form-date').value = txn.transaction_date.split('T')[0];
          }
          document.getElementById('modal-title').textContent = 'Edit Transaction';
          document.getElementById('modal-submit').textContent = 'Save Changes';
          document.getElementById('transaction-modal').classList.add('active');
        } catch (error) {
          showToast(`Error fetching transaction: ${error.message}`, 'error');
        }
      });
    });

    deleteButtons.forEach(btn => {
      btn.addEventListener('click', async () => {
        const id = btn.dataset.id;
        if (confirm('Are you sure you want to delete this transaction?')) {
          try {
            await Api.deleteTransaction(id);
            showToast('Transaction deleted successfully', 'success');
            this.refreshData();
          } catch (error) {
            showToast(`Delete failed: ${error.message}`, 'error');
          }
        }
      });
    });
  },

  // Load Analytics page
  async loadAnalytics() {
    try {
      const summaryData = await Api.getAnalyticsSummary();
      const summary = summaryData.summary;

      document.getElementById('analytics-txn-count').textContent = summary.transaction_count || 0;
      document.getElementById('analytics-top-category').textContent = summary.top_expense_category
        ? `${summary.top_expense_category} (¥${Number(summary.top_expense_amount).toLocaleString()})`
        : '—';

      // Compute averages from monthly trend
      const monthly = summaryData.monthly_trend || [];
      let avgIncome = 0;
      let avgExpense = 0;
      if (monthly.length > 0) {
        avgIncome = monthly.reduce((acc, m) => acc + m.total_income, 0) / monthly.length;
        avgExpense = monthly.reduce((acc, m) => acc + m.total_expense, 0) / monthly.length;
      }
      document.getElementById('analytics-avg-income').textContent = this.formatCurrency(avgIncome);
      document.getElementById('analytics-avg-expense').textContent = this.formatCurrency(avgExpense);

      // Render Analytics Charts
      if (typeof Charts !== 'undefined') {
        Charts.renderCategoryChart('analytics-chart-categories', summaryData.category_breakdown);
        Charts.renderMonthlyAnalyticsChart('analytics-chart-monthly', summaryData.monthly_trend);
      }

      // Check alerts
      try {
        const alerts = await Api.getAnalyticsAlerts();
        const alertsContainer = document.getElementById('spending-alerts-body');
        if (alerts && alerts.length > 0) {
          alertsContainer.innerHTML = alerts.map(a => `
            <div style="padding:14px;background:rgba(251,191,36,0.1);border-left:3px solid var(--warning-color);border-radius:var(--radius-sm);margin-bottom:10px;">
              <div style="font-weight:600;color:var(--warning-color);font-size:0.9rem;">⚠️ Unusual spending in ${a.category}</div>
              <div style="font-size:0.85rem;color:var(--text-secondary);margin-top:4px;">
                Current month: ¥${a.current_month.toLocaleString()} vs Last month: ¥${a.previous_month.toLocaleString()}
                (+${a.increase_pct}% increase)
              </div>
            </div>
          `).join('');
        } else {
          alertsContainer.innerHTML = `
            <div class="empty-state">
              <div class="empty-icon">✅</div>
              <p>No unusual spending detected. Spending is healthy across all categories.</p>
            </div>
          `;
        }
      } catch (err) {
        console.warn('Failed to load spending alerts:', err);
      }

    } catch (error) {
      showToast('Failed to load analytics: ' + error.message, 'error');
    }
  }
};

// Start Dashboard on load
document.addEventListener('DOMContentLoaded', () => {
  Dashboard.init();
});
