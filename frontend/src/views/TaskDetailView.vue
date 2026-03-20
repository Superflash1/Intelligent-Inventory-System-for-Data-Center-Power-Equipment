<template>
  <section class="stack">
    <div class="card">
      <h2>任务详情</h2>
      <p class="muted" v-if="detail">
        {{ detail.city }} / {{ detail.site }} / {{ detail.device_type }} / {{ detail.person || '未填写人员' }} /
        {{ detail.inventory_date }}（{{ detail.status }}）
      </p>
      <div class="inline-actions">
        <button class="btn-outline" @click="load">刷新</button>
        <button class="btn-primary" @click="downloadTaskXlsx">导出任务Excel</button>
      </div>
      <p v-if="tip" class="success-text">{{ tip }}</p>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>

    <div class="card">
      <h3>图片列表与预览</h3>
      <div v-if="!detail || !detail.images || detail.images.length === 0" class="muted">暂无图片</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>图片ID</th>
              <th>文件名</th>
              <th>预览</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="img in detail.images" :key="img.id">
              <td>{{ img.id }}</td>
              <td>{{ img.file_name }}</td>
              <td>
                <img
                  :src="fileUrl(img.file_path)"
                  alt="preview"
                  class="thumb"
                  @click="openImagePreview(img)"
                  title="点击放大预览"
                />
              </td>
              <td class="inline-actions">
                <button class="btn-outline" @click="openImagePreview(img)">查看/编辑</button>
                <button class="btn-outline" :disabled="recognizingImageId === img.id" @click="recognizeSingleImage(img.id)">
                  {{ recognizingImageId === img.id ? '识别中...' : '识别' }}
                </button>
                <button class="btn-outline" @click="removeImage(img.id)">删除图片</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <h3>识别结果汇总</h3>
      <div v-if="!detail || !detail.device_records || detail.device_records.length === 0" class="muted">暂无识别结果</div>
      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>记录ID</th>
              <th>图片ID</th>
              <th>品牌</th>
              <th>型号</th>
              <th>序列号</th>
              <th>生产日期</th>
              <th>置信度</th>
              <th>校验</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in detail.device_records" :key="r.id">
              <td>{{ r.id }}</td>
              <td>{{ r.image_id }}</td>
              <td>{{ r.brand }}</td>
              <td>{{ r.model }}</td>
              <td>{{ r.serial_number }}</td>
              <td>{{ r.production_date }}</td>
              <td>{{ r.confidence }}</td>
              <td>{{ r.validation_status }}<span v-if="r.validation_message">（{{ r.validation_message }}）</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <div v-if="previewImage" class="preview-mask" @click.self="closeImagePreview">
      <div class="preview-dialog">
        <div class="preview-header">
          <h3>图片预览与识别信息</h3>
          <button class="btn-outline" @click="closeImagePreview">关闭</button>
        </div>

        <div class="preview-body">
          <div class="preview-image-wrap">
            <img :src="fileUrl(previewImage.file_path)" alt="preview-large" class="preview-image" />
          </div>

          <div class="preview-form-wrap">
            <div class="inline-actions" style="margin-bottom: 12px">
              <button class="btn-outline" :disabled="recognizingImageId === previewImage.id" @click="recognizeSingleImage(previewImage.id)">
                {{ recognizingImageId === previewImage.id ? '识别中...' : '重新识别当前图片' }}
              </button>
            </div>

            <p v-if="!previewRecord" class="muted">当前图片暂无识别结果，请先点击“重新识别当前图片”。</p>

            <form v-else class="stack" @submit.prevent="savePreviewRecord">
              <label>
                品牌
                <input type="text" v-model="editForm.brand" list="brand-options" placeholder="可输入或选择" />
                <datalist id="brand-options">
                  <option v-for="v in brandOptions" :key="`brand-${v}`" :value="v" />
                </datalist>
                <div class="inline-actions">
                  <button type="button" class="btn-outline" @click="hideCurrentOption('brand', editForm.brand)">隐藏当前值</button>
                </div>
              </label>
              <label>
                型号
                <input type="text" v-model="editForm.model" list="model-options" placeholder="可输入或选择" />
                <datalist id="model-options">
                  <option v-for="v in modelOptions" :key="`model-${v}`" :value="v" />
                </datalist>
                <div class="inline-actions">
                  <button type="button" class="btn-outline" @click="hideCurrentOption('model', editForm.model)">隐藏当前值</button>
                </div>
              </label>
              <label>
                序列号
                <input type="text" v-model="editForm.serial_number" list="serial-options" placeholder="可输入或选择" />
                <datalist id="serial-options">
                  <option v-for="v in serialOptions" :key="`serial-${v}`" :value="v" />
                </datalist>
                <div class="inline-actions">
                  <button type="button" class="btn-outline" @click="hideCurrentOption('serial_number', editForm.serial_number)">隐藏当前值</button>
                </div>
              </label>
              <label>
                生产日期
                <input type="text" v-model="editForm.production_date" list="production-options" placeholder="可输入或选择" />
                <datalist id="production-options">
                  <option v-for="v in productionDateOptions" :key="`prod-${v}`" :value="v" />
                </datalist>
                <div class="inline-actions">
                  <button type="button" class="btn-outline" @click="hideCurrentOption('production_date', editForm.production_date)">隐藏当前值</button>
                </div>
              </label>
              <label>
                置信度
                <input type="text" v-model="editForm.confidence" />
              </label>
              <label>
                原始识别文本
                <textarea v-model="editForm.raw_text" rows="4" />
              </label>

              <div class="inline-actions">
                <button class="btn-primary" type="submit" :disabled="savingRecord">{{ savingRecord ? '保存中...' : '保存修改' }}</button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { deleteImage, exportTaskXlsx, getFieldOptions, getTaskDetail, hideFieldOption, recognizeImage, updateDeviceRecord } from '../api'

