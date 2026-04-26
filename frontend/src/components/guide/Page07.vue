<script setup>
import { 
  CheckCircle, 
  Terminal, 
  Package, 
  Container, 
  Github, 
  Workflow,
  RefreshCw,
  Box,
  Server,
  Code2
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Quality & Deployment Visualization -->
      <div class="qa-visual">
        <div class="visual-stack">
          <!-- 1. Nix Foundation -->
          <div class="nix-layer glass-card">
            <div class="layer-header">
              <Package :size="18" class="icon-accent" />
              <span>Nix Reproducible Foundation</span>
            </div>
            <div class="nix-pills">
              <div class="nix-pill">Python 3.x Env</div>
              <div class="nix-pill">Node.js / Vite</div>
              <div class="nix-pill">Pre-built Bundle</div>
            </div>
            <div class="nix-caption">"It works on my machine" is guaranteed by Flakes</div>
          </div>

          <!-- 2. Testing Pipeline -->
          <div class="test-pipeline glass-card">
            <div class="pipeline-header">
              <CheckCircle :size="18" class="icon-ok" />
              <span>Automated Quality Gate (Pytest)</span>
            </div>
            <div class="test-grid">
              <div class="test-item ok">
                <Code2 :size="12" /> Unit Tests
              </div>
              <div class="test-item ok">
                <Server :size="12" /> Integration
              </div>
              <div class="test-item ok">
                <Workflow :size="12" /> Async Workflows
              </div>
            </div>
          </div>

          <!-- 3. Orchestration & CI -->
          <div class="infra-row">
            <!-- Docker Compose -->
            <div class="infra-box docker glass-card">
              <div class="infra-icon"><Container :size="20" /></div>
              <div class="infra-text">
                <strong>Docker Compose</strong>
                <span>Full System Orchestration</span>
              </div>
            </div>
            <!-- GitHub Workflow -->
            <div class="infra-box github glass-card">
              <div class="infra-icon"><Github :size="20" /></div>
              <div class="infra-text">
                <strong>GitHub Actions</strong>
                <span>CI/CD Pipeline</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="qa-details">
          <div class="detail-block">
            <h3>Reproducible Engineering</h3>
            <p>We use <strong>Nix</strong> to define a hermetic development environment and production build. Every dependency is pinned, ensuring consistent behavior from dev to production.</p>
          </div>
          <div class="detail-block">
            <h3>Exhaustive Test Coverage</h3>
            <p>Our <strong>Pytest</strong> suite covers everything from individual agent logic (Unit) to full API workflows (Integration), reaching over 70% code coverage.</p>
          </div>
          <div class="detail-block">
            <h3>Continuous Validation</h3>
            <p>Every commit triggers a <strong>GitHub Workflow</strong> that spins up the full stack using <strong>Docker</strong> and Nix, executing the test suite before any build is finalized.</p>
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

/* QA Visual */
.qa-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(5deg);
}

/* Nix Layer */
.nix-layer {
  padding: 1.25rem;
  background: var(--bg-accent);
  border-left: 4px solid var(--accent);
}

.layer-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--headings);
  margin-bottom: 1rem;
}

.nix-pills {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.nix-pill {
  font-size: 0.65rem;
  font-weight: 700;
  background: var(--bg);
  padding: 0.3rem 0.6rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  color: var(--muted);
}

.nix-caption {
  font-size: 0.65rem;
  color: var(--muted);
  font-style: italic;
  text-align: right;
}

/* Test Pipeline */
.test-pipeline {
  padding: 1.25rem;
  border-color: var(--ok-glow);
}

.pipeline-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--ok);
  margin-bottom: 1rem;
}

.test-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

.test-item {
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.5rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
}

.test-item.ok {
  color: var(--ok);
  border-color: var(--ok-glow);
  background: var(--ok-glow);
}

/* Infra Row */
.infra-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
}

.infra-box {
  padding: 1rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.infra-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--muted);
}

.infra-text {
  display: flex;
  flex-direction: column;
}

.infra-text strong {
  font-size: 0.8rem;
  color: var(--headings);
}

.infra-text span {
  font-size: 0.6rem;
  color: var(--muted);
}

.docker .infra-icon { color: #2496ed; border-color: rgba(36, 150, 237, 0.2); }
.github .infra-icon { color: var(--text); border-color: var(--border); }

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

.qa-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.detail-block h3 {
  font-size: 1.1rem;
  margin-bottom: 0.5rem;
  color: var(--text);
  border-left: 3px solid var(--accent);
  padding-left: 1rem;
}

.detail-block p {
  font-size: 0.95rem;
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
