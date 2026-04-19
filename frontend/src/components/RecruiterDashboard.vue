<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { marked } from 'marked'
import { 
  ChevronLeft, 
  ChevronRight, 
  RotateCw, 
  Download, 
  AlertTriangle,
  RefreshCw,
  CheckCircle,
  Users,
  ArrowRight
} from 'lucide-vue-next'
import JobManager from './JobManager.vue'
import CandidateSnapshot from './CandidateSnapshot.vue'

const props = defineProps(['modelValue'])
const emit = defineEmits(['context-change'])

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
  emit('context-change', { job: job.title, job_id: job.id, candidate: null, candidate_id: null })
}

function selectCandidate(candidate) {
  selectedCandidate.value = candidate
  window.scrollTo({ top: 0, behavior: 'smooth' })
  emit('context-change', { 
    job: selectedJob.value?.title || 'Unknown', 
    job_id: selectedJob.value?.id, 
    candidate: candidate.candidate_ref, 
    candidate_id: candidate.ranking_id 
  })
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
      emit('context-change', { job: data.title, job_id: data.id })
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
  emit('context-change', { job: null, job_id: null, candidate: null, candidate_id: null })
}

defineExpose({ reset, onSelectJob, selectCandidate })

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
      <div class="job-header-bar">
        <button class="mini secondary" @click="selectedJob = null">
          <ChevronLeft :size="14" />
          Back
        </button>
        <h2 class="job-title">{{ selectedJob.title }}</h2>
      </div>

      <!-- Job Preview/Edit Section -->
      <div class="job-desc-readonly glass-card">
        <div v-if="!isEditingJob">
          <div class="preview-header">
            <label>Job Requirements</label>
            <button class="mini secondary" @click="startEditJob">Edit Profile</button>
          </div>
          <div :class="['description-content', { 'expanded': isJobExpanded }]">
            <div class="markdown-body" v-html="renderMarkdown(selectedJob.description)"></div>
          </div>
          <button class="text-btn" @click="isJobExpanded = !isJobExpanded">
            {{ isJobExpanded ? 'Show Less' : 'Show Full Requirements' }}
          </button>
        </div>
        <div v-else class="job-edit-form">
          <h3>Modify Position</h3>
          <div class="form-grid">
            <div class="form-group">
              <label>Role Title</label>
              <input v-model="editJobData.title" type="text" />
            </div>
            <div class="form-group">
              <label>Description & Requirements (Markdown)</label>
              <textarea v-model="editJobData.description" rows="12"></textarea>
            </div>
          </div>
          <div class="form-actions">
            <button @click="saveJobUpdate">Update Job</button>
            <button class="secondary" @click="isEditingJob = false">Cancel</button>
          </div>
          <p v-if="jobStatus" class="err">{{ jobStatus }}</p>
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
                <div :class="['status-pill', c.status]">
                  <span class="status-dot"></span>
                  {{ c.status === 'evaluating' ? 'Evaluating' : 'Ready' }}
                </div>
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
              <div class="view-details">
                Review Details 
                <ChevronRight :size="14" />
              </div>
            </div>
          </div>
        </div>
        <p v-else-if="!status" class="empty-state glass-card">
          <Users :size="24" class="empty-icon" />
          No applications received yet.
        </p>
      </div>
    </div>

    <!-- 3. INDIVIDUAL CANDIDATE PAGE -->
    <div v-else class="candidate-page">
      <div class="page-header">
        <div class="title-area">
          <button class="mini secondary" @click="selectedCandidate = null">← Back</button>
          <div class="candidate-title">
            <h2 class="cand-page-name">{{ selectedCandidate.candidate_ref }}</h2>
            <div :class="['status-pill large', selectedCandidate.status]">
               <span class="status-dot"></span>
               {{ selectedCandidate.status }}
            </div>
          </div>
        </div>
        <div class="header-actions">
           <button class="secondary" @click="downloadResume(selectedCandidate.ranking_id)">
             <Download :size="14" />
             Download CV
           </button>
           <button class="secondary warn" @click="reEvaluate(selectedCandidate.ranking_id)">
             <RotateCw :size="14" />
             Re-evaluate
           </button>
        </div>
      </div>

      <div class="candidate-meta-bar glass-card">
          <div v-if="selectedCandidate.candidate_info?.github" class="meta-item">
            <span class="meta-label">GitHub</span>
            <a :href="'https://github.com/' + selectedCandidate.candidate_info.github" target="_blank">@{{ selectedCandidate.candidate_info.github }}</a>
          </div>
          <div v-if="selectedCandidate.candidate_info?.scholar_url" class="meta-item">
             <span class="meta-label">Academic</span>
             <a :href="selectedCandidate.candidate_info.scholar_url" target="_blank">Scholar Profile</a>
          </div>
          <div v-if="selectedCandidate.candidate_info?.name_override" class="meta-item">
             <span class="meta-label">Legal Name</span>
             <span>{{ selectedCandidate.candidate_info.name_override }}</span>
          </div>
          <div class="meta-item">
             <span class="meta-label">Application Date</span>
             <span>{{ formatDate(selectedCandidate.submitted_at) }}</span>
          </div>
      </div>

      <div class="dual-pane">
        <!-- Left: Structured Data -->
        <div class="pane pane-left glass-card">
          <div class="pane-header">
            <h3>Structured Experience</h3>
            <p>Objective extraction by AI Agents</p>
          </div>
          <div class="pane-content">
            <CandidateSnapshot :arranged-resume="selectedCandidate.arranged_resume" />
          </div>
        </div>

        <!-- Right: Analysis -->
        <div class="pane pane-right glass-card">
          <div class="pane-header">
            <h3>Match Evaluation</h3>
            <p>Subjective fit analysis</p>
          </div>
          <div class="pane-content">
            <div v-if="selectedCandidate.status === 'ready'">
              <div class="overall-result">
                <div class="match-score-wrap">
                  <span class="big-score">{{ selectedCandidate.overall_score.toFixed(0) }}<small>%</small></span>
                  <span class="match-label">Overall Fit</span>
                </div>
                <div class="analysis-summary">{{ selectedCandidate.summary }}</div>
              </div>
              
              <div class="details-list">
                <div v-for="d in selectedCandidate.dimensions" :key="d.name" class="detail-item glass-card">
                  <div class="detail-header">
                    <strong>{{ d.name }}</strong>
                    <span class="detail-score">{{ d.score }}</span>
                  </div>
                  <div class="detail-rationale">{{ d.rationale }}</div>
                </div>
              </div>
            </div>
            <div v-else class="evaluating-placeholder">
              <RefreshCw class="loader spin" :size="48" />
              <p>Evaluating candidate data...</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard { animation: fadeIn 0.4s ease-out; }

