import api from './client'

export const getAuthStatus = async () => (await api.get('/auth/status')).data
export const login = async (password) => (await api.post('/auth/login', { password })).data
export const logout = async () => (await api.post('/auth/logout')).data
export const setPassword = async (password) => (await api.post('/auth/set-password', { password })).data
export const getReminder = async () => (await api.get('/auth/reminder')).data

export const createTask = async (payload) => (await api.post('/tasks', payload)).data
export const listTasks = async () => (await api.get('/tasks')).data
export const getTaskDetail = async (taskId) => (await api.get(`/tasks/${taskId}`)).data
export const deleteTask = async (taskId) => (await api.delete(`/tasks/${taskId}`)).data
export const exportTaskXlsx = async (taskId) => (await api.get(`/tasks/${taskId}/export-xlsx`, { responseType: 'blob', timeout: 120000 })).data
export const uploadFiles = async (taskId, files) => {
  const form = new FormData()
  files.forEach((file) => form.append('files', file))
  return (await api.post(`/tasks/${taskId}/upload`, form)).data
}
export const listTaskImages = async (taskId) => (await api.get(`/tasks/${taskId}/images`)).data
export const recognizeTask = async (taskId) => (await api.post(`/tasks/${taskId}/recognize`, null, { timeout: 120000 })).data
export const recognizeImage = async (imageId) => (await api.post(`/images/${imageId}/recognize`, null, { timeout: 120000 })).data
export const updateDeviceRecord = async (recordId, payload) => (await api.patch(`/device-records/${recordId}`, payload)).data

export const getPendingUpdates = async () => (await api.get('/tasks/pending-updates')).data
export const confirmActive = async (taskId) => (await api.post('/tasks/confirm-active', { task_id: taskId })).data

export const getSummary = async () => (await api.get('/summary')).data
export const exportSummary = async () => (await api.get('/summary/export', { responseType: 'blob', timeout: 120000 })).data
export const exportSummaryXlsx = async () => (await api.get('/summary/export-xlsx', { responseType: 'blob', timeout: 120000 })).data
export const getDict = async (category) => (await api.get(`/dict/${category}`)).data
export const getFieldOptions = async (category) => (await api.get(`/dict/options/${category}`)).data
export const hideFieldOption = async (category, value) => (await api.post('/dict/options/hide', { category, value })).data

export const getLLMConfig = async () => (await api.get('/system/llm-config')).data
export const setLLMConfig = async (payload) => (await api.post('/system/llm-config', payload)).data
export const testLLM = async (text) => (await api.post('/system/llm-test', { text })).data

export const getRuleConfig = async () => (await api.get('/system/rule-config')).data
export const setRuleConfig = async (payload) => (await api.post('/system/rule-config', payload)).data

export const getLogs = async (limit = 200) => (await api.get('/logs', { params: { limit } })).data
export const deleteImage = async (imageId) => (await api.delete(`/images/${imageId}`)).data