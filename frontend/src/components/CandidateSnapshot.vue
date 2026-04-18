<script setup>
const props = defineProps(['arrangedResume'])
</script>

<template>
  <div class="resume-snapshot">
    <div v-if="!arrangedResume">No structured data available.</div>
    <div v-else class="snapshot-content">
      
      <!-- Summary -->
      <div v-if="arrangedResume.summary" class="section">
        <h4>Professional Summary</h4>
        <p>{{ arrangedResume.summary }}</p>
      </div>

      <!-- Education -->
      <div v-if="arrangedResume.education?.length" class="section">
        <h4>Education</h4>
        <div v-for="(edu, idx) in arrangedResume.education" :key="idx" class="item">
          <div class="item-header">
            <strong>{{ edu.institution }}</strong>
            <span>{{ edu.start }} - {{ edu.end }}</span>
          </div>
          <div class="item-sub">
            <span v-if="edu.degree">{{ edu.degree }}</span>
            <span v-if="edu.field"> in {{ edu.field }}</span>
          </div>
          <p v-if="edu.summary" class="item-desc">{{ edu.summary }}</p>
        </div>
      </div>

      <!-- Experience -->
      <div v-if="arrangedResume.experience?.length" class="section">
        <h4>Experience</h4>
        <div v-for="(exp, idx) in arrangedResume.experience" :key="idx" class="item">
          <div class="item-header">
            <strong>{{ exp.company }}</strong>
            <span>{{ exp.start }} - {{ exp.end }} <small v-if="exp.duration">({{ exp.duration }})</small></span>
          </div>
          <div class="item-sub">{{ exp.title }} <span v-if="exp.location">| {{ exp.location }}</span></div>
          <p v-if="exp.summary" class="item-desc">{{ exp.summary }}</p>
          <ul v-if="exp.highlights?.length" class="highlights">
            <li v-for="(hi, hIdx) in exp.highlights" :key="hIdx">{{ hi }}</li>
          </ul>
        </div>
      </div>

      <!-- Projects -->
      <div v-if="arrangedResume.projects?.length" class="section">
        <h4>Projects & Research</h4>
        <div v-for="(prj, idx) in arrangedResume.projects" :key="idx" class="item">
          <div class="item-header">
            <strong>{{ prj.title }}</strong>
            <span>{{ prj.start }} - {{ prj.end }} <small v-if="prj.duration">({{ prj.duration }})</small></span>
          </div>
          <p v-if="prj.summary" class="item-desc">{{ prj.summary }}</p>
        </div>
      </div>

      <!-- Skills -->
      <div v-if="arrangedResume.skills?.length" class="section">
        <h4>Skills</h4>
        <div class="skills-grid">
          <div v-for="(sk, idx) in arrangedResume.skills" :key="idx" class="skill-pill">
            <span class="skill-name">{{ sk.name }}</span>
            <span :class="['skill-rating', { 'na': sk.rating === 'N/A' }]">{{ sk.rating }}</span>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
.resume-snapshot { color: var(--fg); }
.section { margin-bottom: 2rem; }
.section h4 { 
  margin-bottom: 1rem; 
  padding-bottom: 0.5rem; 
  border-bottom: 1px solid var(--border); 
  color: var(--ok);
  font-size: 1.1rem;
}

.item { margin-bottom: 1.5rem; }
.item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.25rem; }
.item-header span { font-size: 0.85rem; color: var(--muted); }
.item-sub { font-weight: 500; font-size: 0.95rem; margin-bottom: 0.5rem; }
.item-desc { font-size: 0.9rem; color: var(--muted); line-height: 1.5; margin-bottom: 0.5rem; }

.highlights { margin-top: 0.5rem; padding-left: 1.2rem; font-size: 0.9rem; color: var(--muted); }
.highlights li { margin-bottom: 0.25rem; }

.skills-grid { display: flex; flex-wrap: wrap; gap: 0.75rem; }
.skill-pill { 
  display: flex; 
  background: var(--bg); 
  border: 1px solid var(--border); 
  border-radius: 6px; 
  overflow: hidden; 
  font-size: 0.85rem; 
}
.skill-name { padding: 0.25rem 0.6rem; background: var(--bg-card); }
.skill-rating { padding: 0.25rem 0.6rem; background: var(--border); color: var(--fg); font-weight: bold; }
.skill-rating.na { font-weight: normal; color: var(--muted); opacity: 0.7; }

small { font-size: 0.8rem; opacity: 0.8; }
</style>
