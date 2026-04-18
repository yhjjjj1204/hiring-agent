<script setup>
const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

function update(key, val) {
  emit('update:modelValue', { ...props.modelValue, [key]: val })
}
</script>

<template>
  <div class="job-input glass-card">
    <h3>Application Details</h3>
    <div class="form-grid">
      <div class="form-group full-width">
        <label>Job Description / Requirements</label>
        <textarea 
          :value="modelValue.jobDescription" 
          @input="update('jobDescription', $event.target.value)"
          placeholder="Paste the job description here..."
          rows="12"
        ></textarea>
      </div>
      
      <div class="form-group">
        <label>GitHub Username (Optional)</label>
        <input 
          type="text" 
          :value="modelValue.github" 
          @input="update('github', $event.target.value)"
          placeholder="e.g. octocat"
        />
      </div>
      
      <div class="form-group">
        <label>Scholar URL (Optional)</label>
        <input 
          type="text" 
          :value="modelValue.scholarUrl" 
          @input="update('scholarUrl', $event.target.value)"
          placeholder="Google Scholar profile link"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
.job-input { padding: 2rem; margin-top: 2rem; }
h3 { margin-bottom: 1.5rem; }
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }
.full-width { grid-column: span 2; }
</style>
