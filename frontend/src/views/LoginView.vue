<script setup>
import { ref } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import { useMessageStore } from '@/stores/message_store';
import { useAuthStore } from '@/stores/auth_store';

const router = useRouter();
// Changed back to 'username' as requested
const username = ref(''); 
const password = ref('');
const isLoading = ref(false);

const messageStore = useMessageStore();
const authStore = useAuthStore();
const backend_url = authStore.getBackendServerURL();

async function login() {
  isLoading.value = true;
  messageStore.setFlashMessage('');

  try {
    const response = await fetch(`${backend_url}/api/v1/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        // Updated to send 'username'
        username: username.value, 
        password: password.value,
      }),
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'Login failed');

    if (data.token && data.user) {
      authStore.setToken(data.token);
      authStore.setUserData(data.user);
      messageStore.setFlashMessage('Login successful!');
      router.push('/Dashboard');
    } else {
      messageStore.setFlashMessage('Unexpected server response.');
    }
  } catch (err) {
    messageStore.setFlashMessage(err.message || 'Login failed.');
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="login-wrapper">
    <div class="login-card">
      <h2 class="card-title">Welcome Back</h2>
      <p class="card-subtitle">Continue your market insights journey</p>

      <form @submit.prevent="login">
        <div class="form-group">
          <label for="username">Username</label>
          <input
            id="username"
            v-model="username"
            type="text"
            placeholder="Enter your username"
            required
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <div class="label-row">
            <label for="password">Password</label>
            <RouterLink to="/forgot-password" class="forgot-link">Forgot password?</RouterLink>
          </div>
          <input
            id="password"
            v-model="password"
            type="password"
            placeholder="Enter your password"
            required
            autocomplete="current-password"
          />
        </div>

        <button type="submit" class="btn primary-btn" :disabled="isLoading">
          <span v-if="isLoading">Signing In...</span>
          <span v-else>Sign In</span>
        </button>

        <p class="signup-text">
          Don't have an account?
          <RouterLink to="/signup" class="create-link">Create account</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* --- General Container and Centering --- */
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f8f9fa; /* Light background for the overall page */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* --- Login Card Styling (Matches the image) --- */
.login-card {
  background: #ffffff;
  padding: 3rem 2.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.08); /* Subtle shadow for elevated look */
  width: 100%;
  max-width: 400px; /* Fixed width for the card */
  text-align: center;
}

.card-title {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 0.5rem;
}

.card-subtitle {
  font-size: 1rem;
  color: #6a6a85;
  margin-bottom: 2rem;
}

/* --- Form Group Styling --- */
form {
    width: 100%;
}

.form-group {
  text-align: left;
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1a1a2e;
  margin-bottom: 0.25rem;
}

.label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
}

input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background-color: #f7f7f9; /* Light gray background for input field */
  font-size: 1rem;
  color: #1a1a2e;
  transition: border-color 0.2s, box-shadow 0.2s;
  box-sizing: border-box; /* Ensures padding is inside the width */
}

input:focus {
  border-color: #3f51b5;
  outline: none;
  box-shadow: 0 0 0 3px rgba(63, 81, 181, 0.1);
}

/* --- Links and Buttons --- */
.forgot-link {
  font-size: 0.8rem;
  color: #3f51b5; /* Primary accent color */
  text-decoration: none;
  font-weight: 500;
}

.forgot-link:hover, .create-link:hover {
  text-decoration: underline;
}

.btn.primary-btn {
  width: 100%;
  padding: 0.8rem 1.5rem;
  margin-top: 1.5rem;
  background-color: #1a1a2e; /* Dark button color from the image */
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s, opacity 0.2s;
}

.btn.primary-btn:hover:not(:disabled) {
  background-color: #33334d;
}

.btn.primary-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* --- Signup Text --- */
.signup-text {
  margin-top: 1.5rem;
  font-size: 0.9rem;
  color: #6a6a85;
}

.create-link {
  color: #1a1a2e; /* Darker link color for emphasis */
  text-decoration: none;
  font-weight: 600;
}
</style>