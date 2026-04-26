<script setup>
import { 
  FileText, 
  Github, 
  GraduationCap, 
  User, 
  Brain, 
  CheckCircle, 
  ShieldCheck, 
  Zap,
  ArrowRight,
  FileUp
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Resume Management Visualization -->
      <div class="resume-mgmt-visual">
        <div class="visual-stack">
          <!-- 1. The Central Identity Card -->
          <div class="manager-demo glass-card">
            <div class="demo-header">
              <div class="header-left">
                <FileText :size="16" class="icon-accent" />
                <span>Resume Manager</span>
              </div>
              <div class="header-status ok">Ready</div>
            </div>

            <div class="demo-upload-box">
              <div class="u-icon"><FileUp :size="24" /></div>
              <div class="u-info">
                <strong>resume_alex_rivera.pdf</strong>
                <span>Analyzed & Verified</span>
              </div>
            </div>

            <div class="demo-links-row">
              <div class="demo-link-item">
                <label><Github :size="10" /> GitHub</label>
                <div class="fake-val">alex_rivera</div>
              </div>
              <div class="demo-link-item">
                <label><GraduationCap :size="10" /> Scholar</label>
                <div class="fake-val">scholar.google...</div>
              </div>
            </div>

            <div class="demo-apply-section">
              <div class="apply-header">
                <Zap :size="14" class="icon-warn" />
                <span>Job Application: AI Lead</span>
              </div>
              <div class="statement-box">
                <label>Personal Statement (200 words)</label>
                <div class="fake-textarea">
                  I am particularly excited about this role because my foundational work in...
                </div>
              </div>
            </div>
          </div>

          <!-- 2. Efficiency Architecture -->
          <div class="efficiency-flow">
            <div class="eff-node glass-card">
              <RefreshCw :size="14" />
              <span>One-Time Analysis</span>
            </div>
            <div class="eff-node glass-card">
              <ShieldCheck :size="14" />
              <span>Cached Background</span>
            </div>
            <div class="eff-node glass-card highlight">
              <Zap :size="14" />
              <span>Contextual Scoring</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="mgmt-details">
          <div class="detail-block">
            <h3>Centralized Candidate Identity</h3>
            <p>Candidates maintain a single, "Source of Truth" profile. Uploading a resume triggers a comprehensive <strong>one-time analysis</strong> of their professional background, which is then cached for all future applications.</p>
          </div>
          <div class="detail-block">
            <h3>Efficient External Validation</h3>
            <p>Background data from <strong>GitHub</strong> and <strong>Google Scholar</strong> is fetched and mapped only once. This reduces API overhead and ensures recruiters see a stable, verified overview of a candidate's technical footprint.</p>
          </div>
          <div class="detail-block">
            <h3>Contextual Personalization</h3>
            <p>For each specific role, candidates can provide a tailored <strong>200-word statement</strong>. This targeted input is dynamically merged with their core profile, allowing the Scoring Agent to evaluate fit for that specific position.</p>
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

/* Resume Management Visual */
.resume-mgmt-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(5deg);
}

/* Manager Demo Card */
.manager-demo {
  padding: 1.5rem;
  background: var(--bg-subtle);
  border-color: var(--border);
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.demo-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.75rem;
}

.header-status.ok { color: var(--ok); background: var(--ok-glow); padding: 0.1rem 0.4rem; border-radius: 4px; font-size: 0.6rem; }

.demo-upload-box {
  background: var(--bg);
  border: 1px dashed var(--border);
  padding: 1rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.u-icon { color: var(--accent); }
.u-info { display: flex; flex-direction: column; }
.u-info strong { font-size: 0.8rem; color: var(--ok); }
.u-info span { font-size: 0.65rem; color: var(--muted); }

.demo-links-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.demo-link-item label { 
  display: flex; align-items: center; gap: 0.3rem; 
  font-size: 0.6rem; font-weight: 800; text-transform: uppercase; 
  color: var(--muted); margin-bottom: 0.25rem;
}
.fake-val { 
  font-size: 0.75rem; padding: 0.4rem; 
  background: var(--bg); border: 1px solid var(--border); 
  border-radius: 4px; color: var(--text);
}

.demo-apply-section {
  background: var(--header-bg);
  border: 1px solid var(--warn-glow);
  padding: 1rem;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.apply-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.7rem;
  font-weight: 800;
  color: var(--warn);
}

.statement-box label { font-size: 0.6rem; color: var(--muted); margin-bottom: 0.25rem; display: block; }
.fake-textarea { 
  height: 60px; font-size: 0.7rem; padding: 0.5rem; 
  background: var(--bg); border: 1px solid var(--border); 
  border-radius: 4px; color: var(--text); font-style: italic;
  overflow: hidden;
}

/* Efficiency architecture nodes */
.efficiency-flow {
  display: flex;
  gap: 1rem;
}

.eff-node {
  flex: 1;
  padding: 0.6rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  font-size: 0.65rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--muted);
}

.eff-node.highlight {
  border-color: var(--ok);
  background: var(--ok-glow);
  color: var(--ok);
}

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

.mgmt-details {
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
