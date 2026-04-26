<script setup>
import { 
  FileEdit, 
  Users, 
  Search, 
  MessageCircle, 
  AlertTriangle,
  Clock,
  BatteryLow,
  FileSearch,
  ArrowRight
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Pain Points Visualization -->
      <div class="pain-points-visual">
        <div class="pain-grid">
          <!-- Item 1: Repetitive Forms -->
          <div class="pain-item glass-card">
            <div class="pain-header">
              <div class="pain-icon-box warn">
                <FileEdit :size="20" />
              </div>
              <h4>Repetitive Forms</h4>
            </div>
            <div class="pain-body">
              <div class="form-stack">
                <div class="mini-form">Education Background...</div>
                <div class="mini-form">Work Experience...</div>
                <div class="mini-form">Skills & Projects...</div>
              </div>
              <div class="repeat-indicator">
                <ArrowRight :size="12" /> Again & Again
              </div>
            </div>
          </div>

          <!-- Item 2: Manual Review -->
          <div class="pain-item glass-card">
            <div class="pain-header">
              <div class="pain-icon-box err">
                <FileSearch :size="20" />
              </div>
              <h4>Manual Review</h4>
            </div>
            <div class="pain-body">
              <div class="resume-pile">
                <div class="resume-sheet"></div>
                <div class="resume-sheet"></div>
                <div class="resume-sheet"></div>
                <div class="resume-sheet"></div>
              </div>
              <p class="pain-caption">Endless resume screening</p>
            </div>
          </div>

          <!-- Item 3: Job Hunt Fatigue -->
          <div class="pain-item glass-card">
            <div class="pain-header">
              <div class="pain-icon-box info">
                <BatteryLow :size="20" />
              </div>
              <h4>Search Fatigue</h4>
            </div>
            <div class="pain-body">
              <div class="search-exhaustion">
                <div class="long-list">
                  <div class="list-item">Job #1...</div>
                  <div class="list-item">Job #2...</div>
                  <div class="list-item">Job #3...</div>
                  <div class="list-item">Job #4...</div>
                </div>
                <div class="fatigue-overlay">
                  <Clock :size="16" /> Low Energy
                </div>
              </div>
            </div>
          </div>

          <!-- Item 4: Support Overhead -->
          <div class="pain-item glass-card">
            <div class="pain-header">
              <div class="pain-icon-box ok">
                <MessageCircle :size="20" />
              </div>
              <h4>Support Load</h4>
            </div>
            <div class="pain-body">
              <div class="chat-bubbles">
                <div class="bubble bubble-left">Is this remote?</div>
                <div class="bubble bubble-left">What's the tech stack?</div>
                <div class="bubble bubble-right">Spending hours replying...</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="central-warning">
          <AlertTriangle :size="32" />
          <span>Inefficient & Bias-Prone</span>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="problem-details">
          <div class="detail-block">
            <h3>Candidate Friction</h3>
            <p>Candidates are exhausted by repetitive data entry and long job lists that lack immediate clarity on their fit.</p>
          </div>
          <div class="detail-block">
            <h3>Recruiter Overload</h3>
            <p>Recruiters spend 80% of their time on manual screening and answering repetitive questions instead of strategic evaluation.</p>
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
  grid-template-columns: 1.2fr 0.8fr;
  gap: 5rem;
  align-items: center;
}

/* Pain Points Grid */
.pain-points-visual {
  position: relative;
  padding: 1rem;
}

.pain-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.pain-item {
  padding: 1.25rem;
  background: var(--bg-subtle);
  border-color: var(--border);
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: transform 0.3s ease;
}

.pain-item:hover {
  transform: translateY(-5px);
  border-color: var(--accent);
}

.pain-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.pain-header h4 {
  margin: 0;
  font-size: 1rem;
  color: var(--headings);
}

.pain-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.pain-icon-box.warn { background: var(--warn-glow); color: var(--warn); }
.pain-icon-box.err { background: var(--err-glow); color: var(--err); }
.pain-icon-box.info { background: var(--accent-glow); color: var(--accent); }
.pain-icon-box.ok { background: var(--ok-glow); color: var(--ok); }

.pain-body {
  height: 100px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  overflow: hidden;
}

/* Visual Components */
.form-stack {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.mini-form {
  font-size: 0.65rem;
  background: var(--bg);
  padding: 0.3rem 0.6rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--muted);
}

.repeat-indicator {
  margin-top: 0.5rem;
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--warn);
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  animation: pulse 2s infinite;
}

.resume-pile {
  position: relative;
  height: 60px;
  display: flex;
  justify-content: center;
}

.resume-sheet {
  position: absolute;
  width: 40px;
  height: 50px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 2px;
}

.resume-sheet:nth-child(1) { transform: rotate(-10deg) translateX(-10px); }
.resume-sheet:nth-child(2) { transform: rotate(5deg) translateX(5px); }
.resume-sheet:nth-child(3) { transform: rotate(-5deg) translateY(5px); }
.resume-sheet:nth-child(4) { transform: rotate(10deg) translateX(10px); z-index: 2; }

.pain-caption {
  font-size: 0.7rem;
  color: var(--muted);
  text-align: center;
  margin-top: 0.5rem;
}

.long-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  opacity: 0.5;
}

.list-item {
  font-size: 0.65rem;
  padding: 0.2rem 0.5rem;
  border-bottom: 1px solid var(--border);
  color: var(--muted);
}

.search-exhaustion {
  position: relative;
}

.fatigue-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--err-glow);
  color: var(--err);
  padding: 0.4rem 0.8rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid var(--err);
  white-space: nowrap;
}

.chat-bubbles {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.bubble {
  font-size: 0.6rem;
  padding: 0.3rem 0.6rem;
  border-radius: 10px;
  max-width: 80%;
}

.bubble-left {
  background: var(--bg);
  border: 1px solid var(--border);
  align-self: flex-start;
  color: var(--muted);
}

.bubble-right {
  background: var(--ok-glow);
  border: 1px solid var(--ok);
  align-self: flex-end;
  color: var(--ok);
  font-weight: 600;
}

.central-warning {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 10;
  background: var(--bg);
  border: 2px solid var(--err);
  padding: 1rem 1.5rem;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 0 30px rgba(239, 68, 68, 0.2);
  color: var(--err);
}

.central-warning span {
  font-weight: 800;
  font-size: 0.8rem;
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

.problem-details {
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

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
