<script setup>
import { 
  User, 
  GraduationCap, 
  Briefcase, 
  Rocket, 
  Wrench 
} from 'lucide-vue-next'

const props = defineProps(['arrangedResume'])
</script>

<template>
  <div class="resume-snapshot">
    <div v-if="!arrangedResume" class="empty-data">
      <div class="loader-mini"></div>
      Parsing data...
    </div>
    <div v-else class="snapshot-content">
      
      <!-- Summary -->
      <div v-if="arrangedResume.summary" class="section glass-card inner-card">
        <h4 class="section-title">
          <User :size="16" class="icon" />
          Professional Summary
        </h4>
        <p class="summary-text">{{ arrangedResume.summary }}</p>
      </div>

      <!-- Education (Timeline) -->
      <div v-if="arrangedResume.education?.length" class="section glass-card inner-card">
        <h4 class="section-title">
          <GraduationCap :size="16" class="icon" />
          Education
        </h4>
        <div class="timeline">
          <div v-for="(edu, idx) in arrangedResume.education" :key="idx" class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="timeline-header">
                <strong class="timeline-title">{{ edu.institution }}</strong>
                <span class="timeline-date">{{ edu.start }} - {{ edu.end }}</span>
              </div>
              <div class="timeline-sub">
                <span v-if="edu.degree" class="accent-text">{{ edu.degree }}</span>
                <span v-if="edu.field"> in {{ edu.field }}</span>
              </div>
              <p v-if="edu.summary" class="timeline-desc">{{ edu.summary }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Experience (Timeline) -->
      <div v-if="arrangedResume.experience?.length" class="section glass-card inner-card">
        <h4 class="section-title">
          <Briefcase :size="16" class="icon" />
          Work Experience
        </h4>
        <div class="timeline">
          <div v-for="(exp, idx) in arrangedResume.experience" :key="idx" class="timeline-item">
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div class="timeline-header">
                <strong class="timeline-title">{{ exp.company }}</strong>
                <div class="timeline-meta">
                  <span class="timeline-date">{{ exp.start }} - {{ exp.end }}</span>
                  <small v-if="exp.duration" class="duration-badge">{{ exp.duration }}</small>
                </div>
              </div>
              <div class="timeline-sub accent-text">{{ exp.title }}</div>
              <p v-if="exp.summary" class="timeline-desc">{{ exp.summary }}</p>
              <ul v-if="exp.highlights?.length" class="highlights">
                <li v-for="(hi, hIdx) in exp.highlights" :key="hIdx">{{ hi }}</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <!-- Projects -->
      <div v-if="arrangedResume.projects?.length" class="section glass-card inner-card">
        <h4 class="section-title">
          <Rocket :size="16" class="icon" />
          Projects & Research
        </h4>
        <div class="projects-grid">
          <div v-for="(prj, idx) in arrangedResume.projects" :key="idx" class="prj-card glass-card">
            <div class="prj-header">
              <strong>{{ prj.title }}</strong>
              <span class="prj-date">{{ prj.start }} - {{ prj.end }}</span>
            </div>
            <p v-if="prj.summary" class="prj-desc">{{ prj.summary }}</p>
            <small v-if="prj.duration" class="prj-duration">{{ prj.duration }}</small>
          </div>
        </div>
      </div>

      <!-- Skills -->
      <div v-if="arrangedResume.skills?.length" class="section glass-card inner-card">
        <h4 class="section-title">
          <Wrench :size="16" class="icon" />
          Technical Skills
        </h4>
        <div class="skills-flex">
          <div v-for="(sk, idx) in arrangedResume.skills" :key="idx" class="skill-chip">
            <span class="skill-name">{{ sk.name }}</span>
            <span :class="['skill-rating', { 'na': sk.rating === 'N/A' }]">{{ sk.rating }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.resume-snapshot { color: var(--text); }

.inner-card { 
  background: var(--bg); 
  border-color: var(--border);
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.section-title { 
  margin-bottom: 1.25rem; 
  padding-bottom: 0.5rem; 
  border-bottom: 1px solid var(--border); 
  color: var(--headings);
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.icon { color: var(--accent); opacity: 0.9; }

.summary-text { font-size: 0.95rem; line-height: 1.6; opacity: 0.9; }

/* Unified Timeline */
.timeline { display: flex; flex-direction: column; }
.timeline-item { 
  padding-left: 1.25rem; 
  padding-bottom: 1.5rem; 
  border-left: 1px solid var(--border); 
  position: relative; 
}
.timeline-item:last-child { border-left-color: transparent; padding-bottom: 0; }

.timeline-dot { 
  position: absolute; left: -5px; top: 0.45rem; 
  width: 9px; height: 9px; border-radius: 50%; background: var(--accent);
}

.timeline-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; margin-bottom: 0.3rem; }
.timeline-title { font-size: 1rem; color: var(--headings); line-height: 1.4; }
.timeline-date { font-size: 0.8rem; color: var(--muted); font-weight: 600; white-space: nowrap; margin-top: 0.2rem; }

.timeline-sub { font-size: 0.9rem; margin-bottom: 0.4rem; font-weight: 600; }
.accent-text { color: var(--accent); }

.timeline-desc { font-size: 0.9rem; color: var(--text); opacity: 0.85; line-height: 1.5; margin-bottom: 0.5rem; }

.highlights { padding-left: 1.1rem; font-size: 0.85rem; color: var(--muted); }
.highlights li { margin-bottom: 0.25rem; }

.timeline-meta { text-align: right; display: flex; flex-direction: column; gap: 0.2rem; }
.duration-badge { background: var(--bg-subtle); padding: 0.05rem 0.3rem; border-radius: 2px; font-size: 0.7rem; color: var(--muted); border: 1px solid var(--border); }

/* Projects */
.projects-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.prj-card { background: var(--glass); padding: 1rem; border-radius: 4px; border: 1px solid var(--border); }
.prj-header { display: flex; justify-content: space-between; margin-bottom: 0.5rem; }
.prj-date { font-size: 0.75rem; color: var(--muted); }
.prj-desc { font-size: 0.85rem; opacity: 0.8; margin-bottom: 0.5rem; line-height: 1.5; }
.prj-duration { color: var(--accent); font-weight: 700; font-size: 0.7rem; }

/* Skills */
.skills-flex { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.skill-chip { 
  display: flex; 
  background: var(--bg-subtle); 
  border: 1px solid var(--border); 
  border-radius: 4px; 
  overflow: hidden; 
  font-size: 0.8rem; 
}
.skill-name { padding: 0.2rem 0.5rem; font-weight: 600; }
.skill-rating { 
  padding: 0.2rem 0.4rem; 
  background: var(--border); 
  color: var(--accent); 
  font-weight: 700; 
}
.skill-rating.na { color: var(--muted); opacity: 0.5; }

.empty-data { text-align: center; padding: 2rem; color: var(--muted); display: flex; flex-direction: column; align-items: center; gap: 0.75rem; }
.loader-mini { border: 2px solid var(--border); border-top-color: var(--accent); width: 18px; height: 18px; border-radius: 50%; animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }

@media (max-width: 1000px) { .projects-grid { grid-template-columns: 1fr; } }
</style>
