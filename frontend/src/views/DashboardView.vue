<script setup>
import { ref } from 'vue'
import SearchView from './SearchView.vue'
import WatchlistView from './WatchlistView.vue'
import PortfolioView from './PortfolioView.vue'
// eslint-disable-next-line no-unused-vars
import ClubsView from './ClubsView.vue'

const activeTab = ref('search')

const tabs = [
  { key: 'search', label: 'Search & Analysis' },
  { key: 'watchlist', label: 'Watchlist' },
  { key: 'portfolio', label: 'Portfolio' },
  { key: 'clubs', label: 'Investment Clubs' }
]
</script>

<template>
  <div class="dashboard-container">
    
    <div class="sub-nav-card">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { 'active-tab': activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <div class="tab-content">
      <SearchView v-if="activeTab === 'search'" />
      <WatchlistView v-if="activeTab === 'watchlist'" />
      <PortfolioView v-if="activeTab === 'portfolio'" />
      <ClubsView v-if="activeTab === 'clubs'" />
    </div>
  </div>
</template>

<style scoped>
/* --- Design Variables --- */
:root {
  --color-dark: #1a1a2e;
  --color-primary-blue: #3f51b5; /* Used for subtle hover */
  --color-text-subtle: #6a6a85;
  --color-bg-light: #f8f9fa;
  --color-active-bg-inner: #ffffff; /* White background for the active pill/tab */
}

/* --- Container and Layout --- */
.dashboard-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
  padding-top: 1.5rem; 
}

/* --- Sub-Navigation Card (Matching Image Look) --- */
.sub-nav-card {
  display: flex;
  justify-content: space-around;
  width: 90%;
  max-width: 1200px;
  
  background: white;
  border-radius: 12px;
  padding: 0.5rem 0.25rem;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08); 
  margin-bottom: 2rem;
}

/* --- Tab Buttons --- */
.tab-btn {
  flex: 1;
  text-align: center;
  
  padding: 0.7rem 1rem;
  border: none;
  background: transparent;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--color-dark); /* Dark text for inactive tabs */
  cursor: pointer;
  transition: all 0.2s ease;
}

/* --- Inactive Tab Hover --- */
.tab-btn:hover:not(.active-tab) {
  color: var(--color-primary-blue);
}

/* --- Active Tab Styling (FIXED: White background with DARK text) --- */
.tab-btn.active-tab {
  /* Set background to white/light gray matching the image */
  background-color: var(--color-active-bg-inner); 
  /* FIX: Set text color to DARK so it's visible on the light background */
  color: var(--color-dark); 
  /* Add a stronger shadow/elevation for the active tab pill */
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1); 
}

/* --- Tab Content Area --- */
.tab-content {
  width: 100%;
  max-width: 1800px; 
  padding: 0 1rem;
}

/* Adjust button width for smaller screens */
@media (max-width: 768px) {
  .sub-nav-card {
    width: 95%;
  }
}
</style>