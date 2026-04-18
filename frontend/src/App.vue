<script setup>
import { ref, reactive, onMounted, onUnmounted, watch } from 'vue'
import { marked } from 'marked'
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
    
    // Start polling
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
      
      // Pre-fill fields for re-submission
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
  <div class="wrap">
    <div class="header">
      <h1 class="logo" @click="goHome">Hiring Agent</h1>
      <div v-if="user" class="user-info">
        <span>Logged in as <b>{{ user.username }}</b> ({{ user.role }})</span>
        <button class="mini" @click="logout">Logout</button>
      </div>
    </div>

    <div v-if="!user">
      <Auth @authenticated="onAuthenticated" />
    </div>

    <div v-else-if="user.role === 'candidate'">
      <div v-if="!selectedJob">
        <JobList @select-job="selectJob" />
      </div>
      <div v-else>
        <div class="job-header">
          <h2>Applying for: {{ selectedJob.title }}</h2>
          <button class="mini" @click="selectedJob = null">← Back</button>
        </div>
        
        <div class="job-desc-readonly">
          <label>Job Description</label>
          <div :class="['description-content', { 'expanded': isJobExpanded || (!existingSubmission || showReSubmitForm) }]">
            <div class="markdown-body" v-html="renderMarkdown(selectedJob.description)"></div>
          </div>
          <button v-if="existingSubmission && !showReSubmitForm" class="text-btn" @click="isJobExpanded = !isJobExpanded">
            {{ isJobExpanded ? 'Show Less' : 'Show More' }}
          </button>
        </div>

        <!-- NEW SUBMISSION OR RE-SUBMISSION FORM -->
        <div v-if="!existingSubmission || showReSubmitForm">
          <div class="section-title">
            <h3>{{ existingSubmission ? 'Re-submit Application' : 'Upload your resume' }}</h3>
            <button v-if="existingSubmission" class="text-btn" @click="showReSubmitForm = false">Cancel</button>
          </div>

          <ResumeUpload v-model="file" />
          
          <div class="background-inputs">
            <h3>Background Info (Optional)</h3>
            <div class="form-group">
              <label>GitHub Username</label>
              <input v-model="requirements.github" type="text" placeholder="username" />
            </div>
            <div class="form-group">
              <label>Google Scholar URL</label>
              <input v-model="requirements.scholarUrl" type="text" placeholder="https://scholar.google.com/..." />
            </div>
            <div class="form-group">
              <label>Name Override (if OCR fails)</label>
              <input v-model="requirements.nameOverride" type="text" placeholder="Full Name" />
            </div>
          </div>

          <div class="actions">
            <button type="button" @click="runAnalysis" :disabled="isWorking">
              {{ existingSubmission ? 'Update Submission' : 'Submit Application' }}
            </button>
            <div v-if="isWorking" class="loader mini-loader"></div>
            <span id="status" :class="statusClass">{{ status }}</span>
          </div>
        </div>

        <!-- VIEW EXISTING SUBMISSION -->
        <div v-else class="submission-view">
          <div class="submission-header">
            <div class="status-info">
              <span class="submitted-label">Application Status:</span>
              <span :class="['status-badge', existingSubmission.status]">
                {{ existingSubmission.status === 'evaluating' ? 'LLM Evaluating...' : 'Submitted' }}
              </span>
            </div>
            <button class="mini" @click="showReSubmitForm = true" :disabled="isWorking">Re-submit</button>
          </div>

          <div v-if="existingSubmission.candidate_info" class="meta-preview">
            <div class="meta-item"><strong>Resume:</strong> {{ existingSubmission.candidate_info.filename }}</div>
            <div v-if="requirements.github" class="meta-item"><strong>GitHub:</strong> {{ requirements.github }}</div>
            <div v-if="requirements.scholarUrl" class="meta-item"><strong>Scholar:</strong> Link</div>
          </div>

          <div v-if="currentArrangedResume" class="arranged-data-card">
            <h3>Your Structured Resume Data</h3>
            <p class="hint">This is an objective summary extracted by our AI agents.</p>
            <CandidateSnapshot :arranged-resume="currentArrangedResume" />
          </div>
          <div v-else-if="isWorking" class="evaluating-card">
            <div class="loader"></div>
            <p>Our AI agents are analyzing your new submission...</p>
          </div>
        </div>

        <pre v-if="errorOutput" id="errorOut">{{ errorOutput }}</pre>
      </div>
    </div>

    <div v-else-if="user.role === 'recruiter'">
      <RecruiterDashboard ref="recruiterDashboardRef" />
    </div>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.5rem; border-bottom: 1px solid var(--border); padding-bottom: 0.75rem; }
