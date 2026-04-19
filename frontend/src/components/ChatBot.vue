<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import { MessageSquare, X, Send, Trash2, Bot, User, Minus, Maximize2, Minimize2 } from 'lucide-vue-next'
import { marked } from 'marked'
import ChatCard from './ChatCard.vue'

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

const emit = defineEmits(['navigate'])

const isOpen = ref(false)
const isFullScreen = ref(false)
const message = ref('')
const history = ref([])
const isTyping = ref(false)
const scrollRef = ref(null)

// Resizable state
const chatWidth = ref(380)
const chatHeight = ref(520)
const isResizing = ref(false)

function startResize(e, direction) {
  if (isFullScreen.value) return
  isResizing.value = true
  const startX = e.clientX
  const startY = e.clientY
  const startWidth = chatWidth.value
  const startHeight = chatHeight.value

  function onMouseMove(moveEvent) {
    if (direction.includes('left')) {
      chatWidth.value = Math.max(300, startWidth + (startX - moveEvent.clientX))
    }
    if (direction.includes('top')) {
      chatHeight.value = Math.max(400, startHeight + (startY - moveEvent.clientY))
    }
  }

  function onMouseUp() {
    isResizing.value = false
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

// Role-based API base
const apiBase = computed(() => `/api/${props.user.role}/chat`)

// Refined context for backend
const filteredContext = computed(() => {
  const ctx = { ...props.context }
  return Object.fromEntries(
    Object.entries(ctx).filter(([_, v]) => v != null && v !== '')
  )
})

// Context for UI display
const displayContext = computed(() => {
  const ctx = { ...filteredContext.value }
  delete ctx.role
  if (ctx.status === 'ready') delete ctx.status
  return Object.fromEntries(
    Object.entries(ctx).filter(([k, _]) => !k.endsWith('_id'))
  )
})

/**
 * Parses message content for [[TYPE:ID]] markers.
 */
function parseSegments(content) {
  if (!content) return []
  const segments = []
  const regex = /\[\[(JOB|CANDIDATE):([\w-]+)\]\]/g
  let lastIndex = 0
  let match

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      const text = content.substring(lastIndex, match.index)
      if (text.trim()) {
        segments.push({ type: 'text', content: text.trim() })
      }
    }
    segments.push({ type: 'card', cardType: match[1], id: match[2] })
    lastIndex = regex.lastIndex
  }

  if (lastIndex < content.length) {
    const remaining = content.substring(lastIndex)
    if (remaining.trim()) {
      segments.push({ type: 'text', content: remaining.trim() })
    }
  }

  return segments.length > 0 ? segments : [{ type: 'text', content }]
}

