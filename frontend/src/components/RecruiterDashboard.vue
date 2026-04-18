<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import JobManager from './JobManager.vue'

const selectedJob = ref(null)
const candidates = ref([])
const status = ref('')
let pollInterval = null

async function fetchCandidates() {
  if (!selectedJob.value) {
    candidates.value = []
    return
  }
  
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/dashboard/rankings?job_id=${selectedJob.value.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok) {
      candidates.value = data.items
    } else {
      status.value = data.detail || 'Failed to fetch'
    }
  } catch (e) {
    status.value = e.message
  }
}

async function reEvaluate(rankingId) {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/analyze/re-evaluate/${rankingId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      fetchCandidates()
    }
  } catch (e) {
    console.error('Re-evaluation failed', e)
  }
}

function downloadResume(rankingId) {
  const token = localStorage.getItem('token')
  window.open(`/analyze/resume/${rankingId}?token=${token}`, '_blank')
}

function onSelectJob(job) {
  selectedJob.value = job
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

watch(selectedJob, (newJob) => {
  fetchCandidates()
  if (newJob && !pollInterval) {
    pollInterval = setInterval(fetchCandidates, 5000)
  } else if (!newJob && pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
})

onMounted(() => {
  if (selectedJob.value) {
    pollInterval = setInterval(fetchCandidates, 5000)
  }
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="dashboard">
    <JobManager @select-job="onSelectJob" />

    <div v-if="selectedJob" class="results-section">
      <div class="results-header">
        <h2>Candidates for: {{ selectedJob.title }}</h2>
        <button class="mini" @click="selectedJob = null">Back to Job List</button>
      </div>
      
      <p v-if="status" class="err">{{ status }}</p>
      
      <div v-if="candidates.length" class="candidate-list">
        <div v-for="c in candidates" :key="c.ranking_id" class="candidate-card">
          <div class="card-header">
            <div class="candidate-info">
              <h3>{{ c.candidate_ref }}</h3>
              <div class="timestamps">
                <span>Submitted: {{ formatDate(c.submitted_at) }}</span>
                <span v-if="c.evaluated_at">Evaluated: {{ formatDate(c.evaluated_at) }}</span>
              </div>
              <div class="provided-info">
                <span v-if="c.candidate_info?.github">GitHub: <a :href="'https://github.com/' + c.candidate_info.github" target="_blank">{{ c.candidate_info.github }}</a></span>
                <span v-if="c.candidate_info?.scholar_url">Scholar: <a :href="c.candidate_info.scholar_url" target="_blank">Link</a></span>
                <span v-if="c.candidate_info?.name_override">Name Override: {{ c.candidate_info.name_override }}</span>
                <button class="mini resume-btn" @click="downloadResume(c.ranking_id)">Download Resume</button>
              </div>
            </div>
            <div class="status-box">
              <span :class="['status-badge', c.status]">
                {{ c.status === 'evaluating' ? 'LLM Evaluating...' : 'Ready' }}
              </span>
              <span v-if="c.status === 'ready'" class="score">
                {{ c.overall_score.toFixed(0) }}%
              </span>
              <button class="mini re-eval" @click="reEvaluate(c.ranking_id)">Re-evaluate</button>
            </div>
          </div>
          
          <div v-if="c.status === 'ready'" class="results-content">
            <p class="summary">{{ c.summary }}</p>
            <div class="details">
              <span v-for="d in c.dimensions" :key="d.name" class="dim">
                <strong>{{ d.name }}:</strong> {{ d.score }}
                <p class="dim-rationale">{{ d.rationale }}</p>
              </span>
            </div>
          </div>
          <div v-else class="evaluating-placeholder">
            <div class="loader"></div>
            <p>Our AI agents are analyzing the resume, checking background, and calculating scores...</p>
          </div>
        </div>
      </div>
      <p v-else-if="!status">No candidates have applied for this job yet.</p>
    </div>
    <div v-else>
      <p class="hint">Select a job above to see candidate submissions and analysis results.</p>
    </div>
  </div>
</template>

<style scoped>
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.candidate-list { display: flex; flex-direction: column; gap: 1.5rem; }
.candidate-card {
  padding: 1.5rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-card);
}
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 1.5rem; }
.candidate-info h3 { margin: 0 0 0.5rem 0; }
.timestamps { font-size: 0.75rem; color: var(--muted); display: flex; flex-direction: column; gap: 0.2rem; margin-bottom: 0.75rem; }
.provided-info { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.8rem; color: var(--fg); align-items: center; }
.provided-info a { color: var(--ok); text-decoration: none; }
.provided-info a:hover { text-decoration: underline; }
.resume-btn { border-color: var(--ok); color: var(--ok); }

.status-box { display: flex; flex-direction: column; align-items: flex-end; gap: 0.5rem; }

.status-badge { padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: bold; }
.status-badge.evaluating { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f644; }
.status-badge.ready { background: #10b98122; color: #10b981; border: 1px solid #10b98144; }

.score { font-weight: bold; color: var(--ok); font-size: 1.5rem; }
.summary { font-style: italic; color: var(--fg); margin-bottom: 1.5rem; padding-left: 1rem; border-left: 3px solid var(--ok); }
.details { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.dim { font-size: 0.9rem; background: var(--bg); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); }
.dim-rationale { font-size: 0.8rem; color: var(--muted); margin-top: 0.5rem; }

.evaluating-placeholder { display: flex; flex-direction: column; align-items: center; padding: 2rem; color: var(--muted); gap: 1rem; }
.loader {
  border: 3px solid var(--border);
  border-top: 3px solid var(--ok);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.re-eval { font-size: 0.7rem; opacity: 0.7; }
.re-eval:hover { opacity: 1; }

.err { color: var(--err); }
.hint { color: var(--muted); text-align: center; margin-top: 3rem; }
.mini { padding: 0.25rem 0.75rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); cursor: pointer; }
</style>
