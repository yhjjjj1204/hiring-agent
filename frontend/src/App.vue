<script setup>
import { ref, reactive, onMounted } from 'vue'
import ResumeUpload from './components/ResumeUpload.vue'
import JobRequirementInput from './components/JobRequirementInput.vue'
import AnalysisResult from './components/AnalysisResult.vue'
import Auth from './components/Auth.vue'
import RecruiterDashboard from './components/RecruiterDashboard.vue'
import JobList from './components/JobList.vue'

const user = ref(null)
const selectedJob = ref(null)
const file = ref(null)
const requirements = reactive({
  github: '',
  scholarUrl: '',
  nameOverride: ''
})

const status = ref('')
const statusClass = ref('')
const isWorking = ref(false)
const analysisData = ref(null)
const errorOutput = ref('')

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
  status.value = "Working…"
  errorOutput.value = ""
  analysisData.value = null

  const token = localStorage.getItem('token')

  try {
    const res = await fetch("/analyze/resume", {
      method: "POST",
      body: fd,
      headers: { 'Authorization': `Bearer ${token}` }
    })
    const text = await res.text()
    let data
    try { data = JSON.parse(text); } catch { data = { raw: text }; }
    
    if (!res.ok) {
      status.value = (data && data.detail) ? String(data.detail) : ("HTTP " + res.status)
      statusClass.value = "err"
      errorOutput.value = JSON.stringify(data, null, 2)
      return
    }
    
    status.value = "Done"
    statusClass.value = "ok"
    analysisData.value = data
  } catch (e) {
    status.value = "Request failed: " + (e && e.message ? e.message : String(e))
    statusClass.value = "err"
  } finally {
    isWorking.value = false
  }
}

function onAuthenticated(u) {
  user.value = u
}

function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  user.value = null
  selectedJob.value = null
}

function selectJob(job) {
  selectedJob.value = job
}

onMounted(() => {
  const savedUser = localStorage.getItem('user')
  if (savedUser) {
    user.value = JSON.parse(savedUser)
  }
})
</script>

<template>
  <div class="wrap">
    <div class="header">
      <h1>Hiring Agent</h1>
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
          <button class="mini" @click="selectedJob = null">Change Job</button>
        </div>
        
        <div class="job-desc-readonly">
          <label>Job Description</label>
          <div class="desc-content">{{ selectedJob.description }}</div>
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
          <button type="button" @click="runAnalysis" :disabled="isWorking">Submit Application</button>
          <span id="status" :class="statusClass">{{ status }}</span>
        </div>

        <pre v-if="errorOutput" id="errorOut">{{ errorOutput }}</pre>

        <AnalysisResult :data="analysisData" />
      </div>
    </div>

    <div v-else-if="user.role === 'recruiter'">
      <RecruiterDashboard />
    </div>
  </div>
</template>

<style scoped>
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 1px solid var(--border); padding-bottom: 1rem; }
.job-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.user-info { display: flex; gap: 1rem; align-items: center; font-size: 0.9rem; }
.mini { padding: 0.25rem 0.75rem; font-size: 0.8rem; background: transparent; border: 1px solid var(--border); }
.job-desc-readonly { background: var(--bg-card); padding: 1rem; border-radius: 8px; border: 1px solid var(--border); margin-bottom: 1.5rem; }
.job-desc-readonly label { display: block; margin-bottom: 0.5rem; font-weight: bold; font-size: 0.9rem; color: var(--muted); }
.desc-content { white-space: pre-wrap; line-height: 1.5; }
.background-inputs { margin-top: 2rem; padding: 1rem; background: var(--bg-card); border-radius: 12px; border: 1px solid var(--border); }
.background-inputs h3 { margin-bottom: 1rem; font-size: 1.1rem; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.3rem; font-size: 0.85rem; }
.form-group input { width: 100%; padding: 0.5rem; background: var(--bg); border: 1px solid var(--border); color: var(--fg); border-radius: 4px; }
.actions { margin-top: 2rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
#status { font-size: 0.9rem; color: var(--muted); }
#status.err { color: var(--err); }
#status.ok { color: var(--ok); }

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
