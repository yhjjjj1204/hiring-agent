<script setup>
import { ref, onMounted, onUnmounted, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useWebSocket } from '../websocket'

const { subscribe: subscribeWS } = useWebSocket()
import { FileText, Github, GraduationCap, User, Loader2, CheckCircle, RefreshCw, AlertCircle, Brain, ChevronLeft } from 'lucide-vue-next'
import ResumeUpload from './ResumeUpload.vue'
import CandidateSnapshot from './CandidateSnapshot.vue'

const props = defineProps(['user'])
const router = useRouter()


const profile = reactive({
  github: '',
  scholar_url: '',
  name_override: '',
  resume_filename: '',
  arranged_resume: null,
  status: 'ready'
})

const file = ref(null)
const isWorking = ref(false)
const statusMsg = ref('')
const statusClass = ref('')

let wsUnsubscribe = null
onMounted(() => {
  fetchProfile()
  
  wsUnsubscribe = subscribeWS((message) => {
    if (message.type === 'profile_update') {
      profile.status = message.status
      if (message.status === 'ready') {
        profile.arranged_resume = message.arranged_resume
        profile.resume_filename = message.resume_filename
        isWorking.value = false
        statusMsg.value = "Resume analyzed successfully"
        statusClass.value = "ok"
      } else if (message.status === 'safety_blocked') {
        isWorking.value = false
        statusMsg.value = "Analysis blocked: " + (message.reason || "Safety Violation")
        statusClass.value = "err"
      } else if (message.status === 'error') {
        isWorking.value = false
        statusMsg.value = "Analysis failed"
        statusClass.value = "err"
      }
    }
  })
})

onUnmounted(() => {
  if (wsUnsubscribe) wsUnsubscribe()
})

async function fetchProfile() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/candidate/profile', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      const data = await res.json()
      Object.assign(profile, data)
    }
  } catch (e) {
    console.error("Failed to fetch profile", e)
  }
}

