<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { marked } from 'marked'
import { 
  ChevronLeft, 
  ChevronRight, 
  RotateCw, 
  Download, 
  RefreshCw,
  CheckCircle,
  Users,
  Bot,
  Brain,
  Edit3
} from 'lucide-vue-next'
import JobManager from './JobManager.vue'
import CandidateSnapshot from './CandidateSnapshot.vue'

const props = defineProps(['modelValue']) // Kept for compatibility if needed
const emit = defineEmits(['context-change'])

const route = useRoute()
const router = useRouter()

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
    const res = await fetch(`/api/recruiter/rankings?job_id=${selectedJob.value.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    if (res.ok) {
      const items = data.items || []
      candidates.value = items
      
      // Sync candidate object from URL if on detail page
      if (route.params.candidate_id) {
         const cand = items.find(c => c.ranking_id === route.params.candidate_id)
         if (cand) selectedCandidate.value = cand
      }
    } else {
      status.value = data.detail || 'Failed to fetch'
    }
  } catch (e) {
    status.value = e.message
  }
}

async function fetchJob(jobId) {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/api/recruiter/jobs/${jobId}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      selectedJob.value = data
    } else if (res.status === 404) {
      router.push({ name: 'NotFound' })
    }
  } catch (e) { console.error("Fetch job failed", e) }
}

async function reEvaluate(rankingId) {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/api/recruiter/re-evaluate/${rankingId}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) fetchCandidates()
  } catch (e) { console.error(e) }
}

async function reEvaluateAll() {
  if (!selectedJob.value || !confirm('Re-evaluate all candidates for this job?')) return
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/api/recruiter/re-evaluate-all/${selectedJob.value.id}`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) fetchCandidates()
  } catch (e) { console.error(e) }
}

function downloadResume(rankingId) {
  const token = localStorage.getItem('token')
  window.open(`/api/recruiter/resume/${rankingId}?token=${token}`, '_blank')
}

// Navigation methods update the URL
function onSelectJob(job) {
  router.push(`/jobs/${job.id}`)
}

function selectCandidate(candidate) {
  router.push(`/jobs/${selectedJob.value.id}/candidates/${candidate.ranking_id}`)
}

function goBackToJobs() {
  router.push('/')
}

function goBackToCandidates() {
  router.push(`/jobs/${selectedJob.value.id}`)
}

function startEditJob() {
  editJobData.title = selectedJob.value.title
  editJobData.description = selectedJob.value.description
  isEditingJob.value = true
}

async function saveJobUpdate() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/api/recruiter/jobs/${selectedJob.value.id}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(editJobData)
    })
    if (res.ok) {
      selectedJob.value = await res.json()
      isEditingJob.value = false
    }
  } catch (e) { console.error(e) }
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString()
}

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}

// SYNC STATE WITH URL (SINGLE SOURCE OF TRUTH)
watch(() => route.params, async (params) => {
  const { job_id, candidate_id } = params
  
  if (!job_id) {
    selectedJob.value = null
    selectedCandidate.value = null
    candidates.value = []
    emit('context-change', { job: null, job_id: null, candidate: null, candidate_id: null })
    return
  }
  
  // 1. Load Job if needed
  if (!selectedJob.value || selectedJob.value.id !== job_id) {
    await fetchJob(job_id)
  }
  
  // 2. Load Candidates if needed
  if (selectedJob.value && candidates.value.length === 0) {
    await fetchCandidates()
  }
  
  // 3. Sync Candidate Detail
  if (candidate_id) {
    const cand = candidates.value.find(c => c.ranking_id === candidate_id)
    if (cand) {
      selectedCandidate.value = cand
      emit('context-change', { 
        job: selectedJob.value?.title, 
        job_id: selectedJob.value?.id, 
        candidate: cand.candidate_ref, 
        candidate_id: cand.ranking_id 
      })
    }
  } else {
    selectedCandidate.value = null
    if (selectedJob.value) {
      emit('context-change', { job: selectedJob.value.title, job_id: selectedJob.value.id, candidate: null, candidate_id: null })
    }
  }
}, { immediate: true, deep: true })

