<script setup>
import { ref } from 'vue'
import { Lock, UserCircle, UserSearch } from 'lucide-vue-next'

const emit = defineEmits(['authenticated'])

const isLogin = ref(true)
const username = ref('')
const password = ref('')
const role = ref('candidate')
const status = ref('')
const statusClass = ref('')

async function submit() {
  status.value = ''
  try {
    const url = isLogin.value ? '/api/auth/login' : '/api/auth/register'
    const body = isLogin.value 
      ? `username=${encodeURIComponent(username.value)}&password=${encodeURIComponent(password.value)}`
      : JSON.stringify({ username: username.value, password: password.value, role: role.value })
    
    const headers = {
      'Content-Type': isLogin.value ? 'application/x-www-form-urlencoded' : 'application/json'
    }

    const res = await fetch(url, {
      method: 'POST',
      headers,
      body
    })
    
    const data = await res.json()
    if (!res.ok) {
      status.value = data.detail || 'Authentication failed'
      statusClass.value = 'err'
      return
    }

    if (isLogin.value) {
      localStorage.setItem('token', data.access_token)
      const userRes = await fetch(`/api/auth/me?token=${data.access_token}`)
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
        <div class="auth-icon">
          <Lock :size="32" />
        </div>
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
              <UserCircle :size="16" />
              <span>Candidate</span>
            </label>
            <label :class="['role-option', { active: role === 'recruiter' }]">
              <input type="radio" value="recruiter" v-model="role" />
              <UserSearch :size="16" />
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
  min-height: 60vh;
  padding: 2rem;
}

.auth-card {
  width: 100%;
  max-width: 440px;
  padding: 2.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.auth-header { text-align: center; }
.auth-icon { 
  margin-bottom: 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  width: 64px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  margin-left: auto;
  margin-right: auto;
  border: 1px solid var(--border);
  color: var(--accent);
}
.auth-subtitle { color: var(--muted); font-size: 0.9rem; margin-top: 0.5rem; }

.auth-form { display: flex; flex-direction: column; gap: 1.25rem; }

.role-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem;
  margin-top: 0.25rem;
}

.role-option {
  background: var(--bg);
  border: 1px solid var(--border);
  padding: 0.6rem;
  border-radius: 4px;
  text-align: center;
  cursor: pointer;
  transition: all 0.15s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--muted);
}

.role-option input { display: none; }
.role-option span { font-size: 0.85rem; font-weight: 700; text-transform: none; }

.role-option.active {
  border-color: var(--accent);
  background: var(--accent-glow);
  color: #fff;
}

.auth-actions { display: flex; flex-direction: column; gap: 0.75rem; margin-top: 0.5rem; }
.full-width { width: 100%; }

.status-msg {
  text-align: center;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 0.6rem;
  border-radius: 4px;
}
.status-msg.err { background: rgba(239, 68, 68, 0.05); color: var(--err); border: 1px solid rgba(239, 68, 68, 0.1); }
.status-msg.ok { background: rgba(16, 185, 129, 0.05); color: var(--ok); border: 1px solid rgba(16, 185, 129, 0.1); }
</style>
