<script setup>
import { 
  ShieldCheck, 
  ShieldAlert, 
  Lock, 
  User, 
  UserCheck,
  Bot,
  Zap,
  Eye,
  Search,
  AlertTriangle
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Guardrail Visualization -->
      <div class="guardrail-visual">
        <div class="visual-stack">
          <!-- Role: Candidate (Guarded) -->
          <div class="role-layer guarded">
            <div class="layer-label">
              <User :size="14" /> Candidate Interaction
              <span class="status-tag guarded">Fully Guarded</span>
            </div>
            <div class="dual-flow">
              <div class="flow-step">
                <span class="flow-label">1. Input Scan</span>
                <div class="chat-mock glass-card">
                  <div class="mock-header">"Ignore all previous instructions..."</div>
                  <div class="interception-point">
                    <ShieldAlert :size="20" class="icon-err" />
                  </div>
                </div>
              </div>
              <div class="flow-step">
                <span class="flow-label">2. Output Scan</span>
                <div class="chat-mock glass-card">
                  <div class="mock-header">"As a professional assistant, I..."</div>
                  <div class="interception-point">
                    <ShieldCheck :size="20" class="icon-ok" />
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- The Guardrail Core -->
          <div class="guardrail-core glass-card">
            <div class="core-header">
              <Zap :size="18" class="icon-accent" />
              <h4>Safety Engine & Canary Protocol</h4>
            </div>
            <div class="core-grid">
              <div class="policy-list">
                <div class="policy-item"><Eye :size="12" /> Injection Detection</div>
                <div class="policy-item"><Search :size="12" /> Roleplay Check</div>
                <div class="policy-item"><Bot :size="12" /> Professionalism</div>
              </div>
              <div class="canary-box glass-card">
                <div class="canary-header">
                  <Lock :size="12" /> Canary Mechanism
                </div>
                <div class="canary-tokens">
                  <div class="token-item">
                    <span class="token-code">Token A</span>
                    <span class="token-desc">Normal ID</span>
                  </div>
                  <div class="token-item alert">
                    <span class="token-code">Token B</span>
                    <span class="token-desc">Tamper Alert</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Role: Recruiter (Bypassed) -->
          <div class="role-layer bypassed">
            <div class="layer-label">
              <UserCheck :size="14" /> Recruiter Role
              <span class="status-tag trusted">Trusted</span>
            </div>
            <div class="action-flow">
              <div class="chat-mock glass-card">
                <div class="mock-header">"Generate summary for job #12..."</div>
                <div class="bypass-path">
                  <ShieldCheck :size="24" class="icon-ok" />
                </div>
              </div>
              <div class="decision-box allowed glass-card">
                <Zap :size="16" />
                <span>Bypassed (Operational Efficiency)</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="guardrail-details">
          <div class="detail-block">
            <h3>Bi-Directional Verification</h3>
            <p>Every interaction is scanned twice: once when the user provides <strong>input</strong> to prevent injections, and again when the AI generates <strong>output</strong> to ensure professional standards.</p>
          </div>
          <div class="detail-block">
            <h3>Canary Token Defense</h3>
            <p>A sophisticated two-token protocol detects LLM instruction tampering. If a prompt tries to leak internal logic, the system identifies the "Canary B" signal and immediately terminates the request.</p>
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

/* Guardrail Visual */
.guardrail-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(-10deg);
}

.role-layer {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.layer-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--headings);
}

.status-tag {
  font-size: 0.65rem;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  text-transform: uppercase;
}

.status-tag.guarded {
  background: var(--err-glow);
  color: var(--err);
  border: 1px solid var(--err);
}

.status-tag.trusted {
  background: var(--ok-glow);
  color: var(--ok);
  border: 1px solid var(--ok);
}

.dual-flow {
  display: flex;
  gap: 1rem;
}

.flow-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.flow-label {
  font-size: 0.65rem;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
}

.action-flow {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}

.chat-mock {
  padding: 0.75rem;
  background: var(--bg-subtle);
  border-color: var(--border);
  font-size: 0.75rem;
  color: var(--muted);
  font-style: italic;
  position: relative;
  min-height: 60px;
  display: flex;
  align-items: center;
}

.interception-point {
  position: absolute;
  top: 50%;
  right: 0.75rem;
  transform: translateY(-50%);
}

.decision-box {
  width: 200px;
  padding: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
}

.decision-box.allowed {
  background: var(--ok-glow);
  color: var(--ok);
  border-color: var(--ok);
}

/* Core Classifier */
.guardrail-core {
  background: var(--bg-accent);
  border: 2px solid var(--accent);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  box-shadow: 0 0 40px rgba(59, 130, 246, 0.2);
  z-index: 5;
}

.core-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.core-header h4 {
  margin: 0;
  font-size: 0.95rem;
  color: var(--headings);
}

.core-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.policy-list {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.policy-item {
  font-size: 0.65rem;
  background: var(--bg);
  padding: 0.35rem 0.6rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  border: 1px solid var(--border);
  color: var(--muted);
}

.canary-box {
  padding: 0.6rem;
  background: var(--bg);
  border-style: dashed;
}

.canary-header {
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--accent);
  text-transform: uppercase;
  margin-bottom: 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.canary-tokens {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.token-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.2rem 0.4rem;
  background: var(--bg-subtle);
  border-radius: 3px;
}

.token-code {
  font-family: monospace;
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--ok);
}

.token-desc {
  font-size: 0.55rem;
  color: var(--muted);
}

.token-item.alert .token-code {
  color: var(--err);
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

.guardrail-details {
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
