const fileBaseUrl = import.meta.env.VITE_FILE_BASE_URL || import.meta.env.VITE_API_BASE_URL || ''

export function resolveFileBaseUrl() {
  if (!fileBaseUrl) return window.location.origin
  if (fileBaseUrl.startsWith('http')) return fileBaseUrl.replace(/\/$/, '')
  if (fileBaseUrl.startsWith('/')) {
    const trimmed = fileBaseUrl.replace(/\/$/, '')
    if (trimmed.endsWith('/api')) {
      return window.location.origin
    }
    return `${window.location.origin}${trimmed}`
  }
  return fileBaseUrl.replace(/\/$/, '')
}

export function fileUrl(filePath) {
  const normalized = String(filePath || '').replace(/\\/g, '/')
  if (!normalized) return ''
  if (normalized.startsWith('http')) return normalized
  const base = resolveFileBaseUrl()
  const cleanPath = normalized.startsWith('/') ? normalized.slice(1) : normalized
  return `${base}/${cleanPath}`
}
