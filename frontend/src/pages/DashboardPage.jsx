import { useCallback, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { useAuth } from '../context/useAuth'
import { apiRequest, endpoints } from '../lib/api'
import { formatMoney } from '../lib/format'

export default function DashboardPage() {
  const { accessToken, me } = useAuth()
  const { groups, reloadGroups } = useOutletContext()
  const [myBalances, setMyBalances] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const loadDashboard = useCallback(async () => {
    setBusy(true)
    setError('')
    try {
      await reloadGroups()
      const payload = await apiRequest(endpoints.myBalances, { token: accessToken })
      setMyBalances(payload.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }, [accessToken, reloadGroups])

  useEffect(() => {
    loadDashboard().catch(() => {})
  }, [loadDashboard])

  const summary = useMemo(() => {
    let owedToYou = 0
    let youOwe = 0

    for (const balance of myBalances) {
      const amount = Number(balance.net_balance || 0)
      if (amount > 0) {
        owedToYou += amount
      } else if (amount < 0) {
        youOwe += Math.abs(amount)
      }
    }

    return {
      groupCount: groups.length,
      owedToYou,
      youOwe,
    }
  }, [groups, myBalances])

  return (
    <section className="stack-lg">
      <div className="section-header">
        <div>
          <p className="section-eyebrow">Overview</p>
          <h2>Welcome back{me ? `, ${me.name}` : ''}</h2>
        </div>
        <button type="button" className="ghost-btn" onClick={loadDashboard} disabled={busy}>
          {busy ? 'Refreshing...' : 'Refresh'}
        </button>
      </div>

      {error && <div className="alert error">{error}</div>}

      <div className="cards-grid">
        <article className="stat-card">
          <p>Total Groups</p>
          <h3>{summary.groupCount}</h3>
        </article>
        <article className="stat-card">
          <p>Owed To You</p>
          <h3>{formatMoney(summary.owedToYou)}</h3>
        </article>
        <article className="stat-card">
          <p>You Owe</p>
          <h3>{formatMoney(summary.youOwe)}</h3>
        </article>
      </div>

      <section className="panel stack">
        <h3>Group Snapshot</h3>
        {groups.length === 0 ? (
          <p className="muted">Create or join a group to start tracking shared expenses.</p>
        ) : (
          <div className="list-grid">
            {groups.map((group) => (
              <article key={group.group_id} className="mini-card">
                <h4>{group.group_name}</h4>
                <p>Group #{group.group_id}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}
