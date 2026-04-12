<template>
  <div class="chatbot-container">
    <!-- Chat Window -->
    <div class="chat-window">
      <!-- Header -->
      <div class="chat-header">
        <div class="header-content">
          <h3>Stock AI Advisor</h3>
          <p class="status">Powered by Gemini AI</p>
        </div>
      </div>

      <!-- Messages -->
      <div class="chat-messages" ref="messagesContainer">
        <!-- Welcome Message -->
        <div v-if="messages.length === 0" class="welcome-section">
          <div class="welcome-icon"></div>
          <h4>Welcome to Stock AI Advisor</h4>
          <p>Ask me anything about stocks, investing, or your portfolio!</p>
          <div class="quick-suggestions">
            <button
              v-for="(suggestion, idx) in quickSuggestions"
              :key="idx"
              @click="sendMessage(suggestion)"
              class="suggestion-btn"
              :disabled="loading"
            >
              {{ suggestion }}
            </button>
          </div>
        </div>

        <!-- Chat Messages -->
        <div
          v-for="(msg, idx) in messages"
          :key="idx"
          :class="['message', msg.role]"
        >
          <div class="message-bubble">
            {{ msg.text }}
          </div>
        </div>

        <!-- Typing Indicator -->
        <div v-if="loading" class="message assistant">
          <div class="message-bubble typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="error-banner">
        <p>⚠️ {{ error }}</p>
        <button @click="error = ''" class="close-error">✕</button>
      </div>

      <!-- Input Area -->
      <div class="chat-input-area">
        <div class="input-wrapper">
          <input
            v-model="inputMessage"
            type="text"
            placeholder="Ask about stocks, portfolio, or investing strategies..."
            class="message-input"
            @keyup.enter="sendMessage"
            :disabled="loading || !isAuthenticated"
          />
          <button
            @click="sendMessage"
            class="send-btn"
            :disabled="!inputMessage.trim() || loading || !isAuthenticated"
            :title="!isAuthenticated ? 'Please login first' : ''"
          >
            <svg fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M16.6915026,12.4744748 L3.50612381,13.2599618 C3.19218622,13.2599618 3.03521743,13.4170592 3.03521743,13.5741566 L1.15159189,20.0151496 C0.8376543,20.8006365 0.99,21.89 1.77946707,22.52 C2.41,22.99 3.50612381,23.1 4.13399899,22.9429026 L21.714504,14.0454487 C22.6563168,13.5741566 23.1272231,12.6315722 22.9702544,11.6889879 L4.13399899,1.16346272 C3.34915502,0.9 2.40734225,1.00636533 1.77946707,1.4776575 C0.994623095,2.10604706 0.837654326,3.0486314 1.15159189,3.99721575 L3.03521743,10.4382088 C3.03521743,10.5953061 3.34915502,10.7524035 3.50612381,10.7524035 L16.6915026,11.5378905 C16.6915026,11.5378905 17.1624089,11.5378905 17.1624089,12.0091827 C17.1624089,12.4744748 16.6915026,12.4744748 16.6915026,12.4744748 Z"></path>
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { useAuthStore } from '@/stores/auth_store'

const authStore = useAuthStore()

// --- State ---
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const error = ref('')
const messagesContainer = ref(null)

// --- Computed ---
const isAuthenticated = computed(() => authStore.isAuthenticated)
const userId = computed(() => authStore.logged_user?.id)
const backendUrl = 'http://127.0.0.1:5001'

const quickSuggestions = [
  'What makes a good investment?',
  'How do I start investing?',
  'Explain portfolio diversification',
  'What is a dividend stock?'
]

const scrollToBottom = () => {
  if (messagesContainer.value) {
    nextTick(() => {
      messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
    })
  }
}

const sendMessage = async (msg) => {
  const messageText = msg || inputMessage.value.trim()
  
  if (!messageText || !isAuthenticated.value) {
    error.value = 'Please login first'
    return
  }

  // Add user message
  messages.value.push({
    role: 'user',
    text: messageText
  })

  inputMessage.value = ''
  loading.value = true
  error.value = ''

  await nextTick()
  scrollToBottom()

  try {
    const token = authStore.getToken()
    
    console.log('[ChatbotView] Sending message:', messageText)
    console.log('[ChatbotView] User ID:', userId.value)
    console.log('[ChatbotView] Token:', token ? 'Present' : 'Missing')
    
    const response = await fetch(`${backendUrl}/api/v1/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authentication-Token': token || '',
        'X-Auth-Token': token || ''
      },
      body: JSON.stringify({
        user_id: userId.value,
        message: messageText
      })
    })

    console.log('[ChatbotView] Response status:', response.status)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const errorMsg = errorData.message || `HTTP error! status: ${response.status}`
      console.error('[ChatbotView] Error response:', errorData)
      throw new Error(errorMsg)
    }

    const data = await response.json()
    console.log('[ChatbotView] Response data:', data)

    // Add AI response
    const aiMessage = data.ai_response || data.response || 'No response received'
    messages.value.push({
      role: 'assistant',
      text: aiMessage
    })

  } catch (err) {
    console.error('[ChatbotView] Error:', err)
    error.value = `Failed to get response: ${err.message}`
    // Remove the user message if request failed
    messages.value.pop()
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}

// Auto-scroll when new messages arrive
watch(messages, () => {
  scrollToBottom()
}, { deep: true })
</script>

<script>
import { watch } from 'vue'

export default {
  name: 'ChatbotView'
}
</script>

<style>
/* Header */
.chat-header {
  background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
  padding: 20px 24px;
  color: white;
}

.header-content h3 {
  color: white;
}

.status {
  color: rgba(255, 255, 255, 0.8);
}

/* Welcome Icon */
.welcome-icon {
  background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
}

/* User Message Bubble */
.message.user .message-bubble {
  background: linear-gradient(135deg, #111111 0%, #1d1d1d 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
}

/* Suggestion Buttons */
.suggestion-btn {
  background: #1d1d1d;
  border: 1px solid #333333;
  color: #f5f5f7;
}

.suggestion-btn:hover:not(:disabled) {
  background: #000000;
  border-color: #f5f5f7;
  color: #f5f5f7;
}

/* Send Button */
.send-btn {
  background: linear-gradient(135deg, #000000 0%, #1a1a1a 100%);
}

.send-btn:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.7);
}

/* Dark Mode Support (Override) */
@media (prefers-color-scheme: dark) {
  .chatbot-container {
    background-color: #0a0a0a;
  }

  .chat-window {
    background: #1c1c1c;
  }

  .chat-messages {
    background: #121212;
  }

  .message.assistant .message-bubble {
    background: #1c1c1c;
    color: #f5f5f7;
    border-color: #2a2a2a;
  }

  .input-wrapper {
    background: #1c1c1c;
  }

  .input-wrapper:focus-within {
    background: #222222;
  }

  .chat-input-area {
    background: #1c1c1c;
    border-top-color: #2a2a2a;
  }

  .message-input {
    color: #f5f5f7;
  }

  .message-input::placeholder {
    color: #888888;
  }

  .suggestion-btn {
    background: #1c1c1c;
    border-color: #2a2a2a;
    color: #f5f5f7;
  }
}

</style>