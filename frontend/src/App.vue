<template>
  <div class="app-shell">
    <TopNav v-if="showNav" />
    <main class="main-container">
      <RouterView />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import TopNav from './components/TopNav.vue'

const route = useRoute()
const showNav = computed(() => route.path !== '/login')
</script>