// Polling
watch(selectedJob, (newJob) => {
  if (newJob) {
    if (!pollInterval) pollInterval = setInterval(fetchCandidates, 5000)
  } else if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
})

onUnmounted(() => { if (pollInterval) clearInterval(pollInterval) })

function reset() {
  router.push('/')
}

defineExpose({ reset, onSelectJob, selectCandidate })
</script>

<template>
  <div class="dashboard">
    <!-- 1. JOB LIST VIEW -->
    <div v-if="!selectedJob">
      <JobManager @select-job="onSelectJob" />
    </div>

    <!-- 2. CANDIDATE LIST VIEW (FOR A JOB) -->
    <div v-else-if="!selectedCandidate" class="results-page">
      <div class="job-header-bar">
        <button class="mini secondary" @click="goBackToJobs"><ChevronLeft :size="14" /> Back</button>
        <h2 class="job-title">{{ selectedJob.title }}</h2>
      </div>

      <div class="job-desc-readonly glass-card">
        <div v-if="!isEditingJob">
          <div class="preview-header">
            <label>Job Requirements</label>
            <button class="mini secondary" @click="startEditJob"><Edit3 :size="14" /> Edit Profile</button>
          </div>
          <div v-if="selectedJob.summary" class="ai-summary-box">
            <div class="summary-label"><Bot :size="12" /> AI Summary</div>
            <p v-if="selectedJob.summary === 'generating'" class="generating-text">
              <Brain :size="14" class="spin-slow" />
              AI summary is generating...
            </p>
            <p v-else>{{ selectedJob.summary }}</p>
          </div>
          <div :class="['description-content', { 'expanded': isJobExpanded }]">
            <div class="markdown-body" v-html="renderMarkdown(selectedJob.description)"></div>
          </div>
          <button class="text-btn" @click="isJobExpanded = !isJobExpanded">
            {{ isJobExpanded ? 'Show Less' : 'Show Full Requirements' }}
          </button>
        </div>
        <div v-else class="job-edit-form">
          <div class="form-grid">
            <div class="form-group"><label>Title</label><input v-model="editJobData.title" /></div>
            <div class="form-group"><label>Description</label><textarea v-model="editJobData.description" rows="12"></textarea></div>
          </div>
          <div class="form-actions">
            <button @click="saveJobUpdate">Update Job</button>
            <button class="secondary" @click="isEditingJob = false">Cancel</button>
          </div>
        </div>
      </div>
      
      <div class="candidates-section">
        <div class="section-header">
          <h3>Applications <span class="count-badge">{{ candidates.length }}</span></h3>
          <button v-if="candidates.length" class="mini secondary warn" @click="reEvaluateAll">
            <RotateCw :size="14" />
            Re-evaluate All
          </button>
        </div>

        <p v-if="status" class="err-banner">{{ status }}</p>
        
        <div v-if="candidates.length" class="candidate-grid">
          <div v-for="c in candidates" :key="c.ranking_id" class="candidate-entry-card glass-card" @click="selectCandidate(c)">
            <div class="entry-header">
              <div class="entry-main">
                <h4 class="cand-name">{{ c.candidate_ref }}</h4>
                <div :class="['status-pill', c.status]"><span class="status-dot"></span>{{ c.status }}</div>
              </div>
              <div v-if="c.status === 'ready'" class="entry-score">
                <span class="score-val">{{ c.overall_score.toFixed(0) }}</span>
                <span class="score-label">MATCH</span>
              </div>
            </div>
            <p class="entry-summary">{{ c.summary }}</p>
            <div v-if="c.status === 'ready'" class="entry-dimensions">
              <div v-for="d in c.dimensions.slice(0, 4)" :key="d.name" class="dim-pill">
                <span class="dim-name">{{ d.name }}</span>
                <span class="dim-val">{{ d.score }}</span>
              </div>
            </div>
            <div class="entry-footer">
              <div class="entry-ts">{{ formatDate(c.submitted_at).split(',')[0] }}</div>
              <div class="view-details">Details <ChevronRight :size="14" /></div>
            </div>
          </div>
        </div>
        <div v-else-if="!status" class="empty-state-container glass-card">
          <Users :size="48" class="empty-icon" />
          <h4>No applications yet</h4>
          <p>When candidates apply for this position, they will appear here for your review.</p>
        </div>
      </div>
    </div>

    <!-- 3. INDIVIDUAL CANDIDATE PAGE -->
    <div v-else class="candidate-page">
      <div class="page-header">
        <div class="title-area">
          <button class="mini secondary" @click="goBackToCandidates"><ChevronLeft :size="14" /> Back</button>
          <div class="candidate-title">
            <h2 class="cand-page-name">{{ selectedCandidate.candidate_ref }}</h2>
            <div :class="['status-pill large', selectedCandidate.status]"><span class="status-dot"></span>{{ selectedCandidate.status }}</div>
          </div>
        </div>
        <div class="header-actions">
           <button class="secondary action-btn" @click="downloadResume(selectedCandidate.ranking_id)">
             <Download :size="14" />
             Download CV
           </button>
           <button class="secondary warn action-btn" @click="reEvaluate(selectedCandidate.ranking_id)">
             <RotateCw :size="14" />
             Re-evaluate
           </button>
        </div>
      </div>

      <div class="candidate-meta-bar glass-card">
          <div v-if="selectedCandidate.candidate_info?.github" class="meta-item">
            <label>GitHub</label>
            <a :href="'https://github.com/' + selectedCandidate.candidate_info.github" target="_blank">@{{ selectedCandidate.candidate_info.github }}</a>
          </div>
          <div v-if="selectedCandidate.candidate_info?.scholar_url" class="meta-item">
             <label>Academic</label>
             <a :href="selectedCandidate.candidate_info.scholar_url" target="_blank">Scholar Profile</a>
          </div>
          <div v-if="selectedCandidate.candidate_info?.name_override" class="meta-item">
             <label>Legal Name</label>
             <span>{{ selectedCandidate.candidate_info.name_override }}</span>
          </div>
          <div class="meta-item">
             <label>Applied</label>
             <span>{{ formatDate(selectedCandidate.submitted_at) }}</span>
          </div>
      </div>

      <div class="dual-pane">
        <div class="pane pane-left glass-card">
          <div class="pane-header"><h3>Structured Experience</h3></div>
          <div class="pane-content"><CandidateSnapshot :arranged-resume="selectedCandidate.arranged_resume" /></div>
        </div>
        <div class="pane pane-right glass-card">
          <div class="pane-header"><h3>Match Evaluation</h3></div>
          <div class="pane-content">
            <div v-if="selectedCandidate.status === 'ready'">
              <div class="overall-result">
                <div class="big-score">{{ selectedCandidate.overall_score.toFixed(0) }}<small>%</small></div>
                <div class="analysis-summary">{{ selectedCandidate.summary }}</div>
              </div>
              <div class="details-list">
                <div v-for="d in selectedCandidate.dimensions" :key="d.name" class="detail-item glass-card">
                  <div class="detail-header"><strong>{{ d.name }}</strong><span class="detail-score">{{ d.score }}</span></div>
                  <div class="detail-rationale">{{ d.rationale }}</div>
                </div>
              </div>
            </div>
            <div v-else class="evaluating-placeholder"><RefreshCw class="loader spin" :size="48" /><p>Evaluating...</p></div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { animation: fadeIn 0.4s ease-out; }