async function updateInfo() {
  const token = localStorage.getItem('token')
  const fd = new FormData()
  fd.append('github', profile.github)
  fd.append('scholar_url', profile.scholar_url)
  fd.append('name_override', profile.name_override)

  try {
    const res = await fetch('/api/candidate/profile/info', {
      method: 'POST',
      body: fd,
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      statusMsg.value = "Profile info updated"
      statusClass.value = "ok"
      setTimeout(() => { statusMsg.value = '' }, 3000)
    }
  } catch (e) {
    statusMsg.value = "Update failed"
    statusClass.value = "err"
  }
}

async function uploadResume() {
  if (!file.value) return

  const token = localStorage.getItem('token')
  const fd = new FormData()
  fd.append('resume', file.value)

  isWorking.value = true
  profile.status = 'evaluating'
  statusMsg.value = "Uploading and analyzing resume..."
  statusClass.value = ""

  try {
    const res = await fetch('/api/candidate/profile/resume', {
      method: 'POST',
      body: fd,
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      // Background task started, WS will notify
    } else {
      isWorking.value = false
      profile.status = 'error'
      statusMsg.value = "Upload failed"
      statusClass.value = "err"
    }
  } catch (e) {
    isWorking.value = false
    profile.status = 'error'
    statusMsg.value = "Request failed"
    statusClass.value = "err"
  }
}

watch(file, () => {
  if (file.value) uploadResume()
})
</script>

<template>
  <div class="resume-manager">
    <div class="page-header-wrap manager-header">
      <div class="page-header-titles">
        <button class="mini secondary back-btn" @click="router.push('/')">
          <ChevronLeft :size="14" />
          Back to Dashboard
        </button>
        <h2>Manage Resume</h2>
        <p class="page-header-subtitle">Your central identity for all applications</p>
      </div>
    </div>

    <div class="manager-sections">
      <div class="glass-card section-card">
        <div class="section-header">
          <FileText :size="18" class="icon-accent" />
          <h3>Resume File</h3>
        </div>
        <p class="section-desc">Upload your primary CV. This will be used for all job applications.</p>
        
        <div class="upload-row">
          <div class="upload-col">
            <ResumeUpload v-model="file" />
          </div>
          <div v-if="profile.resume_filename" class="current-file-info">
            <label>Current Resume</label>
            <div class="file-status-box">
              <CheckCircle v-if="profile.status === 'ready'" :size="14" class="text-ok" />
              <RefreshCw v-else-if="profile.status === 'evaluating'" :size="14" class="text-accent spin" />
              <AlertCircle v-else :size="14" class="text-err" />
              <span class="filename">{{ profile.resume_filename }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="glass-card section-card">
        <div class="section-header">
          <User :size="18" class="icon-accent" />
          <h3>Personal Details & Links</h3>
        </div>
        <div class="form-grid-horizontal">
          <div class="form-group">
            <label>Full Name Override</label>
            <input v-model="profile.name_override" type="text" placeholder="If OCR misses your name" @change="updateInfo" />
          </div>
          <div class="form-group">
            <label><Github :size="14" /> GitHub Username</label>
            <input v-model="profile.github" type="text" placeholder="username" @change="updateInfo" />
          </div>
          <div class="form-group">
            <label><GraduationCap :size="14" /> Google Scholar URL</label>
            <input v-model="profile.scholar_url" type="text" placeholder="https://scholar.google.com/..." @change="updateInfo" />
          </div>
        </div>
        <div v-if="statusMsg" :class="['status-toast', statusClass]">{{ statusMsg }}</div>
      </div>

      <div v-if="profile.arranged_resume" class="glass-card snapshot-card">
        <div class="card-header-with-hint">
          <div class="header-main">
            <Brain :size="20" class="icon-accent" />
            <h3>Structured AI Profile</h3>
          </div>
          <p class="hint">This is how our AI agents interpret your professional background from the uploaded resume.</p>
        </div>
        <CandidateSnapshot :arranged-resume="profile.arranged_resume" />
      </div>
      <div v-else-if="profile.status === 'evaluating'" class="glass-card empty-state">
        <Loader2 :size="32" class="spin text-muted" />
        <p>Analyzing your resume layout and content...</p>
      </div>
      <div v-else class="glass-card empty-state">
        <FileText :size="32" class="text-muted" />
        <p>Upload a resume to generate your structured profile snapshot</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.resume-manager {
  max-width: 900px;
  margin: 0 auto;
  animation: fadeIn 0.4s ease-out;
}

.manager-header {
  margin-bottom: 2rem;
}

.back-btn {
  margin-bottom: 1rem;
}

.manager-sections {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-card {
  padding: 1.5rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}

.section-header h3 {
  margin: 0;
  font-size: 1.1rem;
}

.section-desc {
  font-size: 0.85rem;
  color: var(--muted);
  margin-bottom: 1.25rem;
}

.upload-row {
  display: flex;
  gap: 2rem;
  align-items: flex-start;
}

.upload-col {
  flex: 1;
}

.current-file-info {
  flex: 1;
  background: var(--bg);
  padding: 1rem;
  border-radius: 4px;
  border: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.file-status-box {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.filename {
  font-size: 0.9rem;
  font-weight: 600;
  word-break: break-all;
}

.form-grid-horizontal {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.25rem;
}

.icon-accent { color: var(--accent); }
.text-ok { color: var(--ok); }
.text-accent { color: var(--accent); }
.text-err { color: var(--err); }

.status-toast {
  margin-top: 1rem;
  font-size: 0.8rem;
  font-weight: 700;
  text-align: center;
  padding: 0.4rem;
  border-radius: 4px;
  background: var(--glass);
}
.status-toast.ok { color: var(--ok); border: 1px solid var(--ok-glow); }
.status-toast.err { color: var(--err); border: 1px solid var(--err-glow); }

.snapshot-card {
  padding: 2rem;
}

.card-header-with-hint {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1.25rem;
}

.header-main {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.25rem;
}

.header-main h3 { margin: 0; font-size: 1.2rem; }

.hint {
  color: var(--muted);
  font-size: 0.85rem;
  margin: 0;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 4rem 2rem;
  text-align: center;
  color: var(--muted);
  gap: 1rem;
}

@media (max-width: 700px) {
  .upload-row {
    flex-direction: column;
  }
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
