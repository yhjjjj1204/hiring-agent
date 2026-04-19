<script setup>
import { useRouter } from 'vue-router'
import { FileQuestion, Home } from 'lucide-vue-next'

const router = useRouter()
function goHome() {
  router.push('/')
}
</script>

<template>
  <div class="not-found-container">
    <div class="not-found-card glass-card">
      <div class="icon-wrap">
        <FileQuestion :size="64" />
      </div>
      <h1>404</h1>
      <h3>Page Not Found</h3>
      <p>The resource you are looking for doesn't exist or has been moved.</p>
      <button @click="goHome">
        <Home :size="18" />
        Return to Dashboard
      </button>
    </div>
  </div>
</template>

<style scoped>
.not-found-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 60vh;
  padding: 2rem;
}

.not-found-card {
  max-width: 480px;
  width: 100%;
  padding: 4rem 2rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.icon-wrap {
  color: var(--accent);
  background: var(--accent-glow);
  padding: 1.5rem;
  border-radius: 12px;
  margin-bottom: 1rem;
}

h1 { font-size: 4rem; margin: 0; color: #fff; line-height: 1; }
h3 { font-size: 1.5rem; margin: 0; }
p { color: var(--muted); line-height: 1.6; }

button { margin-top: 1rem; padding: 0.75rem 2rem; }
</style>
