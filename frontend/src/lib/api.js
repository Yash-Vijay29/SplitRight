const API_BASE = (import.meta.env.VITE_API_BASE_URL || '/api').replace(/\/$/, '')

function buildUrl(path, params) {
  const normalizedPath = path.startsWith('/') ? path.slice(1) : path
  const url = new URL(`${API_BASE}/${normalizedPath}`, window.location.origin)

  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value === undefined || value === null || value === '') {
        continue
      }
      url.searchParams.set(key, String(value))
    }
  }

  if (API_BASE.startsWith('http://') || API_BASE.startsWith('https://')) {
    return url.toString()
  }

  return `${API_BASE}/${normalizedPath}${url.search ? `?${url.searchParams.toString()}` : ''}`
}

function parseApiError(payload, fallback) {
  if (!payload) {
    return fallback
  }

  if (typeof payload === 'string') {
    return payload
  }

  if (payload.detail) {
    return String(payload.detail)
  }

  if (payload.message) {
    return String(payload.message)
  }

  return Object.entries(payload)
    .map(([key, value]) => {
      if (Array.isArray(value)) {
        return `${key}: ${value.join(', ')}`
      }
      if (value && typeof value === 'object') {
        return `${key}: ${JSON.stringify(value)}`
      }
      return `${key}: ${value}`
    })
    .join(' | ')
}

export async function apiRequest(path, options = {}) {
  const {
    method = 'GET',
    token,
    body,
    headers = {},
    params,
  } = options

  const requestHeaders = {
    'Content-Type': 'application/json',
    ...headers,
  }

  if (token) {
    requestHeaders.Authorization = `Bearer ${token}`
  }

  const response = await fetch(buildUrl(path, params), {
    method,
    headers: requestHeaders,
    body: body ? JSON.stringify(body) : undefined,
  })

  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new Error(parseApiError(payload, `HTTP ${response.status}`))
  }

  return payload
}

export const endpoints = {
  signup: 'auth/signup',
  login: 'auth/login',
  me: 'users/me',
  userSearch: 'users/search',
  groups: 'groups',
  discoverGroups: 'groups/discover',
  groupMembers: (groupId) => `groups/${groupId}/members`,
  groupJoin: (groupId) => `groups/${groupId}/join`,
  groupExpenses: (groupId) => `groups/${groupId}/expenses`,
  groupBalances: (groupId) => `groups/${groupId}/balances`,
  groupPairwiseBalances: (groupId) => `groups/${groupId}/balances/pairwise`,
  myBalances: 'users/me/balances',
  groupSettlements: (groupId) => `groups/${groupId}/settlements`,
}
