import { useState } from 'react'
import { useAuth } from '../context/useAuth'
import { apiRequest, endpoints } from '../lib/api'
import { formatMoney } from '../lib/format'

export default function BalancesPage() {
  const { accessToken, selectedGroupId } = useAuth()
  const [groupBalances, setGroupBalances] = useState([])
  const [pairwise, setPairwise] = useState([])
  const [myBalances, setMyBalances] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState('')

  async function loadGroupBalances() {
    if (!selectedGroupId) {
      setError('Select a current group from the top bar first.')
      return
    }

    setBusy('group')
    setError('')
    try {
      const payload = await apiRequest(endpoints.groupBalances(selectedGroupId), {
        token: accessToken,
      })
      setGroupBalances(payload.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function loadPairwise() {
    if (!selectedGroupId) {
      setError('Select a current group from the top bar first.')
      return
    }

    setBusy('pairwise')
    setError('')
    try {
      const payload = await apiRequest(endpoints.groupPairwiseBalances(selectedGroupId), {
        token: accessToken,
      })
      setPairwise(payload.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function loadMine() {
    setBusy('mine')
    setError('')
    try {
      const payload = await apiRequest(endpoints.myBalances, { token: accessToken })
      setMyBalances(payload.results || [])
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <section className="stack-lg">
      <div className="section-header">
        <div>
          <p className="section-eyebrow">Balances</p>
          <h2>Group and personal standing</h2>
        </div>
      </div>

      {error && <div className="alert error">{error}</div>}

      <section className="panel stack">
        <div className="button-row">
          <button type="button" className="ghost-btn" onClick={loadGroupBalances} disabled={busy === 'group'}>
            {busy === 'group' ? 'Loading...' : 'Load Group Balances'}
          </button>
          <button type="button" className="ghost-btn" onClick={loadPairwise} disabled={busy === 'pairwise'}>
            {busy === 'pairwise' ? 'Loading...' : 'Load Pairwise Owes'}
          </button>
          <button type="button" className="ghost-btn" onClick={loadMine} disabled={busy === 'mine'}>
            {busy === 'mine' ? 'Loading...' : 'Load My Balances'}
          </button>
        </div>
      </section>

      <section className="panel stack">
        <h3>Group Balances</h3>
        {groupBalances.length === 0 ? (
          <p className="muted">Load group balances to see each member's net position.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>User</th>
                <th>Net Balance</th>
              </tr>
            </thead>
            <tbody>
              {groupBalances.map((row, index) => (
                <tr key={`${row.user_id || index}-group`}>
                  <td>{row.user_name || row.user?.name || row.user_id}</td>
                  <td>{formatMoney(row.net_balance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel stack">
        <h3>Pairwise Owes</h3>
        {pairwise.length === 0 ? (
          <p className="muted">Load pairwise balances to view who owes whom.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>From</th>
                <th>To</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {pairwise.map((row, index) => (
                <tr key={`${index}-pairwise`}>
                  <td>{row.from_user_name || row.from_user?.name || row.from_user_id}</td>
                  <td>{row.to_user_name || row.to_user?.name || row.to_user_id}</td>
                  <td>{formatMoney(row.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="panel stack">
        <h3>My Balances Across Groups</h3>
        {myBalances.length === 0 ? (
          <p className="muted">Load personal balances to view your status by group.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Group</th>
                <th>Net Balance</th>
              </tr>
            </thead>
            <tbody>
              {myBalances.map((row, index) => (
                <tr key={`${row.group_id || index}-mine`}>
                  <td>{row.group_name || row.group_id}</td>
                  <td>{formatMoney(row.net_balance)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </section>
  )
}
