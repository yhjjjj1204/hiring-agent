<script setup>
import { 
  Lock, 
  ShieldCheck, 
  UserCircle, 
  UserSearch, 
  Key, 
  Server,
  Network,
  Cpu,
  ArrowRight
} from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container">
    <div class="slide-main">
      <!-- Auth & Role Visualization -->
      <div class="auth-visual">
        <div class="visual-stack">
          <!-- 1. Login UI Demo -->
          <div class="auth-demo-slice glass-card">
            <div class="demo-auth-header">
              <div class="demo-auth-icon"><Lock :size="24" /></div>
              <h4>Account Access</h4>
            </div>
            <div class="demo-fields">
              <div class="demo-input"><span>Username</span><div class="fake-input"></div></div>
              <div class="demo-input"><span>Password</span><div class="fake-input"></div></div>
            </div>
            <div class="demo-roles-mini">
              <div class="role-pill-mini active"><UserCircle :size="12" /> Candidate</div>
              <div class="role-pill-mini"><UserSearch :size="12" /> Recruiter</div>
            </div>
            <div class="demo-btn">Sign In</div>
          </div>

          <!-- 2. Technical Hardening Architecture -->
          <div class="auth-arch-flow">
            <div class="arch-box glass-card">
              <Server :size="16" class="icon-accent" />
              <div class="arch-info">
                <strong>Harden Gateway (Nginx)</strong>
                <span>Role-based IP/Path Gating</span>
              </div>
            </div>
            <div class="arch-connector"><ArrowRight :size="14" /></div>
            <div class="arch-box glass-card ok">
              <Key :size="16" class="icon-ok" />
              <div class="arch-info">
                <strong>Bearer Token Auth</strong>
                <span>Validated on every API call</span>
              </div>
            </div>
          </div>

          <!-- 3. LLM Session Harness -->
          <div class="harness-context glass-card">
            <div class="harness-header">
              <Cpu :size="16" class="icon-warn" />
              <span>Identity-Aware LLM Session</span>
            </div>
            <div class="context-pills">
              <div class="ctx-pill">user_id: 0824c...</div>
              <div class="ctx-pill role">role: recruiter</div>
            </div>
            <p class="harness-desc">Permissions pass down to AI tool execution</p>
          </div>
        </div>
      </div>

      <!-- Text Content -->
      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <div class="auth-details">
          <div class="detail-block">
            <h3>Role-Based Access Control (RBAC)</h3>
            <p>The platform maintains strict separation between <strong>Recruiters</strong> and <strong>Candidates</strong>. This isolation is enforced at the network level using distinct API endpoints, enabling targeted hardening via reverse proxies.</p>
          </div>
          <div class="detail-block">
            <h3>Stateless Token Security</h3>
            <p>Every request is secured by a Bearer token. Identity is established at the gateway, ensuring that unauthorized users cannot traverse paths or access data outside their assigned role.</p>
          </div>
          <div class="detail-block">
            <h3>End-to-End Identity Flow</h3>
            <p>User identity and role permissions are not just for the UI. They are passed directly into the <strong>AI Orchestration Harness</strong>, ensuring that LLM agents only execute tools and access data matching the user's active session.</p>
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

/* Auth Visual */
.auth-visual {
  perspective: 1200px;
}

.visual-stack {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  transform: rotateY(-5deg);
}

/* Auth Demo Slice */
.auth-demo-slice {
  padding: 1.5rem;
  background: var(--bg-subtle);
  border-color: var(--border);
  width: 320px;
  margin: 0 auto;
}

.demo-auth-header { text-align: center; margin-bottom: 1.25rem; }
.demo-auth-icon { 
  width: 48px; height: 48px; background: var(--glass); 
  border: 1px solid var(--border); border-radius: 8px; 
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 0.75rem auto; color: var(--accent);
}
.demo-auth-header h4 { margin: 0; font-size: 1rem; color: var(--headings); }

.demo-fields { display: flex; flex-direction: column; gap: 0.75rem; margin-bottom: 1rem; }
.demo-input span { font-size: 0.6rem; font-weight: 800; text-transform: uppercase; color: var(--muted); margin-bottom: 0.2rem; display: block; }
.fake-input { height: 32px; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; }

.demo-roles-mini { display: flex; gap: 0.5rem; margin-bottom: 1.25rem; }
.role-pill-mini { 
  flex: 1; font-size: 0.6rem; font-weight: 800; padding: 0.4rem; 
  background: var(--bg); border: 1px solid var(--border); border-radius: 4px;
  display: flex; align-items: center; justify-content: center; gap: 0.3rem; color: var(--muted);
}
.role-pill-mini.active { border-color: var(--accent); background: var(--accent-glow); color: var(--headings); }

.demo-btn { 
  background: var(--accent); color: white; text-align: center; 
  padding: 0.6rem; border-radius: 4px; font-weight: 800; font-size: 0.8rem;
}

/* Arch Flow */
.auth-arch-flow { display: flex; align-items: center; gap: 1rem; }
.arch-box { 
  flex: 1; padding: 0.75rem; display: flex; align-items: center; gap: 0.75rem; 
  border-style: dashed;
}
.arch-box.ok { border-color: var(--ok); background: var(--ok-glow); }
.arch-info { display: flex; flex-direction: column; }
.arch-info strong { font-size: 0.7rem; color: var(--headings); }
.arch-info span { font-size: 0.55rem; color: var(--muted); }
.arch-connector { color: var(--border); }

/* Harness Context */
.harness-context { padding: 1rem; background: var(--bg-accent); border-color: var(--warn); }
.harness-header { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; font-weight: 800; color: var(--warn); margin-bottom: 0.75rem; }
.context-pills { display: flex; gap: 0.5rem; margin-bottom: 0.5rem; }
.ctx-pill { font-family: monospace; font-size: 0.6rem; padding: 0.2rem 0.5rem; background: var(--bg); border: 1px solid var(--border); border-radius: 4px; color: var(--muted); }
.ctx-pill.role { border-color: var(--ok); color: var(--ok); }
.harness-desc { font-size: 0.65rem; color: var(--muted); margin: 0; font-style: italic; }

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

.auth-details {
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
