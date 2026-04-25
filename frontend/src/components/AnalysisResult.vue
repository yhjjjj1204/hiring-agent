<script setup>
import { ref, computed } from 'vue'
import { 
  ShieldCheck, 
  ShieldAlert, 
  XCircle
} from 'lucide-vue-next'
import { marked } from 'marked'

const props = defineProps(['data'])
const activeExpert = ref('advocacy') // 'advocacy' or 'criticism'

function renderMarkdown(text) {
  if (!text) return ''
  try {
    return marked.parse(String(text))
  } catch (e) {
    console.error("Markdown parse error", e, text)
    return String(text)
  }
}

const currentPoints = computed(() => {
  if (!props.data?.scorecard?.competing_analysis) return []
  return activeExpert.value === 'advocacy' 
    ? props.data.scorecard.competing_analysis.advocate_points 
    : props.data.scorecard.competing_analysis.critic_points
})
</script>

<template>
  <div v-if="data" class="analysis-result">
    <div class="result-header">
      <h3>AI Analysis Summary</h3>
      <div v-if="data.scorecard" class="score-badge">
        <span class="score-val">{{ data.scorecard.overall_score }}</span>
        <span class="score-total">/100</span>
      </div>
    </div>

    <div v-if="data.scorecard" class="score-content">
      <!-- Debug: Remove after fixing -->
      <!-- <pre style="font-size: 8px; opacity: 0.5">{{ JSON.stringify(data.scorecard.competing_analysis, null, 2) }}</pre> -->
      
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

      <!-- Competing Experts Analysis (Simplified Tabs) -->
      <div v-if="data.scorecard.competing_analysis" class="competing-experts">
        <div class="expert-tabs-row">
          <div class="tab-group full-width">
            <button 
              :class="['tab-btn', { active: activeExpert === 'advocacy' }]" 
              @click="activeExpert = 'advocacy'"
            >
              <ShieldCheck :size="14" /> Advocate
            </button>
            <span class="tab-sep">|</span>
            <button 
              :class="['tab-btn', { active: activeExpert === 'criticism' }]" 
              @click="activeExpert = 'criticism'"
            >
              <ShieldAlert :size="14" /> Critic
            </button>
          </div>
        </div>

        <div class="points-grid">
          <div v-for="(p, i) in currentPoints" :key="i" class="point-card glass-card" :class="activeExpert">
            <div class="point-header">
              <span class="point-index">#{{ i + 1 }}</span>
              <h4 class="point-title">{{ p.title }}</h4>
            </div>
            
            <div class="point-body">
              <div class="description-block">
                <div class="markdown-body" v-html="renderMarkdown(p.description)"></div>
              </div>
              
              <div v-if="p.refutation" class="refutation-block">
                <div class="refutation-header">
                  <XCircle :size="12" /> Auditor Challenge
                </div>
                <div class="markdown-body" v-html="renderMarkdown(p.refutation)"></div>
              </div>
            </div>
          </div>
          
          <div v-if="currentPoints.length === 0" class="empty-points">
            No specific points identified by this agent.
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.analysis-result { padding: 0.25rem; margin-top: 0.25rem; }
.result-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.result-header h3 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); }

.score-badge { 
  background: var(--bg); 
  border: 1px solid var(--ok); 
  padding: 0.2rem 0.5rem; 
  border-radius: 4px; 
  color: var(--ok);
}
.score-val { font-size: 1.25rem; font-weight: 800; }
.score-total { font-size: 0.8rem; opacity: 0.7; }

.summary { font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem; font-style: italic; opacity: 0.9; }

.dimensions-grid { display: grid; grid-template-columns: 1fr; gap: 0.4rem; margin-bottom: 1.25rem; }
.dim-card { padding: 0.75rem; background: var(--glass); border: 1px solid var(--border-subtle); }
.dim-header { display: flex; justify-content: space-between; margin-bottom: 0.2rem; font-size: 1rem; }
.dim-score { color: var(--ok); font-weight: 700; }
.dim-rationale { font-size: 0.9rem; color: var(--muted); line-height: 1.4; }

/* Competing Experts Tabs Paired Style */
.competing-experts { margin-top: 1.25rem; border-top: 1px solid var(--border); padding-top: 0.75rem; }

.expert-tabs-row { 
  display: flex; 
  margin-bottom: 1rem; 
}

.tab-group.full-width {
  width: 100%;
  display: flex;
  align-items: center;
  background: var(--header-bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 2px;
}

.tab-btn {
  flex: 1;
  background: transparent;
  border: none;
  color: var(--muted);
  padding: 0.45rem 0.2rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  transition: all 0.1s ease;
  border-radius: 3px;
}

.tab-sep {
  color: var(--border);
  font-size: 0.9rem;
  user-select: none;
  opacity: 0.5;
}

.tab-btn:hover { color: var(--text); }
.tab-btn.active { 
  background: var(--panel); 
  color: var(--accent); 
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.tab-pane { animation: fadeIn 0.15s ease-out; }

/* Points Grid */
.points-grid {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.point-card {
  padding: 0.75rem;
  border: 1px solid var(--border);
  border-radius: 4px;
  background: var(--bg-subtle);
  animation: slideIn 0.2s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(5px); }
  to { opacity: 1; transform: translateY(0); }
}

.point-card.advocacy { border-left: 2px solid var(--ok); }
.point-card.criticism { border-left: 2px solid var(--err); }

.point-header {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.point-index {
  font-size: 0.8rem;
  font-weight: 800;
  color: var(--muted);
  margin-top: 0.1rem;
}

.point-title {
  font-size: 1rem;
  font-weight: 700;
  color: var(--headings);
  margin: 0;
  line-height: 1.3;
}

.point-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.description-block {
  font-size: 0.95rem;
  line-height: 1.5;
  color: var(--text);
}

.refutation-block {
  padding: 0.6rem 0.75rem;
  background: var(--err-glow);
  border: 1px solid var(--err);
  border-radius: 2px;
  position: relative;
  animation: fadeIn 0.2s ease-in;
}

.refutation-header {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--err);
  display: flex;
  align-items: center;
  gap: 0.3rem;
  margin-bottom: 0.4rem;
}

.refutation-block .markdown-body {
  font-size: 0.9rem;
  color: var(--text);
  line-height: 1.4;
  font-style: italic;
}

.empty-points {
  text-align: center;
  padding: 2rem;
  color: var(--muted);
  font-size: 0.9rem;
  font-style: italic;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