.logo { cursor: pointer; transition: opacity 0.2s; font-size: 1.4rem; margin: 0; }
.logo:hover { opacity: 0.7; }
.job-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.user-info { display: flex; gap: 1rem; align-items: center; font-size: 0.9rem; }
.mini { padding: 0.25rem 0.75rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); cursor: pointer; border-radius: 4px; }

.job-desc-readonly { background: var(--bg-card); padding: 1.25rem; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 1.5rem; }
.job-desc-readonly label { display: block; margin-bottom: 0.75rem; font-weight: bold; font-size: 0.9rem; color: var(--muted); border-bottom: 1px solid var(--border); padding-bottom: 0.4rem; }

.description-content { max-height: 200px; overflow: hidden; position: relative; mask-image: linear-gradient(to bottom, black 60%, transparent 100%); transition: max-height 0.4s ease; }
.description-content.expanded { max-height: 5000px; mask-image: none; }
.text-btn { background: none; border: none; color: var(--ok); cursor: pointer; padding: 0.5rem 0; font-size: 0.9rem; font-weight: bold; }
.text-btn:hover { text-decoration: underline; }

.markdown-body { line-height: 1.6; font-size: 0.95rem; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin-top: 1rem; margin-bottom: 0.75rem; font-size: 1.1rem; }
.markdown-body :deep(p) { margin-bottom: 0.75rem; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin-bottom: 0.75rem; padding-left: 1.5rem; }

.section-title { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.section-title h3 { margin: 0; }
.text-btn { background: none; border: none; color: var(--err); cursor: pointer; font-size: 0.9rem; }

.background-inputs { margin-top: 1.5rem; padding: 1rem; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border); }
.background-inputs h3 { margin-bottom: 1rem; font-size: 1.1rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.3rem; font-size: 0.85rem; }
.form-group input { width: 100%; padding: 0.5rem; background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: 4px; }

.actions { margin-top: 1.5rem; display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }
#status { font-size: 0.9rem; color: var(--muted); }
#status.err { color: var(--err); }
#status.ok { color: var(--ok); }

.submission-view { margin-top: 1.5rem; animation: fadeIn 0.3s ease-out; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

.submission-header { display: flex; justify-content: space-between; align-items: center; background: var(--bg-card); padding: 1rem 1.5rem; border-radius: 12px; border: 1px solid var(--border); margin-bottom: 1.5rem; }
.status-info { display: flex; align-items: center; gap: 1rem; }
.submitted-label { font-weight: bold; font-size: 0.9rem; }

.status-badge { padding: 0.2rem 0.6rem; border-radius: 20px; font-size: 0.75rem; font-weight: bold; width: fit-content; }
.status-badge.evaluating { background: #3b82f622; color: #3b82f6; border: 1px solid #3b82f644; }
.status-badge.ready { background: #10b98122; color: #10b981; border: 1px solid #10b98144; }

.meta-preview { display: flex; flex-wrap: wrap; gap: 1.5rem; margin-bottom: 1.5rem; padding: 0 0.5rem; font-size: 0.9rem; }

.arranged-data-card { background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }
.arranged-data-card h3 { margin-bottom: 0.25rem; color: var(--fg); }
.arranged-data-card .hint { color: var(--muted); font-size: 0.85rem; margin-bottom: 1.5rem; }

.evaluating-card { text-align: center; padding: 3rem; background: var(--bg-card); border: 1px solid var(--border); border-radius: 16px; display: flex; flex-direction: column; align-items: center; gap: 1rem; color: var(--muted); }

.loader {
  border: 3px solid var(--border);
  border-top: 3px solid var(--ok);
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}
.mini-loader { width: 16px; height: 16px; border-width: 2px; }
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

#errorOut {
  margin-top: 1rem;
  padding: 1rem;
  border-radius: 10px;
  background: #241a1a;
  border: 1px solid #7f1d1d;
  color: var(--err);
  overflow: auto;
  max-height: 40vh;
  font-size: 0.8rem;
}
</style>
