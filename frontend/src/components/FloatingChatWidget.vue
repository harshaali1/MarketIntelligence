<template>
  <div class="floating-chat-widget">
    <!-- Floating Button -->
    <div
      v-if="!isOpen"
      class="chat-bubble"
      @click="openChat"
      :title="'Stock AI Advisor'"
    >
      <svg
        class="chat-icon"
        fill="currentColor"
        viewBox="0 0 24 24"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H8l-2 2v-2H4V4h16v12z"></path>
      </svg>
      <span class="unread-badge" v-if="unreadCount > 0">{{ unreadCount }}</span>
    </div>

    <!-- Chat Window -->
    <transition name="slide-up">
      <div v-if="isOpen" class="chat-window">
        <!-- Header -->
        <div class="chat-header">
          <div class="header-content">
            <h3>Stock AI Advisor</h3>
            <p class="status">Powered by Gemini AI</p>
          </div>
          <button @click="closeChat" class="close-btn" aria-label="Close chat">
            <svg fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12 19 6.41z"></path>
            </svg>
          </button>
        </div>

        <!-- Messages -->
        <div class="chat-messages" ref="messagesContainer">
          <!-- Welcome Message -->
          <div v-if="messages.length === 0" class="welcome-section">
            <div class="welcome-icon"></div>
            <h4>Welcome to Stock AI Advisor</h4>
            <p>Ask me anything about stocks, investing, or financial advice!</p>
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
            <div class="message-bubble" v-html="formatMessage(msg.text)"></div>
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

        <!-- Input Area -->
        <div class="chat-input-area">
          <div class="input-wrapper">
            <input
              v-model="inputMessage"
              type="text"
              placeholder="Ask about stocks..."
              class="message-input"
              @keyup.enter="sendMessage"
              :disabled="loading || !isAuthenticated"
            />
            <button
              @click="sendMessage"
              class="send-btn"
              :disabled="!inputMessage.trim() || loading || !isAuthenticated"
              aria-label="Send message"
              :title="!isAuthenticated ? 'Please login first' : ''"
            >
              <svg fill="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M16.6915026,12.4744748 L3.50612381,13.2599618 C3.19218622,13.2599618 3.03521743,13.4170592 3.03521743,13.5741566 L1.15159189,20.0151496 C0.8376543,20.8006365 0.99,21.89 1.77946707,22.52 C2.41,22.99 3.50612381,23.1 4.13399899,22.9429026 L21.714504,14.0454487 C22.6563168,13.5741566 23.1272231,12.6315722 22.9702544,11.6889879 L4.13399899,1.16346272 C3.34915502,0.9 2.40734225,1.00636533 1.77946707,1.4776575 C0.994623095,2.10604706 0.837654326,3.0486314 1.15159189,3.99721575 L3.03521743,10.4382088 C3.03521743,10.5953061 3.34915502,10.7524035 3.50612381,10.7524035 L16.6915026,11.5378905 C16.6915026,11.5378905 17.1624089,11.5378905 17.1624089,12.0091827 C17.1624089,12.4744748 16.6915026,12.4744748 16.6915026,12.4744748 Z"></path>
              </svg>
            </button>
          </div>
          <p v-if="error" class="error-text">{{ error }}</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, nextTick, computed } from 'vue'
import { useAuthStore } from '@/stores/auth_store'

const authStore = useAuthStore()

const isOpen = ref(false)
const inputMessage = ref('')
const messages = ref([])
const loading = ref(false)
const error = ref('')
const messagesContainer = ref(null)
const unreadCount = ref(0)

const backendUrl = 'http://127.0.0.1:5001'

const isAuthenticated = computed(() => authStore.isAuthenticated)
const userId = computed(() => authStore.getUserId())

const quickSuggestions = [
  'What makes a good investment?',
  'How do I start investing?',
  'What is diversification?',
  'Tell me about dividend stocks'
]

const openChat = () => {
  isOpen.value = true
  unreadCount.value = 0
  nextTick(() => {
    scrollToBottom()
  })
}

const closeChat = () => {
  isOpen.value = false
}

