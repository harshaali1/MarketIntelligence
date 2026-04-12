<script setup>
import { reactive, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth_store'

const authStore = useAuthStore()

const state = reactive({
  clubs: [],
  loading: false,
  selectedClub: null,
  dashboardData: null,
  showCreateModal: false,
  showJoinModal: false,
  showPermissionModal: false,
  permissionAction: null, // 'create', 'join', or 'update'
})

const form = reactive({
  clubName: '',
  joinCode: '',
  permissions: {
    sharePortfolioValue: false,
    shareHoldings: false,
    sharePerformance: false
  }
})

const apiUrl = authStore.getBackendServerURL()
const token = authStore.getToken()

const headers = {
  'Authentication-Token': token,
  'Content-Type': 'application/json'
}

onMounted(() => {
  loadClubs()
})

async function loadClubs() {
  state.loading = true
  try {
    const response = await fetch(`${apiUrl}/api/v1/club/my-clubs`, { headers })
    if (!response.ok) throw new Error('Failed to load clubs')
    const data = await response.json()
    if (data.success) {
      state.clubs = data.clubs || []
    }
  } catch (error) {
    console.error('Error loading clubs:', error)
  } finally {
    state.loading = false
  }
}

async function viewClubDetails(club) {
  console.log('Viewing club details:', club)
  state.selectedClub = club
  try {
    const response = await fetch(`${apiUrl}/api/v1/club/dashboard/${club.id}`, { headers })
    if (!response.ok) throw new Error('Failed to load dashboard')
    const data = await response.json()
    console.log('Dashboard data received:', data)
    if (data.success) {
      state.dashboardData = data.dashboard || {}
      console.log('Dashboard loaded:', state.dashboardData)
    }
  } catch (error) {
    console.error('Error loading dashboard:', error)
  }
}

function openCreateClubDialog() {
  console.log('Opening create club dialog')
  state.showPermissionModal = true
  state.permissionAction = 'create'
}

function openJoinClubDialog() {
  console.log('Opening join club dialog')
  state.showPermissionModal = true
  state.permissionAction = 'join'
}

async function confirmAction() {
  if (state.permissionAction === 'update') {
    await updatePermissions()
    return
  }
  
  state.showPermissionModal = false
  
  if (state.permissionAction === 'create') {
    state.showCreateModal = true
  } else if (state.permissionAction === 'join') {
    state.showJoinModal = true
  }
}

async function submitCreateClub() {
  if (!form.clubName.trim()) return
  
  try {
    const response = await fetch(`${apiUrl}/api/v1/club/create`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        club_name: form.clubName,
        share_portfolio_value: form.permissions.sharePortfolioValue,
        share_holdings_list: form.permissions.shareHoldings,
        share_performance: form.permissions.sharePerformance
      })
    })
    
    const data = await response.json()
    if (data.success) {
      form.clubName = ''
      form.permissions = { sharePortfolioValue: false, shareHoldings: false, sharePerformance: false }
      state.showCreateModal = false
      await loadClubs()
      alert('Club created successfully! Join code: ' + data.club.join_code)
    }
  } catch (error) {
    console.error('Error creating club:', error)
  }
}

async function submitJoinClub() {
  if (!form.joinCode.trim()) return
  
  try {
    const response = await fetch(`${apiUrl}/api/v1/club/join`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        join_code: form.joinCode,
        share_portfolio_value: form.permissions.sharePortfolioValue,
        share_holdings_list: form.permissions.shareHoldings,
        share_performance: form.permissions.sharePerformance
      })
    })
    
    const data = await response.json()
    if (data.success) {
      form.joinCode = ''
      form.permissions = { sharePortfolioValue: false, shareHoldings: false, sharePerformance: false }
      state.showJoinModal = false
      await loadClubs()
      alert('Successfully joined club!')
    }
  } catch (error) {
    console.error('Error joining club:', error)
  }
}

async function updatePermissions() {
  if (!state.selectedClub) return
  
  try {
    const response = await fetch(`${apiUrl}/api/v1/club/sharing`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        club_id: state.selectedClub.id,
        share_portfolio_value: form.permissions.sharePortfolioValue,
        share_holdings_list: form.permissions.shareHoldings,
        share_performance: form.permissions.sharePerformance
      })
    })
    
    const data = await response.json()
    if (data.success) {
      state.showPermissionModal = false
      alert('Sharing preferences updated!')
      await viewClubDetails(state.selectedClub)
    }
  } catch (error) {
    console.error('Error updating permissions:', error)
  }
}

