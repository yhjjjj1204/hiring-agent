<script setup>
import { ref } from 'vue'

const props = defineProps(['modelValue'])
const emit = defineEmits(['update:modelValue', 'authenticated'])

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const role = ref('candidate')
const status = ref('')
const statusClass = ref('')

async function submit() {
  const url = isLogin.value ? '/auth/login' : '/auth/register'
  const payload = {
    username: username.value,
    password: password.value,
    role: role.value
  }

  try {
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })
    const data = await res.json()

    if (!res.ok) {
      status.value = data.detail || 'Error'
      statusClass.value = 'err'
      return
    }

    if (isLogin.value) {
      localStorage.setItem('token', data.access_token)
      // Get user info
      const userRes = await fetch(`/auth/me?token=${data.access_token}`)
      const userData = await userRes.json()
      localStorage.setItem('user', JSON.stringify(userData))
      emit('authenticated', userData)
    } else {
      status.value = 'Registered successfully! Please login.'
      statusClass.value = 'ok'
      isLogin.value = true
    }
  } catch (e) {
    status.value = e.message
    statusClass.value = 'err'
  }
}
</script>

<template>
  <div class="auth-wrap">
    <h2>{{ isLogin ? 'Login' : 'Register' }}</h2>
    <div class="form-group">
      <label>Username</label>
      <input v-model="username" type="text" />
    </div>
    <div class="form-group">
      <label>Password</label>
      <input v-model="password" type="password" />
    </div>
    <div v-if="!isLogin" class="form-group">
      <label>Role</label>
      <select v-model="role">
        <option value="candidate">Candidate</option>
        <option value="recruiter">Recruiter</option>
      </select>
    </div>
    <div class="actions">
      <button @click="submit">{{ isLogin ? 'Login' : 'Register' }}</button>
      <button class="secondary" @click="isLogin = !isLogin">
        {{ isLogin ? 'Need an account?' : 'Already have an account?' }}
      </button>
    </div>
    <p :class="statusClass">{{ status }}</p>
  </div>
</template>

<style scoped>
.auth-wrap {
  max-width: 400px;
  margin: 2rem auto;
  padding: 2rem;
  border: 1px solid var(--border);
  border-radius: 12px;
  background: var(--bg-card);
}
.form-group { margin-bottom: 1rem; }
label { display: block; margin-bottom: 0.5rem; }
input, select { width: 100%; padding: 0.5rem; border-radius: 4px; border: 1px solid var(--border); background: var(--bg); color: var(--fg); }
.actions { display: flex; gap: 1rem; margin-top: 1rem; }
.secondary { background: transparent; border: 1px solid var(--border); }
.err { color: var(--err); margin-top: 1rem; }
.ok { color: var(--ok); margin-top: 1rem; }
</style>