const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const formatMessage = (text) => {
  if (!text) return ''
  
  // Ensure text is a string
  const textStr = String(text)
  
  // Convert markdown formatting to HTML
  let formatted = textStr
    // Bold: **text** or __text__ -> <strong>text</strong>
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/__(.+?)__/g, '<strong>$1</strong>')
    // Italic: *text* or _text_ -> <em>text</em>
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(/_(.+?)_/g, '<em>$1</em>')
    // Line breaks
    .replace(/\n/g, '<br>')
  
  return formatted
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
    const requestBody = {
      user_id: userId.value,
      message: messageText
    }
    
    console.log('[FloatingChat] Sending message:', messageText)
    console.log('[FloatingChat] User ID:', userId.value)
    console.log('[FloatingChat] Token:', token ? 'Present' : 'Missing')
    console.log('[FloatingChat] Request Body:', JSON.stringify(requestBody))
    
    const response = await fetch(`${backendUrl}/api/v1/ai/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': `Bearer ${token || ''}`,
      },
      body: JSON.stringify(requestBody)
    })

    console.log('[FloatingChat] Response status:', response.status)
    
    if (!response.ok) {
      let errorData = {}
      try {
        errorData = await response.json()
      } catch (e) {
        console.log('[FloatingChat] Could not parse error response as JSON')
      }
      
      const errorMsg = errorData.message || errorData.error || `HTTP error! status: ${response.status}`
      console.error('[FloatingChat] Error response:', errorData)
      throw new Error(errorMsg)
    }

    const data = await response.json()
    console.log('[FloatingChat] Response data:', data)

    // Add AI response - use ai_response field
    const aiMessage = data.ai_response || data.response || 'No response received'
    messages.value.push({
      role: 'assistant',
      text: aiMessage
    })

    // If chat is closed, show unread badge
    if (!isOpen.value) {
      unreadCount.value++
    }
  } catch (err) {
    console.error('[FloatingChat] Error:', err)
    error.value = `Failed to get response: ${err.message}`
    // Remove the user message if request failed
    messages.value.pop()
  } finally {
    loading.value = false
    await nextTick()
    scrollToBottom()
  }
}
</script>

<style scoped>
.floating-chat-widget {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 9999;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Floating Bubble Button */
.chat-bubble {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1f1f1f, #2c2c2c);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  animation: float 3s ease-in-out infinite;
}

.chat-bubble:hover {
  transform: scale(1.1) translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.7);
}

.chat-bubble:active {
  transform: scale(0.95);
}

@keyframes float {
  0%, 100% { transform: translateY(0px); }
  50% { transform: translateY(-10px); }
}

.chat-icon {
  width: 28px;
  height: 28px;
  color: #f5f5f5;
}

/* Unread Badge */
.unread-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  background: #ef4444;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  border: 2px solid #1f1f1f;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

/* Chat Window */
.chat-window {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 380px;
  height: 600px;
  background: #1a1a1a;
  border-radius: 16px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(20px) scale(0.95); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}

/* Slide Up Transition */
.slide-up-enter-active,
.slide-up-leave-active { transition: all 0.3s ease; }
.slide-up-enter-from,
.slide-up-leave-to { opacity: 0; transform: translateY(20px) scale(0.95); }

/* Header */
.chat-header {
  background: #2c2c2c;
  padding: 18px 20px;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #3a3a3a;
}

.header-content h3 {
  margin: 0 0 4px 0;
  font-size: 18px;
  font-weight: 600;
  color: #f5f5f5;
}

.status {
  margin: 0;
  font-size: 12px;
  color: #b0b0b0;
  font-weight: 400;
}

.close-btn {
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #f5f5f5;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.close-btn:hover { background: rgba(255,255,255,0.2); transform: rotate(90deg); }
.close-btn svg { width: 18px; height: 18px; }

/* Messages Area */
.chat-messages {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: #1a1a1a;
}

.chat-messages::-webkit-scrollbar { width: 5px; }
.chat-messages::-webkit-scrollbar-track { background: transparent; }
.chat-messages::-webkit-scrollbar-thumb {
  background: #3a3a3c;
  border-radius: 3px;
}
.chat-messages::-webkit-scrollbar-thumb:hover { background: #555; }

/* Welcome Section */
.welcome-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 20px 10px;
  height: 100%;
}

.welcome-icon {
  width: 60px;
  height: 60px;
  background: #2c2c2c;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  position: relative;
}

.welcome-icon::before {
  content: '💬';
  font-size: 28px;
}

.welcome-section h4 { color: #f5f5f5; margin: 0 0 6px 0; font-size: 18px; font-weight: 600; }
.welcome-section > p { color: #b0b0b0; margin: 0 0 20px 0; font-size: 13px; line-height: 1.4; }

/* Quick Suggestions */
.quick-suggestions {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

.suggestion-btn {
  background: #2a2a2a;
  border: 1px solid #3a3a3a;
  border-radius: 16px;
  padding: 10px 16px;
  font-size: 12px;
  color: #e0e0e0;
  cursor: pointer;
  font-weight: 500;
  text-align: left;
  transition: all 0.2s ease;
}

.suggestion-btn:hover:not(:disabled) {
  background: #3a3a3a;
  border-color: #777;
  color: #fff;
  transform: translateX(4px);
}

.suggestion-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Message Bubbles */
.message { display: flex; animation: messageSlide 0.3s ease; }
.message.user { justify-content: flex-end; }
.message.assistant { justify-content: flex-start; }

.message-bubble {
  max-width: 75%;
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 13px;
  line-height: 1.5;
  word-wrap: break-word;
}

.message.user .message-bubble {
  background: linear-gradient(135deg, #2a2a2a, #3b3b3b);
  color: #f5f5f5;
  border-bottom-right-radius: 4px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.5);
}

.message.assistant .message-bubble {
  background: #1f1f1f;
  color: #e0e0e0;
  border: 1px solid #3a3a3a;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.message-bubble :deep(strong) { font-weight: 600; }
.message-bubble :deep(em) { font-style: italic; }
.message-bubble :deep(br) { display: block; content: ''; margin: 4px 0; }

/* Typing Indicator */
.message-bubble.typing { display: flex; gap: 5px; padding: 14px 16px; align-items: center; }
.message-bubble.typing span {
  width: 7px; height: 7px; background: #b0b0b0; border-radius: 50%; animation: typing 1.4s infinite;
}
.message-bubble.typing span:nth-child(2) { animation-delay: 0.2s; }
.message-bubble.typing span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%,60%,100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-8px); opacity: 1; }
}

/* Input Area */
.chat-input-area {
  padding: 14px 16px;
  background: #1a1a1a;
  border-top: 1px solid #3a3a3a;
}

.input-wrapper {
  display: flex;
  gap: 8px;
  align-items: center;
  background: #2a2a2a;
  border-radius: 20px;
  padding: 4px 4px 4px 14px;
  border: 1px solid #3a3a3a;
  transition: all 0.2s ease;
}

.input-wrapper:focus-within {
  border-color: #777;
  box-shadow: 0 0 0 2px rgba(119,119,119,0.2);
}

.message-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  font-size: 13px;
  color: #f5f5f5;
  font-family: inherit;
  padding: 6px 0;
}

.message-input::placeholder { color: #808080; }
.message-input:disabled { opacity: 0.5; cursor: not-allowed; }

.send-btn {
  width: 36px; height: 36px; border-radius: 50%;
  background: #2c2c2c; border: none; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s ease; flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  transform: scale(1.05); box-shadow: 0 3px 10px rgba(0,0,0,0.5);
}

.send-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: scale(1); }
.send-btn svg { width: 18px; height: 18px; color: #f5f5f5; }

/* Error Text */
.error-text { margin: 8px 0 0 0; font-size: 11px; color: #ef4444; font-weight: 500; }

/* Message Slide Animation */
@keyframes messageSlide { from { opacity: 0; transform: translateY(8px); } to { opacity:1; transform: translateY(0); } }

/* Responsive Design */
@media (max-width: 480px) {
  .floating-chat-widget { bottom: 16px; right: 16px; }
  .chat-window { bottom:16px; right:16px; left:16px; width:auto; height:calc(100vh - 100px); max-height:600px; }
  .chat-bubble { width: 56px; height: 56px; }
  .chat-icon { width: 26px; height: 26px; }
}

/* Focus Styles */
.send-btn:focus,
.message-input:focus,
.suggestion-btn:focus,
.close-btn:focus,
.chat-bubble:focus {
  outline: 2px solid #777;
  outline-offset: 2px;
}

/* Accessibility */
@media (prefers-reduced-motion: reduce) {
  .chat-bubble,
  .unread-badge,
  .message,
  .chat-window { animation: none; }
  .close-btn:hover, .send-btn:hover:not(:disabled) { transform: none; }
}

/* Bounce effect on new messages when closed */
@keyframes bounce {
  0%,20%,50%,80%,100% { transform: translateY(0); }
  40% { transform: translateY(-20px); }
  60% { transform: translateY(-10px); }
}

.chat-bubble.has-new-message { animation: bounce 1s ease; }
</style>
