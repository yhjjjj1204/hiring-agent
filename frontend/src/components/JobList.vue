<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['select-job'])

const jobs = ref([])
const status = ref('')

async function fetchJobs() {
  try {
    const res = await fetch('/jobs/')
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
        <h4>{{ j.title }}</h4>
        <p class="date">Posted: {{ new Date(j.created_at).toLocaleDateString() }}</p>
      </div>
    </div>
    <p v-else-if="!status">No open positions at the moment.</p>
    <p v-if="status" class="err">{{ status }}</p>
  </div>
</template>

<style scoped>
.jobs { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem; margin-top: 1rem; }
.job-card {
  padding: 1.5rem; background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 12px; cursor: pointer; transition: transform 0.2s, border-color 0.2s;
}
.job-card:hover { transform: translateY(-2px); border-color: var(--ok); }
.date { font-size: 0.8rem; color: var(--muted); margin-top: 0.5rem; }
.err { color: var(--err); }
</style>
