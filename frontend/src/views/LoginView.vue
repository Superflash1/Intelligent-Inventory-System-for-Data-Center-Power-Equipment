<template>
  <section class="card auth-card">
    <h2>登录</h2>
    <p class="muted">首次登录免密，第二次起需输入密码。</p>

    <div v-if="status" class="alert" :class="status.is_first_login ? 'alert-success' : 'alert-info'">
      <span v-if="status.is_first_login">当前为首次登录，输入任意值即可进入。</span>
      <span v-else>当前需密码登录。</span>
    </div>

    <form class="form-grid" @submit.prevent="submit">
      <label>
        密码
        <input v-model="password" type="password" placeholder="请输入密码" />
      </label>
      <button class="btn-primary" :disabled="loading">{{ loading ? '登录中...' : '登录' }}</button>
    </form>

    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { getAuthStatus, login } from '../api'

const router = useRouter()
const status = ref(null)
const password = ref('')
const loading = ref(false)
const error = ref('')

onMounted(async () => {
  error.value = ''
  try {
    status.value = await getAuthStatus()
  } catch (e) {
    error.value = e.message || '获取登录状态失败'
  }
})

async function submit() {
  loading.value = true
  error.value = ''
  try {
    const data = await login(password.value || 'first-login')
    localStorage.setItem('loggedIn', '1')
    localStorage.setItem('authToken', data.token)
    router.push('/dashboard')
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
}
</script>