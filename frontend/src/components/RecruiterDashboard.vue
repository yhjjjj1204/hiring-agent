<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { marked } from 'marked'
import JobManager from './JobManager.vue'

const selectedJob = ref(null)
const candidates = ref([])
const status = ref('')
let pollInterval = null

// Job editing and preview state
const isEditingJob = ref(false)
const isJobExpanded = ref(false)
const editJobData = reactive({ title: '', description: '' })
const jobStatus = ref('')

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

async function reEvaluateAll() {
  if (!selectedJob.value || !confirm('Re-evaluate all candidates for this job?')) return
  
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/analyze/re-evaluate-all/${selectedJob.value.id}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      fetchCandidates()
    }
  } catch (e) {
    console.error('Re-evaluation all failed', e)
  }
}

function downloadResume(rankingId) {
  const token = localStorage.getItem('token')
  window.open(`/analyze/resume/${rankingId}?token=${token}`, '_blank')
}

function onSelectJob(job) {
  selectedJob.value = job
  status.value = ''
  isEditingJob.value = false
  isJobExpanded.value = false
}

function startEditJob() {
  editJobData.title = selectedJob.value.title
  editJobData.description = selectedJob.value.description
  isEditingJob.value = true
}

async function saveJobUpdate() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/jobs/${selectedJob.value.id}`, {
      method: 'PATCH',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}` 
      },
      body: JSON.stringify(editJobData)
    })
    const data = await res.json()
    if (res.ok) {
      selectedJob.value = data
      isEditingJob.value = false
      jobStatus.value = ''
    } else {
      jobStatus.value = data.detail || 'Update failed'
    }
  } catch (e) {
    jobStatus.value = e.message
  }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

function reset() {
  selectedJob.value = null
}

defineExpose({ reset })

watch(selectedJob, (newJob) => {
  if (newJob) {
    fetchCandidates()
    if (!pollInterval) {
      pollInterval = setInterval(fetchCandidates, 5000)
    }
  } else {
    if (pollInterval) {
      clearInterval(pollInterval)
      pollInterval = null
    }
  }
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div class="dashboard">
    <div v-if="!selectedJob">
      <JobManager @select-job="onSelectJob" />
    </div>

    <div v-else class="results-page">
      <div class="results-header">
        <div class="title-area">
          <button class="mini back-btn" @click="selectedJob = null">← Jobs</button>
          <h2>{{ selectedJob.title }} <small>Dashboard</small></h2>
        </div>
        <div class="header-actions">
          <button class="mini re-eval-all" @click="reEvaluateAll">Re-evaluate All</button>
        </div>
      </div>

      <!-- Job Preview/Edit Section -->
      <div class="job-preview-card">
        <div v-if="!isEditingJob">
          <div class="preview-header">
            <h3>Job Details</h3>
            <button class="mini" @click="startEditJob">Edit Job</button>
          </div>
          <div :class="['description-content', { 'expanded': isJobExpanded }]">
            <div class="markdown-body" v-html="renderMarkdown(selectedJob.description)"></div>
          </div>
          <button class="text-btn" @click="isJobExpanded = !isJobExpanded">
            {{ isJobExpanded ? 'Show Less' : 'Show More' }}
          </button>
        </div>
        <div v-else class="job-edit-form">
          <h3>Edit Job Posting</h3>
          <div class="form-group">
            <label>Title</label>
            <input v-model="editJobData.title" type="text" />
          </div>
          <div class="form-group">
            <label>Description (Markdown)</label>
            <textarea v-model="editJobData.description" rows="10"></textarea>
          </div>
          <div class="form-actions">
            <button @click="saveJobUpdate">Save Changes</button>
            <button class="secondary" @click="isEditingJob = false">Cancel</button>
          </div>
          <p v-if="jobStatus" class="err">{{ jobStatus }}</p>
        </div>
      </div>
      
      <div class="candidates-section">
        <div class="section-header">
          <h3>Candidates ({{ candidates.length }})</h3>
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
                <div v-for="d in c.dimensions" :key="d.name" class="dim">
                  <div class="dim-header">
                    <strong>{{ d.name }}</strong>
                    <span class="dim-score">{{ d.score }}</span>
                  </div>
                  <p class="dim-rationale">{{ d.rationale }}</p>
                </div>
              </div>
            </div>
            <div v-else class="evaluating-placeholder">
              <div class="loader"></div>
              <p>Our AI agents are analyzing the resume, checking background, and calculating scores...</p>
            </div>
          </div>
        </div>
        <p v-else-if="!status" class="empty-msg">No candidates have applied for this job yet.</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.results-page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; }
.title-area { display: flex; align-items: center; gap: 1rem; }
.title-area h2 small { color: var(--muted); font-weight: normal; margin-left: 0.5rem; }
.header-actions { display: flex; gap: 0.5rem; }

.back-btn { background: var(--bg-card); border-color: var(--border); padding: 0.4rem 0.8rem; }
.re-eval-all { border-color: #f59e0b; color: #f59e0b; }

.job-preview-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem; }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.description-content { max-height: 200px; overflow: hidden; position: relative; mask-image: linear-gradient(to bottom, black 50%, transparent 100%); transition: max-height 0.3s ease; }
.description-content.expanded { max-height: 2000px; mask-image: none; }
.text-btn { background: none; border: none; color: var(--ok); cursor: pointer; padding: 0.5rem 0; font-size: 0.9rem; font-weight: bold; }
.text-btn:hover { text-decoration: underline; }

.job-edit-form .form-group { margin-bottom: 1rem; }
.job-edit-form label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; }
.job-edit-form input, .job-edit-form textarea { width: 100%; padding: 0.75rem; background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: 8px; }
.form-actions { display: flex; gap: 1rem; margin-top: 1.5rem; }
.secondary { background: transparent; border: 1px solid var(--border); }

