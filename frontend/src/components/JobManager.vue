<script setup>
import { ref, onMounted } from 'vue'
import { Plus, X, Briefcase, ChevronRight } from 'lucide-vue-next'

const emit = defineEmits(['select-job'])

const jobs = ref([])
const showCreate = ref(false)
const newJob = ref({ title: '', description: '' })
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
    <div class="page-header-wrap">
      <div class="page-header-titles">
        <h2>Active Positions</h2>
        <p class="page-header-subtitle">Manage your open roles and review candidates</p>
      </div>
      <button :class="['create-btn', showCreate ? 'secondary' : '']" @click="showCreate = !showCreate">
        <Plus v-if="!showCreate" :size="16" />
        <X v-else :size="16" />
        <span v-if="!showCreate">Add Position</span>
        <span v-else>Close</span>
      </button>
    </div>

    <div v-if="showCreate" class="create-form glass-card">
      <h3>Post a New Position</h3>
      <div class="form-grid">
        <div class="form-group">
          <label>Job Title</label>
          <input v-model="newJob.title" type="text" placeholder="e.g. Senior AI Engineer" />
        </div>
        <div class="form-group">
          <label>Requirements & Description (Markdown)</label>
          <textarea v-model="newJob.description" rows="10" placeholder="Outline the role, expectations, and desired skills..."></textarea>
        </div>
      </div>
      <div class="form-actions">
        <button @click="createJob">Publish Role</button>
        <p v-if="status" class="err-msg">{{ status }}</p>
      </div>
    </div>

    <div class="job-grid">
      <div v-for="j in jobs" :key="j.id" class="job-card glass-card" @click="emit('select-job', j)">
        <div class="job-card-header">
          <div class="job-card-title-group">
            <div class="title-with-icon">
              <Briefcase :size="16" class="title-icon" />
              <h4>{{ j.title }}</h4>
            </div>
            <span class="job-card-date">Posted {{ new Date(j.created_at).toLocaleDateString() }}</span>
          </div>
          <div class="status-badge-outline ok">Active</div>
        </div>
        <div class="job-card-preview">
           {{ j.description.split('\n')[0].substring(0, 120) }}...
        </div>
        <div class="job-card-footer">
          <span class="job-card-type">Corporate</span>
          <span class="job-card-action">
            Manage 
            <ChevronRight :size="14" />
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.job-manager { margin-bottom: 2rem; animation: fadeIn 0.4s ease-out; }

.create-btn { min-width: 130px; }

.create-form { padding: 2rem; margin-bottom: 2.5rem; border-color: var(--glass-border); }
.create-form h3 { margin-bottom: 1.5rem; font-size: 1.25rem; }
.form-grid { display: flex; flex-direction: column; gap: 1.25rem; }

.form-actions { margin-top: 2rem; display: flex; align-items: center; gap: 1.5rem; }
.err-msg { color: var(--err); font-size: 0.9rem; font-weight: 600; }

.title-with-icon { display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.2rem; }
.title-icon { color: var(--accent); opacity: 0.8; }
.title-with-icon h4 { margin: 0; }

.job-card-action { display: flex; align-items: center; gap: 0.25rem; }
</style>
