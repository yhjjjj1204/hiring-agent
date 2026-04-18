<script setup>
import { computed } from 'vue'
import CandidateSnapshot from './CandidateSnapshot.vue'

const props = defineProps(['data'])

const scorecard = computed(() => props.data?.scorecard || {})
const overallScore = computed(() => {
  const ov = scorecard.value.overall_score
  return ov != null && ov !== "" ? String(ov) : "—"
})
const confidence = computed(() => {
  const conf = scorecard.value.overall_confidence
  if (conf != null && conf !== "") {
    return (Number(conf) * 100).toFixed(0) + "%"
  }
  return "—"
})
const dimensions = computed(() => Array.isArray(scorecard.value.dimensions) ? scorecard.value.dimensions : [])
</script>

<template>
  <section v-if="data" id="results">
    <h2>Results</h2>
    <div class="score-hero">
      <div>
        <div class="big">{{ overallScore }}</div>
        <div class="meta">Overall score (0–100)</div>
      </div>
      <div class="meta">
        Model confidence: <strong>{{ confidence }}</strong>
        <span v-if="scorecard.hitl_suggested"> · HITL suggested</span>
      </div>
    </div>

    <h3>Short summary</h3>
    <div class="summary-box">
      {{ scorecard.summary || "(No summary returned.)" }}
    </div>

    <div v-if="data.hitl_style_note" class="callout">
      {{ data.hitl_style_note }}
    </div>

    <h3>Scores by dimension</h3>
    <table class="dim">
      <thead>
        <tr>
          <th>Dimension</th>
          <th class="num">Score</th>
          <th>Why (brief)</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!dimensions.length">
          <td colspan="3">No dimension rows returned.</td>
        </tr>
        <tr v-for="d in dimensions" :key="d.name">
          <td>{{ d.name || "—" }}</td>
          <td class="num">{{ d.score != null ? d.score : "—" }}</td>
          <td>{{ d.rationale || "" }}</td>
        </tr>
      </tbody>
    </table>

    <h3>Candidate snapshot (from resume)</h3>
    <CandidateSnapshot :arrangedResume="data.arranged_resume" />

    <details class="raw">
      <summary>Show raw JSON response</summary>
      <pre>{{ JSON.stringify(data, null, 2) }}</pre>
    </details>
  </section>
</template>

<style scoped>
#results { margin-top: 1.5rem; }
.score-hero {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 1rem 1.5rem;
  padding: 1rem 1.1rem;
  border-radius: 12px;
  background: var(--panel);
  border: 1px solid var(--border);
}
.score-hero .big {
  font-size: 2.5rem;
  font-weight: 700;
  line-height: 1;
  letter-spacing: -0.02em;
}
.score-hero .meta { color: var(--muted); font-size: 0.9rem; }
.score-hero .meta strong { color: var(--text); }

.summary-box {
  margin-top: 0.85rem;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  background: #111923;
  border: 1px solid var(--border);
  font-size: 0.95rem;
}

.callout {
  margin-top: 0.85rem;
  padding: 0.75rem 1rem;
  border-radius: 10px;
  background: var(--warn-bg);
  border: 1px solid var(--warn-border);
  font-size: 0.9rem;
  color: #fcd34d;
}

details.raw { margin-top: 1rem; }
details.raw summary {
  cursor: pointer;
  color: var(--accent);
  font-size: 0.9rem;
}
</style>
