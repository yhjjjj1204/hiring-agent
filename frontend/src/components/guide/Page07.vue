<script setup>
import { 
  EyeOff, 
  UserX, 
  ShieldCheck, 
  FileText, 
  ArrowRight,
  Fingerprint,
  Mail,
  User,
  Search,
  Scan
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Blind Screening Visualization -->
      <div class="blind-visual">
        <div class="visual-stack">
          <!-- 1. Raw Profile (With Identifiers) -->
          <div class="profile-raw glass-card">
            <div class="profile-h">
              <User :size="16" /> Raw Candidate Profile
            </div>
            <div class="raw-data">
              <div class="data-line ident"><Mail :size="10" /> alex.rivera@gmail.com</div>
              <div class="data-line ident"><Fingerprint :size="10" /> Name: Alex Rivera</div>
              <div class="data-line ident">Gender: Male</div>
              <div class="data-line">Lead Engineer at TechFlow...</div>
              <div class="data-line">Expert in Kubernetes...</div>
            </div>
            <div class="bias-indicator">High Bias Risk</div>
          </div>

          <!-- 2. The Sanitization Process -->
          <div class="sanitizer-engine">
            <div class="scan-bar"></div>
            <div class="processor glass-card">
              <EyeOff :size="20" class="icon-warn" />
              <span>Bias Neutralizer</span>
            </div>
          </div>

          <!-- 3. Blinded Profile (Safe for Scoring) -->
          <div class="profile-blinded glass-card">
            <div class="profile-h ok">
              <ShieldCheck :size="16" /> Blinded Profile
            </div>
            <div class="blinded-data">
              <div class="data-line redacted">[identifier removed]</div>
              <div class="data-line redacted">Name: [blinded]</div>
              <div class="data-line redacted">Gender: [blinded]</div>
              <div class="data-line">Lead Engineer at TechFlow...</div>
              <div class="data-line">Expert in Kubernetes...</div>
            </div>
            <div class="neutral-indicator">Merit-Only Analysis</div>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="blind-details">
          <div class="detail-block">
            <h3>Eliminating Unconscious Bias</h3>
            <p>HiringAgent automatically redacts PII (Personally Identifiable Information) before candidate data reaches the Scoring Agent. By removing <strong>Names</strong>, <strong>Emails</strong>, <strong>Gender</strong>, and <strong>Photos</strong>, we ensure evaluation is based strictly on merit.</p>
          </div>
          <div class="detail-block">
            <h3>Preventing Identity Inference</h3>
            <p>Modern LLMs are aware of many industry professionals. We strip specific identifiers that could allow the model to "guess" who the candidate is, preventing famous or well-known individuals from receiving an unfair advantage.</p>
          </div>
          <div class="detail-block">
            <h3>Focus on Professional Impact</h3>
            <p>The sanitization layer preserves all professional highlights, skills, and metrics while stripping away age or demographic markers. This forces the competing experts to judge candidates solely on their <strong>actual technical contributions</strong>.</p>
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
  grid-template-columns: 1fr 1fr;
  gap: 5rem;
  align-items: center;
}

/* Blind Visual */
.blind-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(5deg);
}

.profile-h {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 0.8rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--headings);
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.5rem;
}
.profile-h.ok { color: var(--ok); border-color: var(--ok-glow); }

.profile-raw, .profile-blinded {
  padding: 1.25rem;
  width: 320px;
  margin: 0 auto;
}

.profile-raw { border-color: var(--err-glow); background: rgba(239, 68, 68, 0.05); }
.profile-blinded { border-color: var(--ok); background: rgba(16, 185, 129, 0.05); }

.data-line {
  font-size: 0.75rem;
  color: var(--muted);
  margin-bottom: 0.5rem;
  padding: 0.2rem 0.4rem;
  background: var(--bg);
  border-radius: 4px;
}

.data-line.ident { border-left: 2px solid var(--err); color: var(--text); }
.data-line.redacted { color: var(--ok); font-weight: 700; border-left: 2px solid var(--ok); }

.bias-indicator {
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--err);
  text-align: right;
  margin-top: 0.5rem;
}

.neutral-indicator {
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  color: var(--ok);
  text-align: right;
  margin-top: 0.5rem;
}

/* Sanitizer Engine */
.sanitizer-engine {
  position: relative;
  display: flex;
  justify-content: center;
  margin: 0.5rem 0;
}

.processor {
  padding: 0.75rem 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--header-bg);
  border-style: dashed;
  z-index: 5;
}

.processor span { font-size: 0.75rem; font-weight: 800; text-transform: uppercase; color: var(--warn); }

.scan-bar {
  position: absolute;
  top: 50%;
  left: 0;
  width: 100%;
  height: 2px;
  background: linear-gradient(to right, transparent, var(--warn), transparent);
  animation: scan 2s infinite ease-in-out;
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

.blind-details {
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

@keyframes scan {
  0% { transform: translateY(-30px); opacity: 0; }
  50% { opacity: 1; }
  100% { transform: translateY(30px); opacity: 0; }
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
  }
}
</style>
