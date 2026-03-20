<template>
  <header class="top-nav">
    <div class="brand">机房动力设备智能盘点系统</div>
    <nav>
      <RouterLink to="/dashboard">首页</RouterLink>
      <RouterLink to="/tasks/create">创建任务</RouterLink>
      <RouterLink to="/tasks">任务管理</RouterLink>
      <RouterLink to="/summary">全省汇总</RouterLink>
      <RouterLink to="/settings">系统配置</RouterLink>
    </nav>
    <button class="btn-outline nav-logout" @click="logout">退出</button>
  </header>
</template>

<style scoped>
.nav-logout {
  min-width: 82px;
}
</style>

<script setup>
import { useRouter } from 'vue-router'
import { logout as logoutApi } from '../api'

const router = useRouter()

async function logout() {
  try {
    await logoutApi()
  } catch (_e) {
    // 忽略退出接口失败，前端仍强制清理本地态
  }
  localStorage.removeItem('loggedIn')
  localStorage.removeItem('authToken')
  router.push('/login')
}
</script>
