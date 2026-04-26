<script setup>
import { 
  Users, 
  Bot, 
  Database, 
  ShieldCheck, 
  Zap, 
  Code, 
  GraduationCap, 
  Search,
  Cpu,
  Layers,
  Layout,
  Share2,
  Workflow
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Complex Architecture Visualization -->
      <div class="arch-visual-container">
        <div class="arch-flow">
          
          <!-- Layer 1: Interface -->
          <div class="arch-group interface-layer">
            <div class="group-label">Access Layer</div>
            <div class="nodes-row">
              <div class="node glass-card">
                <Users :size="18" />
                <span>Recruiter Portal</span>
              </div>
              <div class="node glass-card">
                <Users :size="18" />
                <span>Candidate Portal</span>
              </div>
            </div>
          </div>

          <div class="connector-v"></div>

          <!-- Layer 2: API & Gateway -->
          <div class="arch-group gateway-layer">
            <div class="node-main glass-card highlight">
              <Zap :size="20" />
              <span>FastAPI / WebSocket Gateway</span>
              <div class="sub-label">Auth • RBAC • SSE</div>
            </div>
          </div>

          <div class="connector-v"></div>

          <!-- Layer 3: Orchestration -->
          <div class="arch-group brain-layer">
            <div class="group-label">Intelligence Orchestration (LangGraph)</div>
            
            <div class="agents-grid">
              <!-- HR Agent -->
              <div class="agent-node glass-card">
                <Bot :size="16" class="text-accent" />
                <div class="agent-info">
                  <strong>HR Strategy</strong>
                  <span>Job Spec Refinement</span>
                </div>
              </div>

              <!-- Data Agent -->
              <div class="agent-node glass-card">
                <Bot :size="16" class="text-ok" />
                <div class="agent-info">
                  <strong>Data Arrangement</strong>
                  <span>OCR & Profile Parsing</span>
                </div>
              </div>

              <!-- Background Agent -->
              <div class="agent-node glass-card">
                <Bot :size="16" class="text-warn" />
                <div class="agent-info">
                  <strong>Background Analysis</strong>
                  <span>GitHub / OpenAlex / Scholar</span>
                </div>
              </div>

              <!-- Scoring Agent Cluster -->
              <div class="agent-node glass-card multi">
                <div class="multi-icons">
                  <ShieldCheck :size="12" />
                  <Bot :size="12" />
                  <Share2 :size="12" />
                </div>
                <div class="agent-info">
                  <strong>Scoring Panel</strong>
                  <span>Advocate • Critic • Judge</span>
                </div>
              </div>
            </div>
          </div>

          <div class="connector-v"></div>

          <!-- Layer 4: Persistence -->
          <div class="arch-group data-layer">
            <div class="group-label">Hybrid Persistence</div>
            <div class="nodes-row">
              <div class="node glass-card">
                <Database :size="18" />
                <span>FerretDB / PostgreSQL</span>
              </div>
              <div class="node glass-card highlight-ok">
                <Search :size="18" />
                <span>CosmosSearch (Vector)</span>
              </div>
            </div>
          </div>

        </div>
      </div>

      <!-- Detailed Explanation -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">Multi-Agent Intelligence</h1>
        
        <div class="arch-details">
          <section class="detail-section">
            <div class="section-title">
              <Workflow :size="18" />
              <h3>Recursive Workflow</h3>
            </div>
            <p>HiringAgent uses <strong>LangGraph</strong> to maintain state across complex multi-turn dialogues and async processing pipelines.</p>
          </section>

          <section class="detail-section">
            <div class="section-title">
              <Share2 :size="18" />
              <h3>Competing Experts</h3>
            </div>
            <p>The Scoring Agent isn't a single LLM call. It's a panel where an <strong>Advocate</strong> finds potential and a <strong>Critic</strong> finds risks, both overseen by <strong>Logic Auditors</strong>.</p>
          </section>

          <section class="detail-section">
            <div class="section-title">
              <Database :size="18" />
              <h3>Vectorized Foundation</h3>
            </div>
            <p>Jobs and candidates are indexed using <strong>CosmosSearch</strong> (HNSW/IVF), enabling dual-vector semantic matching between resumes and job specs.</p>
          </section>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-content-container {
  max-width: 1300px;
  width: 100%;
}

.slide-main {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 4rem;
  align-items: flex-start;
}

/* Architecture Graph Styles */
.arch-visual-container {
  padding: 1rem;
  background: var(--glass);
  border-radius: 12px;
  border: 1px solid var(--border-subtle);
}

.arch-flow {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.arch-group {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  position: relative;
}

.group-label {
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
  letter-spacing: 0.1em;
}

.nodes-row {
  display: flex;
  gap: 1rem;
  justify-content: center;
  width: 100%;
}

.node, .node-main {
  padding: 0.75rem 1.25rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 8px;
}

.node-main {
  flex-direction: column;
  gap: 0.25rem;
  padding: 1rem 2rem;
}

.node-main .sub-label {
  font-size: 0.7rem;
  font-weight: 400;
  color: var(--muted);
}

.highlight { border-color: var(--accent) !important; background: var(--accent-glow) !important; }
.highlight-ok { border-color: var(--ok) !important; background: var(--ok-glow) !important; }

.agents-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  width: 100%;
}

.agent-node {
  padding: 0.75rem;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: var(--bg-subtle);
  border-color: var(--border);
}

.agent-info {
  display: flex;
  flex-direction: column;
}

.agent-info strong {
  font-size: 0.85rem;
  color: var(--headings);
}

.agent-info span {
  font-size: 0.7rem;
  color: var(--muted);
}

.agent-node.multi {
  border-style: dashed;
  border-color: var(--accent);
}

.multi-icons {
  display: flex;
  flex-wrap: wrap;
  width: 24px;
  gap: 2px;
  color: var(--accent);
}

/* Connectors */
.connector-v {
  height: 20px;
  width: 2px;
  background: linear-gradient(to bottom, var(--accent), var(--border));
}

/* Text Side */
.slide-text {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.slide-subtitle {
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.slide-title {
  font-size: 3rem;
  line-height: 1.1;
  margin: 0;
  color: var(--headings);
}

.arch-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1rem;
}

.detail-section {
  background: var(--glass);
  padding: 1.25rem;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
  color: var(--accent);
}

.section-title h3 {
  margin: 0;
  font-size: 1.1rem;
}

.detail-section p {
  font-size: 0.95rem;
  color: var(--muted);
  line-height: 1.5;
  margin: 0;
}

.detail-section strong {
  color: var(--text);
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