async function leaveClub() {
  if (!state.selectedClub) return
  
  if (!confirm('Are you sure you want to leave this club?')) return
  
  try {
    const response = await fetch(`${apiUrl}/api/v1/club/leave`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ club_id: state.selectedClub.id })
    })
    
    const data = await response.json()
    if (data.success) {
      state.selectedClub = null
      state.dashboardData = null
      await loadClubs()
      alert('You have left the club')
    }
  } catch (error) {
    console.error('Error leaving club:', error)
  }
}

function openUpdatePermissions() {
  console.log('Opening update permissions dialog')
  if (!state.selectedClub || !state.dashboardData) {
    console.warn('Missing club or dashboard data')
    return
  }
  
  const currentUserMember = state.dashboardData.members.find(
    m => m.user_id === authStore.getUserId()
  )
  console.log('Current user member:', currentUserMember)
  
  if (currentUserMember) {
    form.permissions.sharePortfolioValue = currentUserMember.sharing.share_portfolio_value
    form.permissions.shareHoldings = currentUserMember.sharing.share_holdings_list
    form.permissions.sharePerformance = currentUserMember.sharing.share_performance
  }
  
  state.permissionAction = 'update'
  state.showPermissionModal = true
}

function copyToClipboard() {
  console.log('Copy to clipboard clicked')
  if (!state.selectedClub) {
    console.warn('No club selected')
    return
  }
  navigator.clipboard.writeText(state.selectedClub.join_code)
  alert('Club code copied to clipboard!')
}

function isSharingAnyData(member) {
  return member.sharing.share_portfolio_value || 
         member.sharing.share_holdings_list || 
         member.sharing.share_performance
}

function formatCurrency(value) {
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0
  }).format(value)
}

function getPerformanceClass(performance) {
  return performance >= 0 ? 'positive' : 'negative'
}

const visibleMembersCount = computed(() => {
  if (!state.dashboardData) return 0
  return state.dashboardData.members.filter(m => isSharingAnyData(m)).length
})
</script>

