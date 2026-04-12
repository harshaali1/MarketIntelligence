<script setup>
import { computed } from 'vue';
import { useRouter, RouterLink, RouterView } from 'vue-router';
import axios from 'axios';
import { useMessageStore } from './stores/message_store';
import { useAuthStore } from './stores/auth_store';
import FloatingChatWidget from './components/FloatingChatWidget.vue';

const messageStore = useMessageStore();
const authStore = useAuthStore();
const router = useRouter();

const message = computed(() => messageStore.getFlashMessage());
const user = computed(() => authStore.getUserData());
const isAuthenticated = computed(() => authStore.isAuthenticated);

async function logout() {
  try {
    await fetch(`${authStore.getBackendServerURL()}/logout`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.getToken()}`
      }
    });
  } catch (error) {
    console.warn("Logout endpoint failed or missing:", error);
  } finally {
    authStore.removeAuthUser();
    messageStore.setFlashMessage("You have been logged out.");
    router.push('/login');
  }
}

// --- Axios Interceptors ---
axios.interceptors.request.use(config => {
  const token = authStore.getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
axios.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401 && authStore.isAuthenticated) {
      messageStore.setFlashMessage('Session expired. Please log in again.');
      authStore.removeAuthUser();
      router.push('/login');
    }
    return Promise.reject(err);
  }
);
</script>

<template>
  <div id="app-layout">
    <nav class="navbar">
      <RouterLink :to="isAuthenticated ? '/dashboard' : '/'" class="brand">
        Market Intelligence
      </RouterLink>

      <div class="nav-links">
        <template v-if="!isAuthenticated">
          <RouterLink to="/login" class="nav-btn">Sign In</RouterLink>
          <RouterLink to="/signup" class="nav-btn">Get Started</RouterLink>
        </template>
        <template v-else>
          <span class="user-text">
            Welcome, {{ user?.username || 'User' }}
          </span>
          <RouterLink to="/dashboard" class="nav-btn subtle">Dashboard</RouterLink>
          <button @click="logout" class="nav-btn logout-btn">Logout</button>
        </template>
      </div>
    </nav>

    <div v-if="message" class="flash">
      {{ message }}
      <button class="close" @click="messageStore.clearFlashMessage()">×</button>
    </div>

    <main class="content">
      <RouterView />
    </main>

    <!-- Floating Chatbot Widget -->
    <FloatingChatWidget />
  </div>
</template>

<style scoped>
/* --- Layout and Font Setup --- */
#app-layout {
  min-height: 100vh;
  font-family: -apple-system, BlinkMacFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #f8f9fa; /* Light background for the overall app */
}

/* --- Navbar Styling (Main Header) --- */
.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  /* NOTE: Added position: fixed/sticky to address layout flow issue,
     but keeping original for minimal change unless user confirms fix */
  background-color: #ffffff; 
  padding: 0.75rem 2rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  height: 60px; 
}

/* --- Brand/Logo Styling --- */
.brand {
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  font-weight: 700;
  text-decoration: none;
  color: #1a1a2e; 
}

/* --- Nav Links / Actions --- */
.nav-links {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.nav-btn {
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, color 0.2s;
  border: 1px solid transparent; 
}

/* --- Unauthenticated Button Styles (Sign In / Get Started) --- */

.nav-btn:not(.subtle) {
  color: #1a1a2e;
  background: transparent;
}

.nav-btn:not(.subtle):hover {
  color: #3f51b5;
}

/* Get Started Button (Dark style) */
.nav-links > .nav-btn:last-child {
  background-color: #1a1a2e; 
  color: #ffffff;
}

.nav-links > .nav-btn:last-child:hover {
  background-color: #33334d;
}

/* --- Authenticated User Info and Buttons --- */

.user-text {
  font-size: 0.95rem;
  color: #1a1a2e;
  margin-right: 0.5rem;
  font-weight: 500;
}

.nav-btn.subtle {
  /* Dashboard Link */
  color: #3f51b5;
  background: none;
  padding: 0.5rem 0.75rem; 
  font-weight: 500;
}

.nav-btn.subtle:hover {
  text-decoration: underline;
}

.nav-btn.club-link {
  /* Invest Together Link */
  color: white;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0.5rem 1rem;
  font-weight: 600;
  border-radius: 6px;
  transition: transform 0.2s, box-shadow 0.2s;
}

.nav-btn.club-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  text-decoration: none;
}

/* Logout button (Dark style) */
.logout-btn {
  background-color: #1a1a2e; 
  color: #ffffff;
  border: none;
  padding: 0.5rem 1rem; 
}

.logout-btn:hover {
  background-color: #33334d;
}

/* --- Flash Message Styling (Elegant and Subtle) --- */
.flash {
  position: sticky;
  top: 60px; /* Position it right below the 60px height navbar */
  left: 0;
  width: 100%;
  padding: 0.75rem 1.5rem; /* Reduced padding */
  text-align: center;
  /* Subtle Green/Info Color Scheme */
  background-color: #e6f7e6; /* Very light, soft green */
  color: #2e7d32; /* Darker green text */
  border-bottom: 1px solid #c8e6c9; /* Subtle separator line */
  z-index: 999; 
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 500; /* Less bold */
  font-size: 0.9rem; /* Smaller font size */
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05); /* Softer shadow for elevation */
}

.flash .close {
  background: none;
  border: none;
  color: #2e7d32; /* Match text color */
  font-size: 1.2rem; /* Smaller close button */
  line-height: 1;
  cursor: pointer;
  margin-left: 1rem;
  padding: 0 0.5rem;
  opacity: 0.8;
  transition: opacity 0.2s;
}

.flash .close:hover {
  opacity: 1;
}

/* --- Main Content Area --- */
.content {
  /* Keep original padding */
  padding: 1rem;
}
</style>