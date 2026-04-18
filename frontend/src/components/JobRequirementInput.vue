<script setup>
const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

function update(key, value) {
  emit('update:modelValue', { ...props.modelValue, [key]: value })
}
</script>

<template>
  <div class="row">
    <label for="jd">Job description / hiring requirements (minimum about 15 characters)</label>
    <textarea 
      id="jd" 
      :value="modelValue.jobDescription" 
      @input="update('jobDescription', $event.target.value)"
    ></textarea>
  </div>

  <div class="grid2">
    <div class="row">
      <label for="gh">GitHub (optional)</label>
      <input 
        type="text" 
        id="gh" 
        :value="modelValue.github"
        @input="update('github', $event.target.value)"
      />
    </div>
    <div class="row">
      <label for="scholar">Google Scholar profile URL (optional)</label>
      <input 
        type="text" 
        id="scholar" 
        :value="modelValue.scholarUrl"
        @input="update('scholarUrl', $event.target.value)"
      />
    </div>
  </div>

  <div class="row">
    <label for="nameOverride">Candidate name override (optional, for background lookup)</label>
    <input 
      type="text" 
      id="nameOverride" 
      :value="modelValue.nameOverride"
      @input="update('nameOverride', $event.target.value)"
    />
  </div>
</template>

<style scoped>
.row { margin-bottom: 1rem; }
.grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
@media (max-width: 640px) { .grid2 { grid-template-columns: 1fr; } }
</style>
