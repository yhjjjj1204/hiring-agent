<script setup>
import { Sparkles, Briefcase, Bot, Plus, ChevronRight } from 'lucide-vue-next'

const props = defineProps({
  slide: Object
})
</script>

<template>
  <div class="slide-content-container with-demo">
    <div class="slide-main">
      <!-- Demo Slice (Recruiter Homepage) -->
      <div class="slide-demo-slice">
        <div class="demo-dashboard">
          <div class="demo-page-header">
            <div class="demo-header-titles">
              <h2>Active Positions</h2>
              <p>Manage your open roles</p>
            </div>
            <div class="demo-plus-btn">
              <Plus :size="14" /> Add Position
            </div>
          </div>

          <div class="demo-job-grid">
            <div class="demo-job-card glass-card">
              <div class="demo-card-header">
                <div class="demo-title-group">
                  <div class="demo-title-with-icon">
                    <Briefcase :size="14" class="icon-accent" />
                    <h4>Senior AI Engineer</h4>
                  </div>
                  <span class="demo-date">Posted 2 days ago</span>
                </div>
                <div class="demo-status-pill">Active</div>
              </div>
              <div class="demo-card-preview">
                <div class="demo-summary-tag"><Bot :size="10" /> AI Summary</div>
                <p>Focus on LLM orchestration and vector database optimization. Requires proficiency in Python and LangGraph.</p>
              </div>
              <div class="demo-card-footer">
                <span class="demo-type-badge">Corporate</span>
                <span class="demo-action-link">Manage <ChevronRight :size="12" /></span>
              </div>
            </div>

            <div class="demo-job-card glass-card dimmed-card">
              <div class="demo-card-header">
                <div class="demo-title-group">
                  <div class="demo-title-with-icon">
                    <Briefcase :size="14" />
                    <h4>Product Designer</h4>
                  </div>
                  <span class="demo-date">Posted 5 days ago</span>
                </div>
                <div class="demo-status-pill">Active</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="slide-text">
        <span class="slide-subtitle" :style="{ color: slide.color }">{{ slide.subtitle }}</span>
        <h1 class="slide-title">{{ slide.title }}</h1>
        <p class="slide-description">{{ slide.content }}</p>
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
  grid-template-columns: 1fr 1.2fr;
  gap: 5rem;
  align-items: center;
}

.slide-demo-slice {
  width: 100%;
  perspective: 1000px;
}

.demo-dashboard {
  background: var(--bg);
  padding: 1.5rem;
  transform: rotateY(15deg) rotateX(5deg);
  box-shadow: -30px 30px 60px rgba(0,0,0,0.5);
  border: 1px solid var(--border);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 480px;
  margin-right: auto;
}

.demo-page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  border-bottom: 1px solid var(--border);
  padding-bottom: 1rem;
}

.demo-header-titles h2 {
  font-size: 1.2rem;
  margin: 0;
}

.demo-header-titles p {
  font-size: 0.75rem;
  color: var(--muted);
  margin: 0;
}

.demo-plus-btn {
  background: var(--accent);
  color: white;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.demo-job-grid {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.demo-job-card {
  padding: 1rem;
  background: var(--bg-subtle);
}

.dimmed-card {
  opacity: 0.4;
  transform: scale(0.95) translateX(-10px);
}

.demo-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.demo-title-with-icon {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.2rem;
}

.demo-title-with-icon h4 {
  margin: 0;
  font-size: 0.95rem;
}

.demo-date {
  font-size: 0.65rem;
  color: var(--muted);
}

.demo-status-pill {
  font-size: 0.6rem;
  font-weight: 800;
  color: var(--ok);
  border: 1px solid var(--ok);
  padding: 0.1rem 0.4rem;
  border-radius: 2px;
  text-transform: uppercase;
}

.demo-card-preview {
  margin-bottom: 1rem;
}

.demo-summary-tag {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.55rem;
  font-weight: 800;
  color: var(--accent);
  margin-bottom: 0.3rem;
}

.demo-card-preview p {
  font-size: 0.75rem;
  margin: 0;
  line-height: 1.4;
  color: var(--muted);
}

.demo-card-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 0.75rem;
  border-top: 1px solid var(--border);
}

.demo-type-badge {
  font-size: 0.6rem;
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  color: var(--muted);
}

.demo-action-link {
  font-size: 0.75rem;
  font-weight: 700;
  color: var(--accent);
  display: flex;
  align-items: center;
  gap: 0.2rem;
}

.slide-text {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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

.slide-description {
  font-size: 1.4rem;
  line-height: 1.6;
  color: var(--muted);
  margin: 0;
}

@media (max-width: 1024px) {
  .slide-main {
    grid-template-columns: 1fr;
    gap: 3rem;
    text-align: center;
  }
  .slide-text {
    align-items: center;
  }
  .slide-title {
    font-size: 2.5rem;
  }
  .slide-description {
    font-size: 1.1rem;
  }
}
</style>
