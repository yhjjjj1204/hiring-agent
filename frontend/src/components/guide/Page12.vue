<script setup>
import { 
  Database, 
  Cpu, 
  Search, 
  Layers, 
  FileCode, 
  Network,
  Zap,
  ArrowDown,
  Code2,
  TableProperties,
  ArrowRight
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Database Architecture Visualization -->
      <div class="db-visual">
        <div class="visual-stack">
          <!-- Top: Data Input -->
          <div class="source-layer">
            <div class="source-pill">
              <Layers :size="14" />
              Incoming Candidate & Job Data
            </div>
          </div>

          <!-- Middle: Parallel Flows -->
          <div class="dual-flows">
            <!-- Flow 1: Document Path -->
            <div class="flow-path">
              <div class="flow-tag">Document Flow</div>
              <div class="flow-step glass-card">
                <Code2 :size="16" class="icon-accent" />
                <div class="step-info">
                  <span class="step-name">MongoDB compatibility API</span>
                  <span class="step-desc">Pymongo / JSON</span>
                </div>
              </div>
              <div class="flow-line">
                <ArrowDown :size="14" />
              </div>
            </div>

            <!-- Flow 2: Vector Path -->
            <div class="flow-path">
              <div class="flow-tag">Vector Flow</div>
              <div class="flow-step glass-card highlight">
                <Cpu :size="16" class="icon-warn" />
                <div class="step-info">
                  <span class="step-name">OpenAI API (to vector)</span>
                  <span class="step-desc">text-embedding-3-small</span>
                </div>
              </div>
              <div class="flow-line">
                <ArrowDown :size="14" />
              </div>
            </div>
          </div>

          <!-- Convergence: FerretDB -->
          <div class="convergence-layer">
            <div class="ferret-node glass-card">
              <div class="node-header">
                <Network :size="20" class="icon-accent" />
                <h4>FerretDB</h4>
              </div>
              <div class="node-capabilities">
                <span>Direct Storage Mapping</span>
                <div class="cap-divider"></div>
                <span>HNSW Vector Indexing</span>
              </div>
            </div>
            <div class="flow-line">
              <ArrowDown :size="14" />
            </div>
          </div>

          <!-- Bottom: PostgreSQL -->
          <div class="storage-layer glass-card">
            <div class="storage-header">
              <Database :size="20" class="icon-ok" />
              <div class="storage-titles">
                <h4>PostgreSQL</h4>
                <p>Relational Stateful Backend</p>
              </div>
            </div>
            <div class="storage-content">
              <div class="data-badge">JSONB</div>
              <div class="data-badge">pgvector / Indexes</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="db-details">
          <div class="detail-block">
            <h3>Open Source Foundation</h3>
            <p>We leverage <strong>FerretDB</strong> to run MongoDB workloads on <strong>PostgreSQL</strong>. This combines the developer-friendly document API with the world-class stability of a relational backend.</p>
          </div>
          <div class="detail-block">
            <h3>Native Vector Search</h3>
            <p>Using FerretDB's <code>cosmosSearch</code>, we perform high-performance K-Nearest Neighbor (KNN) searches directly on stored OpenAI embeddings, enabling semantic job matching.</p>
          </div>
          <div class="detail-block">
            <h3>Unified Data Model</h3>
            <p>Both structured metadata and high-dimensional vectors live together in the same database, ensuring atomic updates and simplified operational complexity.</p>
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

/* DB Visual */
.db-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
  transform: rotateY(-5deg);
}

/* Source Layer */
.source-layer {
  width: 100%;
  display: flex;
  justify-content: center;
  margin-bottom: 0.5rem;
}

.source-pill {
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

/* Dual Flows */
.dual-flows {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  width: 100%;
}

.flow-path {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.flow-tag {
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
  letter-spacing: 0.05em;
}

.flow-step {
  width: 100%;
  padding: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
}

.flow-step.highlight {
  border-color: var(--warn-glow);
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.1);
}

.step-info {
  display: flex;
  flex-direction: column;
}

.step-name {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--headings);
}

.step-desc {
  font-size: 0.6rem;
  color: var(--muted);
  font-family: monospace;
}

.flow-line {
  color: var(--border);
}

/* Convergence Layer */
.convergence-layer {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}

.ferret-node {
  width: 80%;
  padding: 1rem;
  background: var(--bg-accent);
  border: 2px solid var(--accent);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 10px 30px rgba(59, 130, 246, 0.1);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.node-header h4 {
  margin: 0;
  font-size: 1rem;
  color: var(--headings);
}

.node-capabilities {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--accent);
}

.cap-divider {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: var(--accent);
}

/* Storage Layer */
.storage-layer {
  width: 90%;
  padding: 1rem;
  border-style: dashed;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.storage-header {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.storage-titles h4 {
  margin: 0;
  font-size: 1rem;
  color: var(--ok);
}

.storage-titles p {
  margin: 0;
  font-size: 0.65rem;
  color: var(--muted);
}

.storage-content {
  display: flex;
  gap: 1rem;
}

.data-badge {
  font-size: 0.6rem;
  font-weight: 800;
  padding: 0.2rem 0.6rem;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--muted);
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

.db-details {
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
