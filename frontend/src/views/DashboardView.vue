<template>
  <section class="stack">
    <div v-if="appStore.needSetPassword" class="alert alert-warning">
      检测到你还未设置登录密码，请尽快前往“系统配置”页面完成设置。
    </div>

    <div class="card guide-card">
      <h2>系统使用指南</h2>
      <p class="muted">适用于“机房动力设备智能盘点”的日常作业流程，新同事可按以下步骤直接上手。</p>

      <div class="guide-section stack">
        <h3>1）使用目标</h3>
        <ul class="guide-list">
          <li>通过上传现场设备铭牌照片，自动识别品牌、型号、序列号、生产日期等关键信息。</li>
          <li>减少手工录入错误，统一设备台账口径，并支持版本化更新确认。</li>
          <li>为后续汇总、核验与导出提供结构化数据基础。</li>
        </ul>
      </div>

      <div class="guide-section stack">
        <h3>2）标准操作流程</h3>
        <ol class="guide-list">
          <li>先在“创建任务”页填写地市、站点、设备类型、盘点日期并创建任务。</li>
          <li>在同一页面上传现场图片，确认缩略图可正常预览后执行识别。</li>
          <li>到“任务列表 / 任务详情”查看识别结果，人工核对异常字段并修正。</li>
          <li>若同一站点同类设备出现多日期版本，回到首页在“待确认更新任务”中确认有效版本。</li>
          <li>在“汇总”页按条件筛选并导出结果，形成可归档台账。</li>
        </ol>
      </div>

      <div class="guide-section stack">
        <h3>3）页面入口速查</h3>
        <ul class="guide-list">
          <li><strong>创建任务：</strong>新建盘点任务、上传图片、触发识别。</li>
          <li><strong>任务列表：</strong>按任务查看执行进度，进入详情。</li>
          <li><strong>任务详情：</strong>核对与编辑识别明细，查看图片与记录关联。</li>
          <li><strong>汇总：</strong>按地市/站点/设备类型/日期汇总查询并导出。</li>
          <li><strong>系统配置：</strong>设置登录密码及系统级参数。</li>
        </ul>
      </div>

      <div class="guide-section stack">
        <h3>4）使用建议与注意事项</h3>
        <ul class="guide-list">
          <li>尽量保证图片清晰、光线均匀、铭牌完整入镜，提升识别准确率。</li>
          <li>同一批次建议按“站点 + 设备类型”分任务上传，便于后续追溯。</li>
          <li>若识别为空或置信度偏低，优先补拍后重传，避免错误台账入库。</li>
          <li>存在多版本任务时，务必在首页完成“有效版本确认”，再进行正式导出。</li>
        </ul>
      </div>
    </div>

    <div class="card">
      <h2>待确认更新任务</h2>
      <p class="muted">同一地市+站点+设备类型有多个日期版本时，需人工确认采用哪个版本。</p>

      <div v-if="loading" class="muted">加载中...</div>
      <div v-else-if="groups.length === 0" class="muted">暂无待确认更新任务</div>

      <div v-else class="stack">
        <div v-for="g in groups" :key="`${g.city}-${g.site}-${g.device_type}`" class="pending-group">
          <h3>{{ g.city }} / {{ g.site }} / {{ g.device_type }}</h3>
          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>任务ID</th>
                  <th>盘点日期</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="t in g.tasks" :key="t.id">
                  <td>{{ t.id }}</td>
                  <td>{{ t.inventory_date }}</td>
                  <td><span class="pill">{{ t.status }}</span></td>
                  <td>
                    <button class="btn-primary" @click="confirm(t.id)">确认此版本为有效</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useAppStore } from '../stores/app'
import { confirmActive, getPendingUpdates } from '../api'

const appStore = useAppStore()
const groups = ref([])
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    groups.value = await getPendingUpdates()
    await appStore.refreshReminder()
  } finally {
    loading.value = false
  }
}

async function confirm(taskId) {
  await confirmActive(taskId)
  await load()
}

onMounted(load)
</script>