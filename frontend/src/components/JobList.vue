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
    <h3>Available Jobs</h3>
    <div v-if="jobs.length" class="jobs">
      <div v-for="j in jobs" :key="j.id" class="job-card" @click="emit('select-job', j)">
        <div class="card-header">
          <h4>{{ j.title }}</h4>
          <span v-if="j.submitted" class="submitted-tag">Submitted</span>
        </div>
        <p class="date">Posted: {{ new Date(j.created_at).toLocaleDateString() }}</p>
      </div>
    </div>
    <p v-else-if="!status">No open positions at the moment.</p>
    <p v-if="status" class="err">{{ status }}</p>
  </div>
</template>

<style scoped>
.jobs { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem; margin-top: 1.5rem; }
.job-card {
  padding: 1.5rem; background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; cursor: pointer; transition: all 0.2s;
  display: flex; flex-direction: column; gap: 0.5rem;
}
.job-card:hover { transform: translateY(-3px); border-color: var(--ok); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }

.card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; }
.card-header h4 { margin: 0; font-size: 1.1rem; }

.submitted-tag { 
  background: #10b98122; color: #10b981; border: 1px solid #10b98144;
  padding: 0.15rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: bold;
  text-transform: uppercase;
}

.date { font-size: 0.8rem; color: var(--muted); margin: 0; }
.err { color: var(--err); }
</style>
