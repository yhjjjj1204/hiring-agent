<script setup>
import { ref, onMounted } from 'vue'
import { Briefcase, ChevronRight, Check, Bot, Brain } from 'lucide-vue-next'

const emit = defineEmits(['select-job'])

const jobs = ref([])
const status = ref('')

async function fetchJobs() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/candidate/jobs', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) jobs.value = await res.json()
  } catch (e) {
    status.value = 'Failed to fetch jobs'
  }
}

onMounted(fetchJobs)
</script>

<template>
  <div class="job-list-candidate">
    <div class="page-header-wrap">
      <div class="page-header-titles">
        <h2>Available Positions</h2>
        <p class="page-header-subtitle">Discover roles that match your expertise</p>
      </div>
    </div>

    <div v-if="jobs.length" class="job-grid">
      <div v-for="j in jobs" :key="j.id" class="job-card glass-card" @click="emit('select-job', j)">
        <div class="job-card-header">
          <div class="job-card-title-group">
            <div class="title-with-icon">
              <Briefcase :size="16" class="title-icon" />
              <h4>{{ j.title }}</h4>
            </div>
            <span class="job-card-date">Posted {{ new Date(j.created_at).toLocaleDateString() }}</span>
          </div>
          <div v-if="j.submitted" class="status-badge-outline ok submitted-tag">
            <Check :size="12" />
            Applied
          </div>
        </div>
        <div class="job-card-preview">
           <template v-if="j.summary">
             <div class="ai-summary-indicator"><Bot :size="12" /> AI Summary</div>
             <div v-if="j.summary === 'generating'" class="generating-text-small">
               <Brain :size="12" class="spin-slow" />
               AI summary is generating...
             </div>
             <div v-else>{{ j.summary }}</div>
           </template>
           <template v-else>
             {{ j.description.split('\n')[0].substring(0, 120) }}...
           </template>
        </div>
        <div class="job-card-footer">
          <span class="job-card-type">Full-time</span>
          <span class="job-card-action">
            Apply Now
            <ChevronRight :size="14" />
          </span>
        </div>
      </div>
    </div>

    <div v-else-if="!status" class="empty-state-container glass-card">
      <Briefcase :size="48" class="empty-icon" />
      <h4>No open positions</h4>
      <p>There are no active job listings at this time. Please check back later for new opportunities.</p>
    </div>
    
    <p v-if="status" class="err-msg">{{ status }}</p>
  </div>
</template>

<style scoped>
.job-list-candidate { margin-top: 1rem; animation: fadeIn 0.4s ease-out; }

.title-with-icon { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.2rem; }
.title-icon { color: var(--accent); opacity: 0.8; }
.title-with-icon h4 { margin: 0; }

.submitted-tag { display: flex; align-items: center; gap: 0.3rem; }

.ai-summary-indicator {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.4rem;
}

.generating-text-small {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.8rem;
  font-style: italic;
  color: var(--muted);
}

.spin-slow { animation: spin 3s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

.job-card-action { display: flex; align-items: center; gap: 0.25rem; }

.empty-state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 5rem 2rem;
  text-align: center;
  color: var(--muted);
}
.empty-icon {
  margin-bottom: 1rem;
  opacity: 0.3;
}
.empty-state-container h4 {
  margin: 0 0 0.5rem 0;
  color: var(--headings);
}
.empty-state-container p {
  margin: 0;
  font-size: 0.9rem;
  max-width: 320px;
}

.err-msg { color: var(--err); font-weight: 600; margin-top: 2rem; text-align: center; }

@media (max-width: 600px) {
  .header-group { padding-left: 0; text-align: center; }
}
</style>