const route = useRoute()
const detail = ref(null)
const tip = ref('')
const error = ref('')
const recognizingImageId = ref(null)
const previewImage = ref(null)
const savingRecord = ref(false)

const brandOptions = ref([])
const modelOptions = ref([])
const serialOptions = ref([])
const productionDateOptions = ref([])

const editForm = ref({
  brand: '',
  model: '',
  serial_number: '',
  production_date: '',
  confidence: '',
  raw_text: '',
})

const previewRecord = computed(() => {
  if (!detail.value || !previewImage.value) return null
  return detail.value.device_records.find((r) => r.image_id === previewImage.value.id) || null
})

function syncFormWithRecord() {
  const record = previewRecord.value
  if (!record) {
    editForm.value = {
      brand: '',
      model: '',
      serial_number: '',
      production_date: '',
      confidence: '',
      raw_text: '',
    }
    return
  }
  editForm.value = {
    brand: record.brand || '',
    model: record.model || '',
    serial_number: record.serial_number || '',
    production_date: record.production_date || '',
    confidence: record.confidence || '',
    raw_text: record.raw_text || '',
  }
}

async function loadFieldOptions() {
  const [brands, models, serials, productions] = await Promise.all([
    getFieldOptions('brand'),
    getFieldOptions('model'),
    getFieldOptions('serial_number'),
    getFieldOptions('production_date'),
  ])
  brandOptions.value = brands || []
  modelOptions.value = models || []
  serialOptions.value = serials || []
  productionDateOptions.value = productions || []
}

function fileUrl(filePath) {
  const normalized = String(filePath || '').replace(/\\/g, '/')
  if (normalized.startsWith('http')) return normalized
  return `http://127.0.0.1:8000/${normalized}`
}

async function load() {
  error.value = ''
  try {
    detail.value = await getTaskDetail(route.params.id)
    if (previewImage.value) {
      syncFormWithRecord()
    }
  } catch (e) {
    error.value = e.message || '任务详情加载失败'
    detail.value = null
  }
}

function openImagePreview(img) {
  previewImage.value = img
  syncFormWithRecord()
}

function closeImagePreview() {
  previewImage.value = null
}

async function recognizeSingleImage(imageId) {
  error.value = ''
  tip.value = ''
  recognizingImageId.value = imageId
  try {
    const data = await recognizeImage(imageId)
    tip.value = data.updated ? `图片 ${imageId} 识别结果已更新` : `图片 ${imageId} 已新增识别结果`
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    recognizingImageId.value = null
  }
}

async function savePreviewRecord() {
  if (!previewRecord.value) return
  error.value = ''
  tip.value = ''
  savingRecord.value = true
  try {
    await updateDeviceRecord(previewRecord.value.id, { ...editForm.value })
    tip.value = '识别信息保存成功'
    await load()
  } catch (e) {
    error.value = e.message
  } finally {
    savingRecord.value = false
  }
}

async function removeImage(imageId) {
  await deleteImage(imageId)
  if (previewImage.value?.id === imageId) {
    closeImagePreview()
  }
  await load()
}

async function downloadTaskXlsx() {
  const taskId = Number(route.params.id)
  const blob = await exportTaskXlsx(taskId)
  const url = window.URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `task_${taskId}.xlsx`
  document.body.appendChild(a)
  a.click()
  a.remove()
  window.URL.revokeObjectURL(url)
}

async function hideCurrentOption(category, value) {
  const cleanValue = String(value || '').trim()
  if (!cleanValue) {
    error.value = '请先输入或选择一个值再隐藏'
    return
  }

  error.value = ''
  tip.value = ''
  try {
    await hideFieldOption(category, cleanValue)
    tip.value = `已隐藏候选项：${cleanValue}`

    if (category === 'brand' && editForm.value.brand === cleanValue) editForm.value.brand = ''
    if (category === 'model' && editForm.value.model === cleanValue) editForm.value.model = ''
    if (category === 'serial_number' && editForm.value.serial_number === cleanValue) editForm.value.serial_number = ''
    if (category === 'production_date' && editForm.value.production_date === cleanValue) editForm.value.production_date = ''

    await loadFieldOptions()
  } catch (e) {
    error.value = e.message || '隐藏候选项失败'
  }
}

onMounted(async () => {
  await Promise.all([load(), loadFieldOptions()])
})
</script>

<style scoped>
.thumb {
  width: 120px;
  border-radius: 6px;
  cursor: zoom-in;
}

.preview-mask {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 24px;
  z-index: 99;
}

.preview-dialog {
  background: #fff;
  width: min(1200px, 96vw);
  max-height: 92vh;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #eee;
}

.preview-body {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 16px;
  padding: 16px;
  overflow: auto;
}

.preview-image-wrap {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  background: #f7f8fa;
  border-radius: 8px;
  padding: 12px;
}

.preview-image {
  width: 100%;
  height: auto;
  max-height: 72vh;
  object-fit: contain;
  border-radius: 8px;
}

.preview-form-wrap label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}

.preview-form-wrap input,
.preview-form-wrap textarea {
  font-size: 14px;
}

@media (max-width: 960px) {
  .preview-body {
    grid-template-columns: 1fr;
  }
}
</style>