.job-header-bar { display: flex; align-items: center; gap: 1.25rem; margin-bottom: 1.25rem; }
.job-title { margin: 0; font-size: 1.6rem; flex-grow: 1; line-height: 1.2; }

.header-actions { display: flex; gap: 0.75rem; align-items: center; }
.warn { color: #f59e0b !important; border-color: rgba(245, 158, 11, 0.3) !important; }

/* Shared Layout Reused */
.job-desc-readonly { padding: 1.25rem; margin-bottom: 2rem; position: relative; }
.job-desc-readonly label { border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; }

.preview-header { display: flex; justify-content: space-between; align-items: center; }

.description-content { 
  max-height: 200px; 
  overflow: hidden; 
  position: relative; 
  transition: max-height 0.4s ease; 
}
.description-content::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 0;
  width: 100%;
  height: 40px;
  background: linear-gradient(to bottom, transparent, var(--bg-subtle));
}
.description-content.expanded::after { display: none; }
.description-content.expanded { max-height: 5000px; }
.text-btn { font-size: 0.85rem; color: var(--accent); cursor: pointer; padding: 0.5rem 0; font-weight: 700; background: none; border: none; }

.job-edit-form { padding: 0.5rem 0; }
.form-grid { display: flex; flex-direction: column; gap: 1.25rem; }
.form-actions { margin-top: 1.5rem; display: flex; gap: 1rem; }

/* Status Pills */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  background: var(--bg);
  border: 1px solid var(--border);
  height: fit-content;
}
.status-pill.evaluating { color: var(--accent); border-color: var(--accent); }
.status-pill.ready { color: var(--ok); border-color: var(--ok); }
.status-pill.large { padding: 0.35rem 0.6rem; font-size: 0.75rem; }

.spin { animation: spin 1.5s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Grid Entry Alignment */
.candidate-grid { 
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); 
  gap: 1.25rem; 
}

