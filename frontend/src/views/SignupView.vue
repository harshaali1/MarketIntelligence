<script setup>
import { ref } from 'vue';
import { useRouter, RouterLink } from 'vue-router';
import { useMessageStore } from '@/stores/message_store';
import { useAuthStore } from '@/stores/auth_store';
import axios from 'axios';

const router = useRouter();
// Changed back to 'username' as requested
const username = ref('');
const email = ref('');
const password = ref('');
const confirm_password = ref('');
const isLoading = ref(false);

const messageStore = useMessageStore();
const authStore = useAuthStore();
const backendURL = authStore.getBackendServerURL();

function validateInput() {
  // Updated validation to use username
  if (!username.value || !email.value || !password.value) {
    messageStore.setFlashMessage('All fields are required.');
    return false;
  }
  if (password.value !== confirm_password.value) {
    messageStore.setFlashMessage('Passwords do not match.');
    return false;
  }
  if (password.value.length < 8) {
    messageStore.setFlashMessage('Password must be at least 8 characters.');
    return false;
  }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  if (!emailRegex.test(email.value)) {
    messageStore.setFlashMessage('Enter a valid email address.');
    return false;
  }
  return true;
}

async function registerUser(userData) {
  isLoading.value = true;
  messageStore.setFlashMessage('');
  try {
    const res = await axios.post(`${backendURL}/api/v1/signup`, userData, {
      headers: { 'Content-Type': 'application/json' },
    });
    return { ok: true, msg: res.data.message || 'Signup successful.' };
  } catch (err) {
    const msg =
      err.response?.data?.message ||
      err.response?.data?.error ||
      'Signup failed.';
    return { ok: false, msg };
  } finally {
    isLoading.value = false;
  }
}

async function onSubmit() {
  if (!validateInput()) return;
  // Updated payload to include username
  const payload = { username: username.value, email: email.value, password: password.value }; 
  const result = await registerUser(payload);
  messageStore.setFlashMessage(result.msg);
  if (result.ok) router.push('/login');
}
</script>

<template>
  <div class="signup-wrapper">
    <div class="signup-card">
      <h2 class="card-title">Create Account</h2>
      <p class="card-subtitle">Start exploring market intelligence</p>

      <form @submit.prevent="onSubmit">
        <div class="form-group">
          <label for="username">Username</label>
          <input 
            id="username"
            v-model="username" 
            type="text" 
            placeholder="Choose a unique username" 
            required 
            autocomplete="username"
          />
        </div>

        <div class="form-group">
          <label for="email">Email Address</label>
          <input 
            id="email"
            v-model="email" 
            type="email" 
            placeholder="you@example.com" 
            required 
            autocomplete="email"
          />
        </div>

        <div class="form-group">
          <label for="password">Password</label>
          <input 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="Create a strong password" 
            required 
            autocomplete="new-password"
          />
        </div>

        <div class="form-group">
          <label for="confirm_password">Confirm Password</label>
          <input 
            id="confirm_password"
            v-model="confirm_password" 
            type="password" 
            placeholder="Confirm your password" 
            required 
            autocomplete="new-password"
          />
        </div>

        <button type="submit" class="btn primary-btn" :disabled="isLoading">
          <span v-if="isLoading">Creating Account...</span>
          <span v-else>Create Account</span>
        </button>

        <p class="login-text">
          Already have an account?
          <RouterLink to="/login" class="sign-in-link">Sign in</RouterLink>
        </p>
      </form>
    </div>
  </div>
</template>

<style scoped>
/* --- General Container and Centering --- */
.signup-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f8f9fa; /* Light background for the overall page */
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}

/* --- Signup Card Styling (Matches the image) --- */
.signup-card {
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

/* --- Button Styling --- */
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

/* --- Login Text --- */
.login-text {
  margin-top: 1.5rem;
  font-size: 0.9rem;
  color: #6a6a85;
}

.sign-in-link {
  color: #1a1a2e; /* Darker link color for emphasis */
  text-decoration: none;
  font-weight: 600;
}

.sign-in-link:hover {
    text-decoration: underline;
}
</style>