<script setup>
import { ref, onMounted } from 'vue'
import { Briefcase, User, ExternalLink, Loader2, AlertCircle } from 'lucide-vue-next'

const props = defineProps({
  type: {
    type: String, 
    required: true
  },
  id: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['navigate'])

const data = ref(null)
const loading = ref(true)
const error = ref(null)

async function fetchData() {
  loading.value = true
  error.value = null
  const token = localStorage.getItem('token')
  
  if (props.type === 'JOB') {
    try {
      const res = await fetch(`/jobs/${props.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        data.value = await res.json()
      } else {
        error.value = 'Job not found'
      }
    } catch (e) {
      error.value = 'Failed to load job'
    }
  } else {
    // For CANDIDATE, try ranking_id first, then fallback to my-submission (if id is job_id)
    try {
      let res = await fetch(`/dashboard/ranking/${props.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        data.value = await res.json()
      } else {
        // Fallback for candidates who might only have access to my-submission by job_id
        res = await fetch(`/analyze/my-submission/${props.id}`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.ok) {
          data.value = await res.json()
        } else {
          error.value = 'Candidate data not found'
        }
      }
    } catch (e) {
      error.value = 'Failed to load candidate'
    }
  }
  
  loading.value = false
}

function handleNavigate() {
  if (!data.value) return
  emit('navigate', { type: props.type, id: props.id, data: data.value })
}

onMounted(fetchData)
</script>

<template>
  <div class="chat-card-wrap" @click="handleNavigate">
    <div v-if="loading" class="card-loading">
      <Loader2 :size="14" class="spin" />
      <span>Loading...</span>
    </div>
    
    <div v-else-if="error" class="card-error">
      <AlertCircle :size="14" />
      <span>{{ error }}</span>
    </div>

    <div v-else :class="['chat-entity-card', type.toLowerCase()]">
      <div class="card-body">
        <div class="icon-side">
          <Briefcase v-if="type === 'JOB'" :size="16" />
          <User v-else :size="16" />
        </div>
        <div class="content-side">
          <div class="header-line">
            <span class="entity-title">{{ type === 'JOB' ? data.title : data.candidate_ref }}</span>
            <div class="nav-indicator"><ExternalLink :size="12" /></div>
          </div>
          <p class="summary-line">
            {{ type === 'JOB' ? data.description.substring(0, 60) : (data.summary ? data.summary.substring(0, 60) : 'Application received') }}...
          </p>
          <div class="footer-line">
             <span v-if="type === 'CANDIDATE'" class="score-pill">
               <template v-if="data.status === 'ready'">{{ data.overall_score.toFixed(0) }}% Match</template>
               <template v-else>Evaluating...</template>
             </span>
             <span v-else class="status-pill-mini">Active</span>
             <span class="id-hint">#{{ id.substring(0, 4) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-card-wrap {
  margin: 0.75rem 0;
  width: 100%;
  max-width: 320px;
  cursor: pointer;
}

.card-loading, .card-error {
  padding: 0.5rem 0.75rem;
  font-size: 0.75rem;
  color: var(--muted);
  border: 1px solid var(--border);
  background: var(--bg);
  border-radius: 4px;
}

.chat-entity-card {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 4px;
  overflow: hidden;
  transition: all 0.2s ease;
}

.chat-entity-card:hover {
  background: rgba(255, 255, 255, 0.03);
  border-color: var(--accent);
}

.card-body {
  display: flex;
  gap: 1rem;
  padding: 1rem;
}

.icon-side {
  width: 36px;
  height: 36px;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
  flex-shrink: 0;
}

.content-side {
  flex-grow: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.header-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 0.5rem;
}

.entity-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.nav-indicator {
  color: var(--muted);
  opacity: 0.5;
}
.chat-entity-card:hover .nav-indicator {
  color: var(--accent);
  opacity: 1;
}

.summary-line {
  font-size: 0.85rem;
  color: var(--muted);
  line-height: 1.4;
  margin: 0;
}

.footer-line {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 0.25rem;
}

.score-pill {
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--ok);
}

.status-pill-mini {
  font-size: 0.7rem;
  font-weight: 700;
  color: var(--muted);
  text-transform: uppercase;
}

.id-hint {
  font-size: 0.7rem;
  font-family: monospace;
  color: var(--border);
}

.spin { animation: spin 1s linear infinite; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
</style>
