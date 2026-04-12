<template>
  <div class="club-dashboard">
    <!-- Dashboard Header -->
    <div class="dashboard-header">
      <button @click="$emit('back')" class="btn-back">
        ← Back to Clubs
      </button>
      <div class="header-content">
        <h2>{{ clubData.name }}</h2>
        <p class="club-code">Club Code: <strong>{{ clubData.join_code }}</strong></p>
      </div>
      <button @click="refreshDashboard" class="btn-refresh" title="Refresh">
        🔄
      </button>
    </div>

    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>Loading club dashboard...</p>
    </div>

    <div v-else-if="dashboardData" class="dashboard-content">
      <!-- Overview Cards -->
      <div class="overview-cards">
        <div class="overview-card">
          <div class="card-icon">👥</div>
          <div class="card-content">
            <h3>Total Members</h3>
            <div class="card-value">{{ dashboardData.total_members }}</div>
          </div>
        </div>

        <div class="overview-card">
          <div class="card-icon">💰</div>
          <div class="card-content">
            <h3>Combined Portfolio</h3>
            <div class="card-value">₹{{ formatNumber(dashboardData.total_net_worth) }}</div>
          </div>
        </div>

        <div class="overview-card">
          <div class="card-icon">📈</div>
          <div class="card-content">
            <h3>Common Holdings</h3>
            <div class="card-value">{{ dashboardData.common_holdings.length }}</div>
          </div>
        </div>
      </div>

      <!-- Common Holdings Section -->
      <div v-if="dashboardData.common_holdings.length > 0" class="common-holdings-section">
        <h3>📊 Popular in Our Club</h3>
        <p class="section-description">Stocks held by multiple club members</p>
        <div class="holdings-list">
          <span 
            v-for="stock in dashboardData.common_holdings" 
            :key="stock"
            class="stock-tag"
          >
            {{ stock }}
          </span>
        </div>
      </div>

      <!-- Members Section -->
      <div class="members-section">
        <div class="section-header">
          <h3>Club Members</h3>
          <button @click="showSharingSettings = true" class="btn-outline">
            ⚙️ My Sharing Settings
          </button>
        </div>

        <div class="members-list">
          <div 
            v-for="member in dashboardData.members" 
            :key="member.user_id"
            class="member-card"
          >
            <!-- Member Avatar & Header -->
            <div class="member-header">
              <div class="member-avatar">
                {{ member.username.charAt(0).toUpperCase() }}
              </div>
              <div class="member-info-header">
                <h4>{{ member.username }}</h4>
                <span class="role" :class="member.role">
                  {{ member.role === 'admin' ? '👑 Club Admin' : '👤 Member' }}
                </span>
              </div>
            </div>

            <!-- Portfolio Data (if shared) -->
            <div v-if="member.sharing.share_portfolio_value && member.portfolio_value" class="portfolio-info">
              <span class="info-label">💼 Portfolio Value:</span>
              <strong class="info-value">₹{{ formatNumber(member.portfolio_value) }}</strong>
            </div>

            <!-- Holdings (if shared) -->
            <div v-if="member.sharing.share_holdings_list && member.top_holdings" class="holdings-info">
              <span class="info-label">📌 Top Holdings:</span>
              <div class="holdings-tags">
                <span 
                  v-for="holding in member.top_holdings" 
                  :key="holding.symbol" 
                  class="holding-tag"
                >
                  {{ holding.symbol }}
                  <span class="holding-value">(₹{{ formatNumber(holding.value) }})</span>
                </span>
              </div>
            </div>

            <!-- Performance (if shared) -->
            <div v-if="member.sharing.share_performance" class="performance-info">
              <span class="info-label">📈 Sharing performance data</span>
            </div>

            <!-- Private Message -->
            <div v-if="!member.sharing.share_portfolio_value && !member.sharing.share_holdings_list && !member.sharing.share_performance" class="private-message">
              <em>🔒 Limited information shared</em>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Sharing Settings Modal -->
    <div v-if="showSharingSettings" class="modal-overlay" @click="handleModalOverlayClick">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>🔒 My Sharing Settings</h3>
          <button @click="showSharingSettings = false" class="btn-close">×</button>
        </div>
        
        <div class="modal-body">
          <p class="info-text">
            Control what information other club members can see about your portfolio.
          </p>

          <div class="sharing-options">
            <label class="checkbox-option">
              <input 
                type="checkbox" 
                v-model="sharingSettings.share_portfolio_value"
              >
              <span class="checkmark"></span>
              <span class="label-text">
                <strong>Share Portfolio Value</strong>
                <em>Others can see your total portfolio value</em>
              </span>
            </label>
            
            <label class="checkbox-option">
              <input 
                type="checkbox" 
                v-model="sharingSettings.share_holdings_list"
              >
              <span class="checkmark"></span>
              <span class="label-text">
                <strong>Share Stock Holdings</strong>
                <em>Others can see your top holdings</em>
              </span>
            </label>
            
            <label class="checkbox-option">
              <input 
                type="checkbox" 
                v-model="sharingSettings.share_performance"
              >
              <span class="checkmark"></span>
              <span class="label-text">
                <strong>Share Performance Data</strong>
                <em>Others can see your investment performance</em>
              </span>
            </label>
          </div>
        </div>

        <div class="modal-actions">
          <button @click="showSharingSettings = false" class="btn-outline">Cancel</button>
          <button @click="saveSharingSettings" class="btn-primary" :disabled="isSaving">
            {{ isSaving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Success Message -->
    <div v-if="successMessage" class="success-message">
      <p>✅ {{ successMessage }}</p>
    </div>

    <!-- Error Message -->
    <div v-if="errorMessage" class="error-message">
      <p>❌ {{ errorMessage }}</p>
    </div>
  </div>
</template>

<script>
import { useAuthStore } from '../stores/auth_store'

export default {
  name: 'ClubDashboardView',
  props: {
    clubId: {
      type: Number,
      required: true
    }
  },
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  },
  data() {
    return {
      clubData: {
        name: '',
        join_code: '',
        created_by: null,
        created_at: null
      },
      dashboardData: null,
      showSharingSettings: false,
      sharingSettings: {
        share_portfolio_value: false,
        share_holdings_list: false,
        share_performance: false
      },
      loading: true,
      isSaving: false,
      successMessage: '',
      errorMessage: ''
    }
  },
  async mounted() {
    await this.loadClubDashboard()
  },
  methods: {
    async loadClubDashboard() {
      this.loading = true
      this.errorMessage = ''
      try {
        const token = this.authStore.getToken()
        const backendUrl = this.authStore.getBackendServerURL()
        const response = await fetch(`${backendUrl}/api/club/dashboard/${this.clubId}`, {
          headers: { 
            'Authentication-Token': token,
            'Content-Type': 'application/json'
          }
        })
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        
        if (data.success) {
          this.clubData = data.club
          this.dashboardData = data.dashboard
          await this.loadSharingSettings()
        } else {
          this.errorMessage = data.error || 'Failed to load club dashboard'
        }
      } catch (error) {
        console.error('Failed to load club dashboard:', error)
        this.errorMessage = 'Error loading dashboard. Please try again.'
      } finally {
        this.loading = false
      }
    },

    async loadSharingSettings() {
      try {
        const token = this.authStore.getToken()
        const backendUrl = this.authStore.getBackendServerURL()
        const response = await fetch(`${backendUrl}/api/club/sharing/${this.clubId}`, {
          headers: { 
            'Authentication-Token': token,
            'Content-Type': 'application/json'
          }
        })
        
        const data = await response.json()
        
        if (data.success) {
          this.sharingSettings = {
            share_portfolio_value: data.sharing.share_portfolio_value,
            share_holdings_list: data.sharing.share_holdings_list,
            share_performance: data.sharing.share_performance
          }
        }
      } catch (error) {
        console.error('Failed to load sharing settings:', error)
      }
    },

    async saveSharingSettings() {
      this.isSaving = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        const token = this.authStore.getToken()
        const backendUrl = this.authStore.getBackendServerURL()
        const response = await fetch(`${backendUrl}/api/club/sharing`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authentication-Token': token
          },
          body: JSON.stringify({
            club_id: this.clubId,
            ...this.sharingSettings
          })
        })
        
        const data = await response.json()
        
        if (data.success) {
          this.successMessage = 'Sharing settings updated successfully!'
          this.showSharingSettings = false
          await this.loadClubDashboard()
          setTimeout(() => this.successMessage = '', 3000)
        } else {
          this.errorMessage = data.error || 'Failed to update settings'
        }
      } catch (error) {
        console.error('Failed to update sharing settings:', error)
        this.errorMessage = 'Error updating settings. Please try again.'
      } finally {
        this.isSaving = false
      }
    },

    async refreshDashboard() {
      await this.loadClubDashboard()
      this.successMessage = 'Dashboard refreshed!'
      setTimeout(() => this.successMessage = '', 2000)
    },

    formatNumber(num) {
      return new Intl.NumberFormat('en-IN').format(Math.round(num))
    },

    handleModalOverlayClick() {
      this.showSharingSettings = false
    }
  }
}
</script>

