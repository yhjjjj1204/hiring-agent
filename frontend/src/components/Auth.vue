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
      status.value = data.detail || 'Authentication failed'
      statusClass.value = 'err'
      return
    }

    if (isLogin.value) {
      localStorage.setItem('token', data.access_token)
      const userRes = await fetch(`/auth/me?token=${data.access_token}`)
      const userData = await userRes.json()
      localStorage.setItem('user', JSON.stringify(userData))
      emit('authenticated', userData)
    } else {
      status.value = 'Account created successfully! Please log in.'
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
  <div class="auth-container">
    <div class="auth-card glass-card">
      <div class="auth-header">
        <div class="auth-icon">🔐</div>
        <h2>{{ isLogin ? 'Welcome Back' : 'Create Account' }}</h2>
        <p class="auth-subtitle">{{ isLogin ? 'Sign in to access your recruitment dashboard' : 'Join the next generation of AI-driven hiring' }}</p>
      </div>
      
      <form @submit.prevent="submit" class="auth-form">
        <div class="form-group">
          <label>Username</label>
          <input v-model="username" type="text" placeholder="Enter your username" required />
        </div>
        
        <div class="form-group">
          <label>Password</label>
          <input v-model="password" type="password" placeholder="••••••••" required />
        </div>
        
        <div v-if="!isLogin" class="form-group">
          <label>Select Role</label>
          <div class="role-selector">
            <label :class="['role-option', { active: role === 'candidate' }]">
              <input type="radio" value="candidate" v-model="role" />
              <span>Candidate</span>
            </label>
            <label :class="['role-option', { active: role === 'recruiter' }]">
              <input type="radio" value="recruiter" v-model="role" />
              <span>Recruiter</span>
            </label>
          </div>
        </div>
        
        <div class="auth-actions">
          <button type="submit" class="full-width">{{ isLogin ? 'Sign In' : 'Register' }}</button>
          <button type="button" class="secondary full-width" @click="isLogin = !isLogin">
            {{ isLogin ? "Don't have an account? Register" : 'Already have an account? Login' }}
          </button>
        </div>
      </form>
      
      <p v-if="status" :class="['status-msg', statusClass]">{{ status }}</p>
    </div>
  </div>
</template>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 2rem;
}

.auth-card {
  width: 100%;
  max-width: 480px;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.auth-header { text-align: center; }
.auth-icon { 
  font-size: 2.5rem; 
  margin-bottom: 1rem;
  background: var(--glass-border);
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  margin-left: auto;
  margin-right: auto;
}
.auth-subtitle { color: var(--muted); font-size: 0.95rem; margin-top: 0.5rem; }

.auth-form { display: flex; flex-direction: column; gap: 1.5rem; }

.role-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 0.5rem;
}

.role-option {
  position: relative;
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid var(--glass-border);
  padding: 0.75rem;
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s ease;
  margin: 0;
  display: block;
}

.role-option input { display: none; }
.role-option span { 
  font-size: 0.9rem; 
  font-weight: 700; 
  color: var(--muted); 
  text-transform: none;
}

.role-option.active {
  border-color: var(--accent);
  background: var(--accent-glow);
}
.role-option.active span { color: white; }

.auth-actions { display: flex; flex-direction: column; gap: 1rem; margin-top: 1rem; }
.full-width { width: 100%; }

.status-msg {
  text-align: center;
  font-size: 0.9rem;
  font-weight: 600;
  padding: 0.75rem;
  border-radius: 8px;
}
.status-msg.err { background: rgba(239, 68, 68, 0.1); color: var(--err); border: 1px solid rgba(239, 68, 68, 0.2); }
.status-msg.ok { background: rgba(16, 185, 129, 0.1); color: var(--ok); border: 1px solid rgba(16, 185, 129, 0.2); }
</style>