.job-header-bar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1rem; }
.job-title { margin: 0; font-size: 1.6rem; flex-grow: 1; }
.job-desc-readonly { padding: 1.25rem; margin-bottom: 2rem; }
.preview-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.description-content { max-height: 150px; overflow: hidden; position: relative; }
.description-content.expanded { max-height: none; }
.text-btn { font-size: 0.85rem; color: var(--accent); cursor: pointer; background: none; border: none; font-weight: 700; padding: 0.5rem 0; }

.ai-summary-box {
  background: rgba(var(--accent-rgb), 0.05);
  border: 1px solid rgba(var(--accent-rgb), 0.2);
  border-radius: 8px;
  padding: 1rem;
  margin-bottom: 1.5rem;
}
.summary-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--accent);
  margin-bottom: 0.5rem;
}
.ai-summary-box p {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
  font-style: italic;
  color: white;
}
.generating-text {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--muted) !important;
}

.form-grid { display: flex; flex-direction: column; gap: 1.25rem; }
.form-actions { margin-top: 1.5rem; display: flex; gap: 0.5rem; }

.candidate-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); gap: 1.25rem; }
.candidate-entry-card { padding: 1.5rem; cursor: pointer; display: flex; flex-direction: column; gap: 1rem; }
.entry-header { display: flex; justify-content: space-between; align-items: flex-start; }
.entry-main { display: flex; align-items: center; gap: 0.75rem; }
.cand-name { font-size: 1.15rem; margin: 0; }
.score-val { display: block; font-size: 1.4rem; font-weight: 700; color: var(--ok); line-height: 1; }
.score-label { font-size: 0.6rem; color: var(--muted); font-weight: 700; }
.entry-summary { font-size: 0.9rem; color: var(--muted); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.entry-dimensions { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-pill { background: var(--bg); border: 1px solid var(--border); padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.7rem; display: flex; gap: 0.4rem; }
.dim-val { color: var(--ok); font-weight: 700; }
.entry-footer { margin-top: auto; display: flex; justify-content: space-between; align-items: center; padding-top: 0.75rem; border-top: 1px solid var(--border); }
.view-details { color: var(--accent); font-weight: 700; font-size: 0.85rem; display: flex; align-items: center; gap: 0.2rem; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
.header-actions { display: flex; gap: 0.75rem; align-items: center; }
.action-btn { padding: 0.6rem 1rem; font-size: 0.85rem; font-weight: 700; }
.title-area { display: flex; align-items: center; gap: 1.25rem; }
.candidate-title { display: flex; align-items: center; gap: 1rem; }
.cand-page-name { margin: 0; font-size: 1.8rem; }
.candidate-meta-bar { display: flex; gap: 4rem; padding: 1.25rem 2rem; margin-bottom: 2rem; }
.meta-item { display: flex; flex-direction: column; gap: 0.25rem; }
.meta-item label { margin: 0; color: var(--muted); font-size: 0.65rem; font-weight: 800; text-transform: uppercase; }
.meta-item a { color: var(--accent); font-weight: 600; text-decoration: none; font-size: 0.9rem; }

.dual-pane { display: grid; grid-template-columns: 1.6fr 1fr; gap: 1.5rem; }
.pane-header { padding: 1rem 1.5rem; border-bottom: 1px solid var(--border); }
.pane-content { padding: 1.5rem; }

.overall-result { text-align: center; background: var(--bg); padding: 1.5rem; border-radius: 4px; margin-bottom: 2rem; border: 1px solid var(--border); }
.big-score { font-size: 3.5rem; font-weight: 700; color: var(--ok); line-height: 1; }
.big-score small { font-size: 1.2rem; margin-left: 2px; }
.analysis-summary { font-size: 1rem; line-height: 1.6; font-style: italic; margin-top: 1rem; opacity: 0.9; }

.detail-item { padding: 1.25rem; margin-bottom: 1rem; }
.detail-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.detail-score { color: var(--ok); font-weight: 800; }
.detail-rationale { font-size: 0.9rem; color: var(--muted); line-height: 1.5; }

.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; }
.count-badge { background: var(--accent); color: white; padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.75rem; margin-left: 0.5rem; }

.status-pill { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; border: 1px solid var(--border); background: var(--bg); }
.status-pill.ready { color: var(--ok); border-color: var(--ok); }
.status-pill.evaluating { color: var(--accent); border-color: var(--accent); }
.status-pill.large { padding: 0.3rem 0.6rem; font-size: 0.75rem; }

.empty-state-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--muted);
}
.empty-icon {
  margin-bottom: 1rem;
  opacity: 0.3;
}
.empty-state-container h4 {
  margin: 0 0 0.5rem 0;
  color: white;
}
.empty-state-container p {
  margin: 0;
  font-size: 0.9rem;
  max-width: 300px;
}

.spin { animation: spin 2s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.warn { color: #f59e0b !important; border-color: rgba(245, 158, 11, 0.3) !important; }
</style>
