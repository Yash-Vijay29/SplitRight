import { useCallback, useEffect, useMemo, useState } from 'react'
import { apiRequest, endpoints } from '../lib/api'
import { AuthContext } from './authContextValue'

const ACCESS_KEY = 'sr_access'
const REFRESH_KEY = 'sr_refresh'
const GROUP_KEY = 'sr_group_id'

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem(ACCESS_KEY) || '')
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem(REFRESH_KEY) || '')
  const [selectedGroupId, setSelectedGroupId] = useState(() => localStorage.getItem(GROUP_KEY) || '')
  const [me, setMe] = useState(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  const persistAuth = useCallback((nextAccess, nextRefresh) => {
    setAccessToken(nextAccess)
    setRefreshToken(nextRefresh)

    if (nextAccess) {
      localStorage.setItem(ACCESS_KEY, nextAccess)
    } else {
      localStorage.removeItem(ACCESS_KEY)
    }

    if (nextRefresh) {
      localStorage.setItem(REFRESH_KEY, nextRefresh)
    } else {
      localStorage.removeItem(REFRESH_KEY)
    }
  }, [])

  const updateSelectedGroup = useCallback((nextGroupId) => {
    const normalized = nextGroupId ? String(nextGroupId) : ''
    setSelectedGroupId(normalized)

    if (normalized) {
      localStorage.setItem(GROUP_KEY, normalized)
    } else {
      localStorage.removeItem(GROUP_KEY)
    }
  }, [])

  const fetchMe = useCallback(async (token = accessToken) => {
    if (!token) {
      setMe(null)
      return null
    }

    const payload = await apiRequest(endpoints.me, { token })
    setMe(payload)
    return payload
  }, [accessToken])

  const login = useCallback(async (credentials) => {
    const payload = await apiRequest(endpoints.login, {
      method: 'POST',
      body: credentials,
    })

    persistAuth(payload.access || '', payload.refresh || '')
    setMe(payload.user || null)

    return payload
  }, [persistAuth])

  const signup = useCallback(async (form) => {
    return apiRequest(endpoints.signup, {
      method: 'POST',
      body: form,
    })
  }, [])

  const logout = useCallback(() => {
    persistAuth('', '')
    updateSelectedGroup('')
    setMe(null)
  }, [persistAuth, updateSelectedGroup])

  useEffect(() => {
    let ignore = false

    async function bootstrap() {
      if (!accessToken) {
        setIsBootstrapping(false)
        return
      }

      try {
        const payload = await apiRequest(endpoints.me, { token: accessToken })
        if (!ignore) {
          setMe(payload)
        }
      } catch {
        if (!ignore) {
          logout()
        }
      } finally {
        if (!ignore) {
          setIsBootstrapping(false)
        }
      }
    }

    bootstrap()

    return () => {
      ignore = true
    }
  }, [accessToken, logout])

  const value = useMemo(() => ({
    accessToken,
    refreshToken,
    selectedGroupId,
    me,
    isAuthenticated: Boolean(accessToken),
    isBootstrapping,
    login,
    signup,
    logout,
    fetchMe,
    updateSelectedGroup,
  }), [
    accessToken,
    refreshToken,
    selectedGroupId,
    me,
    isBootstrapping,
    login,
    signup,
    logout,
    fetchMe,
    updateSelectedGroup,
  ])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
