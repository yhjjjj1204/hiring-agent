<script setup>
import { 
  BarChart3, 
  Cpu, 
  Brain, 
  MessageSquare, 
  FileText,
  TrendingUp,
  AlertCircle,
  Clock,
  ArrowRight
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})

// Mock data for the usage chart
const mockChartData = [
  { label: 'Mon', total: 45000, colors: ['#3b82f6', '#10b981'] },
  { label: 'Tue', total: 62000, colors: ['#3b82f6', '#f59e0b', '#10b981'] },
  { label: 'Wed', total: 38000, colors: ['#3b82f6', '#8b5cf6'] },
  { label: 'Thu', total: 89000, colors: ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6'] },
  { label: 'Fri', total: 55000, colors: ['#3b82f6', '#10b981'] },
  { label: 'Sat', total: 12000, colors: ['#3b82f6'] },
  { label: 'Sun', total: 15000, colors: ['#3b82f6', '#8b5cf6'], selected: true }
]

const maxVal = 100000

// Detail items for the "expanded" day
const mockDetails = [
  { name: 'Chatbot', calls: 42, input: 8420, output: 4150, color: '#3b82f6', icon: MessageSquare },
  { name: 'Auto Score', calls: 12, input: 12400, output: 2800, color: '#f59e0b', icon: Brain }
]
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Token Statistics Visualization -->
      <div class="usage-visual">
        <div class="visual-stack">
          <!-- 1. Usage History Chart -->
          <div class="chart-box glass-card">
            <div class="chart-header">
              <div class="c-title">Token History (7 Days)</div>
              <div class="c-peak">Peak: 89k</div>
            </div>
            <div class="chart-bars">
              <div v-for="d in mockChartData" :key="d.label" class="bar-col" :class="{ selected: d.selected }">
                <div class="bar-val" v-if="d.selected">{{ d.total.toLocaleString() }}</div>
                <div class="bar-fill" :style="{ 
                  height: (d.total / maxVal * 150) + 'px',
                  background: d.colors.length > 1 
                    ? `linear-gradient(to top, ${d.colors.join(', ')})`
                    : d.colors[0]
                }"></div>
                <div class="bar-lab">{{ d.label }}</div>
              </div>
            </div>
          </div>

          <!-- 2. Detailed Breakdown (Expanded Day) -->
          <div class="details-box">
            <div class="details-header">
              <Clock :size="14" />
              <span>Detailed Breakdown (Sunday)</span>
            </div>
            <div class="func-list">
              <div v-for="f in mockDetails" :key="f.name" class="func-mini-card glass-card">
                <div class="f-head">
                  <div class="f-identity">
                    <div class="f-icon-box" :style="{ color: f.color, background: f.color + '15' }">
                      <component :is="f.icon" :size="12" />
                    </div>
                    <strong>{{ f.name }}</strong>
                  </div>
                  <span class="f-calls">{{ f.calls }} calls</span>
                </div>
                <div class="f-metrics">
                  <div class="f-m"><span>Input</span><strong>{{ f.input }}</strong></div>
                  <div class="f-m"><span>Output</span><strong>{{ f.output }}</strong></div>
                  <div class="f-m total"><span>Total</span><strong>{{ f.input + f.output }}</strong></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="usage-details">
          <div class="detail-block">
            <h3>Granular Consumption Tracking</h3>
            <p>We monitor every single token processed by our agents. Usage is attributed to both the <strong>User</strong> and the specific <strong>Tool</strong> (e.g., <em>auto_score</em>, <em>chatbot</em>), providing total transparency.</p>
          </div>
          <div class="detail-block">
            <h3>Cost & Resource Management</h3>
            <p>Our analytics dashboard helps recruiters manage operational costs by identifying high-volume tasks and potential anomalies in LLM behavior before they impact the budget.</p>
          </div>
          <div class="detail-block">
            <h3>Identity-Aware Auditing</h3>
            <p>Because every tool call is linked to a user session, we maintain a complete audit trail of how AI resources are being utilized across different users and roles.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.slide-content-container {
  max-width: 1200px;
  width: 100%;
}

.slide-main {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 5rem;
  align-items: center;
}

/* Usage Visual */
.usage-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(-5deg);
}

/* Chart Box */
.chart-box {
  padding: 1.5rem;
  background: var(--bg-subtle);
  border-color: var(--border);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}
.c-title { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: var(--muted); }
.c-peak { font-size: 0.7rem; font-weight: 800; color: var(--accent); }

.chart-bars {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 180px;
  padding: 0 0.5rem;
}

.bar-col {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
  position: relative;
}

.bar-fill {
  width: 100%;
  border-radius: 4px 4px 0 0;
  transition: all 0.3s ease;
  opacity: 0.4;
}

.bar-col.selected .bar-fill { opacity: 1; box-shadow: 0 0 20px rgba(59, 130, 246, 0.3); }

.bar-val {
  position: absolute;
  top: -20px;
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--accent);
  white-space: nowrap;
}

.bar-lab {
  margin-top: 0.75rem;
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
}

.bar-col.selected .bar-lab { color: var(--accent); }

/* Details Box */
.details-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.details-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--headings);
}

.func-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
}

.func-mini-card {
  padding: 0.75rem;
  background: var(--bg);
  border: 1px solid var(--border);
}

.f-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.f-identity { display: flex; align-items: center; gap: 0.5rem; }
.f-icon-box {
  width: 24px; height: 24px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
}
.f-identity strong { font-size: 0.75rem; color: var(--headings); }
.f-calls { font-size: 0.6rem; color: var(--muted); font-weight: 700; }

.f-metrics {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 0.4rem;
  background: var(--bg-subtle);
  padding: 0.4rem;
  border-radius: 4px;
}

.f-m { display: flex; flex-direction: column; gap: 0.1rem; }
.f-m span { font-size: 0.5rem; text-transform: uppercase; color: var(--muted); }
.f-m strong { font-size: 0.65rem; color: var(--text); }
.f-m.total strong { color: var(--accent); }

/* Text Side */
.slide-text {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.slide-subtitle {
  font-size: 1rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.slide-title {
  font-size: 3.5rem;
  line-height: 1.1;
  margin: 0;
  color: var(--headings);
}

.usage-details {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.detail-block h3 {
  font-size: 1.25rem;
  margin-bottom: 0.75rem;
  color: var(--text);
  border-left: 3px solid var(--accent);
  padding-left: 1rem;
}

.detail-block p {
  font-size: 1.1rem;
  color: var(--muted);
  line-height: 1.6;
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
