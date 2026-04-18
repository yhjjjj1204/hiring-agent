<script setup>
const props = defineProps(['data'])
</script>

<template>
  <div v-if="data" class="analysis-result glass-card">
    <div class="result-header">
      <h3>AI Analysis Summary</h3>
      <div v-if="data.scorecard" class="score-badge">
        <span class="score-val">{{ data.scorecard.overall_score }}</span>
        <span class="score-total">/100</span>
      </div>
    </div>

    <div v-if="data.scorecard" class="score-content">
      <p class="summary">{{ data.scorecard.summary }}</p>
      
      <div class="dimensions-grid">
        <div v-for="d in data.scorecard.dimensions" :key="d.name" class="dim-card glass-card">
          <div class="dim-header">
            <strong>{{ d.name }}</strong>
            <span class="dim-score">{{ d.score }}</span>
          </div>
          <p class="dim-rationale">{{ d.rationale }}</p>
        </div>
      </div>

      <div v-if="data.scorecard.hitl_suggested" class="hitl-alert">
        <strong>⚠️ Human Review Recommended</strong>
        <p>{{ data.scorecard.hitl_reason }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-result { padding: 2.5rem; margin-top: 2rem; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; }

.score-badge { 
  background: var(--ok-glow); 
  border: 1px solid var(--ok); 
  padding: 0.5rem 1.25rem; 
  border-radius: 12px; 
  color: var(--ok);
}
.score-val { font-size: 1.8rem; font-weight: 800; }
.score-total { font-size: 0.9rem; opacity: 0.7; }

.summary { font-size: 1.1rem; line-height: 1.7; margin-bottom: 2rem; font-style: italic; opacity: 0.9; }

.dimensions-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.dim-card { padding: 1.25rem; background: rgba(255,255,255,0.02); }
.dim-header { display: flex; justify-content: space-between; margin-bottom: 0.75rem; }
.dim-score { color: var(--ok); font-weight: 700; }
.dim-rationale { font-size: 0.9rem; color: var(--muted); line-height: 1.5; }

.hitl-alert { 
  margin-top: 2rem; 
  background: rgba(245, 158, 11, 0.1); 
  border: 1px solid rgba(245, 158, 11, 0.3); 
  padding: 1.5rem; 
  border-radius: 12px; 
  color: #f59e0b;
}
.hitl-alert p { margin-top: 0.5rem; font-size: 0.95rem; }

@media (max-width: 800px) {
  .dimensions-grid { grid-template-columns: 1fr; }
}
</style>
