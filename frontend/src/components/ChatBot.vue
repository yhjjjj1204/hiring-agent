<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { MessageSquare, X, Send, Trash2, Bot, User } from 'lucide-vue-next'

const props = defineProps({
  context: {
    type: Object,
    default: () => ({})
  },
  user: {
    type: Object,
    required: true
  }
})

const isOpen = ref(false)
const message = ref('')
const history = ref([])
const isTyping = ref(false)
const scrollRef = ref(null)

// Refined context for UI display and backend
const filteredContext = computed(() => {
  const ctx = { ...props.context }
  delete ctx.role
  if (ctx.status === 'ready') delete ctx.status
  
  // Filter out empty/null values
  return Object.fromEntries(
    Object.entries(ctx).filter(([_, v]) => v != null && v !== '')
  )
})

async function loadHistory() {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/chat/history', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      if (data && data.length > 0) {
        history.value = data
      } else {
        // Initial welcome message if history is empty
        history.value = [{
          role: 'assistant',
          content: `Hello ${props.user.username}! I'm your AI hiring assistant. I have access to the current page context to help you better. How can I assist you today?`,
          timestamp: new Date().toISOString()
        }]
      }
    }
  } catch (e) {
    console.error("Failed to load chat history", e)
  }
}

async function clearChat() {
  if (!confirm("Clear all chat history?")) return
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/chat/clear', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      history.value = [{ 
        role: 'assistant', 
        content: `History cleared. How can I help you now, ${props.user.username}?`,
        timestamp: new Date().toISOString()
      }]
    }
  } catch (e) {
    console.error("Failed to clear chat", e)
  }
}

async function sendMessage() {
  if (!message.value.trim() || isTyping.value) return

  const userMsg = { role: 'user', content: message.value, timestamp: new Date().toISOString() }
  history.value.push(userMsg)
  const currentMsg = message.value
  message.value = ''
  
  scrollToBottom()
  isTyping.value = true
  
  try {
    const token = localStorage.getItem('token')
    const res = await fetch('/chat/message', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        message: currentMsg,
        context: filteredContext.value
      })
    })
    
    if (res.ok) {
      const data = await res.json()
      history.value.push({ 
        role: 'assistant', 
        content: data.reply,
        timestamp: new Date().toISOString()
      })
    } else {
      history.value.push({ 
        role: 'assistant', 
        content: "Sorry, I'm having trouble connecting to the AI service right now.",
        timestamp: new Date().toISOString()
      })
    }
  } catch (e) {
    history.value.push({ 
      role: 'assistant', 
      content: "Error: " + e.message,
      timestamp: new Date().toISOString()
    })
  } finally {
    isTyping.value = false
    scrollToBottom()
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
}

function toggleChat() {
  isOpen.value = !isOpen.value
  if (isOpen.value) scrollToBottom()
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="chatbot-wrapper" :class="{ 'is-open': isOpen }">
    <!-- Floating Button -->
    <button class="chat-toggle glass-card" @click="toggleChat" v-if="!isOpen">
      <MessageSquare :size="24" />
    </button>

    <!-- Chat Window -->
    <div class="chat-window glass-card" v-if="isOpen">
      <header class="chat-header">
        <div class="header-info">
          <Bot :size="18" class="bot-icon" />
          <h3>AI Assistant</h3>
        </div>
        <div class="header-actions">
          <button class="mini-icon" title="Clear History" @click="clearChat"><Trash2 :size="16" /></button>
          <button class="mini-icon" title="Close" @click="isOpen = false"><X :size="16" /></button>
        </div>
      </header>

      <div class="chat-messages" ref="scrollRef">
        <div v-for="(msg, idx) in history" :key="idx" :class="['message-wrap', msg.role]">
          <div class="message-icon">
            <User v-if="msg.role === 'user'" :size="16" />
            <Bot v-else :size="16" />
          </div>
          <div class="message-content">{{ msg.content }}</div>
        </div>
        <div v-if="isTyping" class="message-wrap assistant">
          <div class="message-icon"><Bot :size="16" /></div>
          <div class="message-content typing">...</div>
        </div>
      </div>

      <!-- Clean Context Footer -->
      <div class="chat-context-footer" v-if="Object.keys(filteredContext).length">
        <div class="context-label">Current Context:</div>
        <div class="context-chips">
          <span v-for="(val, key) in filteredContext" :key="key" class="chip">
            {{ key }}: {{ val }}
          </span>
        </div>
      </div>

      <form class="chat-input" @submit.prevent="sendMessage">
        <input v-model="message" placeholder="Ask me anything..." @keydown.enter.prevent="sendMessage" />
        <button type="submit" :disabled="!message.trim() || isTyping">
          <Send :size="16" />
        </button>
      </form>
    </div>
  </div>
</template>

<style scoped>
.chatbot-wrapper {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: 1000;
}

.chat-toggle {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(0,0,0,0.3);
  border: none;
  transition: all 0.2s ease;
}
.chat-toggle:hover {
  transform: translateY(-2px);
  background: #2563eb;
}

.chat-window {
  width: 380px;
  height: 520px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #1e293b;
  border: 1px solid var(--border);
  box-shadow: 0 12px 40px rgba(0,0,0,0.5);
}

.chat-header {
  padding: 0.75rem 1rem;
  background: #0f172a;
  border-bottom: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header-info { display: flex; align-items: center; gap: 0.6rem; }
.bot-icon { color: var(--accent); }
.header-actions { display: flex; gap: 0.5rem; }
.mini-icon {
  background: transparent;
  padding: 4px;
  border-radius: 4px;
  color: var(--muted);
  cursor: pointer;
  border: none;
}
.mini-icon:hover { background: rgba(255,255,255,0.05); color: white; }

.chat-messages {
  flex-grow: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.message-wrap {
  display: flex;
  gap: 0.8rem;
  max-width: 90%;
}
.message-wrap.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}
.message-wrap.user .message-content {
  background: var(--accent);
  color: white;
  border-radius: 6px 6px 0 6px;
}
.message-wrap.assistant .message-content {
  background: #0f172a;
  border: 1px solid var(--border);
  border-radius: 6px 6px 6px 0;
}

.message-icon {
  width: 32px;
  height: 32px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
  color: var(--muted);
}
.user .message-icon { color: var(--accent); border-color: var(--accent); }

.message-content {
  padding: 0.6rem 1rem;
  font-size: 0.9rem;
  line-height: 1.5;
  white-space: pre-wrap;
}

.chat-context-footer {
  padding: 0.5rem 1rem;
  background: #0f172a;
  border-top: 1px solid var(--border);
  font-size: 0.7rem;
}
.context-label { font-weight: 700; color: var(--muted); text-transform: uppercase; font-size: 0.6rem; margin-bottom: 0.2rem; }
.context-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.chip { 
  background: var(--bg-subtle); 
  border: 1px solid var(--border); 
  padding: 1px 4px; 
  border-radius: 2px; 
  color: var(--text);
  font-weight: 600;
}

.chat-input {
  padding: 0.75rem 1rem;
  background: #0f172a;
  border-top: 1px solid var(--border);
  display: flex;
  gap: 0.5rem;
}
.chat-input input {
  flex-grow: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 0.45rem 0.75rem;
  border-radius: 4px;
  color: white;
  font-size: 0.9rem;
}
.chat-input button {
  width: 36px;
  height: 36px;
  padding: 0;
  flex-shrink: 0;
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