<style scoped>
.club-dashboard {
  min-height: 100vh;
  background: #f5f7fa;
  padding-bottom: 30px;
}

/* Dashboard Header */
.dashboard-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  margin-bottom: 30px;
  border-radius: 12px;
  gap: 20px;
}

.btn-back {
  background: rgba(255,255,255,0.2);
  color: white;
  border: 2px solid white;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
  white-space: nowrap;
}

.btn-back:hover {
  background: white;
  color: #667eea;
}

.header-content {
  flex: 1;
  text-align: center;
}

.header-content h2 {
  margin: 0;
  font-size: 2em;
}

.club-code {
  margin: 8px 0 0 0;
  opacity: 0.95;
  font-size: 0.95em;
}

.btn-refresh {
  background: rgba(255,255,255,0.2);
  border: 2px solid white;
  color: white;
  padding: 10px 15px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1.3em;
  transition: all 0.3s;
}

.btn-refresh:hover {
  background: white;
  color: #667eea;
}

/* Loading */
.loading-spinner {
  text-align: center;
  padding: 80px 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 50px;
  height: 50px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Dashboard Content */
.dashboard-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

/* Overview Cards */
.overview-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.overview-card {
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  gap: 20px;
  transition: all 0.3s;
}

.overview-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.12);
}

