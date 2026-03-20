<template>
  <section class="card">
    <div class="inline-actions" style="justify-content: space-between; align-items: center">
      <h2>任务管理</h2>
      <button class="btn-outline" @click="load">刷新</button>
    </div>
    <p class="muted">统一查看任务状态，支持单任务识别、详情查看与删除。</p>

    <div class="table-wrap" style="margin-top: 16px">
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>地市</th>
            <th>站点</th>
            <th>设备类型</th>
            <th>人员</th>
            <th>日期</th>
            <th>状态</th>
            <th>识别条数</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="t in tasks" :key="t.id">
            <td>{{ t.id }}</td>
            <td>{{ t.city }}</td>
            <td>{{ t.site }}</td>
            <td>{{ t.device_type }}</td>
            <td>{{ t.person || '-' }}</td>
            <td>{{ t.inventory_date }}</td>
            <td><span class="pill">{{ t.status }}</span></td>
            <td>{{ t.devices_count }}</td>
            <td class="inline-actions">
              <button class="btn-outline" @click="openDetail(t.id)">查看详情</button>
              <button
                v-if="t.status === 'pending_confirm'"
                class="btn-outline"
                :disabled="confirmingTaskId === t.id"
                @click="confirmNow(t.id)"
              >
                {{ confirmingTaskId === t.id ? '确认中...' : '确认' }}
              </button>
              <button class="btn-outline" :disabled="recognizingTaskId === t.id" @click="recognizeNow(t.id)">
                {{ recognizingTaskId === t.id ? '识别中...' : '识别' }}
              </button>
              <button class="btn-outline" @click="removeTask(t.id)">删除任务</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <p v-if="tip" class="success-text">{{ tip }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { confirmActive, deleteTask, listTasks, recognizeTask } from '../api'

const tasks = ref([])
const router = useRouter()
const tip = ref('')
const error = ref('')
const recognizingTaskId = ref(null)
const confirmingTaskId = ref(null)

async function load() {
  error.value = ''
  try {
    tasks.value = await listTasks()
  } catch (e) {
    error.value = e.message || '任务列表加载失败'
    tasks.value = []
  }
}

function openDetail(taskId) {
  router.push(`/tasks/${taskId}`)
}

async function recognizeNow(taskId) {
  error.value = ''
  tip.value = ''
  recognizingTaskId.value = taskId
  try {
    const data = await recognizeTask(taskId)
    tip.value = `任务 ${taskId} 识别完成，新增 ${data.inserted_count} 条`
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    recognizingTaskId.value = null
  }
}

async function confirmNow(taskId) {
  error.value = ''
  tip.value = ''
  confirmingTaskId.value = taskId
  try {
    await confirmActive(taskId)
    tip.value = `任务 ${taskId} 已确认`
    await load()
  } catch (e) {
    error.value = e.message || '任务确认失败'
  } finally {
    confirmingTaskId.value = null
  }
}

async function removeTask(taskId) {
  await deleteTask(taskId)
  await load()
}

onMounted(load)
</script>
