<template>
  <div class="portfolio-container">
    <!-- Header -->
    <div class="portfolio-header">
      <h1>Portfolio Dashboard</h1>
      <button class="btn-add-position" @click="showAddPositionModal = true">
        <span>+</span> Add Position
      </button>
    </div>

    <!-- Summary Cards -->
    <div class="summary-cards">
      <div class="card">
        <div class="card-label">Total Invested</div>
        <div class="card-value">₹{{ totalInvested.toFixed(2) }}</div>
      </div>

      <div class="card">
        <div class="card-label">Current Value</div>
        <div class="card-value">₹{{ totalValue.toFixed(2) }}</div>
      </div>

      <div class="card">
        <div class="card-label">Total P/L</div>
        <div class="card-value" :class="totalPL >= 0 ? 'profit' : 'loss'">
          ₹{{ totalPL.toFixed(2) }}
          <span class="percentage" :class="totalPL >= 0 ? 'profit' : 'loss'">
            {{ totalPLPercent >= 0 ? '↗' : '↘' }} {{ Math.abs(totalPLPercent).toFixed(2) }}%
          </span>
        </div>
      </div>
    </div>

    <!-- Portfolio Holdings -->
    <div class="holdings-section">
      <h2>Portfolio Holdings ({{ holdings.length }} positions)</h2>
      
      <div v-if="holdings.length === 0" class="empty-state">
        <p class="empty-title">No positions yet</p>
        <p class="empty-desc">Add stocks to your portfolio to track performance</p>
      </div>

      <div v-else class="holdings-table">
        <div class="table-header">
          <div class="col col-symbol">Symbol</div>
          <div class="col col-qty">Qty</div>
          <div class="col col-buy-price">Buy Price</div>
          <div class="col col-current">Current</div>
          <div class="col col-invested">Invested</div>
          <div class="col col-value">Current Value</div>
          <div class="col col-gain">Gain/Loss</div>
          <div class="col col-percent">Gain %</div>
          <div class="col col-action">Action</div>
        </div>

        <div
          v-for="holding in holdings"
          :key="holding.id"
          class="table-row"
          :class="holding.gainLoss >= 0 ? 'positive' : 'negative'" >
          <div class="col col-symbol">
            <span class="symbol-badge">{{ holding.symbol }}</span>
          </div>
          <div class="col col-qty">{{ holding.quantity }}</div>
          <div class="col col-buy-price">₹{{ holding.buyPrice.toFixed(2) }}</div>
          <div class="col col-current">
            <span class="price-tag">₹{{ holding.currentPrice.toFixed(2) }}</span>
          </div>
          <div class="col col-invested">₹{{ holding.invested.toFixed(2) }}</div>
          <div class="col col-value">₹{{ holding.currentValue.toFixed(2) }}</div>
          <div class="col col-gain" :class="holding.gainLoss >= 0 ? 'profit' : 'loss'">
            ₹{{ holding.gainLoss.toFixed(2) }}
          </div>
          <div class="col col-percent" :class="holding.gainLossPercent >= 0 ? 'profit' : 'loss'">
            {{ holding.gainLossPercent >= 0 ? '+' : '' }}{{ holding.gainLossPercent.toFixed(2) }}%
          </div>
          <div class="col col-action">
            <button class="btn-action btn-delete" @click="deleteHolding(holding.id)" title="Delete">
              🗑️
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add Position Modal -->
    <div v-if="showAddPositionModal" class="modal-overlay" @click="showAddPositionModal = false">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Add Stock Position</h2>
          <button class="btn-close" @click="showAddPositionModal = false">✕</button>
        </div>

        <form @submit.prevent="addPosition" class="modal-form">
          <div class="form-group">
            <label for="symbol">Stock Symbol</label>
            <input
              id="symbol"
              v-model="newPosition.symbol"
              type="text"
              placeholder="e.g., TCS.NS"
              required
            />
          </div>

          <div class="form-group">
            <label for="quantity">Quantity</label>
            <input
              id="quantity"
              v-model.number="newPosition.quantity"
              type="number"
              placeholder="Number of shares"
              min="0.01"
              step="0.01"
              required
            />
          </div>

          <div class="form-group">
            <label for="buyPrice">Buy Price (₹)</label>
            <input
              id="buyPrice"
              v-model.number="newPosition.buyPrice"
              type="number"
              placeholder="Price per share"
              min="0.01"
              step="0.01"
              required
            />
          </div>

          <div class="form-group">
            <label for="buyDate">Buy Date</label>
            <input
              id="buyDate"
              v-model="newPosition.buyDate"
              type="date"
              required
            />
          </div>

          <div class="form-actions">
            <button type="button" class="btn-cancel" @click="showAddPositionModal = false">
              Cancel
            </button>
            <button type="submit" class="btn-submit" :disabled="loading">
              {{ loading ? 'Adding...' : 'Add Position' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Loading Overlay -->
    <div v-if="loading" class="loading-overlay">
      <div class="spinner"></div>
      <p>Loading portfolio...</p>
    </div>

    <!-- Error Message -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
      <button @click="error = null">Dismiss</button>
    </div>

    <!-- Success Message -->
    <div v-if="success" class="success-message">
      <p>{{ success }}</p>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '@/stores/auth_store';

export default {
  name: 'PortfolioView',
  data() {
    return {
      holdings: [],
      totalInvested: 0,
      totalValue: 0,
      totalPL: 0,
      totalPLPercent: 0,
      showAddPositionModal: false,
      loading: false,
      error: null,
      success: null,
      newPosition: {
        symbol: '',
        quantity: null,
        buyPrice: null,
        buyDate: new Date().toISOString().split('T')[0],
      },
      authStore: null,
    };
  },
  computed: {
    userId() {
      return this.authStore?.getUserId() || null;
    },
    backendURL() {
      return this.authStore?.getBackendServerURL() || 'http://127.0.0.1:5001';
    }
  },
  created() {
    this.authStore = useAuthStore();
  },
  mounted() {
    this.fetchPortfolio();
  },
  methods: {
    getAuthHeaders() {
      const headers = { "Content-Type": "application/json" };
      const authToken = sessionStorage.getItem('auth_token');
      if (authToken) {
        headers["Authorization"] = authToken;
        headers["X-Auth-Token"] = authToken;
      }
      return headers;
    },

    async fetchPortfolio() {
      if (!this.userId) {
        this.error = 'Please log in to view your portfolio';
        return;
      }

      this.loading = true;
      this.error = null;
      
      try {
        const url = `${this.backendURL}/api/v1/portfolio/dashboard/${this.userId}`;
        const response = await fetch(url, {
          headers: this.getAuthHeaders()
        });

        const text = await response.text();
        let data = null;

        try {
          data = text ? JSON.parse(text) : null;
        } catch (err) {
          console.warn('Portfolio JSON parse failed:', text, err);
        }

        if (!response.ok || !data) {
          throw new Error(data?.message || `HTTP ${response.status}`);
        }

        this.holdings = [];

        if (data.holdings && Array.isArray(data.holdings)) {
          data.holdings.forEach(holding => {
            this.holdings.push({
              id: holding.id,
              symbol: holding.symbol,
              quantity: holding.quantity,
              buyPrice: holding.purchase_price,
              currentPrice: holding.current_price || holding.purchase_price,
              invested: holding.total_invested,
              currentValue: holding.current_value,
              gainLoss: holding.gain_loss,
              gainLossPercent: holding.gain_loss_percent,
            });
          });
        }

        const summary = data.summary || {};
        this.totalInvested = summary.total_invested || 0;
        this.totalValue = summary.total_value || 0;
        this.totalPL = summary.total_gain_loss || 0;
        this.totalPLPercent = summary.total_gain_loss_percent || 0;
      } catch (err) {
        console.error('Error fetching portfolio:', err);
        this.error = err.message || 'Failed to load portfolio. Please try again.';
      } finally {
        this.loading = false;
      }
    },

    async addPosition() {
      if (!this.newPosition.symbol || !this.newPosition.quantity || !this.newPosition.buyPrice) {
        this.error = 'Please fill all fields';
        return;
      }

      if (!this.userId) {
        this.error = 'Please log in to add positions';
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        const url = `${this.backendURL}/api/v1/portfolio/add`;
        const response = await fetch(url, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({
            user_id: this.userId,
            symbol: this.newPosition.symbol.toUpperCase(),
            quantity: this.newPosition.quantity,
            purchase_price: this.newPosition.buyPrice,
            purchase_date: this.newPosition.buyDate,
          })
        });

        const text = await response.text();
        let data = null;

        try {
          data = text ? JSON.parse(text) : null;
        } catch (err) {
          console.warn('Add position JSON parse failed:', text, err);
        }

        if (!response.ok || !data) {
          throw new Error(data?.message || 'Failed to add position');
        }

        this.success = 'Position added successfully!';
        setTimeout(() => {
          this.success = null;
          this.showAddPositionModal = false;
          this.newPosition = {
            symbol: '',
            quantity: null,
            buyPrice: null,
            buyDate: new Date().toISOString().split('T')[0],
          };
          this.fetchPortfolio();
        }, 1500);
      } catch (err) {
        console.error('Error adding position:', err);
        this.error = err.message || 'Failed to add position';
      } finally {
        this.loading = false;
      }
    },

    async deleteHolding(holdingId) {
      if (!confirm('Are you sure you want to delete this position?')) return;

      if (!this.userId) {
        this.error = 'Please log in to delete positions';
        return;
      }

      this.loading = true;
      this.error = null;

      try {
        const url = `${this.backendURL}/api/v1/portfolio/${holdingId}`;
        const response = await fetch(url, {
          method: 'DELETE',
          headers: this.getAuthHeaders(),
          body: JSON.stringify({ user_id: this.userId })
        });

        const text = await response.text();
        let data = null;

        try {
          data = text ? JSON.parse(text) : null;
        } catch (err) {
          console.warn('Delete position JSON parse failed:', text, err);
        }

        if (!response.ok || !data) {
          throw new Error(data?.message || 'Failed to delete position');
        }

        this.success = 'Position deleted successfully!';
        setTimeout(() => {
          this.success = null;
          this.fetchPortfolio();
        }, 1500);
      } catch (err) {
        console.error('Error deleting position:', err);
        this.error = err.message || 'Failed to delete position';
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.portfolio-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
  background-color: #f5f5f7;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  min-height: 100vh;
}

/* Header */
.portfolio-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.portfolio-header h1 {
  font-size: 24px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

.btn-add-position {
  background: black;
  color: white;
  border: none;
  padding: 10px 24px;
  border-radius: 24px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.2s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.btn-add-position:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-add-position span {
  font-size: 18px;
  font-weight: 600;
}

/* Summary Cards */
.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 32px;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  transition: all 0.2s ease;
}

.card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.card-label {
  font-size: 13px;
  color: #86868b;
  font-weight: 500;
  margin-bottom: 8px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.card-value {
  font-size: 28px;
  font-weight: 600;
  color: #1d1d1f;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.card-value.profit {
  color: #10b981;
}

.card-value.loss {
  color: #ef4444;
}

.percentage {
  font-size: 14px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 6px;
  background: #f5f5f7;
}

.percentage.profit {
  color: #10b981;
  background: #ecfdf5;
}

.percentage.loss {
  color: #ef4444;
  background: #fef2f2;
}

/* Holdings Section */
.holdings-section {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.holdings-section h2 {
  font-size: 18px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 20px 0;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-title {
  font-size: 18px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0 0 8px 0;
}

.empty-desc {
  font-size: 14px;
  color: #86868b;
  margin: 0;
}

/* Table */
.holdings-table {
  width: 100%;
}

.table-header {
  display: grid;
  grid-template-columns: 120px 80px 100px 100px 120px 130px 120px 100px 80px;
  gap: 12px;
  padding: 12px 16px;
  background: #f5f5f7;
  border-radius: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 600;
  color: #86868b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.table-row {
  display: grid;
  grid-template-columns: 120px 80px 100px 100px 120px 130px 120px 100px 80px;
  gap: 12px;
  padding: 16px;
  background: white;
  border-bottom: 1px solid #f5f5f7;
  align-items: center;
  transition: background 0.15s ease;
}

.table-row:hover {
  background: #fafafa;
}

.table-row:last-child {
  border-bottom: none;
}

.col {
  font-size: 14px;
  color: #1d1d1f;
}

.symbol-badge {
  display: inline-block;
  padding: 6px 12px;
  background: #f5f5f7;
  border-radius: 6px;
  font-weight: 600;
  font-size: 13px;
  color: #1d1d1f;
}

.price-tag {
  font-weight: 500;
}

.profit {
  color: #10b981 !important;
  font-weight: 500;
}

.loss {
  color: #ef4444 !important;
  font-weight: 500;
}

/* Action Buttons */
.btn-action {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.15s ease;
  font-size: 16px;
}

.btn-delete:hover {
  background: #fef2f2;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  padding: 32px;
  width: 90%;
  max-width: 500px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.modal-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #1d1d1f;
  margin: 0;
}

.btn-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #86868b;
  padding: 4px;
  line-height: 1;
  transition: color 0.15s ease;
}

.btn-close:hover {
  color: #1d1d1f;
}

/* Form */
.modal-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-size: 13px;
  font-weight: 500;
  color: #1d1d1f;
}

.form-group input {
  padding: 12px 16px;
  border: 1px solid #d2d2d7;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.15s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}

.btn-cancel,
.btn-submit {
  flex: 1;
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
  border: none;
}

.btn-cancel {
  background: #f5f5f7;
  color: #1d1d1f;
}

.btn-cancel:hover {
  background: #e8e8ed;
}

.btn-submit {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-submit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-submit:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Loading Overlay */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  gap: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f5f5f7;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-overlay p {
  font-size: 14px;
  color: #86868b;
  margin: 0;
}

/* Messages */
.error-message,
.success-message {
  position: fixed;
  bottom: 24px;
  right: 24px;
  padding: 16px 24px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  z-index: 1001;
  display: flex;
  align-items: center;
  gap: 12px;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.error-message {
  background: #fef2f2;
  color: #ef4444;
  border: 1px solid #fecaca;
}

.success-message {
  background: #ecfdf5;
  color: #10b981;
  border: 1px solid #a7f3d0;
}

.error-message p,
.success-message p {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  flex: 1;
}

.error-message button {
  background: none;
  border: none;
  color: inherit;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background 0.15s ease;
}

.error-message button:hover {
  background: rgba(239, 68, 68, 0.1);
}

/* Responsive */
@media (max-width: 1200px) {
  .table-header,
  .table-row {
    grid-template-columns: 100px 60px 90px 90px 100px 110px 100px 80px 60px;
    gap: 8px;
    font-size: 13px;
  }
}

@media (max-width: 768px) {
  .portfolio-container {
    padding: 16px;
  }

  .summary-cards {
    grid-template-columns: 1fr;
  }

  .holdings-table {
    overflow-x: auto;
  }

  .table-header,
  .table-row {
    min-width: 900px;
  }

  .modal-content {
    width: 95%;
    padding: 24px;
  }
}
</style>