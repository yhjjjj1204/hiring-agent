<script setup>
import { ref } from 'vue'
import { 
  MessageSquare, 
  Bot, 
  User, 
  Send, 
  ArrowRight,
  MousePointer2,
  Lock,
  Zap,
  ExternalLink,
  Briefcase
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- ChatBot Demo Visualization -->
      <div class="chatbot-visual">
        <div class="visual-stack">
          <!-- The Chat Window Demo -->
          <div class="chat-window-demo glass-card">
            <header class="demo-chat-header">
              <Bot :size="16" class="icon-accent" />
              <span>AI Assistant</span>
            </header>
            
            <div class="demo-chat-messages">
              <!-- User Message -->
              <div class="demo-msg user">
                <div class="demo-msg-header"><User :size="12" /> You</div>
                <div class="demo-msg-bubble">
                  <div class="demo-context-tags">
                    <span class="demo-tag">job: AI Devops Engineer</span>
                  </div>
                  who are our candidates?
                </div>
              </div>

              <!-- Assistant Message -->
              <div class="demo-msg assistant">
                <div class="demo-msg-header"><Bot :size="12" /> AI Assistant</div>
                <div class="demo-msg-bubble">
                  <p>There is 1 candidate at present:</p>
                  
                  <!-- Entity Card -->
                  <div class="demo-entity-card">
                    <div class="card-icon"><User :size="14" /></div>
                    <div class="card-info">
                      <div class="card-top">
                        <strong>Alex Rivera</strong>
                        <ExternalLink :size="10" />
                      </div>
                      <p>Senior Infrastructure Lead with 8 years of cloud automation...</p>
                      <div class="card-footer">
                        <span class="score">94% Match</span>
                        <span class="id">#0824</span>
                      </div>
                    </div>
                  </div>

                  <p>The candidate shows exceptional depth in Kubernetes and multi-cloud orchestration.</p>
                </div>
              </div>
            </div>

            <div class="demo-chat-input">
              <div class="fake-input-text">Ask me anything...</div>
              <Send :size="14" class="icon-muted" />
            </div>
          </div>

          <!-- Feature Highlights -->
          <div class="chat-features-row">
            <div class="feat-box glass-card">
              <MousePointer2 :size="14" class="icon-accent" />
              <span>Selection as Context</span>
            </div>
            <div class="feat-box glass-card">
              <Lock :size="14" class="icon-ok" />
              <span>Identity Passthrough</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="chat-details">
          <div class="detail-block">
            <h3>Deep Context Awareness</h3>
            <p>The assistant is natively aware of your current page context. Whether you're looking at a specific job or a candidate, the bot captures IDs and names to provide precise, relevant answers.</p>
          </div>
          <div class="detail-block">
            <h3>Dynamic User Selection</h3>
            <p>Select any text on the page, and it is automatically injected into the chat context. This allows you to ask targeted questions about specific resume points or job requirements without typing.</p>
          </div>
          <div class="detail-block">
            <h3>Identity-Preserving Tools</h3>
            <p>The chatbot acts as your proxy. Every tool call passes your identity to the service layer, ensuring the bot can only perform actions (like creating jobs or re-evaluating) that your role allows.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-content-container {
  max-width: 1200px;
  width: 100%;
}

.slide-main {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 5rem;
  align-items: center;
}

/* ChatBot Visual */
.chatbot-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(5deg);
}

/* Chat Window Demo */
.chat-window-demo {
  background: var(--bg-subtle);
  border-color: var(--border);
  display: flex;
  flex-direction: column;
  height: 480px;
  overflow: hidden;
}

.demo-chat-header {
  padding: 0.6rem 1rem;
  background: var(--header-bg);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--headings);
}

.demo-chat-messages {
  flex: 1;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  overflow-y: auto;
}

.demo-msg { display: flex; flex-direction: column; gap: 0.25rem; max-width: 90%; }
.demo-msg.user { align-self: flex-end; align-items: flex-end; }
.demo-msg.assistant { align-self: flex-start; align-items: flex-start; }

.demo-msg-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
}

.demo-msg-bubble {
  padding: 0.6rem 0.8rem;
  border-radius: 4px;
  font-size: 0.85rem;
  line-height: 1.4;
}

.user .demo-msg-bubble { background: var(--accent); color: white; border-radius: 8px 0 8px 8px; }
.assistant .demo-msg-bubble { background: var(--header-bg); border: 1px solid var(--border); border-radius: 0 8px 8px 8px; color: var(--text); }

.demo-context-tags {
  display: flex;
  margin-bottom: 0.4rem;
}
.demo-tag {
  background: rgba(255, 255, 255, 0.15);
  padding: 2px 6px;
  border-radius: 2px;
  font-size: 0.65rem;
  font-weight: 600;
  color: white;
}

/* Entity Card in Demo */
.demo-entity-card {
  margin: 0.75rem 0;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  display: flex;
  gap: 0.75rem;
  padding: 0.75rem;
  width: 100%;
}

.card-icon {
  width: 32px; height: 32px; background: var(--bg-subtle);
  border: 1px solid var(--border); border-radius: 4px;
  display: flex; align-items: center; justify-content: center;
  color: var(--accent); flex-shrink: 0;
}

.card-info { flex: 1; min-width: 0; }
.card-top { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
.card-top strong { font-size: 0.8rem; color: #fff; }
.card-info p { font-size: 0.7rem; color: var(--muted); margin: 0; line-height: 1.3; }
.card-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 0.4rem; }
.card-footer .score { font-size: 0.65rem; font-weight: 800; color: var(--ok); }
.card-footer .id { font-size: 0.65rem; font-family: monospace; color: var(--border); }

.assistant .demo-msg-bubble p { margin: 0; }

.demo-chat-input {
  padding: 0.75rem 1rem;
  background: var(--header-bg);
  border-top: 1px solid var(--border);
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.fake-input-text { font-size: 0.8rem; color: var(--muted); }

/* Features Row */
.chat-features-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.feat-box {
  padding: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
}

/* Text Side */
.slide-text {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.slide-subtitle {
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.slide-title {
  font-size: 3.5rem;
  line-height: 1.1;
  margin: 0;
  color: var(--headings);
}

.chat-details {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.detail-block h3 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  color: var(--text);
  border-left: 3px solid var(--accent);
  padding-left: 1rem;
}

.detail-block p {
  font-size: 1.1rem;
  color: var(--muted);
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
