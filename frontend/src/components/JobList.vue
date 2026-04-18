<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['select-job'])

const jobs = ref([])
const status = ref('')

async function fetchJobs() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/jobs/', {
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
            <h4>{{ j.title }}</h4>
            <span class="job-card-date">Posted {{ new Date(j.created_at).toLocaleDateString() }}</span>
          </div>
          <div v-if="j.submitted" class="status-badge-outline ok">Applied</div>
        </div>
        <div class="job-card-preview">
           {{ j.description.split('\n')[0].substring(0, 120) }}...
        </div>
        <div class="job-card-footer">
          <span class="job-card-type">Full-time</span>
          <span class="job-card-action">Apply Now →</span>
        </div>
      </div>
    </div>

    <div v-else-if="!status" class="empty-state glass-card">
      No open positions at the moment.
    </div>
    
    <p v-if="status" class="err-msg">{{ status }}</p>
  </div>
</template>

<style scoped>
.job-list-candidate { margin-top: 1rem; animation: fadeIn 0.4s ease-out; }

.empty-state { text-align: center; padding: 4rem 2rem; color: var(--muted); }
</style>
