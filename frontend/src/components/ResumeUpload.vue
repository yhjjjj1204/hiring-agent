<script setup>
import { ref } from 'vue'

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue'])

const isDragOver = ref(false)
const fileInput = ref(null)

const ACCEPT = new Set([
  "application/pdf", "image/png", "image/jpeg", "image/webp", "image/gif",
  "image/bmp", "image/tiff", "image/x-ms-bmp",
]);
const ACCEPT_EXT = /\.(pdf|png|jpe?g|webp|gif|bmp|tiff?)$/i;

function humanSize(n) {
  if (n < 1024) return n + " B";
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + " KB";
  return (n / (1024 * 1024)).toFixed(1) + " MB";
}

function onFileChange(e) {
  const f = e.target.files && e.target.files[0];
  if (f) emit('update:modelValue', f);
}

function onDrop(e) {
  isDragOver.value = false;
  const files = e.dataTransfer && e.dataTransfer.files;
  if (!files || !files.length) return;
  const f = files[0];
  const okType = ACCEPT.has(f.type) || ACCEPT_EXT.test(f.name || "");
  if (okType) {
    emit('update:modelValue', f);
  }
}

function pickFile() {
  fileInput.value.click();
}
</script>

<template>
  <div class="row">
    <label>Resume file</label>
    <div 
      class="dropzone" 
      :class="{ dragover: isDragOver }"
      role="button" 
      tabindex="0" 
      aria-label="Choose file or drop resume here"
      @click="pickFile"
      @keydown.enter.prevent="pickFile"
      @keydown.space.prevent="pickFile"
      @dragenter.prevent="isDragOver = true"
      @dragover.prevent="isDragOver = true"
      @dragleave.prevent="isDragOver = false"
      @drop.prevent="onDrop"
    >
      <input 
        type="file" 
        ref="fileInput"
        id="file" 
        accept=".pdf,.png,.jpg,.jpeg,.webp,.gif,.bmp,.tiff,.tif,application/pdf" 
        @change="onFileChange"
      />
      <p class="dz-title">Click to choose a file, or drag and drop</p>
      <p class="dz-sub">PDF and common image formats</p>
      <p class="dz-file" :class="{ empty: !modelValue }">
        {{ modelValue ? `${modelValue.name} · ${humanSize(modelValue.size)}` : 'No file selected' }}
      </p>
    </div>
  </div>
</template>

<style scoped>
.row { margin-bottom: 1rem; }
.dropzone {
  border: 2px dashed var(--border);
  border-radius: 12px;
  padding: 1.25rem 1rem;
  text-align: center;
  background: #111923;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}
.dropzone:hover, .dropzone.dragover {
  border-color: var(--accent);
  background: #141d2a;
}
.dropzone .dz-title { font-size: 0.95rem; margin: 0 0 0.35rem; }
.dropzone .dz-sub { font-size: 0.8rem; color: var(--muted); margin: 0; }
.dropzone .dz-file {
  margin: 0.75rem 0 0;
  font-size: 0.9rem;
  color: var(--ok);
  word-break: break-all;
}
.dropzone .dz-file.empty { color: var(--muted); }
#file { position: absolute; width: 0; height: 0; opacity: 0; pointer-events: none; }
</style>
