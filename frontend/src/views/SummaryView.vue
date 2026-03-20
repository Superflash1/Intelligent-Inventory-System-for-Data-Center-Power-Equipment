<template>
  <section class="stack">
    <div class="card">
      <h2>全省站点汇总（active版本）</h2>
      <div class="inline-actions">
        <button class="btn-outline" @click="load">刷新</button>
        <button class="btn-outline" @click="downloadCsv">导出CSV</button>
        <button class="btn-primary" @click="downloadXlsx">导出Excel</button>
      </div>
      <p v-if="error" class="error-text" style="margin-top: 10px">{{ error }}</p>
    </div>

    <div class="card">
      <h3>总体概览</h3>
      <div class="kpi-grid">
        <div class="kpi-item">
          <div class="kpi-label">活跃任务数</div>
          <div class="kpi-value">{{ kpi.activeTasks }}</div>
        </div>
        <div class="kpi-item">
          <div class="kpi-label">设备总数</div>
          <div class="kpi-value">{{ kpi.totalDevices }}</div>
        </div>
        <div class="kpi-item">
          <div class="kpi-label">校验失败总数</div>
          <div class="kpi-value">{{ kpi.totalValidationFails }}</div>
        </div>
        <div class="kpi-item">
          <div class="kpi-label">校验通过率</div>
          <div class="kpi-value">{{ kpi.passRate }}%</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>地市设备数量可视化</h3>
      <div v-if="cityBars.length === 0" class="muted">暂无数据</div>
      <div v-else class="bar-list">
        <div class="bar-row" v-for="item in cityBars" :key="item.city">
          <div class="bar-label">{{ item.city }}</div>
          <div class="bar-track">
            <div class="bar-fill" :style="{ width: item.width + '%' }"></div>
          </div>
          <div class="bar-value">{{ item.count }}</div>
        </div>
      </div>
    </div>

    <div class="card">
      <h3>汇总明细</h3>
      <div class="table-wrap" style="margin-top: 16px">
        <table>
          <thead>
            <tr>
              <th>地市</th>
              <th>站点</th>
              <th>设备类型</th>
              <th>人员</th>
              <th>盘点日期</th>
              <th>状态</th>
              <th>设备数量</th>
              <th>校验失败数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in rows" :key="`${item.city}-${item.site}-${item.device_type}`">
              <td>{{ item.city }}</td>
              <td>{{ item.site }}</td>
              <td>{{ item.device_type }}</td>
              <td>{{ item.person || '-' }}</td>
              <td>{{ item.inventory_date }}</td>
              <td><span class="pill">{{ item.status }}</span></td>
              <td>{{ item.devices_count }}</td>
              <td>{{ item.validation_fail_count }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { exportSummary, exportSummaryXlsx, getSummary } from '../api'

const rows = ref([])

const error = ref('')

async function load() {
  error.value = ''
  try {
    rows.value = await getSummary()
  } catch (e) {
    error.value = e.message || '汇总数据加载失败'
    rows.value = []
  }
}

const kpi = computed(() => {
  const activeTasks = rows.value.length
  const totalDevices = rows.value.reduce((sum, item) => sum + (item.devices_count || 0), 0)
  const totalValidationFails = rows.value.reduce((sum, item) => sum + (item.validation_fail_count || 0), 0)
  const passRate = totalDevices > 0 ? (((totalDevices - totalValidationFails) / totalDevices) * 100).toFixed(1) : '0.0'
  return { activeTasks, totalDevices, totalValidationFails, passRate }
})

const cityBars = computed(() => {
  const agg = {}
  rows.value.forEach((item) => {
    const city = item.city || '未知'
    agg[city] = (agg[city] || 0) + (item.devices_count || 0)
  })

  const list = Object.entries(agg).map(([city, count]) => ({ city, count }))
  list.sort((a, b) => b.count - a.count)
  const maxCount = list[0]?.count || 1
  return list.map((x) => ({ ...x, width: Math.max((x.count / maxCount) * 100, 2) }))
})

async function downloadCsv() {
  const blob = await exportSummary()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'summary.csv'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

async function downloadXlsx() {
  const blob = await exportSummaryXlsx()
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'summary.xlsx'
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

onMounted(load)
</script>

<style scoped>
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.kpi-item {
  border: 1px solid #e7ebf3;
  border-radius: 10px;
  padding: 12px;
}

.kpi-label {
  font-size: 12px;
  color: #63708b;
}

.kpi-value {
  margin-top: 6px;
  font-size: 24px;
  font-weight: 700;
  color: #1f2a44;
}

.bar-list {
  display: grid;
  gap: 10px;
}

.bar-row {
  display: grid;
  grid-template-columns: 100px 1fr 80px;
  align-items: center;
  gap: 10px;
}

.bar-label,
.bar-value {
  font-size: 13px;
  color: #3a4763;
}

.bar-track {
  height: 10px;
  border-radius: 999px;
  background: #eef2f8;
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #5b8cff, #77a8ff);
}
</style>
