<script setup>
import { 
  Network, 
  GitBranch, 
  Lock, 
  Key, 
  Database,
  Cpu,
  Share2,
  Workflow,
  Zap,
  User,
  Users,
  Check,
  X,
  Minus
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- LangGraph/Harness Visualization -->
      <div class="harness-visual">
        <div class="visual-stack">
          <!-- 1. Permission Matrix (The Harness) -->
          <div class="harness-matrix-card glass-card">
            <div class="matrix-header">
              <Lock :size="16" class="icon-accent" />
              <span>Permission-Based Injection Matrix</span>
            </div>
            <div class="matrix-grid">
              <!-- Recruiter Specific -->
              <div class="matrix-col recruiter">
                <div class="col-label"><Key :size="10" /> Recruiter</div>
                <div class="tool-entry plus">create_job</div>
                <div class="tool-entry plus">re_evaluate</div>
              </div>
              
              <!-- Shared -->
              <div class="matrix-col shared">
                <div class="col-label"><Users :size="10" /> Shared</div>
                <div class="tool-entry">list_jobs</div>
                <div class="tool-entry">get_details</div>
              </div>

              <!-- Candidate Specific -->
              <div class="matrix-col candidate">
                <div class="col-label"><User :size="10" /> Candidate</div>
                <div class="tool-entry plus">my_status</div>
                <div class="tool-entry plus">my_profile</div>
              </div>
            </div>
            <div class="matrix-footer">
              Tools are injected dynamically based on session role
            </div>
          </div>

          <!-- 2. LangGraph Node Isolation -->
          <div class="graph-nodes-stack">
            <div class="node-isolation glass-card">
              <div class="node-title">
                <Workflow :size="14" /> node_auto_score
              </div>
              <div class="node-context-box">
                <div class="context-item blocked"><Minus :size="8" /> Raw Resume</div>
                <div class="context-item allowed"><Check :size="8" /> Blinded Snapshot</div>
                <div class="context-item allowed"><Check :size="8" /> Job Spec</div>
              </div>
              <div class="isolation-label">Narrow Context Exposure</div>
            </div>
          </div>

          <!-- 3. Shared Service Path -->
          <div class="shared-path-v2 glass-card">
            <div class="unified-core">
              <div class="entry-points">
                <div class="entry">Web UI</div>
                <div class="entry-divider"></div>
                <div class="entry">AI Tool</div>
              </div>
              <div class="core-logic-box">
                <Database :size="20" />
                <span>Unified Service Layer</span>
                <p>Shared RBAC & Validation Logic</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="harness-details">
          <div class="detail-block">
            <h3>Role-Based Tool Injections</h3>
            <p>The AI Assistant's capabilities are dynamically constructed. Tools like <code>create_job</code> or <code>re_evaluate</code> are only injected into the session if the user's role permits it.</p>
          </div>
          <div class="detail-block">
            <h3>Unified Service Execution</h3>
            <p>AI tools and web interfaces share the exact same code paths. This ensures that permissions, validations, and business logic remain consistent across all interaction methods.</p>
          </div>
          <div class="detail-block">
            <h3>Stateful Task Isolation</h3>
            <p>Using LangGraph, complex workflows are broken into discrete nodes. Each node only has access to the specific data it needs, minimizing the "attack surface" exposed to the LLM.</p>
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

/* Harness Visual */
.harness-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(10deg);
}

/* Harness Matrix Card */
.harness-matrix-card {
  padding: 1.25rem;
  background: var(--bg-accent);
  border-color: var(--accent);
}

.matrix-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--headings);
  margin-bottom: 1.25rem;
}

.matrix-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.matrix-col {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  padding: 0.6rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
}

.matrix-col.recruiter { border-color: var(--accent-glow); }
.matrix-col.candidate { border-color: var(--ok-glow); }
.matrix-col.shared { border-color: var(--border); background: var(--bg-subtle); }

.col-label {
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 0.2rem;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.matrix-col.recruiter .col-label { color: var(--accent); }
.matrix-col.candidate .col-label { color: var(--ok); }

.tool-entry {
  font-size: 0.55rem;
  font-family: monospace;
  padding: 0.25rem 0.4rem;
  background: var(--bg-subtle);
  border-radius: 3px;
  color: var(--muted);
}

.tool-entry.plus {
  background: var(--bg);
  border: 1px solid var(--border);
  color: var(--text);
  font-weight: 600;
}

.matrix-footer {
  font-size: 0.6rem;
  text-align: center;
  color: var(--muted);
  font-style: italic;
  padding-top: 0.5rem;
  border-top: 1px solid var(--border);
}

/* Node Isolation */
.node-isolation {
  padding: 1rem;
  border-style: dashed;
}

.node-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--headings);
  margin-bottom: 0.75rem;
}

.node-context-box {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.context-item {
  font-size: 0.55rem;
  padding: 0.3rem 0.5rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.context-item.blocked {
  background: var(--err-glow);
  color: var(--err);
  border: 1px solid var(--err);
  opacity: 0.5;
  text-decoration: line-through;
}

.context-item.allowed {
  background: var(--ok-glow);
  color: var(--ok);
  border: 1px solid var(--ok);
  font-weight: 700;
}

.isolation-label {
  font-size: 0.6rem;
  text-align: right;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
}

/* Shared Path V2 */
.unified-core {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
}

.entry-points {
  display: flex;
  align-items: center;
  gap: 1rem;
  width: 100%;
  justify-content: center;
}

.entry-divider {
  width: 40px;
  height: 1px;
  background: var(--border);
}

.entry {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--muted);
}

.core-logic-box {
  background: var(--ok-glow);
  border: 2px solid var(--ok);
  padding: 0.75rem;
  border-radius: 8px;
  text-align: center;
  width: 90%;
}

.core-logic-box span {
  display: block;
  font-weight: 800;
  font-size: 0.85rem;
  color: var(--ok);
  margin-top: 0.4rem;
}

.core-logic-box p {
  margin: 0;
  font-size: 0.6rem;
  color: var(--ok);
  opacity: 0.8;
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

.harness-details {
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
