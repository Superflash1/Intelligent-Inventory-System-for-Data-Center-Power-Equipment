import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import CreateTaskView from '../views/CreateTaskView.vue'
import TasksView from '../views/TasksView.vue'
import TaskDetailView from '../views/TaskDetailView.vue'
import SummaryView from '../views/SummaryView.vue'
import SettingsView from '../views/SettingsView.vue'

const routes = [
  { path: '/login', component: LoginView },
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: DashboardView },
  { path: '/tasks/create', component: CreateTaskView },
  { path: '/tasks', component: TasksView },
  { path: '/tasks/:id', component: TaskDetailView },
  { path: '/summary', component: SummaryView },
  { path: '/settings', component: SettingsView }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  const loggedIn = localStorage.getItem('loggedIn') === '1'
  const authToken = localStorage.getItem('authToken')
  const hasAuth = loggedIn && !!authToken

  if (to.path !== '/login' && !hasAuth) {
    next('/login')
    return
  }
  if (to.path === '/login' && hasAuth) {
    next('/dashboard')
    return
  }
  next()
})

export default router