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
  Workflow,
  ShieldAlert,
  Activity,
  Network,
  Lock,
  ArrowDown,
  Globe,
  FileJson,
  Key,
  MessageSquare,
  RefreshCw,
  EyeOff,
  UserCheck,
  FileText,
  MessageCircle
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- High-Fidelity Audit-Compliant Architecture -->
      <div class="arch-visual-v3">
        <div class="arch-tiers-v3">
          
          <!-- C1: Client & Frontend -->
          <div class="tier-v3">
            <div class="tier-label-v3 c1">Client & Frontend</div>
            <div class="node-grid-v3">
              <div class="node-v3 glass-card mini"><Users :size="10" /> Cand UI</div>
              <div class="node-v3 glass-card mini"><Users :size="10" /> Rec UI</div>
              <div class="node-v3 glass-card highlight"><Layout :size="12" /> Vue App Shell</div>
              <div class="node-v3 glass-card mini"><MessageSquare :size="10" /> ChatBot UI</div>
              <div class="node-v3 glass-card mini"><Zap :size="10" /> WS Client</div>
            </div>
          </div>

          <!-- C2: FastAPI Gateway -->
          <div class="tier-v3">
            <div class="tier-label-v3 c2">FastAPI Gateway</div>
            <div class="node-grid-v3">
              <div class="node-v3 glass-card"><Code :size="12" /> REST API</div>
              <div class="node-v3 glass-card"><Key :size="12" /> Auth Svc</div>
              <div class="node-v3 glass-card"><MessageCircle :size="12" /> Chat Route</div>
              <div class="node-v3 glass-card ok"><Network :size="12" /> WebSocket</div>
              <div class="node-v3 glass-card ok"><RefreshCw :size="12" /> SSE Stream</div>
            </div>
          </div>

          <!-- C3: Domain & Security -->
          <div class="tier-v3">
            <div class="tier-label-v3 c3">Domain & Security</div>
            <div class="node-grid-v3">
              <div class="node-v3 glass-card ok"><EyeOff :size="12" /> Blind Screen</div>
              <div class="node-v3 glass-card warn"><ShieldAlert :size="12" /> Guardrails</div>
              <div class="node-v3 glass-card highlight"><Lock :size="12" /> Service Modules</div>
              <div class="node-v3 glass-card"><UserCheck :size="12" /> Internal RBAC</div>
            </div>
          </div>

          <!-- C4: AI & Data Pipeline -->
          <div class="tier-v3">
            <div class="tier-label-v3 c4">AI & Data Pipeline</div>
            <div class="node-grid-v3">
              <div class="node-v3 glass-card accent"><Activity :size="12" /> Arrangement</div>
              <div class="node-v3 glass-card accent"><Globe :size="12" /> Analysis</div>
              <div class="node-v3 glass-card accent"><Cpu :size="12" /> Scoring Panel</div>
            </div>
          </div>

          <!-- C5: Storage & External -->
          <div class="tier-v3">
            <div class="tier-label-v3 c5">Storage & External</div>
            <div class="node-grid-v3">
              <div class="node-v3 glass-card"><Database :size="12" /> PG / FerretDB</div>
              <div class="node-v3 glass-card ok"><Search :size="12" /> Vector Search</div>
              <div class="node-v3 glass-card"><FileText :size="12" /> Resumes</div>
              <div class="node-v3 glass-card"><Share2 :size="12" /> External APIs</div>
            </div>
          </div>

          <!-- Vertical Flow Backbone -->
          <div class="backbone-v3"></div>
        </div>
      </div>

      <!-- Detailed Explanation -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">Runtime Architecture</h1>
        
        <div class="arch-details">
          <div class="detail-block">
            <h3>Optimized Multi-Tier Gateway</h3>
            <p>HiringAgent orchestrates a complex runtime where <strong>FastAPI</strong> serves as the central hub for RESTful state, real-time WebSockets, and unidirectional SSE streams.</p>
          </div>
          <div class="detail-block">
            <h3>Intercepted Security Layer</h3>
            <p>Domain logic is protected by a unified security layer. Requests are validated via <strong>Internal RBAC</strong> and sanitized through <strong>Guardrails</strong> and <strong>Blind Screening</strong> before pipeline execution.</p>
          </div>
          <div class="detail-block">
            <h3>Hybrid Pipeline & Foundation</h3>
            <p>The AI pipeline integrates structural parsing and adversarial scoring with a foundation built on <strong>FerretDB</strong>, <strong>PostgreSQL</strong>, and native <strong>Vector retrieval</strong>.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-content-container {
  max-width: 1500px;
  width: 100%;
}

.slide-main {
  display: grid;
  grid-template-columns: 1.3fr 0.7fr;
  gap: 4rem;
  align-items: center;
}

/* Audited Architecture Styles */
.arch-visual-v3 {
  position: relative;
  padding: 1.5rem;
  background: var(--bg-subtle);
  border-radius: 12px;
  border: 1px solid var(--border);
}

.arch-tiers-v3 {
  display: flex;
  flex-direction: column;
  gap: 2.5rem;
  position: relative;
  z-index: 5;
}

.tier-v3 {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.tier-label-v3 {
  font-size: 0.55rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  background: var(--bg);
}

.tier-label-v3.c1 { border-color: #0ea5e9; color: #0ea5e9; }
.tier-label-v3.c2 { border-color: #f97316; color: #f97316; }
.tier-label-v3.c3 { border-color: #a855f7; color: #a855f7; }
.tier-label-v3.c4 { border-color: #22c55e; color: #22c55e; }
.tier-label-v3.c5 { border-color: #64748b; color: #64748b; }

.node-grid-v3 {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
}

.node-v3 {
  padding: 0.4rem 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 4px;
  white-space: nowrap;
}

.node-v3.mini { font-size: 0.65rem; opacity: 0.8; }
.node-v3.highlight { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }
.node-v3.ok { border-color: var(--ok); color: var(--ok); }
.node-v3.warn { border-color: var(--warn); color: var(--warn); }
.node-v3.accent { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }

.backbone-v3 {
  position: absolute;
  top: 2rem;
  bottom: 2rem;
  left: 50%;
  width: 1px;
  background: linear-gradient(to bottom, transparent, var(--border), var(--border), transparent);
  z-index: -1;
  opacity: 0.5;
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
  font-size: 3rem;
  line-height: 1.1;
  margin: 0;
  color: var(--headings);
}

.arch-details {
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
  line-height: 1.5;
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
