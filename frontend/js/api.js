/**
 * FinMate — API communication layer.
 * All REST API calls are centralized here.
 */

const API_BASE = window.location.origin + '/api';

const Api = {
  /**
   * Generic fetch wrapper with error handling.
   */
  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const config = {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    };

    try {
      const response = await fetch(url, config);

      if (response.status === 204) return null;

      const data = await response.json();

      if (!response.ok) {
        const errorMsg = data.detail || data.message || `HTTP ${response.status}`;
        throw new Error(typeof errorMsg === 'object' ? JSON.stringify(errorMsg) : errorMsg);
      }

      return data;
    } catch (error) {
      if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
        throw new Error('Unable to connect to the server. Please check if the backend is running.');
      }
      throw error;
    }
  },

  // ── Health ──
  health() {
    return this.request('/health');
  },

  // ── Transactions ──
  getTransactions(params = {}) {
    const query = new URLSearchParams();
    if (params.page) query.set('page', params.page);
    if (params.page_size) query.set('page_size', params.page_size);
    if (params.category) query.set('category', params.category);
    if (params.transaction_type) query.set('transaction_type', params.transaction_type);
    const qs = query.toString();
    return this.request(`/transactions${qs ? '?' + qs : ''}`);
  },

  getTransaction(id) {
    return this.request(`/transactions/${id}`);
  },

  createTransaction(data) {
    return this.request('/transactions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  updateTransaction(id, data) {
    return this.request(`/transactions/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  deleteTransaction(id) {
    return this.request(`/transactions/${id}`, {
      method: 'DELETE',
    });
  },

  // ── Analytics ──
  getAnalyticsSummary() {
    return this.request('/analytics/summary');
  },

  getAnalyticsCategories(startDate, endDate) {
    const query = new URLSearchParams();
    if (startDate) query.set('start_date', startDate);
    if (endDate) query.set('end_date', endDate);
    const qs = query.toString();
    return this.request(`/analytics/categories${qs ? '?' + qs : ''}`);
  },

  getAnalyticsMonthly(months = 6) {
    return this.request(`/analytics/monthly?months=${months}`);
  },

  getAnalyticsTrend(days = 30) {
    return this.request(`/analytics/trend?days=${days}`);
  },

  getAnalyticsAlerts() {
    return this.request('/analytics/alerts');
  },

  // ── Chat ──
  sendChatMessage(message) {
    return this.request('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, user_id: 1 }),
    });
  },

  // ── User ──
  getCurrentUser() {
    return this.request('/users/me');
  },
};
