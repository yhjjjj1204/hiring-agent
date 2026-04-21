<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { BarChart3, ChevronLeft, Calendar, Brain, Cpu, MessageSquare, FileText } from 'lucide-vue-next'

const router = useRouter()
const stats = ref([])
const loading = ref(true)
const selectedDate = ref(new Date().toISOString().split('T')[0])
const windowWidth = ref(window.innerWidth)

const maxBarHeight = 200 // px

function handleResize() {
  windowWidth.value = window.innerWidth
}

async function fetchStats() {
  const token = localStorage.getItem('token')
  try {
    const res = await fetch('/api/recruiter/usage', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (res.ok) {
      stats.value = await res.json()
    }
  } catch (e) {
    console.error("Failed to fetch usage stats", e)
  } finally {
    loading.value = false
  }
}

const fullChartData = computed(() => {
  const daysMap = {}
  stats.value.forEach(s => {
    if (!daysMap[s.date]) daysMap[s.date] = { date: s.date, total: 0, items: [] }
    daysMap[s.date].total += (s.input_tokens + s.output_tokens)
    daysMap[s.date].items.push(s)
  })

  // Generate exactly 20 days ending today
  const range = []
  for (let i = 0; i < 20; i++) {
    const d = new Date()
    d.setDate(d.getDate() - i)
    const ds = d.toISOString().split('T')[0]
    range.push({
      date: ds,
      total: daysMap[ds]?.total || 0,
      items: daysMap[ds]?.items || []
    })
  }
  return range.reverse()
})

const visibleChartData = computed(() => {
  // Show 7 days if width < 800px, otherwise 20
  const count = windowWidth.value < 800 ? 7 : 20
  return fullChartData.value.slice(-count)
})

const maxTokens = computed(() => {
  const peak = Math.max(...visibleChartData.value.map(d => d.total))
  return peak === 0 ? 1000 : peak
})

const selectedDayData = computed(() => {
  const found = visibleChartData.value.find(d => d.date === selectedDate.value)
  if (found) return found
  return visibleChartData.value[visibleChartData.value.length - 1]
})

function getBarStyle(day) {
  if (day.total === 0) return { height: '2px' }
  
  const height = (day.total / maxTokens.value) * maxBarHeight
  
  let gradientParts = []
  let currentPercentage = 0
  const sortedItems = [...day.items].sort((a, b) => a.function.localeCompare(b.function))
  
  sortedItems.forEach(item => {
    const segmentRatio = (item.input_tokens + item.output_tokens) / day.total
    const nextPercentage = currentPercentage + (segmentRatio * 100)
    const color = getFunctionColor(item.function)
    gradientParts.push(`${color} ${currentPercentage.toFixed(1)}% ${nextPercentage.toFixed(1)}%`)
    currentPercentage = nextPercentage
  })
  
  return {
    height: `${Math.max(height, 4)}px`,
    background: `linear-gradient(to top, ${gradientParts.join(', ')})`
  }
}

function selectDate(date) {
  selectedDate.value = date
}

function getFunctionIcon(fid) {
  if (fid === 'chatbot') return MessageSquare
  if (fid === 'resume_ocr') return FileText
  if (fid === 'auto_score') return Brain
  if (fid === 'job_summary') return FileText
  return Cpu
}

function getFunctionColor(fid) {
  if (fid === 'chatbot') return '#3b82f6'
  if (fid === 'resume_ocr') return '#10b981'
  if (fid === 'auto_score') return '#f59e0b'
  if (fid === 'job_summary') return '#8b5cf6'
  return '#94a3b8'
}

function formatDayLabel(dateStr) {
  const d = new Date(dateStr)
  const today = new Date().toISOString().split('T')[0]
  if (dateStr === today) return 'Today'
  return d.toLocaleDateString(undefined, { weekday: 'short' })
}

function formatFullDate(dateStr) {
  return new Date(dateStr).toLocaleDateString(undefined, { 
    weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' 
  })
}

function goHome() {
  router.push('/')
}

onMounted(() => {
  fetchStats()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<template>
  <div class="usage-stats-page">
    <div class="header-nav">
      <button class="mini secondary" @click="goHome">
        <ChevronLeft :size="14" />
        Back to Dashboard
      </button>
    </div>

    <div class="page-header-wrap">
      <div class="page-header-titles">
        <h2>AI Usage Statistics</h2>
        <p class="page-header-subtitle">Detailed token consumption by date and function</p>
      </div>
      <div class="header-icon-box glass-card">
        <BarChart3 :size="24" />
      </div>
    </div>

    <div v-if="loading" class="loading-state">
      <Cpu class="spin" :size="48" />
      <p>Loading analytics...</p>
    </div>

    <div v-else class="stats-content">
      <!-- CENTERED RESPONSIVE RECTANGULAR CHART -->
      <div class="chart-section glass-card">
        <div class="chart-outer">
          <div class="chart-container">
            <div 
              v-for="day in visibleChartData" 
              :key="day.date" 
              class="bar-column"
              :class="{ 'is-selected': selectedDate === day.date }"
              @click="selectDate(day.date)"
            >
              <div class="bar-value-hint" v-if="selectedDate === day.date && day.total > 0">
                {{ day.total.toLocaleString() }}
              </div>
              <div class="bar-rect" :style="getBarStyle(day)"></div>
              <div class="bar-label">{{ formatDayLabel(day.date) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- SELECTED DATE DETAILS -->
      <div class="details-section">
        <div class="section-title-row">
          <div class="date-display">
            <h3>{{ formatFullDate(selectedDate) }}</h3>
            <span v-if="selectedDate === new Date().toISOString().split('T')[0]" class="today-badge">TODAY</span>
          </div>
          <div class="day-total-summary" v-if="selectedDayData?.total > 0">
            <span class="val">{{ selectedDayData.total.toLocaleString() }}</span>
            <span class="unit">TOTAL TOKENS</span>
          </div>
        </div>

        <div v-if="selectedDayData?.items.length > 0" class="function-grid">
          <div v-for="item in selectedDayData.items" :key="item.function" class="func-card glass-card">
            <div class="func-header">
              <div class="func-identity">
                <div class="icon-circle" :style="{ color: getFunctionColor(item.function), background: getFunctionColor(item.function) + '15' }">
                  <component :is="getFunctionIcon(item.function)" :size="16" />
                </div>
                <span class="func-name">{{ item.function.replace('_', ' ') }}</span>
              </div>
              <div class="call-count">{{ item.total_calls }} calls</div>
            </div>
            <div class="func-metrics-row">
              <div class="metric-group">
                <label>Prompt</label>
                <span class="m-val">{{ item.input_tokens.toLocaleString() }}</span>
              </div>
              <div class="metric-group">
                <label>Completion</label>
                <span class="m-val">{{ item.output_tokens.toLocaleString() }}</span>
              </div>
              <div class="metric-group total">
                <label>Subtotal</label>
                <span class="m-val">{{ (item.input_tokens + item.output_tokens).toLocaleString() }}</span>
              </div>
            </div>
          </div>
        </div>
        <div v-else class="empty-day-state glass-card">
          <Calendar :size="32" class="muted-icon" />
          <p>No activity recorded for this date.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.usage-stats-page { animation: fadeIn 0.3s ease-out; }
.header-nav { margin-bottom: 1.5rem; }

.header-icon-box {
  width: 52px; height: 52px;
  display: flex; align-items: center; justify-content: center;
  color: var(--accent); border-radius: 12px;
}

/* RECTANGULAR CHART STYLES */
.chart-section {
  padding: 3.5rem 1rem 2rem;
  margin-bottom: 2.5rem;
  background: var(--panel);
  overflow-x: auto;
}

.chart-outer {
  width: 100%;
  display: flex;
  justify-content: center;
  min-width: fit-content;
}

.chart-container {
  height: 240px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 0.75rem;
}

.bar-column {
  width: 36px;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  cursor: pointer;
  position: relative;
}

.bar-rect {
  width: 100%;
  background: var(--glass);
  margin-bottom: 1rem;
  transition: all 0.3s ease;
  opacity: 0.3;
}

.bar-label {
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.02em;
  text-align: center;
  width: 100%;
  white-space: nowrap;
}

/* Interactions */
.bar-column.is-selected .bar-rect {
  opacity: 1;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}
.bar-column.is-selected .bar-label {
  color: var(--accent);
}
.bar-column:hover .bar-rect {
  opacity: 0.8;
}

.bar-value-hint {
  position: absolute;
  top: -24px;
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--accent);
  white-space: nowrap;
}

/* DETAILS SECTION */
.section-title-row {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 1.5rem; padding: 0 0.5rem;
}
.date-display { display: flex; align-items: center; gap: 1rem; }
.date-display h3 { margin: 0; font-size: 1.2rem; color: var(--headings); }
.today-badge {
  background: var(--accent-glow); color: var(--accent);
  font-size: 0.6rem; font-weight: 800; padding: 0.15rem 0.4rem; border-radius: 4px;
}
.day-total-summary { text-align: right; }
.day-total-summary .val { font-size: 1.6rem; font-weight: 800; color: var(--headings); display: block; line-height: 1; }
.day-total-summary .unit { font-size: 0.6rem; font-weight: 700; color: var(--muted); }

.function-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 1.25rem;
}
.func-card { padding: 1.25rem; display: flex; flex-direction: column; gap: 1.25rem; }
.func-header { display: flex; justify-content: space-between; align-items: center; }
.func-identity { display: flex; align-items: center; gap: 0.75rem; }
.icon-circle { width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; }
.func-name { font-size: 0.9rem; font-weight: 700; color: var(--headings); text-transform: capitalize; }
.call-count { font-size: 0.75rem; color: var(--muted); font-weight: 600; }

.func-metrics-row {
  display: grid; grid-template-columns: 1fr 1fr 1.2fr;
  gap: 1rem; background: var(--bg); padding: 0.75rem; border-radius: 6px;
}
.metric-group { display: flex; flex-direction: column; gap: 0.2rem; }
.metric-group label { font-size: 0.6rem; color: var(--muted); margin: 0; text-transform: uppercase; letter-spacing: 0.05em; }
.metric-group .m-val { font-size: 0.85rem; font-weight: 700; color: var(--text); }
.metric-group.total .m-val { color: var(--accent); }

.empty-day-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 4rem; color: var(--muted); text-align: center;
}
.muted-icon { opacity: 0.2; margin-bottom: 1rem; }

.loading-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  padding: 8rem; color: var(--muted);
}
.spin { animation: spin 2s linear infinite; margin-bottom: 1rem; }
@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

@media (max-width: 600px) {
  .chart-container { gap: 0.5rem; }
  .bar-column { width: 28px; }
  .bar-label { font-size: 0.55rem; }
}
</style>
