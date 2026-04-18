<script setup>
import { ref, reactive } from 'vue'
import ResumeUpload from './components/ResumeUpload.vue'
import JobRequirementInput from './components/JobRequirementInput.vue'
import AnalysisResult from './components/AnalysisResult.vue'

const file = ref(null)
const requirements = reactive({
  jobDescription: `We are building an internal AI agent platform for recruiting workflows (resume intake, structured extraction, scoring, and human-in-the-loop review). We need a Staff-level AI Engineer to own agent architecture and production reliability.

Responsibilities:
- Design and implement multi-step agents using LangGraph or equivalent orchestration, including state, checkpoints, and resume or interrupt patterns
- Integrate LLM calls with structured outputs, JSON schema validation, and guardrails for prompt injection and unsafe tool use
- Ship FastAPI services, background workers, and observability (tracing, metrics, cost and token accounting) for agent runs

Requirements:
- Strong Python and async patterns; experience shipping LLM features to production, not only notebooks
- Hands-on experience with LangChain or LangGraph or similar agent frameworks, plus OpenAI or compatible APIs
- Solid software engineering: testing, code review, versioning of prompts and tools, and clear failure modes when models are uncertain

Nice to have:
- Experience with resume or document OCR pipelines, vector search, or RAG evaluation
- Familiarity with hiring or compliance-sensitive domains and fairness or red-team testing for agent behavior`,
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
  if (requirements.jobDescription.trim().length < 15) {
    status.value = "Job description must be at least about 15 characters."
    statusClass.value = "err"
    return
  }

  const fd = new FormData()
  fd.append("resume", file.value, file.value.name)
  fd.append("hr_requirement_text", requirements.jobDescription.trim())
  if (requirements.github.trim()) fd.append("candidate_github", requirements.github.trim())
  if (requirements.scholarUrl.trim()) fd.append("google_scholar_url", requirements.scholarUrl.trim())
  if (requirements.nameOverride.trim()) fd.append("candidate_name_override", requirements.nameOverride.trim())

  isWorking.value = true
  statusClass.value = ""
  status.value = "Working…"
  errorOutput.value = ""
  analysisData.value = null

  try {
    const res = await fetch("/analyze/resume", { method: "POST", body: fd })
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
</script>

<template>
  <div class="wrap">
    <h1>Resume analysis</h1>

    <ResumeUpload v-model="file" />
    
    <JobRequirementInput v-model="requirements" />

    <div class="actions">
      <button type="button" @click="runAnalysis" :disabled="isWorking">Run analysis</button>
      <span id="status" :class="statusClass">{{ status }}</span>
    </div>

    <pre v-if="errorOutput" id="errorOut">{{ errorOutput }}</pre>

    <AnalysisResult :data="analysisData" />
  </div>
</template>

<style scoped>
.actions { margin-top: 1rem; display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
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
