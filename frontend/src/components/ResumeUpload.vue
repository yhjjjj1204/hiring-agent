<script setup>
import { ref } from 'vue'
import { FileUp } from 'lucide-vue-next'

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
      <div class="upload-icon-wrap">
        <FileUp :size="32" class="upload-icon" />
      </div>
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
  border: 1px dashed var(--border);
  background: var(--bg);
  border-radius: 4px;
  padding: 2.5rem 2rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}

.upload-box:hover, .upload-box.is-over {
  border-color: var(--accent);
  background: rgba(59, 130, 246, 0.05);
}

.upload-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.upload-icon-wrap {
  width: 56px;
  height: 56px;
  background: var(--bg-subtle);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--border);
  color: var(--muted);
  transition: all 0.2s ease;
}
.upload-box:hover .upload-icon-wrap {
  color: var(--accent);
  border-color: var(--accent);
  background: var(--accent-glow);
}

.main-text { font-size: 1rem; font-weight: 700; color: #fff; }
.sub-text { font-size: 0.8rem; color: var(--muted); }

.file-info { display: flex; flex-direction: column; gap: 0.25rem; }
.file-name { font-weight: 700; color: var(--ok); font-size: 1rem; }
.change-link { font-size: 0.75rem; color: var(--accent); font-weight: 700; text-transform: uppercase; }

.is-over::after {
  content: 'Drop to upload';
  position: absolute;
  inset: 0;
  background: var(--accent);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.1rem;
  opacity: 0.95;
}
</style>
