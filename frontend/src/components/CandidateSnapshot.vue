<script setup>
import { computed } from 'vue'

const props = defineProps(['arrangedResume'])

const snapshotParts = computed(() => {
  const arr = props.arrangedResume || {}
  const parts = []
  if (arr.candidate_name) parts.push("Name: " + String(arr.candidate_name))
  if (arr.headline) parts.push("Headline: " + String(arr.headline))
  if (arr.summary) parts.push("Profile summary: " + String(arr.summary))
  
  if (Array.isArray(arr.experience) && arr.experience.length) {
    const lines = arr.experience.slice(0, 3).map((ex) => {
      const co = ex && ex.company ? String(ex.company) : ""
      const ti = ex && ex.title ? String(ex.title) : ""
      return (co && ti) ? (ti + " @ " + co) : (co || ti || "—")
    })
    parts.push("Recent roles: " + lines.join(" · "))
  }
  
  if (Array.isArray(arr.skills) && arr.skills.length) {
    const names = arr.skills.slice(0, 12).map((sk) => (sk && sk.name) ? String(sk.name) : "").filter(Boolean)
    if (names.length) parts.push("Skills (sample): " + names.join(", "))
  }
  return parts
})
</script>

<template>
  <div class="snap">
    <div v-if="!snapshotParts.length">No structured candidate fields returned.</div>
    <ul v-else>
      <li v-for="part in snapshotParts" :key="part">{{ part }}</li>
    </ul>
  </div>
</template>

<style scoped>
.snap { font-size: 0.88rem; color: var(--muted); }
.snap ul { margin: 0.35rem 0 0 1.1rem; padding: 0; }
.snap li { margin: 0.2rem 0; }
</style>
