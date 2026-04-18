<script setup>
import { ref, onMounted } from 'vue'

const emit = defineEmits(['select-job'])

const jobs = ref([])
const showCreate = ref(false)
const newJob = ref({ title: '', description: '' })
const status = ref('')

async function fetchJobs() {
  try {
    const res = await fetch('/jobs/')
    if (res.ok) jobs.value = await res.json()
  } catch (e) {
    status.value = 'Failed to fetch jobs'
  }
}

async function createJob() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/jobs/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(newJob.value)
    })
    if (res.ok) {
      newJob.value = { title: '', description: '' }
      showCreate.value = false
      fetchJobs()
    } else {
      const data = await res.json()
      status.value = data.detail || 'Failed to create job'
    }
  } catch (e) {
    status.value = e.message
  }
}

onMounted(fetchJobs)
</script>

<template>
  <div class="job-manager">
    <div class="header">
      <h3>Jobs Management</h3>
      <button @click="showCreate = !showCreate">{{ showCreate ? 'Cancel' : 'Create Job' }}</button>
    </div>

    <div v-if="showCreate" class="create-form">
      <div class="form-group">
        <label>Job Title</label>
        <input v-model="newJob.title" type="text" placeholder="e.g. Senior AI Engineer" />
      </div>
      <div class="form-group">
        <label>Description / Requirements</label>
        <textarea v-model="newJob.description" rows="5" placeholder="Minimum 15 characters..."></textarea>
      </div>
      <button @click="createJob">Save Job</button>
      <p v-if="status" class="err">{{ status }}</p>
    </div>

    <div class="job-list">
      <div v-for="j in jobs" :key="j.id" class="job-item" @click="emit('select-job', j)">
        <div class="job-info">
          <strong>{{ j.title }}</strong>
          <span class="date">{{ new Date(j.created_at).toLocaleDateString() }}</span>
        </div>
        <button class="mini">View Candidates</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.job-manager { margin-bottom: 2rem; }
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.create-form { background: var(--bg-card); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 1rem; }
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; }
input, textarea { width: 100%; padding: 0.5rem; background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: 4px; }
.job-list { display: flex; flex-direction: column; gap: 0.5rem; }
.job-item {
  display: flex; justify-content: space-between; align-items: center;
  padding: 0.75rem 1rem; background: var(--bg-card); border: 1px solid var(--border);
  border-radius: 8px; cursor: pointer; transition: border-color 0.2s;
}
.job-item:hover { border-color: var(--ok); }
.job-info { display: flex; flex-direction: column; }
.date { font-size: 0.8rem; color: var(--muted); }
.mini { padding: 0.2rem 0.6rem; font-size: 0.75rem; }
.err { color: var(--err); font-size: 0.8rem; margin-top: 0.5rem; }
</style>