.candidates-section { margin-top: 3rem; }
.section-header { margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; }

.candidate-list { display: flex; flex-direction: column; gap: 2rem; }
.candidate-card {
  padding: 2rem;
  border: 1px solid var(--border);
  border-radius: 16px;
  background: var(--bg-card);
  box-shadow: 0 4px 20px rgba(0,0,0,0.1);
}
.card-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; }
.candidate-info h3 { margin: 0 0 0.5rem 0; font-size: 1.4rem; }
.timestamps { font-size: 0.8rem; color: var(--muted); display: flex; gap: 1.5rem; margin-bottom: 1rem; }
.provided-info { display: flex; flex-wrap: wrap; gap: 1rem; font-size: 0.85rem; color: var(--fg); align-items: center; }
.provided-info a { color: var(--ok); text-decoration: none; }
.provided-info a:hover { text-decoration: underline; }
.resume-btn { border-color: var(--ok); color: var(--ok); }

.status-box { display: flex; flex-direction: column; align-items: flex-end; gap: 0.75rem; }

.status-badge { padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: bold; }
.status-badge.evaluating { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f644; }
.status-badge.ready { background: #10b98122; color: #10b981; border: 1px solid #10b98144; }

.score { font-weight: bold; color: var(--ok); font-size: 2rem; line-height: 1; }
.summary { font-size: 1.1rem; color: var(--fg); margin-bottom: 2rem; padding: 1rem; background: var(--bg); border-radius: 8px; border-left: 4px solid var(--ok); }

.details { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.dim { font-size: 0.95rem; background: var(--bg); padding: 1.25rem; border-radius: 12px; border: 1px solid var(--border); }
.dim-header { display: flex; justify-content: space-between; margin-bottom: 0.75rem; }
.dim-score { font-weight: bold; color: var(--ok); }
.dim-rationale { font-size: 0.85rem; color: var(--muted); line-height: 1.5; }

.evaluating-placeholder { display: flex; flex-direction: column; align-items: center; padding: 3rem; color: var(--muted); gap: 1.5rem; }
.loader {
  border: 4px solid var(--border);
  border-top: 4px solid var(--ok);
  border-radius: 50%;
  width: 32px;
  height: 32px;
  animation: spin 1s linear infinite;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.re-eval { font-size: 0.75rem; opacity: 0.6; }
.re-eval:hover { opacity: 1; }

.empty-msg { text-align: center; padding: 4rem; color: var(--muted); background: var(--bg-card); border-radius: 16px; border: 1px dashed var(--border); }
.err { color: var(--err); background: #7f1d1d22; padding: 1rem; border-radius: 8px; border: 1px solid #7f1d1d44; }
.mini { padding: 0.25rem 0.75rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); cursor: pointer; border-radius: 4px; }

.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 1rem; margin-bottom: 0.5rem; font-size: 1.1rem; }
.markdown-body :deep(p) { margin-bottom: 0.5rem; }
.markdown-body :deep(ul) { padding-left: 1.2rem; margin-bottom: 0.5rem; }
</style>