async function loadHistory() {
  try {
    const token = localStorage.getItem('token')
    const res = await fetch(`${apiBase.value}/history`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      if (data && data.length > 0) {
        history.value = data
      } else {
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
    const res = await fetch(`${apiBase.value}/clear`, {
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
    const res = await fetch(`${apiBase.value}/message`, {
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

function toggleFullScreen() {
  isFullScreen.value = !isFullScreen.value
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function onCardNavigate(payload) {
  emit('navigate', payload)
}

onMounted(() => {
  loadHistory()
})
</script>

<template>
  <div class="chatbot-wrapper" :class="{ 'is-open': isOpen, 'full-screen-mode': isFullScreen }">
    <button class="chat-toggle glass-card" @click="toggleChat" v-if="!isOpen">
      <MessageSquare :size="24" />
    </button>

    <div 
      :class="['chat-window', 'glass-card', { 'full-screen': isFullScreen, 'is-resizing': isResizing }]" 
      v-if="isOpen"
      :style="!isFullScreen ? { width: chatWidth + 'px', height: chatHeight + 'px' } : {}"
    >
      <!-- Resize Handles -->
      <div v-if="!isFullScreen" class="resize-handle top" @mousedown.prevent="startResize($event, 'top')"></div>
      <div v-if="!isFullScreen" class="resize-handle left" @mousedown.prevent="startResize($event, 'left')"></div>
      <div v-if="!isFullScreen" class="resize-handle top-left" @mousedown.prevent="startResize($event, 'top-left')"></div>

      <header class="chat-header">
        <div class="header-info">
          <Bot :size="18" class="bot-icon" />
          <h3>AI Assistant</h3>
        </div>
        <div class="header-actions">
          <button class="mini-icon" title="Clear History" @click="clearChat"><Trash2 :size="16" /></button>
          <button class="mini-icon" :title="isFullScreen ? 'Exit Fullscreen' : 'Fullscreen'" @click="toggleFullScreen">
            <Minimize2 v-if="isFullScreen" :size="16" />
            <Maximize2 v-else :size="16" />
          </button>
          <button class="mini-icon" title="Close" @click="isOpen = false"><X :size="16" /></button>
        </div>
      </header>

      <div class="chat-messages" ref="scrollRef">
        <div v-for="(msg, idx) in history" :key="idx" :class="['message-group', msg.role]">
          <div class="sender-header">
            <Bot v-if="msg.role === 'assistant'" :size="14" class="header-icon" />
            <span class="sender-label">{{ msg.role === 'user' ? 'You' : 'AI Assistant' }}</span>
            <User v-if="msg.role === 'user'" :size="14" class="header-icon" />
          </div>
          <div :class="['message-bubble', msg.role]">
            <div v-if="msg.role === 'user'" class="message-content user-msg">{{ msg.content }}</div>
            <div v-else class="message-content multi-segment">
              <template v-for="(seg, sIdx) in parseSegments(msg.content)" :key="sIdx">
                <div v-if="seg.type === 'text'" class="markdown-body chat-md" v-html="renderMarkdown(seg.content)"></div>
                <ChatCard 
                  v-else-if="seg.type === 'card'" 
                  :type="seg.cardType" 
                  :id="seg.id" 
                  :user="user"
                  @navigate="onCardNavigate" 
                />
              </template>
            </div>
          </div>
        </div>
        <div v-if="isTyping" class="message-group assistant">
          <div class="sender-header">
            <Bot :size="14" class="header-icon" />
            <span class="sender-label">AI Assistant</span>
          </div>
          <div class="message-bubble assistant">
            <div class="message-content typing">...</div>
          </div>
        </div>
      </div>

      <div class="chat-context-footer" v-if="Object.keys(displayContext).length">
        <div class="context-label">Current Context:</div>
        <div class="context-chips">
          <span v-for="(val, key) in displayContext" :key="key" class="chip">
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
.chatbot-wrapper { position: fixed; bottom: 2rem; right: 2rem; z-index: 1000; }

.chat-toggle {
  width: 56px; height: 56px; border-radius: 50%; background: var(--accent);
  color: white; display: flex; align-items: center; justify-content: center;
  cursor: pointer; box-shadow: 0 4px 20px rgba(0,0,0,0.3); border: none; transition: all 0.2s ease;
}
.chat-toggle:hover { transform: translateY(-2px); background: #2563eb; }

.chat-window {
  width: 380px; height: 520px; display: flex; flex-direction: column;
  overflow: visible; background: #1e293b; border: 1px solid var(--border); box-shadow: 0 12px 40px rgba(0,0,0,0.5);
  transition: width 0.3s ease, height 0.3s ease, transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.chat-window.is-resizing {
  transition: none !important;
  user-select: none;
}

.chat-window.full-screen {
  position: fixed; top: 1rem; left: 1rem; right: 1rem; bottom: 1rem;
  width: calc(100vw - 2rem) !important; height: calc(100vh - 2rem) !important; z-index: 1001;
}

/* Resize Handles */
.resize-handle {
  position: absolute;
  z-index: 10;
}
.resize-handle.top {
  top: -4px; left: 0; right: 0; height: 8px; cursor: ns-resize;
}
.resize-handle.left {
  left: -4px; top: 0; bottom: 0; width: 8px; cursor: ew-resize;
}
.resize-handle.top-left {
  top: -4px; left: -4px; width: 12px; height: 12px; cursor: nwse-resize;
}

.chat-header {
  padding: 0.6rem 1rem; background: #0f172a; border-bottom: 1px solid var(--border);
  display: flex; justify-content: space-between; align-items: center;
}
.header-info { display: flex; align-items: center; gap: 0.6rem; }
.bot-icon { color: var(--accent); }
.header-actions { display: flex; gap: 0.4rem; }
.mini-icon {
  background: transparent; padding: 4px; border-radius: 4px;
  color: var(--muted); cursor: pointer; border: none;
}
.mini-icon:hover { background: rgba(255,255,255,0.05); color: white; }

.chat-messages {
  flex-grow: 1; overflow-y: auto; padding: 1rem; display: flex; flex-direction: column; gap: 1.25rem;
}

.message-group { display: flex; flex-direction: column; gap: 0.25rem; max-width: 85%; }
.full-screen .message-group { max-width: 70%; }
.message-group.user { align-self: flex-end; align-items: flex-end; }
.message-group.assistant { align-self: flex-start; align-items: flex-start; }

.sender-header { display: flex; align-items: center; gap: 0.4rem; }
.sender-label { font-size: 0.65rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }
.user .sender-label { color: var(--accent); }
.header-icon { opacity: 0.7; }
.assistant .header-icon { color: var(--muted); }
.user .header-icon { color: var(--accent); }

.message-bubble { 
  padding: 0.6rem 0.9rem; 
  border-radius: 4px; 
  font-size: 0.9rem; 
  line-height: 1.5;
  max-width: 100%;
  overflow-x: auto;
  scrollbar-width: thin;
}
.message-bubble.user { background: var(--accent); color: white; border-radius: 8px 0 8px 8px; }
.message-bubble.assistant { background: #0f172a; border: 1px solid var(--border); border-radius: 0 8px 8px 8px; }

.user-msg { white-space: pre-wrap; word-break: break-word; }
.message-content { width: 100%; }

/* Eliminate large markdown gaps */
.chat-md :deep(p) { margin: 0 0 0.4rem 0; }
.chat-md :deep(p:last-child) { margin-bottom: 0; }
.chat-md :deep(ul), .chat-md :deep(ol) { padding-left: 1.1rem; margin: 0 0 0.4rem 0; }
.chat-md :deep(li) { margin-bottom: 0.2rem; }
.chat-md :deep(strong) { color: #fff; }
.chat-md :deep(pre) { 
  background: #1e293b; 
  padding: 0.5rem; 
  border-radius: 4px; 
  overflow-x: auto; 
  margin: 0.5rem 0;
  border: 1px solid var(--border);
}
.chat-md :deep(code) {
  font-family: monospace;
  background: rgba(255,255,255,0.1);
  padding: 0.1rem 0.3rem;
  border-radius: 3px;
}
.chat-md :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 0.5rem 0;
}
.chat-md :deep(th), .chat-md :deep(td) {
  border: 1px solid var(--border);
  padding: 0.4rem;
  text-align: left;
}

.multi-segment { display: flex; flex-direction: column; gap: 0.5rem; }

.chat-context-footer { padding: 0.4rem 1rem; background: #0f172a; border-top: 1px solid var(--border); font-size: 0.7rem; }
.context-label { font-weight: 700; color: var(--muted); text-transform: uppercase; font-size: 0.6rem; margin-bottom: 0.15rem; }
.context-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.chip { background: var(--bg-subtle); border: 1px solid var(--border); padding: 1px 4px; border-radius: 2px; color: var(--text); font-weight: 600; }

.chat-input { padding: 0.75rem 1rem; background: #0f172a; border-top: 1px solid var(--border); display: flex; gap: 0.5rem; }
.chat-input input { flex-grow: 1; background: var(--bg); border: 1px solid var(--border); padding: 0.5rem 0.75rem; border-radius: 4px; color: white; font-size: 0.9rem; }
.chat-input button { width: 36px; height: 36px; padding: 0; flex-shrink: 0; }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
