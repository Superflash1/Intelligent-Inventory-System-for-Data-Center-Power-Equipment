<template>
  <section class="stack">
    <div class="card">
      <h2>系统配置</h2>
      <p class="muted">登录密码配置</p>

      <form class="form-grid" @submit.prevent="submitPassword">
        <label>
          新密码（至少6位）
          <input type="password" v-model="password" minlength="6" required />
        </label>
        <button class="btn-primary" :disabled="loadingPassword">
          {{ loadingPassword ? '保存中...' : '保存密码' }}
        </button>
      </form>
    </div>

    <div class="card">
      <h2>识别 API 配置（OpenAI 兼容）</h2>
      <p class="muted">支持 gpt-5.3-codex 兼容的 /v1/chat/completions 视觉请求格式。</p>

      <form class="form-grid" @submit.prevent="submitLLM">
        <label>
          Base URL
          <input type="text" v-model="llm.base_url" placeholder="例如：https://your-api-host" required />
        </label>

        <label>
          API Key
          <input type="password" v-model="llm.api_key" placeholder="sk-..." required />
        </label>

        <label>
          Model
          <input type="text" v-model="llm.model" placeholder="gpt-5.3-codex" required />
        </label>

        <label>
          Timeout(秒)
          <input type="number" min="10" v-model.number="llm.timeout_seconds" required />
        </label>

        <label>
          <input type="checkbox" v-model="llm.enabled" /> 启用真实识别（关闭则使用本地模拟识别）
        </label>

        <button class="btn-primary" :disabled="loadingLLM">
          {{ loadingLLM ? '保存中...' : '保存识别配置' }}
        </button>
      </form>

      <p class="muted">当前是否已保存 API Key：{{ hasApiKey ? '是' : '否' }}</p>
    </div>

    <div class="card">
      <h2>识别规则校验</h2>
      <p class="muted">用于识别后基础规则校验（可配置）。</p>

      <form class="form-grid" @submit.prevent="submitRules">
        <label>
          最低置信度（0~1）
          <input
            type="number"
            min="0"
            max="1"
            step="0.01"
            v-model.number="rules.min_confidence"
            required
          />
        </label>

        <label>
          <input type="checkbox" v-model="rules.require_serial_number" /> 要求序列号非空
        </label>

        <button class="btn-primary" :disabled="loadingRules">
          {{ loadingRules ? '保存中...' : '保存规则' }}
        </button>
      </form>
    </div>

    <div class="card">
      <h2>模型连通性测试</h2>
      <p class="muted">先在这里验证配置的模型是否可用，再进行任务识别。</p>

      <form class="form-grid" @submit.prevent="submitLLMTest">
        <label>
          测试文本
          <input type="text" v-model="llmTestText" placeholder="例如：hello" required />
        </label>

        <button class="btn-primary" :disabled="loadingLLMTest">
          {{ loadingLLMTest ? '测试中...' : '测试模型' }}
        </button>
      </form>

      <p v-if="llmTestResult" class="muted">测试结果：{{ llmTestResult }}</p>
    </div>

    <p v-if="ok" class="success-text">{{ ok }}</p>
    <p v-if="error" class="error-text">{{ error }}</p>
  </section>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { getLLMConfig, getRuleConfig, setLLMConfig, setPassword, setRuleConfig, testLLM } from '../api'

const password = ref('')
const loadingPassword = ref(false)
const loadingLLM = ref(false)
const ok = ref('')
const error = ref('')
const hasApiKey = ref(false)

const llm = ref({
  base_url: '',
  api_key: '',
  model: 'gpt-5.3-codex',
  timeout_seconds: 60,
  enabled: false,
})

const rules = ref({
  min_confidence: 0,
  require_serial_number: true,
})

const loadingRules = ref(false)
const llmTestText = ref('hello')
const llmTestResult = ref('')
const loadingLLMTest = ref(false)

onMounted(async () => {
  try {
    const data = await getLLMConfig()
    llm.value.base_url = data.base_url || ''
    llm.value.model = data.model || 'gpt-5.3-codex'
    llm.value.timeout_seconds = data.timeout_seconds || 60
    llm.value.enabled = !!data.enabled
    hasApiKey.value = !!data.has_api_key

    const ruleData = await getRuleConfig()
    rules.value.min_confidence = ruleData.min_confidence
    rules.value.require_serial_number = !!ruleData.require_serial_number
  } catch {
    // ignore initial load error
  }
})

async function submitPassword() {
  loadingPassword.value = true
  ok.value = ''
  error.value = ''

  try {
    await setPassword(password.value)
    ok.value = '密码设置成功'
    password.value = ''
  } catch (e) {
    error.value = e.message
  } finally {
    loadingPassword.value = false
  }
}

async function submitLLM() {
  loadingLLM.value = true
  ok.value = ''
  error.value = ''

  try {
    const data = await setLLMConfig(llm.value)
    hasApiKey.value = !!data.has_api_key
    llm.value.api_key = ''
    ok.value = '识别 API 配置已保存'
  } catch (e) {
    error.value = e.message
  } finally {
    loadingLLM.value = false
  }
}

async function submitRules() {
  loadingRules.value = true
  ok.value = ''
  error.value = ''

  try {
    const data = await setRuleConfig(rules.value)
    rules.value.min_confidence = data.min_confidence
    rules.value.require_serial_number = !!data.require_serial_number
    ok.value = '识别规则已保存'
  } catch (e) {
    error.value = e.message
  } finally {
    loadingRules.value = false
  }
}

async function submitLLMTest() {
  loadingLLMTest.value = true
  llmTestResult.value = ''
  error.value = ''

  try {
    const data = await testLLM(llmTestText.value)
    llmTestResult.value = data.message
  } catch (e) {
    error.value = e.message
  } finally {
    loadingLLMTest.value = false
  }
}
</script>
