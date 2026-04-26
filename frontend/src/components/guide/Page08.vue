<script setup>
import { 
  Users, 
  ShieldCheck, 
  ShieldAlert, 
  XCircle, 
  Scale, 
  Zap,
  ArrowRight,
  TrendingUp,
  Target,
  ArrowDown
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})

// Mock data for high-fidelity split UI demo
const mockData = {
  score: 92,
  summary: "Elite candidate with foundational impact in core infrastructure. Auditor-verified evidence confirms leadership in high-scale environments.",
  dimensions: [
    { name: "Skills", score: 95 },
    { name: "Experience", score: 90 },
    { name: "Culture", score: 88 }
  ],
  points: {
    advocacy: [
      {
        title: "Ecosystem Leadership",
        description: "Core maintainer of key infra projects.",
        refutation: null
      },
      {
        title: "Technical Adaptation",
        description: "Mastered LangGraph in two weeks.",
        refutation: "Production scale not fully specified."
      }
    ],
    criticism: [
      {
        title: "Enterprise Scale",
        description: "Most experience is in startups.",
        refutation: "Open-source work handles millions of requests."
      }
    ]
  }
}
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Expert System Visualization -->
      <div class="experts-visual">
        <div class="visual-stack">
          <!-- Cleaner Flow Chart -->
          <div class="clean-flow">
            <div class="flow-row">
              <div class="agent-group advocate">
                <div class="main-node"><ShieldCheck :size="14" /> Advocate</div>
                <div class="audit-node-small"><XCircle :size="10" /> Logic Auditor</div>
              </div>
              
              <div class="flow-connector"><ArrowRight :size="16" /></div>
              
              <div class="judge-node-main glass-card">
                <Scale :size="18" class="icon-accent" />
                <div class="judge-label">Meritocratic Judge</div>
              </div>

              <div class="flow-connector"><ArrowRight :size="16" class="rev" /></div>

              <div class="agent-group critic">
                <div class="main-node"><ShieldAlert :size="14" /> Critic</div>
                <div class="audit-node-small"><XCircle :size="10" /> Logic Auditor</div>
              </div>
            </div>
            <div class="flow-caption">Parallel analysis with real-time factual auditing</div>
          </div>

          <!-- High-Fidelity Split UI Demo -->
          <div class="ui-demo-split glass-card">
            <div class="demo-top-bar">
              <div class="demo-badge">Evaluation Dashboard</div>
              <div class="demo-score-v3">
                <span class="v">92</span><span class="t">/100</span>
              </div>
            </div>

            <div class="demo-summary-v3">{{ mockData.summary }}</div>

            <div class="demo-split-grid">
              <!-- Advocate Column -->
              <div class="demo-col">
                <div class="col-header adv"><ShieldCheck :size="12" /> Advocated Potential</div>
                <div class="col-points">
                  <div v-for="(p, i) in mockData.points.advocacy" :key="i" class="p-card-mini advocacy">
                    <div class="p-t-mini">{{ p.title }}</div>
                    <div v-if="p.refutation" class="p-r-mini"><XCircle :size="8" /> {{ p.refutation }}</div>
                  </div>
                </div>
              </div>

              <!-- Critic Column -->
              <div class="demo-col">
                <div class="col-header cri"><ShieldAlert :size="12" /> Critical Risks</div>
                <div class="col-points">
                  <div v-for="(p, i) in mockData.points.criticism" :key="i" class="p-card-mini criticism">
                    <div class="p-t-mini">{{ p.title }}</div>
                    <div v-if="p.refutation" class="p-r-mini"><XCircle :size="8" /> {{ p.refutation }}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="experts-details">
          <div class="detail-block">
            <h3>Adversarial Synthesis</h3>
            <p>HiringAgent employs a competing experts architecture where <strong>Advocates</strong> and <strong>Critics</strong> operate in parallel. Dedicated <strong>Logic Auditors</strong> fact-check every claim before it reaches the final stage.</p>
          </div>
          <div class="detail-block">
            <h3>Meritocratic Judgment</h3>
            <p>The <strong>Judge Agent</strong> arbitrates verified evidence using a high-impact scoring reference. This design is optimized to identify elite professional excellence while explicitly avoiding <strong>regression to the mean</strong>.</p>
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

/* Experts Visual */
.experts-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  transform: rotateY(-5deg);
}

/* Cleaner Flow Chart */
.clean-flow {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.flow-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
  justify-content: center;
}

.agent-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;
}

.main-node {
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.advocate .main-node { border-left: 3px solid var(--ok); }
.critic .main-node { border-left: 3px solid var(--err); }

.audit-node-small {
  font-size: 0.55rem;
  font-weight: 800;
  color: var(--err);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: 0.7;
}

.flow-connector { color: var(--border); opacity: 0.5; }
.flow-connector .rev { transform: rotate(180deg); }

.judge-node-main {
  padding: 1rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  border: 2px solid var(--accent);
  background: var(--bg-accent);
  box-shadow: 0 0 40px rgba(59, 130, 246, 0.15);
}

.judge-label { font-size: 0.8rem; font-weight: 800; color: var(--headings); }

.flow-caption {
  font-size: 0.65rem;
  color: var(--muted);
  font-style: italic;
}

/* UI Demo Split */
.ui-demo-split {
  padding: 1.25rem;
  background: var(--bg-subtle);
  border-color: var(--border);
}

.demo-top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.demo-badge {
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
}

.demo-score-v3 {
  background: var(--ok-glow);
  color: var(--ok);
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  border: 1px solid var(--ok);
}

.demo-score-v3 .v { font-size: 1.1rem; font-weight: 800; }
.demo-score-v3 .t { font-size: 0.75rem; opacity: 0.7; }

.demo-summary-v3 {
  font-size: 0.8rem;
  line-height: 1.4;
  color: var(--text);
  margin-bottom: 1.25rem;
  opacity: 0.9;
  border-left: 2px solid var(--accent);
  padding-left: 0.75rem;
}

.demo-split-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.col-header {
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.col-header.adv { color: var(--ok); }
.col-header.cri { color: var(--err); }

.col-points {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.p-card-mini {
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 0.6rem;
  border-radius: 4px;
}

.p-card-mini.advocacy { border-left: 2px solid var(--ok); }
.p-card-mini.criticism { border-left: 2px solid var(--err); }

.p-t-mini { font-size: 0.75rem; font-weight: 700; color: var(--headings); margin-bottom: 0.2rem; }
.p-r-mini {
  font-size: 0.6rem;
  color: var(--err);
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-top: 0.4rem;
  padding-top: 0.4rem;
  border-top: 1px dashed var(--err);
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

.experts-details {
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
