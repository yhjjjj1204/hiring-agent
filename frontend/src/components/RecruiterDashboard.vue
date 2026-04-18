<script setup>
import { ref, onMounted, watch } from 'vue'
import JobManager from './JobManager.vue'

const selectedJob = ref(null)
const candidates = ref([])
const status = ref('')

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

function onSelectJob(job) {
  selectedJob.value = job
}

watch(selectedJob, fetchCandidates)
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
            <h3>{{ c.candidate_ref }}</h3>
            <span class="score">Score: {{ (c.overall_score * 100).toFixed(0) }}%</span>
          </div>
          <p class="summary">{{ c.summary }}</p>
          <div class="details">
            <span v-for="d in c.dimensions" :key="d.name" class="dim">
              {{ d.name }}: {{ d.score }}
            </span>
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
.candidate-list { display: flex; flex-direction: column; gap: 1rem; }
.candidate-card {
  padding: 1.5rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-card);
}
.card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.score { font-weight: bold; color: var(--ok); font-size: 1.2rem; }
.summary { font-style: italic; color: var(--muted); margin-bottom: 1rem; }
.details { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.dim { font-size: 0.8rem; background: var(--bg); padding: 0.2rem 0.5rem; border-radius: 4px; border: 1px solid var(--border); }
.err { color: var(--err); }
.hint { color: var(--muted); text-align: center; margin-top: 3rem; }
.mini { padding: 0.25rem 0.75rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); }
</style>