.candidate-entry-card {
  padding: 1.5rem;
  cursor: pointer;
  transition: background 0.15s ease;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.candidate-entry-card:hover { background: rgba(255, 255, 255, 0.03); border-color: var(--muted); }

.entry-header { display: flex; justify-content: space-between; align-items: flex-start; }
.entry-main { display: flex; align-items: center; gap: 0.75rem; }
.cand-name { font-size: 1.15rem; margin: 0; color: #fff; line-height: 1.2; }

.entry-score { text-align: right; }
.score-val { display: block; font-size: 1.5rem; font-weight: 700; color: var(--ok); line-height: 1; }
.score-label { font-size: 0.6rem; color: var(--muted); font-weight: 700; }

.entry-summary { 
  font-size: 0.9rem; color: var(--muted); display: -webkit-box; -webkit-line-clamp: 2; 
  -webkit-box-orient: vertical; overflow: hidden; line-height: 1.5;
}

/* Individual Page Alignment */
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 1.25rem; }
.title-area { display: flex; align-items: center; gap: 1.25rem; }
.candidate-title { display: flex; align-items: center; gap: 1rem; }
.cand-page-name { margin: 0; line-height: 1; display: flex; align-items: center; font-size: 1.75rem; }

.candidate-meta-bar { display: flex; gap: 4rem; padding: 1rem 1.5rem; margin-bottom: 2rem; }
.meta-item { display: flex; flex-direction: column; gap: 0.25rem; }
.meta-label { font-size: 0.65rem; font-weight: 800; color: var(--muted); text-transform: uppercase; }
.meta-item a { color: var(--accent); text-decoration: none; font-weight: 600; font-size: 0.9rem; }

.dual-pane { display: grid; grid-template-columns: 1.6fr 1fr; gap: 1.5rem; }

/* Dimensions and Footer */
.entry-dimensions { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.dim-pill { 
  background: var(--bg); border: 1px solid var(--border); padding: 0.2rem 0.5rem; 
  border-radius: 4px; font-size: 0.7rem; display: flex; gap: 0.4rem; 
}
.dim-val { color: var(--ok); font-weight: 700; }

.entry-footer { 
  margin-top: auto; display: flex; justify-content: space-between; align-items: center; 
  padding-top: 1rem; border-top: 1px solid var(--border); 
}
.entry-ts { font-size: 0.8rem; color: var(--muted); }
.view-details { color: var(--accent); font-weight: 700; font-size: 0.9rem; display: flex; align-items: center; gap: 0.25rem; }

.pane-header { padding: 1.25rem 2rem; border-bottom: 1px solid var(--border); }
.pane-header h3 { font-size: 1.1rem; margin-bottom: 0.25rem; }
.pane-header p { font-size: 0.8rem; color: var(--muted); }
.pane-content { padding: 2rem; }

.overall-result { 
  text-align: center; background: var(--bg); padding: 2rem; border-radius: var(--card-radius);
  margin-bottom: 2.5rem; border: 1px solid var(--border);
}
.match-score-wrap { margin-bottom: 1rem; }
.big-score { display: block; font-size: 3.5rem; font-weight: 700; color: var(--ok); line-height: 1; }
.big-score small { font-size: 1.2rem; margin-left: 2px; opacity: 0.7; }
.match-label { font-size: 0.75rem; font-weight: 800; color: var(--muted); text-transform: uppercase; }
.analysis-summary { font-size: 1.05rem; color: var(--text); line-height: 1.7; font-style: italic; opacity: 0.95; }

.detail-item { padding: 1.5rem; margin-bottom: 1.5rem; border-color: var(--border); }
.detail-header { display: flex; justify-content: space-between; margin-bottom: 0.75rem; }
.detail-score { color: var(--ok); font-weight: 800; font-size: 1.1rem; }
.detail-rationale { font-size: 0.95rem; color: var(--muted); line-height: 1.6; }

.candidates-section { margin-top: 3.5rem; }
.section-header { 
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem; 
  border-bottom: 1px solid var(--border); 
  padding-bottom: 1rem; 
}
.section-header h3 { margin: 0; font-size: 1.4rem; }

.count-badge { background: var(--accent); color: white; padding: 0.1rem 0.6rem; border-radius: 4px; font-size: 0.8rem; vertical-align: middle; margin-left: 0.5rem; }

.empty-state { text-align: center; padding: 6rem 2rem; color: var(--muted); display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.empty-icon { opacity: 0.2; }

.err-banner { 
  background: rgba(239, 68, 68, 0.05); color: var(--err); padding: 1rem 2rem; 
  border-radius: 6px; margin-bottom: 2rem; font-weight: 600; font-size: 0.95rem;
  border: 1px solid rgba(239, 68, 68, 0.1);
}

.mini { padding: 0.5rem 1rem; font-size: 0.85rem; }

.evaluating-placeholder { display: flex; flex-direction: column; align-items: center; gap: 1.5rem; padding: 4rem 0; color: var(--muted); }
.loader { opacity: 0.6; }
</style>
