<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { marked } from 'marked'
import JobManager from './JobManager.vue'
import CandidateSnapshot from './CandidateSnapshot.vue'

const selectedJob = ref(null)
const selectedCandidate = ref(null)
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
      if (selectedCandidate.value) {
        const updated = data.items.find(c => c.ranking_id === selectedCandidate.value.ranking_id)
        if (updated) selectedCandidate.value = updated
      }
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
  selectedCandidate.value = null
  status.value = ''
  isEditingJob.value = false
  isJobExpanded.value = false
}

function selectCandidate(candidate) {
  selectedCandidate.value = candidate
  window.scrollTo(0, 0)
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
  selectedCandidate.value = null
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
    <!-- 1. JOB LIST VIEW -->
    <div v-if="!selectedJob">
      <JobManager @select-job="onSelectJob" />
    </div>

    <!-- 2. CANDIDATE LIST VIEW (FOR A JOB) -->
    <div v-else-if="!selectedCandidate" class="results-page">
      <div class="results-header">
        <div class="title-area">
          <button class="mini back-btn" @click="selectedJob = null">← Jobs</button>
          <h2>{{ selectedJob.title }} <small>Candidates</small></h2>
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
        
        <div v-if="candidates.length" class="candidate-grid">
          <div v-for="c in candidates" :key="c.ranking_id" class="candidate-entry-card" @click="selectCandidate(c)">
            <div class="entry-header">
              <div class="entry-main">
                <h3>{{ c.candidate_ref }}</h3>
                <span :class="['status-badge', c.status]">
                  {{ c.status === 'evaluating' ? 'Evaluating...' : 'Ready' }}
                </span>
              </div>
              <div v-if="c.status === 'ready'" class="entry-score">
                {{ c.overall_score.toFixed(0) }}%
              </div>
            </div>
            
            <p class="entry-summary">{{ c.summary }}</p>
            
            <div v-if="c.status === 'ready'" class="entry-dimensions">
              <div v-for="d in c.dimensions" :key="d.name" class="dim-mini">
                <span class="dim-name">{{ d.name }}</span>
                <span class="dim-val">{{ d.score }}</span>
              </div>
            </div>
            
            <div class="entry-footer">
              <span class="entry-ts">{{ formatDate(c.submitted_at) }}</span>
              <span class="view-link">View Details →</span>
            </div>
          </div>
        </div>
        <p v-else-if="!status" class="empty-msg">No candidates have applied for this job yet.</p>
      </div>
    </div>

    <!-- 3. INDIVIDUAL CANDIDATE PAGE -->
    <div v-else class="candidate-page">
      <div class="page-header">
        <div class="title-area">
          <button class="mini back-btn" @click="selectedCandidate = null">← Candidates</button>
          <div class="candidate-title">
            <h2>{{ selectedCandidate.candidate_ref }}</h2>
            <span :class="['status-badge', selectedCandidate.status]">{{ selectedCandidate.status }}</span>
          </div>
        </div>
        <div class="header-actions">
           <button class="mini resume-btn" @click="downloadResume(selectedCandidate.ranking_id)">Download Resume</button>
           <button class="mini re-eval" @click="reEvaluate(selectedCandidate.ranking_id)">Re-evaluate</button>
        </div>
      </div>

      <div class="candidate-provided-meta">
          <span v-if="selectedCandidate.candidate_info?.github">GitHub: <a :href="'https://github.com/' + selectedCandidate.candidate_info.github" target="_blank">{{ selectedCandidate.candidate_info.github }}</a></span>
          <span v-if="selectedCandidate.candidate_info?.scholar_url">Scholar: <a :href="selectedCandidate.candidate_info.scholar_url" target="_blank">Link</a></span>
          <span v-if="selectedCandidate.candidate_info?.name_override">Name Override: {{ selectedCandidate.candidate_info.name_override }}</span>
          <span>Submitted: {{ formatDate(selectedCandidate.submitted_at) }}</span>
      </div>

      <div class="dual-pane">
        <!-- Left: Structured Data (Takes more space) -->
        <div class="pane pane-left">
          <div class="pane-header">
            <h3>Structured Resume Data</h3>
            <p>Objective facts extracted from the resume</p>
          </div>
          <div class="pane-content">
            <CandidateSnapshot :arranged-resume="selectedCandidate.arranged_resume" />
          </div>
        </div>

        <!-- Right: Analysis (Takes less space) -->
        <div class="pane pane-right">
          <div class="pane-header">
            <h3>LLM Analysis Results</h3>
            <p>Subjective evaluation and scoring</p>
          </div>
          <div class="pane-content">
            <div v-if="selectedCandidate.status === 'ready'">
              <div class="overall-result">
                <div class="big-score">{{ selectedCandidate.overall_score.toFixed(0) }}%</div>
                <p class="summary">{{ selectedCandidate.summary }}</p>
              </div>
              
              <div class="details-list">
                <div v-for="d in selectedCandidate.dimensions" :key="d.name" class="detail-item">
                  <div class="detail-header">
                    <strong>{{ d.name }}</strong>
                    <span class="detail-score">{{ d.score }}</span>
                  </div>
                  <p class="detail-rationale">{{ d.rationale }}</p>
                </div>
              </div>
            </div>
            <div v-else class="evaluating-placeholder">
              <div class="loader"></div>
              <p>Evaluating candidate background and resume...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Page Transitions */
.results-page, .candidate-page { animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

/* Shared */
.back-btn { background: var(--bg-card); border-color: var(--border); padding: 0.4rem 0.8rem; margin-right: 1rem; }
.status-badge { padding: 0.2rem 0.5rem; border-radius: 20px; font-size: 0.7rem; font-weight: bold; width: fit-content; }
.status-badge.evaluating { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f644; }
.status-badge.ready { background: #10b98122; color: #10b981; border: 1px solid #10b98144; }

/* Candidate Grid (Main Entry) */
.candidate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(400px, 1fr)); gap: 1.25rem; }
.candidate-entry-card { 
  background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; 
  cursor: pointer; transition: all 0.2s; display: flex; flex-direction: column; gap: 0.75rem;
}
.candidate-entry-card:hover { border-color: var(--ok); transform: translateY(-3px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }

.entry-header { display: flex; justify-content: space-between; align-items: flex-start; }
.entry-main { display: flex; flex-direction: column; gap: 0.25rem; }
.entry-main h3 { margin: 0; font-size: 1.1rem; }
.entry-score { font-size: 1.5rem; font-weight: bold; color: var(--ok); line-height: 1; }

.entry-summary { font-size: 0.9rem; color: var(--muted); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; line-height: 1.4; }

.entry-dimensions { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-mini { background: var(--bg); border: 1px solid var(--border); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.7rem; display: flex; gap: 0.35rem; }
.dim-val { color: var(--ok); font-weight: bold; }

.entry-footer { margin-top: auto; display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border); padding-top: 0.75rem; font-size: 0.75rem; color: var(--muted); }
.view-link { color: var(--ok); font-weight: bold; }

/* Candidate Individual Page */
.candidate-page { display: flex; flex-direction: column; gap: 1rem; }
.page-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
.candidate-title { display: flex; align-items: center; gap: 0.75rem; }
.candidate-title h2 { margin: 0; font-size: 1.5rem; }

.candidate-provided-meta { display: flex; gap: 1.25rem; font-size: 0.85rem; color: var(--muted); padding: 0 0.25rem; }
.candidate-provided-meta a { color: var(--ok); text-decoration: none; }

.dual-pane { display: grid; grid-template-columns: 1.6fr 1fr; gap: 2rem; align-items: start; }
.pane { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; overflow: hidden; display: flex; flex-direction: column; }
.pane-header { padding: 1.25rem 1.5rem; border-bottom: 1px solid var(--border); background: rgba(255,255,255,0.02); }
.pane-header h3 { margin: 0 0 0.25rem 0; font-size: 1.1rem; }
.pane-header p { margin: 0; font-size: 0.8rem; color: var(--muted); }
.pane-content { padding: 1.5rem; }

.overall-result { margin-bottom: 1.5rem; text-align: center; background: var(--bg); padding: 1.25rem; border-radius: 10px; border: 1px solid var(--border); }
.big-score { font-size: 3rem; font-weight: bold; color: var(--ok); margin-bottom: 0.5rem; }
.summary { font-size: 1rem; font-style: italic; color: var(--fg); line-height: 1.5; }

.details-list { display: flex; flex-direction: column; gap: 1rem; }
.detail-item { background: var(--bg); padding: 1.25rem; border-radius: 10px; border: 1px solid var(--border); }
.detail-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.detail-score { color: var(--ok); font-weight: bold; font-size: 1rem; }
.detail-rationale { font-size: 0.9rem; color: var(--muted); line-height: 1.5; }

/* Job Section in List View */
.results-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.title-area { display: flex; align-items: center; gap: 0.75rem; }
.title-area h2 { font-size: 1.4rem; margin: 0; }
.title-area h2 small { color: var(--muted); font-weight: normal; margin-left: 0.4rem; }
.header-actions { display: flex; gap: 0.75rem; }

.re-eval-all { border-color: #f59e0b; color: #f59e0b; }
.resume-btn { border-color: var(--ok); color: var(--ok); }
.re-eval { opacity: 0.7; }

.job-preview-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; margin-bottom: 2rem; }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.preview-header h3 { margin: 0; font-size: 1.1rem; }
.description-content { max-height: 200px; overflow: hidden; position: relative; mask-image: linear-gradient(to bottom, black 60%, transparent 100%); transition: max-height 0.3s ease; }
.description-content.expanded { max-height: 5000px; mask-image: none; }
.text-btn { background: none; border: none; color: var(--ok); cursor: pointer; padding: 0.75rem 0; font-size: 0.9rem; font-weight: bold; }

.job-edit-form input, .job-edit-form textarea { width: 100%; padding: 0.75rem; background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: 8px; font-size: 0.95rem; }

.candidates-section { margin-top: 1.5rem; }
.section-header { margin-bottom: 1rem; border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }
.section-header h3 { margin: 0; font-size: 1.1rem; }

.evaluating-placeholder { display: flex; flex-direction: column; align-items: center; padding: 2.5rem; color: var(--muted); gap: 1.25rem; }
.loader { border: 4px solid var(--border); border-top: 4px solid var(--ok); border-radius: 50%; width: 32px; height: 32px; animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 1rem; margin-bottom: 0.75rem; font-size: 1.1rem; }
.markdown-body :deep(p) { margin-bottom: 0.75rem; }
.markdown-body :deep(ul) { padding-left: 1.25rem; margin-bottom: 0.75rem; }

.mini { padding: 0.35rem 0.75rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); cursor: pointer; border-radius: 4px; }
</style>
