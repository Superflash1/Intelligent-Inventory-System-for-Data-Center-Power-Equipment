<template>
  <section class="stack">
    <div class="card">
      <h2>创建任务</h2>
      <p class="muted">支持创建盘点任务并快速进入上传识别流程。</p>
      <form class="form-grid" @submit.prevent="submitTask">
        <label>
          地市
          <input type="text" v-model="form.city" list="city-options" required placeholder="可输入或选择" />
          <datalist id="city-options">
            <option v-for="v in visibleCityOptions" :key="`city-${v}`" :value="v" />
          </datalist>
          <div class="candidate-list" v-if="visibleCityOptions.length > 0">
            <div class="candidate-item" v-for="v in visibleCityOptions" :key="`city-candidate-${v}`">
              <button type="button" class="candidate-value" @click="form.city = v">{{ v }}</button>
              <button type="button" class="candidate-remove" @click="hideCandidate('city', v)">×</button>
            </div>
          </div>
        </label>

        <label>
          站点
          <input type="text" v-model="form.site" list="site-options" required placeholder="可输入或选择" />
          <datalist id="site-options">
            <option v-for="v in visibleSiteOptions" :key="`site-${v}`" :value="v" />
          </datalist>
          <div class="candidate-list" v-if="visibleSiteOptions.length > 0">
            <div class="candidate-item" v-for="v in visibleSiteOptions" :key="`site-candidate-${v}`">
              <button type="button" class="candidate-value" @click="form.site = v">{{ v }}</button>
              <button type="button" class="candidate-remove" @click="hideCandidate('site', v)">×</button>
            </div>
          </div>
        </label>

        <label>
          设备类型
          <input type="text" v-model="form.device_type" list="type-options" required placeholder="可输入或选择" />
          <datalist id="type-options">
            <option v-for="v in visibleTypeOptions" :key="`type-${v}`" :value="v" />
          </datalist>
          <div class="candidate-list" v-if="visibleTypeOptions.length > 0">
            <div class="candidate-item" v-for="v in visibleTypeOptions" :key="`type-candidate-${v}`">
              <button type="button" class="candidate-value" @click="form.device_type = v">{{ v }}</button>
              <button type="button" class="candidate-remove" @click="hideCandidate('device_type', v)">×</button>
            </div>
          </div>
        </label>

        <label>
          人员
          <input type="text" v-model="form.person" list="person-options" placeholder="如：张三（可输入或选择）" />
          <datalist id="person-options">
            <option v-for="v in visiblePersonOptions" :key="`person-${v}`" :value="v" />
          </datalist>
          <div class="candidate-list" v-if="visiblePersonOptions.length > 0">
            <div class="candidate-item" v-for="v in visiblePersonOptions" :key="`person-candidate-${v}`">
              <button type="button" class="candidate-value" @click="form.person = v">{{ v }}</button>
              <button type="button" class="candidate-remove" @click="hideCandidate('person', v)">×</button>
            </div>
          </div>
        </label>

        <label>
          盘点日期
          <input type="date" v-model="form.inventory_date" required />
        </label>

        <button class="btn-primary" :disabled="loadingTask">{{ loadingTask ? '创建中...' : '创建任务' }}</button>
      </form>

      <p v-if="taskTip" class="success-text">{{ taskTip }}</p>
      <p v-if="error" class="error-text">{{ error }}</p>
    </div>

    <div class="card">
      <h3>上传文件并识别</h3>
      <p class="muted">支持当场上传、当场识别，并展示预览。</p>
      <form class="form-grid" @submit.prevent="submitUpload">
        <label>
          任务 ID
          <input type="number" v-model.number="uploadTaskId" required />
        </label>
        <label>
          选择图片
          <input type="file" accept="image/*" multiple @change="onFilesChange" required />
        </label>
        <div class="inline-actions">
          <button class="btn-primary" :disabled="loadingUpload">{{ loadingUpload ? '上传中...' : '上传' }}</button>
          <button type="button" class="btn-outline" :disabled="loadingRecognize" @click="recognize">{{ loadingRecognize ? '识别中...' : '执行识别' }}</button>
        </div>
      </form>

      <p v-if="uploadTip" class="success-text">{{ uploadTip }}</p>

      <div v-if="uploadTaskId" class="stack" style="margin-top: 16px">
        <h4>当前任务图片与预览</h4>
        <div v-if="uploadedImages.length === 0" class="muted">暂无图片</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>文件名</th>
                <th>预览</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="img in uploadedImages" :key="img.id">
                <td>{{ img.id }}</td>
                <td>{{ img.file_name }}</td>
                <td>
                  <img
                    :src="fileUrl(img.file_path)"
                    alt="preview"
                    style="width: 120px; border-radius: 8px; box-shadow: 0 8px 18px rgba(15, 23, 42, 0.12)"
                  />
                </td>
                <td>
                  <button class="btn-outline" @click="removeImage(img.id)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="recognizedRows.length > 0" class="stack" style="margin-top: 16px">
        <h4>识别结果预览</h4>
        <div class="table-wrap">
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
              <tr v-for="r in recognizedRows" :key="r.id">
                <td>{{ r.id }}</td>
                <td>{{ r.image_id }}</td>
                <td>{{ r.brand }}</td>
                <td>{{ r.model }}</td>
                <td>{{ r.serial_number }}</td>
                <td>{{ r.production_date }}</td>
                <td>{{ r.confidence }}</td>
                <td>{{ r.validation_status }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { createTask, deleteImage, getFieldOptions, getTaskDetail, listTaskImages, recognizeTask, uploadFiles } from '../api'
import { fileUrl } from '../utils/fileUrl'

const form = ref({ city: '', site: '', device_type: '', person: '', inventory_date: '' })
const loadingTask = ref(false)
const taskTip = ref('')
const error = ref('')

const cityOptions = ref([])
const siteOptions = ref([])
const typeOptions = ref([])
const personOptions = ref([])

const hiddenCandidates = ref({
  city: [],
  site: [],
  device_type: [],
  person: [],
})

const visibleCityOptions = computed(() => cityOptions.value.filter((v) => !hiddenCandidates.value.city.includes(v)))
const visibleSiteOptions = computed(() => siteOptions.value.filter((v) => !hiddenCandidates.value.site.includes(v)))
const visibleTypeOptions = computed(() => typeOptions.value.filter((v) => !hiddenCandidates.value.device_type.includes(v)))
const visiblePersonOptions = computed(() => personOptions.value.filter((v) => !hiddenCandidates.value.person.includes(v)))

const uploadTaskId = ref(null)
const selectedFiles = ref([])
const loadingUpload = ref(false)
const loadingRecognize = ref(false)
const uploadTip = ref('')
const uploadedImages = ref([])
const recognizedRows = ref([])

async function loadFieldOptions() {
  const [cities, sites, types, persons] = await Promise.all([
    getFieldOptions('city'),
    getFieldOptions('site'),
    getFieldOptions('device_type'),
    getFieldOptions('person'),
  ])
  cityOptions.value = cities || []
  siteOptions.value = sites || []
  typeOptions.value = types || []
  personOptions.value = persons || []
}

onMounted(async () => {
  error.value = ''
  try {
    await loadFieldOptions()
  } catch (e) {
    error.value = e.message || '加载基础字典失败'
  }
})

async function submitTask() {
  loadingTask.value = true
  error.value = ''
  taskTip.value = ''
  try {
    const payload = {
      ...form.value,
      city: String(form.value.city || '').trim(),
      site: String(form.value.site || '').trim(),
      device_type: String(form.value.device_type || '').trim(),
      person: String(form.value.person || '').trim(),
    }
    const data = await createTask(payload)
    taskTip.value = `任务创建成功，任务ID=${data.task_id}，类型=${data.task_kind}`
    uploadTaskId.value = data.task_id
    await loadFieldOptions()
    await refreshImages()
    await refreshRecords()
  } catch (e) {
    error.value = e.message
  } finally {
    loadingTask.value = false
  }
}

function onFilesChange(evt) {
  selectedFiles.value = Array.from(evt.target.files || [])
}

async function refreshImages() {
  if (!uploadTaskId.value) {
    uploadedImages.value = []
    return
  }
  uploadedImages.value = await listTaskImages(uploadTaskId.value)
}

async function refreshRecords() {
  if (!uploadTaskId.value) {
    recognizedRows.value = []
    return
  }
  const detail = await getTaskDetail(uploadTaskId.value)
  recognizedRows.value = detail.device_records || []
}

async function removeImage(imageId) {
  await deleteImage(imageId)
  await refreshImages()
  await refreshRecords()
}

async function submitUpload() {
  if (!uploadTaskId.value || selectedFiles.value.length === 0) return
  loadingUpload.value = true
  uploadTip.value = ''
  error.value = ''
  try {
    await uploadFiles(uploadTaskId.value, selectedFiles.value)
    uploadTip.value = '上传成功'
    await refreshImages()
  } catch (e) {
    error.value = e.message
  } finally {
    loadingUpload.value = false
  }
}

async function recognize() {
  if (!uploadTaskId.value) return
  loadingRecognize.value = true
  uploadTip.value = ''
  error.value = ''
  try {
    const data = await recognizeTask(uploadTaskId.value)
    uploadTip.value = `识别完成，新增记录 ${data.inserted_count} 条`
    await refreshRecords()
  } catch (e) {
    error.value = e.message
  } finally {
    loadingRecognize.value = false
  }
}

function hideCandidate(category, value) {
  const cleanValue = String(value || '').trim()
  if (!cleanValue) return

  const list = hiddenCandidates.value[category] || []
  if (!list.includes(cleanValue)) {
    hiddenCandidates.value[category] = [...list, cleanValue]
  }

  if (category === 'city' && form.value.city === cleanValue) form.value.city = ''
  if (category === 'site' && form.value.site === cleanValue) form.value.site = ''
  if (category === 'device_type' && form.value.device_type === cleanValue) form.value.device_type = ''
  if (category === 'person' && form.value.person === cleanValue) form.value.person = ''

  taskTip.value = `已临时隐藏候选项：${cleanValue}`
}
</script>