.card-icon {
  font-size: 2.5em;
}

.card-content h3 {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 0.95em;
  font-weight: 500;
}

.card-value {
  font-size: 1.8em;
  font-weight: bold;
  color: #333;
}

/* Common Holdings Section */
.common-holdings-section {
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
  margin-bottom: 30px;
}

.section-description {
  color: #666;
  margin: 5px 0 15px 0;
  font-size: 0.95em;
}

.holdings-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.stock-tag {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 0.95em;
}

/* Members Section */
.members-section {
  background: white;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0,0,0,0.08);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.section-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.3em;
}

.btn-outline {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
  padding: 10px 20px;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-outline:hover {
  background: #667eea;
  color: white;
}

/* Members List */
.members-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.member-card {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 10px;
  border: 2px solid #f0f0f0;
  transition: all 0.3s;
}

.member-card:hover {
  border-color: #667eea;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.1);
}

.member-header {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.member-avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.3em;
  flex-shrink: 0;
}

.member-info-header h4 {
  margin: 0 0 5px 0;
  color: #333;
  font-size: 1.1em;
}

.role {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 0.85em;
  font-weight: 600;
}

.role.admin {
  background: #fff3cd;
  color: #856404;
}

.role.member {
  background: #d1ecf1;
  color: #0c5460;
}

/* Member Info */
.portfolio-info,
.holdings-info,
.performance-info {
  margin: 12px 0;
  padding: 10px;
  background: white;
  border-left: 4px solid #667eea;
  border-radius: 4px;
}

.info-label {
  display: block;
  font-weight: 600;
  color: #333;
  margin-bottom: 5px;
}

.info-value {
  color: #667eea;
  font-size: 1.1em;
}

.holdings-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.holding-tag {
  background: #f0f0f0;
  color: #333;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 0.9em;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.holding-value {
  font-size: 0.8em;
  color: #666;
  margin-top: 2px;
}

.private-message {
  color: #999;
  font-style: italic;
  padding: 10px;
  text-align: center;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 30px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 10px 40px rgba(0,0,0,0.3);
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 2px solid #f0f0f0;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.btn-close {
  background: none;
  border: none;
  font-size: 1.8em;
  cursor: pointer;
  color: #999;
  transition: color 0.2s;
}

.btn-close:hover {
  color: #333;
}

.modal-body {
  margin-bottom: 25px;
}

.info-text {
  color: #666;
  font-size: 0.95em;
  margin-bottom: 20px;
}

.sharing-options {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.checkbox-option {
  display: flex;
  align-items: flex-start;
  cursor: pointer;
  gap: 12px;
}

.checkbox-option input {
  width: 20px;
  height: 20px;
  margin-top: 2px;
  cursor: pointer;
}

.label-text {
  display: flex;
  flex-direction: column;
}

.label-text strong {
  color: #333;
  margin-bottom: 2px;
}

.label-text em {
  color: #999;
  font-size: 0.9em;
  font-style: italic;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-primary, .btn-outline {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Messages */
.success-message, .error-message {
  position: fixed;
  bottom: 20px;
  right: 20px;
  padding: 15px 20px;
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease;
  z-index: 999;
}

.success-message {
  background: #d4edda;
  color: #155724;
  border-left: 4px solid #28a745;
}

.error-message {
  background: #f8d7da;
  color: #721c24;
  border-left: 4px solid #f5c6cb;
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

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
    text-align: center;
  }

  .header-content h2 {
    font-size: 1.5em;
  }

  .members-list {
    grid-template-columns: 1fr;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .overview-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>
