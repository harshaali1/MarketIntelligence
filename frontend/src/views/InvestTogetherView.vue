<template>
  <div class="invest-together-container">
    <div class="header">
      <h1>🤝 Invest Together</h1>
      <p>Create or join investment clubs to share insights and grow your wealth together</p>
    </div>

    <!-- Create/Join Club Setup -->
    <div v-if="activeView === 'setup'" class="setup-section">
      <div class="card create-card">
        <h3>🆕 Create Investment Club</h3>
        <p>Start a new club and invite friends or family to join</p>
        <form @submit.prevent="createClub" class="club-form">
          <input 
            v-model="newClubName" 
            type="text"
            placeholder="Club name (e.g., Tech Investors, Family Fund)"
            required
            class="input-field"
          >
          <button type="submit" class="btn-primary" :disabled="isLoading">
            {{ isLoading ? 'Creating...' : 'Create Club' }}
          </button>
        </form>
      </div>

      <div class="divider">
        <span>OR</span>
      </div>

      <div class="card join-card">
        <h3>📨 Join Existing Club</h3>
        <p>Enter a club code shared by the admin</p>
        <form @submit.prevent="joinClub" class="join-form">
          <input 
            v-model="joinCode" 
            type="text"
            placeholder="Enter club code (e.g., CLUB-ABC123)"
            required
            class="input-field"
          >
          <button type="submit" class="btn-outline" :disabled="isLoading">
            {{ isLoading ? 'Joining...' : 'Join Club' }}
          </button>
        </form>
      </div>
    </div>

    <!-- My Clubs View -->
    <div v-else-if="activeView === 'clubs'" class="clubs-section">
      <div class="section-header">
        <h2>My Investment Clubs</h2>
        <button @click="activeView = 'setup'" class="btn-primary">
          + Create or Join Club
        </button>
      </div>

      <div v-if="loading" class="loading-spinner">
        <div class="spinner"></div>
        <p>Loading your clubs...</p>
      </div>
      
      <div v-else-if="clubs.length === 0" class="empty-state">
        <p>📚 You haven't joined any investment clubs yet.</p>
        <button @click="activeView = 'setup'" class="btn-primary">
          Create Your First Club
        </button>
      </div>

      <div v-else class="clubs-grid">
        <div 
          v-for="club in clubs" 
          :key="club.club_id"
          class="club-card"
        >
          <div class="club-header">
            <h3>{{ club.club_name }}</h3>
            <span class="role-badge" :class="club.role">
              {{ club.role === 'admin' ? '👑 Admin' : '👤 Member' }}
            </span>
          </div>
          <div class="club-details">
            <div class="detail-row">
              <span class="label">Code:</span>
              <span class="code">{{ club.join_code }}</span>
              <button @click="copyToClipboard(club.join_code)" class="copy-btn" title="Copy code">
                📋
              </button>
            </div>
            <div class="detail-row">
              <span class="label">Members:</span>
              <span class="value">{{ club.total_members }}</span>
            </div>
            <div class="detail-row">
              <span class="label">Joined:</span>
              <span class="value">{{ formatDate(club.joined_at) }}</span>
            </div>
          </div>
          <div class="club-actions">
            <button 
              @click="viewClubDashboard(club.club_id)" 
              class="btn-small"
            >
              📊 Dashboard
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Club Dashboard View -->
    <div v-else-if="activeView === 'dashboard'" class="dashboard-view">
      <ClubDashboard 
        :club-id="selectedClubId"
        @back="handleDashboardBack"
      />
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
import ClubDashboard from './ClubDashboardView.vue'

export default {
  name: 'InvestTogetherView',
  components: { 
    ClubDashboard 
  },
  setup() {
    const authStore = useAuthStore()
    return { authStore }
  },
  data() {
    return {
      activeView: 'clubs',  // 'setup', 'clubs', or 'dashboard'
      newClubName: '',
      joinCode: '',
      clubs: [],
      selectedClubId: null,
      loading: false,
      isLoading: false,
      successMessage: '',
      errorMessage: ''
    }
  },
  async mounted() {
    await this.loadMyClubs()
  },
  methods: {
    async loadMyClubs() {
      this.loading = true
      this.errorMessage = ''
      try {
        const token = this.authStore.getToken()
        const backendUrl = this.authStore.getBackendServerURL()
        
        console.log('DEBUG: Token =', token ? 'exists' : 'NULL')
        console.log('DEBUG: Backend URL =', backendUrl)
        
        if (!token) {
          this.errorMessage = 'Not authenticated. Please log in again.'
          this.loading = false
          return
        }
        
        const response = await fetch(`${backendUrl}/api/club/my-clubs`, {
          headers: { 
            'Authentication-Token': token,
            'Content-Type': 'application/json'
          }
        })
        
        console.log('DEBUG: Response status =', response.status)
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        
        const data = await response.json()
        console.log('DEBUG: Response data =', data)
        
        if (data.success) {
          this.clubs = data.clubs
        } else {
          this.errorMessage = data.error || 'Failed to load clubs'
        }
      } catch (error) {
        console.error('Failed to load clubs:', error)
        this.errorMessage = 'Error loading clubs. Please try again.'
      } finally {
        this.loading = false
      }
    },

    async createClub() {
      if (!this.newClubName.trim()) {
        this.errorMessage = 'Please enter a club name'
        return
      }

      this.isLoading = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        const token = this.authStore.getToken()
        const backendUrl = this.authStore.getBackendServerURL()
        const response = await fetch(`${backendUrl}/api/club/create`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authentication-Token': token
          },
          body: JSON.stringify({ club_name: this.newClubName })
        })
        
        const data = await response.json()
        
        if (data.success) {
          this.successMessage = `Club created! Share this code: ${data.join_code}`
          this.newClubName = ''
          await this.loadMyClubs()
          this.activeView = 'clubs'
          setTimeout(() => this.successMessage = '', 3000)
        } else {
          this.errorMessage = data.error || 'Failed to create club'
        }
      } catch (error) {
        console.error('Failed to create club:', error)
        this.errorMessage = 'Error creating club. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    async joinClub() {
      if (!this.joinCode.trim()) {
        this.errorMessage = 'Please enter a club code'
        return
      }

      this.isLoading = true
      this.errorMessage = ''
      this.successMessage = ''

      try {
        const token = this.authStore.getToken()
        const backendUrl = this.authStore.getBackendServerURL()
        const response = await fetch(`${backendUrl}/api/club/join`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json', 
            'Authentication-Token': token
          },
          body: JSON.stringify({ join_code: this.joinCode })
        })
        
        const data = await response.json()
        
        if (data.success) {
          this.successMessage = `Successfully joined ${data.club_name}!`
          this.joinCode = ''
          await this.loadMyClubs()
          this.activeView = 'clubs'
          setTimeout(() => this.successMessage = '', 3000)
        } else {
          this.errorMessage = data.error || 'Failed to join club'
        }
      } catch (error) {
        console.error('Failed to join club:', error)
        this.errorMessage = 'Error joining club. Please try again.'
      } finally {
        this.isLoading = false
      }
    },

    viewClubDashboard(clubId) {
      this.selectedClubId = clubId
      this.activeView = 'dashboard'
    },

    handleDashboardBack() {
      this.activeView = 'clubs'
      this.loadMyClubs()
    },

    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    },

    copyToClipboard(text) {
      navigator.clipboard.writeText(text).then(() => {
        this.successMessage = 'Code copied to clipboard!'
        setTimeout(() => this.successMessage = '', 2000)
      })
    }
  }
}
</script>

