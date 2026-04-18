<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { marked } from 'marked'
import { 
  ChevronLeft, 
  LogOut, 
  LayoutDashboard, 
  FileText, 
  CheckCircle, 
  RefreshCw,
  Loader2,
  Briefcase
} from 'lucide-vue-next'
import ResumeUpload from './components/ResumeUpload.vue'
import JobRequirementInput from './components/JobRequirementInput.vue'
import AnalysisResult from './components/AnalysisResult.vue'
import CandidateSnapshot from './components/CandidateSnapshot.vue'
import Auth from './components/Auth.vue'
import RecruiterDashboard from './components/RecruiterDashboard.vue'
import JobList from './components/JobList.vue'

const user = ref(null)
const selectedJob = ref(null)
const recruiterDashboardRef = ref(null)
const file = ref(null)
const requirements = reactive({
  github: '',
  scholarUrl: '',
  nameOverride: ''
})

const status = ref('')
const statusClass = ref('')
const isWorking = ref(false)
const errorOutput = ref('')

// Candidate analysis tracking
const currentRankingId = ref(null)
const currentArrangedResume = ref(null)
const existingSubmission = ref(null)
const showReSubmitForm = ref(false)
const isJobExpanded = ref(false)
let candidatePollInterval = null

async function runAnalysis() {
  if (!file.value) {
    status.value = "Please choose or drop a resume file."
    statusClass.value = "err"
    return
  }

  const fd = new FormData()
  fd.append("resume", file.value, file.value.name)
  fd.append("job_id", selectedJob.value.id)
  if (requirements.github.trim()) fd.append("candidate_github", requirements.github.trim())
  if (requirements.scholarUrl.trim()) fd.append("google_scholar_url", requirements.scholarUrl.trim())
  if (requirements.nameOverride.trim()) fd.append("candidate_name_override", requirements.nameOverride.trim())

  isWorking.value = true
  statusClass.value = ""
  status.value = "Uploading and starting evaluation…"
  errorOutput.value = ""
  currentArrangedResume.value = null

  const token = localStorage.getItem('token')

  try {
    const res = await fetch("/analyze/resume", {
      method: "POST",
      body: fd,
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const data = await res.json()
    
    if (!res.ok) {
      status.value = data.detail || ("HTTP " + res.status)
      statusClass.value = "err"
      errorOutput.value = JSON.stringify(data, null, 2)
      isWorking.value = false
      return
    }
    
    currentRankingId.value = data.ranking_id
    status.value = "Application submitted! AI agents are summarizing your data..."
    statusClass.value = "ok"
    
    startPollingCandidateStatus()
  } catch (e) {
    status.value = "Request failed: " + (e && e.message ? e.message : String(e))
    statusClass.value = "err"
    isWorking.value = false
  }
}

async function fetchMySubmission() {
  if (!selectedJob.value) return
  
  const token = localStorage.getItem('token')
  try {
    const res = await fetch(`/analyze/my-submission/${selectedJob.value.id}`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      existingSubmission.value = data
      currentRankingId.value = data.ranking_id
      currentArrangedResume.value = data.arranged_resume
      
      if (data.candidate_info) {
        requirements.github = data.candidate_info.github || ''
        requirements.scholarUrl = data.candidate_info.scholar_url || ''
        requirements.nameOverride = data.candidate_info.name_override || ''
      }

      if (data.status === 'evaluating') {
        isWorking.value = true
        startPollingCandidateStatus()
      }
    } else {
      existingSubmission.value = null
      currentRankingId.value = null
      currentArrangedResume.value = null
    }
  } catch (e) {
    console.error("Failed to fetch submission", e)
  }
}

async function startPollingCandidateStatus() {
  if (candidatePollInterval) clearInterval(candidatePollInterval)
  
  const token = localStorage.getItem('token')
  
  candidatePollInterval = setInterval(async () => {
    try {
      const res = await fetch(`/analyze/my-submission/${selectedJob.value.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      const data = await res.json()
      if (res.ok) {
        if (data.status === 'ready') {
          currentArrangedResume.value = data.arranged_resume
          existingSubmission.value = data
          status.value = "Update complete! Here is your objective resume summary."
          clearInterval(candidatePollInterval)
          candidatePollInterval = null
          isWorking.value = false
          showReSubmitForm.value = false
        }
      }
    } catch (e) {
      console.error("Polling failed", e)
    }
  }, 3000)
}

function onAuthenticated(u) {
  user.value = u
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  selectedJob.value = null
  if (candidatePollInterval) clearInterval(candidatePollInterval)
}

function selectJob(job) {
  selectedJob.value = job
  currentArrangedResume.value = null
  currentRankingId.value = null
  existingSubmission.value = null
  showReSubmitForm.value = false
  requirements.github = ''
  requirements.scholarUrl = ''
  requirements.nameOverride = ''
  fetchMySubmission()
}

function goHome() {
  selectedJob.value = null
  if (recruiterDashboardRef.value) {
    recruiterDashboardRef.value.reset()
  }
  status.value = ''
  statusClass.value = ''
  errorOutput.value = ''
  if (candidatePollInterval) clearInterval(candidatePollInterval)
}

onMounted(() => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    user.value = JSON.parse(savedUser)
  }
})

onUnmounted(() => {
  if (candidatePollInterval) clearInterval(candidatePollInterval)
})

function renderMarkdown(text) {
  if (!text) return ''
  return marked.parse(text)
}
</script>

<template>
  <div class="app-root">
    <header class="main-header">
      <div class="header-inner">
        <div class="header-left">
          <h1 class="logo" @click="goHome">
            <span class="logo-icon"><Briefcase :size="16" /></span> HiringAgent
          </h1>
        </div>
        <div v-if="user" class="header-right">
          <div class="user-info">
            <span class="user-name">{{ user.username }}</span>
            <span class="user-role badge">{{ user.role }}</span>
            <button class="mini secondary" @click="logout">
              <LogOut :size="14" />
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>

    <main class="main-container">
      <div v-if="!user">
        <Auth @authenticated="onAuthenticated" />
      </div>

      <div v-else-if="user.role === 'candidate'" class="candidate-view">
        <div v-if="!selectedJob">
          <JobList @select-job="selectJob" />
        </div>
        <div v-else class="job-detail-view">
          <div class="job-header-bar">
            <button class="mini secondary" @click="selectedJob = null">
              <ChevronLeft :size="14" />
              Back to Jobs
            </button>
            <h2 class="job-title">{{ selectedJob.title }}</h2>
          </div>
          
          <div class="job-desc-readonly glass-card">
            <label>Job Requirements</label>
            <div :class="['description-content', { 'expanded': isJobExpanded || (!existingSubmission || showReSubmitForm) }]">
              <div class="markdown-body" v-html="renderMarkdown(selectedJob.description)"></div>
            </div>
            <button v-if="existingSubmission && !showReSubmitForm" class="text-btn" @click="isJobExpanded = !isJobExpanded">
              {{ isJobExpanded ? 'Show Less' : 'Show Full Requirements' }}
            </button>
          </div>

          <!-- NEW SUBMISSION OR RE-SUBMISSION FORM -->
          <div v-if="!existingSubmission || showReSubmitForm" class="submission-section glass-card">
            <div class="section-title">
              <h3>{{ existingSubmission ? 'Update Application' : 'Apply for this position' }}</h3>
              <button v-if="existingSubmission" class="text-btn err" @click="showReSubmitForm = false">Cancel</button>
            </div>

            <ResumeUpload v-model="file" />
            
            <div class="background-inputs">
              <h3>External Profiles <small>(Optional)</small></h3>
              <div class="inputs-grid">
                <div class="form-group">
                  <label>GitHub</label>
                  <input v-model="requirements.github" type="text" placeholder="username" />
                </div>
                <div class="form-group">
                  <label>Google Scholar</label>
                  <input v-model="requirements.scholarUrl" type="text" placeholder="https://scholar.google.com/..." />
                </div>
                <div class="form-group full-width">
                  <label>Full Name Override</label>
                  <input v-model="requirements.nameOverride" type="text" placeholder="Only if OCR fails to detect your name" />
                </div>
              </div>
            </div>

            <div class="actions">
              <button type="button" @click="runAnalysis" :disabled="isWorking">
                {{ existingSubmission ? 'Update Submission' : 'Submit Application' }}
              </button>
              <Loader2 v-if="isWorking" class="loader mini-loader spin" :size="16" />
              <span id="status" :class="statusClass">{{ status }}</span>
            </div>
          </div>

          <!-- VIEW EXISTING SUBMISSION -->
          <div v-else class="submission-view">
            <div class="submission-status-bar glass-card">
              <div class="status-info">
                <span class="submitted-label">Status</span>
                <span :class="['status-badge', existingSubmission.status]">
                  <RefreshCw v-if="existingSubmission.status === 'evaluating'" :size="12" class="spin" />
                  <CheckCircle v-else :size="12" />
                  {{ existingSubmission.status === 'evaluating' ? 'Evaluating' : 'Submitted' }}
                </span>
              </div>
              <button class="secondary" @click="showReSubmitForm = true" :disabled="isWorking">Update Application</button>
            </div>

            <div v-if="currentArrangedResume" class="arranged-data-card glass-card">
              <div class="card-header-with-hint">
                <h3>Structured Profile</h3>
                <p class="hint">Objective summary as seen by our agents</p>
              </div>
              <CandidateSnapshot :arranged-resume="currentArrangedResume" />
            </div>
            
            <div v-else-if="isWorking" class="evaluating-card glass-card">
              <Loader2 class="loader spin" :size="32" />
              <p>Evaluating submission...</p>
            </div>
          </div>

          <pre v-if="errorOutput" id="errorOut">{{ errorOutput }}</pre>
        </div>
      </div>

      <div v-else-if="user.role === 'recruiter'">
        <RecruiterDashboard ref="recruiterDashboardRef" />
      </div>
    </main>
  </div>
</template>

<style scoped>
.main-header {
  background: var(--header-bg);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 100;
  width: 100%;
}
.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  padding: 0.75rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.logo {
  cursor: pointer;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin: 0;
  font-weight: 700;
}

.logo-icon {
  background: var(--accent);
  color: white;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.user-info { display: flex; gap: 1rem; align-items: center; }
.user-name { font-size: 0.9rem; font-weight: 600; color: var(--muted); }
.badge {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid var(--border);
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
}

.job-header-bar { display: flex; align-items: center; gap: 1rem; margin-bottom: 1.25rem; }
.job-title { margin: 0; font-size: 1.5rem; }

.job-desc-readonly { padding: 1.25rem; margin-bottom: 1.5rem; }
.job-desc-readonly label { border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-bottom: 1rem; }

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

.text-btn { 
  background: none; border: none; color: var(--accent); 
  cursor: pointer; padding: 0.5rem 0; font-size: 0.9rem; font-weight: 700;
}
.text-btn.err { color: var(--err); }

.submission-section { padding: 1.5rem; }
.section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; }
.section-title h3 { margin: 0; font-size: 1.1rem; }

.background-inputs { margin-top: 1.5rem; }
.background-inputs h3 { margin-bottom: 1rem; font-size: 1rem; border-left: 3px solid var(--accent); padding-left: 0.75rem; }
.inputs-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.full-width { grid-column: span 2; }

.actions { margin-top: 1.5rem; display: flex; align-items: center; gap: 1rem; }
#status { font-size: 0.9rem; color: var(--muted); }
#status.ok { color: var(--ok); }
#status.err { color: var(--err); }

.submission-status-bar { display: flex; justify-content: space-between; align-items: center; padding: 0.75rem 1.5rem; margin-bottom: 1.5rem; }
.status-info { display: flex; align-items: center; gap: 1rem; }
.submitted-label { font-weight: 700; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; }

.status-badge { display: inline-flex; align-items: center; gap: 0.4rem; padding: 0.2rem 0.6rem; border-radius: 4px; font-size: 0.7rem; font-weight: 700; border: 1px solid var(--border); text-transform: uppercase; }
.status-badge.evaluating { color: var(--accent); border-color: var(--accent); }
.status-badge.ready { color: var(--ok); border-color: var(--ok); }

.arranged-data-card { padding: 1.5rem; }
.card-header-with-hint { margin-bottom: 1.5rem; }
.card-header-with-hint h3 { margin-bottom: 0.25rem; font-size: 1.1rem; }
.card-header-with-hint .hint { color: var(--muted); font-size: 0.85rem; }

.evaluating-card { text-align: center; padding: 3rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; color: var(--muted); }

.spin { animation: spin 1s linear infinite; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

#errorOut {
  margin-top: 1.25rem;
  background: rgba(239, 68, 68, 0.05);
  border-color: rgba(239, 68, 68, 0.1);
  color: var(--err);
}
</style>