<template>
  <div class="clubs-view">
    <!-- Header -->
    <div class="header">
      <h2>Investment Clubs</h2>
      <div class="header-actions">
        <button @click="openCreateClubDialog" class="btn-primary">
          Create Club
        </button>
        <button @click="openJoinClubDialog" class="btn-secondary">
          Join Club
        </button>
      </div>
    </div>

    <!-- Main Layout: Clubs List + Details -->
    <div class="clubs-layout">
      <!-- Left: Clubs List -->
      <div class="clubs-list-section">
        <h3>My Clubs</h3>
        <div v-if="state.loading" class="loading">Loading clubs...</div>
        <div v-else-if="state.clubs.length === 0" class="empty-state">
          <p>No clubs yet. Create or join one to get started!</p>
        </div>
        <div v-else class="clubs-list">
          <div
            v-for="club in state.clubs"
            :key="club.id"
            class="club-card"
            :class="{ active: state.selectedClub?.id === club.id }"
            @click="viewClubDetails(club)"
          >
            <div class="club-card-name">{{ club.club_name }}</div>
            <div class="club-card-code">{{ club.join_code }}</div>
          </div>
        </div>
      </div>

      <!-- Right: Club Details -->
      <div class="club-details-section" v-if="state.selectedClub && state.dashboardData">
        <!-- Club Header -->
        <div class="club-header">
          <h2>{{ state.selectedClub.club_name }}</h2>
          <div class="club-stats">
            <div class="stat">
              <span class="stat-value">{{ state.dashboardData.total_members }}</span>
              <span class="stat-label">Members</span>
            </div>
            <div class="stat">
              <span class="stat-value">{{ visibleMembersCount }}</span>
              <span class="stat-label">Sharing Data</span>
            </div>
            <div class="stat" v-if="state.dashboardData.total_net_worth > 0">
              <span class="stat-value">{{ formatCurrency(state.dashboardData.total_net_worth) }}</span>
              <span class="stat-label">Combined Portfolio</span>
            </div>
          </div>
        </div>

        <!-- Club Code -->
        <div class="club-code-section">
          <span class="label">Club Code:</span>
          <div class="code-container">
            <code>{{ state.selectedClub.join_code }}</code>
            <button @click="copyToClipboard" class="btn-copy" title="Copy code">
              📋
            </button>
          </div>
        </div>

        <!-- Common Holdings -->
        <div v-if="state.dashboardData.common_holdings && state.dashboardData.common_holdings.length > 0" class="common-holdings">
          <h4>Popular Stocks</h4>
          <div class="stocks-list">
            <span v-for="stock in state.dashboardData.common_holdings" :key="stock" class="stock-tag">
              {{ stock }}
            </span>
          </div>
        </div>

        <!-- Members Section -->
        <div class="members-section">
          <h4>Club Members</h4>
          <div v-if="state.dashboardData.members.length === 0" class="no-data">
            <p>No members yet</p>
          </div>
          <div v-else class="members-list">
            <div
              v-for="member in state.dashboardData.members"
              :key="member.user_id"
              class="member-card"
            >
              <!-- Member Basic Info (Always Visible) -->
              <div class="member-basic">
                <div class="member-avatar">{{ member.username[0].toUpperCase() }}</div>
                <div class="member-info">
                  <div class="member-name">{{ member.username }}</div>
                  <span class="member-role">{{ member.role }}</span>
                </div>
              </div>

              <!-- Shared Data (Only if User Shared) -->
              <div class="member-shared-data">
                <!-- Portfolio Value -->
                <div
                  v-if="member.sharing.share_portfolio_value && member.portfolio_value > 0"
                  class="shared-item"
                >
                  <span class="shared-label">Portfolio Value:</span>
                  <span class="shared-value">{{ formatCurrency(member.portfolio_value) }}</span>
                </div>

                <!-- Holdings -->
                <div
                  v-if="member.sharing.share_holdings_list && member.top_holdings.length > 0"
                  class="shared-item holdings-item"
                >
                  <span class="shared-label">Top Holdings:</span>
                  <div class="holdings-details">
                    <div
                      v-for="holding in member.top_holdings"
                      :key="holding.symbol"
                      class="holding-detail"
                    >
                      <span class="holding-symbol">{{ holding.symbol }}</span>
                      <span class="holding-qty">{{ holding.quantity }} shares</span>
                      <span class="holding-value">{{ formatCurrency(holding.value) }}</span>
                    </div>
                  </div>
                </div>

                <!-- Performance -->
                <div
                  v-if="member.sharing.share_performance"
                  class="shared-item"
                >
                  <span class="shared-label">Returns:</span>
                  <span
                    class="shared-value"
                    :class="getPerformanceClass(member.performance)"
                  >
                    {{ member.performance > 0 ? '+' : '' }}{{ member.performance }}%
                  </span>
                </div>

                <!-- No Data Message -->
                <div v-if="!isSharingAnyData(member)" class="no-share-message">
                  <span>Not sharing data</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Action Buttons -->
        <div class="action-buttons">
          <button @click="openUpdatePermissions" class="btn-primary">
            Change Permissions
          </button>
          <button @click="leaveClub" class="btn-danger">
            Leave Club
          </button>
        </div>

        <!-- Empty State -->
        <div v-if="visibleMembersCount === 0" class="empty-share-state">
          <h4>No one is sharing data yet</h4>
          <p>Members need to update their sharing preferences to see club insights.</p>
        </div>
      </div>

      <!-- No Club Selected -->
      <div v-else class="no-selection">
        <p>Select a club to view details</p>
      </div>
    </div>

    <!-- Create Club Modal -->
    <div v-if="state.showCreateModal" class="modal-overlay" @click.self="state.showCreateModal = false">
      <div class="modal">
        <h3>Create New Club</h3>
        <input
          v-model="form.clubName"
          type="text"
          placeholder="Club name"
          class="form-input"
        />
        <div class="modal-actions">
          <button @click="submitCreateClub" class="btn-primary">Create</button>
          <button @click="state.showCreateModal = false" class="btn-secondary">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Join Club Modal -->
    <div v-if="state.showJoinModal" class="modal-overlay" @click.self="state.showJoinModal = false">
      <div class="modal">
        <h3>Join Club</h3>
        <input
          v-model="form.joinCode"
          type="text"
          placeholder="Enter join code"
          class="form-input"
        />
        <div class="modal-actions">
          <button @click="submitJoinClub" class="btn-primary">Join</button>
          <button @click="state.showJoinModal = false" class="btn-secondary">Cancel</button>
        </div>
      </div>
    </div>

    <!-- Permissions Modal -->
    <div v-if="state.showPermissionModal" class="modal-overlay" @click.self="state.showPermissionModal = false">
      <div class="modal">
        <h3>{{ state.permissionAction === 'update' ? 'Update Sharing Preferences' : 'What do you want to share?' }}</h3>
        
        <div class="permission-options">
          <label class="permission-checkbox">
            <input
              v-model="form.permissions.sharePortfolioValue"
              type="checkbox"
            />
            <div class="permission-content">
              <strong>Portfolio Total Value</strong>
              <p>Club members will see your total portfolio value</p>
            </div>
          </label>

          <label class="permission-checkbox">
            <input
              v-model="form.permissions.shareHoldings"
              type="checkbox"
            />
            <div class="permission-content">
              <strong>Stock Holdings</strong>
              <p>Club members will see which stocks you own</p>
            </div>
          </label>

          <label class="permission-checkbox">
            <input
              v-model="form.permissions.sharePerformance"
              type="checkbox"
            />
            <div class="permission-content">
              <strong>Investment Performance</strong>
              <p>Club members will see your returns percentage</p>
            </div>
          </label>
        </div>

        <div class="modal-actions">
          <button @click="confirmAction" class="btn-primary">
            {{ state.permissionAction === 'update' ? 'Update' : 'Continue' }}
          </button>
          <button @click="state.showPermissionModal = false" class="btn-secondary">Cancel</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.clubs-view {
  padding: 1.5rem;
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f5f5;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.header h2 {
  margin: 0;
  color: #1a1a2e;
  font-size: 1.8rem;
}

.header-actions {
  display: flex;
  gap: 0.8rem;
}

.btn-primary, .btn-secondary, .btn-danger {
  padding: 0.7rem 1.2rem;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.btn-primary {
  background: #3f51b5;
  color: white;
}

.btn-primary:hover {
  background: #303f9f;
}

.btn-secondary {
  background: #e0e0e0;
  color: #1a1a2e;
}

.btn-secondary:hover {
  background: #d0d0d0;
}

.btn-danger {
  background: #e53935;
  color: white;
}

.btn-danger:hover {
  background: #c62828;
}

.clubs-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;
  flex: 1;
  overflow: hidden;
}

.clubs-list-section {
  background: white;
  border-radius: 8px;
  padding: 1.2rem;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.clubs-list-section h3 {
  margin: 0 0 1rem 0;
  color: #1a1a2e;
  font-size: 1.1rem;
}

.clubs-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  overflow-y: auto;
  flex: 1;
}

.club-card {
  padding: 0.9rem;
  background: #f8f9fa;
  border-left: 3px solid transparent;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.club-card:hover {
  background: #e8eaf6;
  border-left-color: #3f51b5;
}

.club-card.active {
  background: #e8eaf6;
  border-left-color: #3f51b5;
}

.club-card-name {
  font-weight: 600;
  color: #1a1a2e;
  font-size: 0.95rem;
  margin-bottom: 0.3rem;
}

.club-card-code {
  font-size: 0.75rem;
  color: #999;
  font-family: monospace;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 2rem 0;
}

.club-details-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.club-header {
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.club-header h2 {
  margin: 0 0 1rem 0;
  color: #1a1a2e;
  font-size: 1.6rem;
}

.club-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat {
  background: #f8f9fa;
  padding: 0.8rem;
  border-radius: 6px;
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
  color: #3f51b5;
  margin-bottom: 0.2rem;
}

.stat-label {
  display: block;
  font-size: 0.8rem;
  color: #999;
}

.club-code-section {
  margin-bottom: 1.2rem;
  padding: 0.8rem;
  background: #f8f9fa;
  border-radius: 6px;
  display: flex;
  align-items: center;
  gap: 0.8rem;
}

.label {
  font-weight: 600;
  color: #666;
}

.code-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

code {
  background: white;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.85rem;
  color: #1a1a2e;
}

.btn-copy {
  background: none;
  border: none;
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.2rem 0.5rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-copy:hover {
  background: #e0e0e0;
}

.common-holdings {
  margin-bottom: 1.5rem;
}

.common-holdings h4 {
  margin: 0 0 0.8rem 0;
  color: #1a1a2e;
  font-size: 1rem;
}

.stocks-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.stock-tag {
  background: #e3f2fd;
  color: #1976d2;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  font-size: 0.85rem;
  font-weight: 500;
}

.members-section {
  margin-bottom: 1.5rem;
}

.members-section h4 {
  margin: 0 0 1rem 0;
  color: #1a1a2e;
  font-size: 1rem;
}

.members-list {
  display: flex;
  flex-direction: column;
  gap: 0.8rem;
  max-height: 300px;
  overflow-y: auto;
}

.member-card {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
  border-left: 3px solid #3f51b5;
}

.member-basic {
  display: flex;
  align-items: center;
  gap: 0.8rem;
  margin-bottom: 0.8rem;
}

.member-avatar {
  width: 40px;
  height: 40px;
  background: #3f51b5;
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 1rem;
}

.member-info {
  flex: 1;
}

.member-name {
  font-weight: 600;
  color: #1a1a2e;
  font-size: 0.95rem;
  margin: 0;
}

.member-role {
  font-size: 0.8rem;
  color: #999;
  text-transform: capitalize;
}

.member-shared-data {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  font-size: 0.9rem;
}

.shared-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.4rem 0;
  border-top: 1px solid #e8eaf6;
  padding-top: 0.6rem;
}

.shared-item:first-of-type {
  border-top: none;
  padding-top: 0;
}

.shared-label {
  font-weight: 600;
  color: #666;
  min-width: 120px;
}

.shared-value {
  color: #1a1a2e;
  font-weight: 500;
}

.shared-value.positive {
  color: #2e7d32;
}

.shared-value.negative {
  color: #c62828;
}

.holdings-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}

.holding-badge {
  background: #c8e6c9;
  color: #2e7d32;
  padding: 0.2rem 0.6rem;
  border-radius: 3px;
  font-size: 0.75rem;
  font-weight: 500;
}

.holdings-details {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.4rem;
}

.holding-detail {
  display: flex;
  gap: 1rem;
  align-items: center;
  padding: 0.5rem;
  background: #f0f8f4;
  border-radius: 4px;
  font-size: 0.85rem;
}

.holding-symbol {
  font-weight: 600;
  color: #2e7d32;
  min-width: 60px;
}

.holding-qty {
  color: #666;
  font-size: 0.8rem;
  flex: 1;
}

.holding-value {
  color: #1a1a2e;
  font-weight: 500;
  min-width: 100px;
  text-align: right;
}

.no-share-message {
  color: #999;
  font-style: italic;
  font-size: 0.85rem;
}

.no-data {
  text-align: center;
  color: #999;
  padding: 1rem;
}

.action-buttons {
  display: flex;
  gap: 0.8rem;
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.empty-share-state {
  text-align: center;
  padding: 2rem;
  background: #fff3e0;
  border-radius: 6px;
  margin-top: 1rem;
}

.empty-share-state h4 {
  margin: 0 0 0.5rem 0;
  color: #e65100;
}

.empty-share-state p {
  margin: 0;
  color: #ff9800;
  font-size: 0.9rem;
}

.no-selection {
  background: white;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  color: #999;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

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
}

.modal {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  max-width: 400px;
  width: 90%;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.modal h3 {
  margin: 0 0 1.5rem 0;
  color: #1a1a2e;
  font-size: 1.3rem;
}

.form-input {
  width: 100%;
  padding: 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1rem;
  margin-bottom: 1.5rem;
  box-sizing: border-box;
}

.form-input:focus {
  outline: none;
  border-color: #3f51b5;
  box-shadow: 0 0 0 3px rgba(63, 81, 181, 0.1);
}

.permission-options {
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.permission-checkbox {
  display: flex;
  gap: 0.8rem;
  cursor: pointer;
  align-items: flex-start;
}

.permission-checkbox input {
  margin-top: 0.3rem;
  cursor: pointer;
  accent-color: #3f51b5;
}

.permission-content {
  flex: 1;
}

.permission-content strong {
  display: block;
  color: #1a1a2e;
  margin-bottom: 0.3rem;
}

.permission-content p {
  margin: 0;
  font-size: 0.85rem;
  color: #999;
}

.modal-actions {
  display: flex;
  gap: 0.8rem;
  justify-content: flex-end;
}

.modal-actions button {
  min-width: 100px;
}

.loading {
  text-align: center;
  color: #999;
  padding: 1rem;
}

@media (max-width: 1024px) {
  .clubs-layout {
    grid-template-columns: 1fr;
  }

  .club-stats {
    grid-template-columns: 1fr;
  }
}
</style>
