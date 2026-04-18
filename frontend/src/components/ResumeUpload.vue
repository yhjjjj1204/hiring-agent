<script setup>
import { ref } from 'vue'

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const isOver = ref(false)
const fileName = ref('')

function onDrop(e) {
  isOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    fileName.value = file.name
    emit('update:modelValue', file)
  }
}

function onFileChange(e) {
  const file = e.target.files[0]
  if (file) {
    fileName.value = file.name
    emit('update:modelValue', file)
  }
}
</script>

<template>
  <div 
    class="upload-box"
    :class="{ 'is-over': isOver }"
    @dragover.prevent="isOver = true"
    @dragleave.prevent="isOver = false"
    @drop.prevent="onDrop"
    @click="$refs.fileInput.click()"
  >
    <input 
      type="file" 
      ref="fileInput" 
      style="display: none" 
      accept=".pdf,.png,.jpg,.jpeg,.webp"
      @change="onFileChange" 
    />
    
    <div class="upload-content">
      <div class="upload-icon">📄</div>
      <div v-if="!fileName" class="upload-text">
        <p class="main-text">Click or drop resume here</p>
        <p class="sub-text">PDF, PNG, JPG or WebP (max 10MB)</p>
      </div>
      <div v-else class="file-info">
        <span class="file-name">{{ fileName }}</span>
        <span class="change-link">Change file</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.upload-box {
  border: 2px dashed var(--glass-border);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 16px;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.upload-box:hover, .upload-box.is-over {
  border-color: var(--accent);
  background: var(--accent-glow);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon {
  font-size: 3rem;
  opacity: 0.8;
  transition: transform 0.3s ease;
}
.upload-box:hover .upload-icon { transform: scale(1.1); }

.main-text { font-size: 1.1rem; font-weight: 700; color: var(--text); }
.sub-text { font-size: 0.85rem; color: var(--muted); }

.file-info { display: flex; flex-direction: column; gap: 0.5rem; }
.file-name { font-weight: 700; color: var(--ok); font-size: 1.1rem; }
.change-link { font-size: 0.8rem; color: var(--accent); font-weight: 600; text-transform: uppercase; }

.is-over::after {
  content: 'Drop to upload';
  position: absolute;
  inset: 0;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-size: 1.25rem;
  opacity: 0.9;
}
</style>
