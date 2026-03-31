import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../context/useAuth'
import { apiRequest, endpoints } from '../lib/api'
import { formatDate } from '../lib/format'

export default function ProfilePage() {
  const { accessToken, me, fetchMe } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    setBusy(true)
    setError('')
    try {
      await apiRequest(endpoints.me, { token: accessToken })
      await fetchMe(accessToken)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }, [accessToken, fetchMe])

  useEffect(() => {
    if (!me) {
      refresh().catch(() => {})
    }
  }, [me, refresh])

  return (
    <section className="stack-lg">
      <div className="section-header">
        <div>
          <p className="section-eyebrow">Account</p>
          <h2>Current User</h2>
        </div>
        <button type="button" className="ghost-btn" onClick={refresh} disabled={busy}>
          {busy ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="alert error">{error}</div>}

      <article className="panel profile-card">
        <div>
          <p className="muted">Name</p>
          <h3>{me?.name || '-'}</h3>
        </div>
        <div>
          <p className="muted">Email</p>
          <h3>{me?.email || '-'}</h3>
        </div>
        <div>
          <p className="muted">User ID</p>
          <h3>{me?.user_id || '-'}</h3>
        </div>
        <div>
          <p className="muted">Joined</p>
          <h3>{formatDate(me?.created_at)}</h3>
        </div>
      </article>
    </section>
  )
}