<style scoped>
.invest-together-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.header {
  text-align: center;
  margin-bottom: 40px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  border-radius: 12px;
}

.header h1 {
  margin: 0;
  font-size: 2.5em;
  margin-bottom: 10px;
}

.header p {
  margin: 0;
  font-size: 1.1em;
  opacity: 0.9;
}

/* Setup Section */
.setup-section {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 30px;
  align-items: center;
  margin-bottom: 40px;
}

.card {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0,0,0,0.1);
  transition: transform 0.3s, box-shadow 0.3s;
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

.card h3 {
  margin-top: 0;
  color: #333;
  font-size: 1.3em;
}

.card p {
  color: #666;
  margin: 10px 0 20px 0;
}

.club-form, .join-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-field {
  padding: 12px;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1em;
  transition: border-color 0.3s;
}

.input-field:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.divider {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
  font-weight: bold;
  font-size: 0.9em;
}

.divider span {
  background: white;
  padding: 0 10px;
}

/* Clubs Section */
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid #e0e0e0;
}

.section-header h2 {
  margin: 0;
  color: #333;
  font-size: 2em;
}

.clubs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.club-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  border: 2px solid #f0f0f0;
  transition: all 0.3s;
}

.club-card:hover {
  border-color: #667eea;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.15);
  transform: translateY(-4px);
}

.club-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 15px;
  gap: 10px;
}

.club-header h3 {
  margin: 0;
  color: #333;
  flex: 1;
}

.role-badge {
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 0.85em;
  font-weight: bold;
  white-space: nowrap;
}

.role-badge.admin {
  background: #fff3cd;
  color: #856404;
}

.role-badge.member {
  background: #d1ecf1;
  color: #0c5460;
}

.club-details {
  margin: 15px 0;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  font-size: 0.95em;
  color: #555;
}

.label {
  font-weight: 600;
  color: #333;
}

.code {
  font-family: 'Courier New', monospace;
  background: #f5f5f5;
  padding: 4px 8px;
  border-radius: 4px;
}

.copy-btn {
  background: none;
  border: none;
  cursor: pointer;
  font-size: 1.2em;
  opacity: 0.6;
  transition: opacity 0.2s;
  padding: 0 5px;
}

.copy-btn:hover {
  opacity: 1;
}

.club-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  border-radius: 12px;
  color: #555;
}

.empty-state p {
  font-size: 1.1em;
  margin-bottom: 20px;
}

/* Loading */
.loading-spinner {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Buttons */
.btn-primary, .btn-outline, .btn-small {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 1em;
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

.btn-outline {
  background: white;
  color: #667eea;
  border: 2px solid #667eea;
}

.btn-outline:hover:not(:disabled) {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
}

.btn-small {
  padding: 8px 16px;
  font-size: 0.9em;
  background: #f5f5f5;
  color: #333;
  border: 1px solid #ddd;
}

.btn-small:hover {
  background: #667eea;
  color: white;
  border-color: #667eea;
}

/* Messages */
.success-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #d4edda;
  color: #155724;
  padding: 15px 20px;
  border-radius: 6px;
  border-left: 4px solid #28a745;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease;
  z-index: 1000;
}

.error-message {
  position: fixed;
  top: 20px;
  right: 20px;
  background: #f8d7da;
  color: #721c24;
  padding: 15px 20px;
  border-radius: 6px;
  border-left: 4px solid #f5c6cb;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease;
  z-index: 1000;
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
  .setup-section {
    grid-template-columns: 1fr;
    gap: 20px;
  }

  .divider {
    height: 1px;
    background: #e0e0e0;
  }

  .divider span {
    display: none;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .clubs-grid {
    grid-template-columns: 1fr;
  }
}
</style>
