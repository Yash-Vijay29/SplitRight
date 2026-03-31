import { useCallback, useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/useAuth'
import SearchSelect from '../components/SearchSelect'
import { apiRequest, endpoints } from '../lib/api'
import { formatDate, formatMoney, toYmd } from '../lib/format'

function memberToOption(member) {
  return {
    value: member.user?.user_id,
    label: `${member.user?.name} (${member.user?.email})`,
    meta: member,
  }
}

export default function SettlementsPage() {
  const { accessToken, selectedGroupId } = useAuth()
  const [members, setMembers] = useState([])
  const [settlements, setSettlements] = useState([])
  const [fromUser, setFromUser] = useState(null)
  const [toUser, setToUser] = useState(null)
  const [amount, setAmount] = useState('')
  const [settlementDate, setSettlementDate] = useState(toYmd())
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  const loadData = useCallback(async () => {
    if (!selectedGroupId) {
      setMembers([])
      setSettlements([])
      return
    }

    const [membersPayload, settlementsPayload] = await Promise.all([
      apiRequest(endpoints.groupMembers(selectedGroupId), { token: accessToken }),
      apiRequest(endpoints.groupSettlements(selectedGroupId), { token: accessToken }),
    ])

    setMembers(membersPayload.results || [])
    setSettlements(settlementsPayload.results || [])
  }, [accessToken, selectedGroupId])

  useEffect(() => {
    loadData().catch((err) => {
      setError(err.message)
      setMembers([])
      setSettlements([])
    })
  }, [loadData])

  const options = useMemo(() => members.map(memberToOption), [members])
  const memberUserIds = useMemo(
    () => new Set(members.map((member) => Number(member.user?.user_id))),
    [members],
  )

  const loadOptions = useCallback(async (query) => {
    const text = (query || '').trim().toLowerCase()
    const localMatches = options.filter((option) => option.label.toLowerCase().includes(text))

    if (text.length < 2) {
      return localMatches
    }

    const payload = await apiRequest(endpoints.userSearch, {
      token: accessToken,
      params: { q: text, limit: 20 },
    })

    const remoteOptions = (payload.results || []).map((user) => {
      const inGroup = memberUserIds.has(Number(user.user_id))
      return {
        value: user.user_id,
        label: inGroup
          ? `${user.name} (${user.email})`
          : `${user.name} (${user.email}) - not in this group`,
        isDisabled: !inGroup,
      }
    })

    const deduped = new Map()
    for (const option of [...localMatches, ...remoteOptions]) {
      deduped.set(String(option.value), option)
    }

    return Array.from(deduped.values())
  }, [accessToken, memberUserIds, options])

  async function handleSubmit(event) {
    event.preventDefault()
    if (!selectedGroupId) {
      setError('Select a current group from the top bar first.')
      return
    }
    if (!fromUser || !toUser) {
      setError('Select both payer and receiver.')
      return
    }

    setBusy(true)
    setError('')
    setMessage('')

    try {
      const payload = await apiRequest(endpoints.groupSettlements(selectedGroupId), {
        method: 'POST',
        token: accessToken,
        body: {
          from_user: Number(fromUser.value),
          to_user: Number(toUser.value),
          amount,
          settlement_date: settlementDate,
        },
      })

      await loadData()
      setFromUser(null)
      setToUser(null)
      setAmount('')
      setSettlementDate(toYmd())
      setMessage(payload.message || 'Settlement recorded successfully.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="stack-lg">
      <div className="section-header">
        <div>
          <p className="section-eyebrow">Settlements</p>
          <h2>Record and review settlements</h2>
        </div>
        <button type="button" className="ghost-btn" onClick={loadData}>Reload</button>
      </div>

      {(error || message) && <div className={error ? 'alert error' : 'alert ok'}>{error || message}</div>}

      {!selectedGroupId ? (
        <section className="panel">
          <p className="muted">Choose a current group from the top bar to record settlements.</p>
        </section>
      ) : (
        <>
          <form className="panel stack" onSubmit={handleSubmit}>
            <h3>Record Settlement</h3>
            <label>
              From User
              <SearchSelect
                loadOptions={loadOptions}
                value={fromUser}
                onChange={setFromUser}
                placeholder="Search member"
                isOptionDisabled={(option) => Boolean(option.isDisabled)}
              />
            </label>

            <label>
              To User
              <SearchSelect
                loadOptions={loadOptions}
                value={toUser}
                onChange={setToUser}
                placeholder="Search member"
                isOptionDisabled={(option) => Boolean(option.isDisabled)}
              />
            </label>

            <div className="form-grid two">
              <label>
                Amount
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={amount}
                  onChange={(event) => setAmount(event.target.value)}
                  required
                />
              </label>
              <label>
                Date
                <input
                  type="date"
                  value={settlementDate}
                  onChange={(event) => setSettlementDate(event.target.value)}
                  required
                />
              </label>
            </div>

            <button type="submit" disabled={busy}>
              {busy ? 'Saving...' : 'Record Settlement'}
            </button>
          </form>

          <section className="panel stack">
            <h3>Settlement History</h3>
            {settlements.length === 0 ? (
              <p className="muted">No settlements have been recorded for this group.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>From</th>
                    <th>To</th>
                    <th>Amount</th>
                    <th>Date</th>
                  </tr>
                </thead>
                <tbody>
                  {settlements.map((settlement) => (
                    <tr key={settlement.settlement_id}>
                      <td>{settlement.from_user?.name || settlement.from_user?.user_id}</td>
                      <td>{settlement.to_user?.name || settlement.to_user?.user_id}</td>
                      <td>{formatMoney(settlement.amount)}</td>
                      <td>{formatDate(settlement.settlement_date)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </>
      )}
    </section>
  )
}
