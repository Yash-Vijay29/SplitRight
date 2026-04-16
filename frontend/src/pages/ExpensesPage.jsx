import React, { useCallback, useEffect, useMemo, useState } from 'react'
import { useAuth } from '../context/useAuth'
import SearchSelect from '../components/SearchSelect'
import { apiRequest, endpoints } from '../lib/api'
import { formatDate, formatMoney, toYmd } from '../lib/format'

function toUserOption(member) {
  return {
    value: member.user?.user_id,
    label: `${member.user?.name} (${member.user?.email})`,
    meta: member,
  }
}

function getConfidenceSummary(confidence) {
  const raw = Number(confidence)
  if (!Number.isFinite(raw)) {
    return null
  }

  const normalizedPercent = raw <= 1 ? raw * 100 : raw
  const percent = Math.max(0, Math.min(100, Math.round(normalizedPercent)))

  let tone = 'low'
  if (percent >= 80) {
    tone = 'high'
  } else if (percent >= 60) {
    tone = 'medium'
  }

  return {
    percent,
    tone,
  }
}

export default function ExpensesPage() {
  const { accessToken, selectedGroupId } = useAuth()
  const [members, setMembers] = useState([])
  const [expenses, setExpenses] = useState([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState('')

  const [formState, setFormState] = useState({
    amount: '',
    description: '',
    expenseDate: toYmd(),
    splitType: 'equal',
  })
  const [payer, setPayer] = useState(null)
  const [splitUsers, setSplitUsers] = useState([])
  const [shareByUser, setShareByUser] = useState({})
  const [billImageFile, setBillImageFile] = useState(null)
  const [billParseResult, setBillParseResult] = useState(null)

  const loadGroupData = useCallback(async () => {
    if (!selectedGroupId) {
      setMembers([])
      setExpenses([])
      setBillImageFile(null)
      setBillParseResult(null)
      return
    }

    const [membersPayload, expensesPayload] = await Promise.all([
      apiRequest(endpoints.groupMembers(selectedGroupId), { token: accessToken }),
      apiRequest(endpoints.groupExpenses(selectedGroupId), { token: accessToken }),
    ])

    setMembers(membersPayload.results || [])
    setExpenses(expensesPayload.results || [])
  }, [accessToken, selectedGroupId])

  useEffect(() => {
    loadGroupData().catch((err) => {
      setError(err.message)
      setMembers([])
      setExpenses([])
    })
  }, [loadGroupData])

  const memberOptions = useMemo(() => members.map(toUserOption), [members])
  const memberUserIds = useMemo(
    () => new Set(members.map((member) => Number(member.user?.user_id))),
    [members],
  )

  const loadMemberOptions = useCallback(async (query) => {
    const input = (query || '').trim().toLowerCase()
    const localMatches = memberOptions.filter((option) => option.label.toLowerCase().includes(input))

    if (input.length < 2) {
      return localMatches
    }

    const payload = await apiRequest(endpoints.userSearch, {
      token: accessToken,
      params: { q: input, limit: 20 },
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
  }, [accessToken, memberOptions, memberUserIds])

  function handleSplitUsers(nextOptions) {
    const options = nextOptions || []
    setSplitUsers(options)

    setShareByUser((prev) => {
      const next = {}
      for (const option of options) {
        next[option.value] = prev[option.value] || ''
      }
      return next
    })
  }

  async function handleSubmit(event) {
    event.preventDefault()
    if (!selectedGroupId) {
      setError('Select a current group from the top bar first.')
      return
    }
    if (!payer) {
      setError('Choose a payer from group members.')
      return
    }
    if (splitUsers.length === 0) {
      setError('Pick at least one split member.')
      return
    }

    setBusy('create')
    setError('')
    setMessage('')

    const body = {
      paid_by: Number(payer.value),
      amount: formState.amount,
      expense_date: formState.expenseDate,
      description: formState.description,
      split_type: formState.splitType,
    }

    if (formState.splitType === 'equal') {
      body.split_user_ids = splitUsers.map((option) => Number(option.value))
    } else {
      const splits = splitUsers.map((option) => ({
        user_id: Number(option.value),
        share_amount: shareByUser[option.value] || '',
      }))
      body.splits = splits
    }

    try {
      const payload = await apiRequest(endpoints.groupExpenses(selectedGroupId), {
        method: 'POST',
        token: accessToken,
        body,
      })

      await loadGroupData()
      setMessage(payload.message || 'Expense added successfully.')
      setFormState({
        amount: '',
        description: '',
        expenseDate: toYmd(),
        splitType: 'equal',
      })
      setPayer(null)
      setSplitUsers([])
      setShareByUser({})
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function handleAnalyzeBill(event) {
    event.preventDefault()

    if (!selectedGroupId) {
      setError('Select a current group from the top bar first.')
      return
    }

    if (!billImageFile) {
      setError('Choose a bill image to analyze.')
      return
    }

    setBusy('parse')
    setError('')
    setMessage('')

    const formData = new FormData()
    formData.append('bill_image', billImageFile)

    try {
      const payload = await apiRequest(endpoints.groupExpenseParseBill(selectedGroupId), {
        method: 'POST',
        token: accessToken,
        body: formData,
      })

      setBillParseResult(payload)
      setMessage('Bill analyzed successfully. Review extracted data and apply it to the form.')
    } catch (err) {
      setBillParseResult(null)
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  function applyParsedExpenseSuggestion() {
    const suggestion = billParseResult?.suggested_expense
    if (!suggestion) {
      setError('No parsed suggestion is available yet.')
      return
    }

    setFormState((prev) => ({
      ...prev,
      amount: suggestion.amount || prev.amount,
      expenseDate: suggestion.expense_date || prev.expenseDate,
      description: suggestion.description || prev.description,
    }))

    const parsedPartySize = Number(billParseResult?.party_size ?? suggestion.party_size)
    if (Number.isInteger(parsedPartySize) && parsedPartySize > 0 && memberOptions.length > 0) {
      const maxSize = Math.min(parsedPartySize, memberOptions.length)
      const autoSelected = memberOptions.slice(0, maxSize)

      setSplitUsers(autoSelected)
      setShareByUser((prev) => {
        const next = {}
        for (const option of autoSelected) {
          next[option.value] = prev[option.value] || ''
        }
        return next
      })

      setMessage(
        `Parsed suggestion applied. Auto-selected ${autoSelected.length} split member(s) from detected party size. You can edit this before creating the expense.`,
      )
      return
    }

    setMessage('Parsed suggestion has been applied to the expense form.')
  }

  const confidenceSummary = useMemo(
    () => getConfidenceSummary(billParseResult?.confidence),
    [billParseResult],
  )

  return (
    <section className="stack-lg">
      <div className="section-header">
        <div>
          <p className="section-eyebrow">Expenses</p>
          <h2>Create and view expenses</h2>
        </div>
        <button type="button" className="ghost-btn" onClick={loadGroupData}>
          Reload Group Data
        </button>
      </div>

      {(error || message) && <div className={error ? 'alert error' : 'alert ok'}>{error || message}</div>}

      {!selectedGroupId ? (
        <section className="panel">
          <p className="muted">Choose a current group from the top bar to create expenses.</p>
        </section>
      ) : (
        <>
          <section className="panel stack">
            <h3>Upload Bill (AI Assist)</h3>
            <p className="muted">
              Upload a bill image to extract line items and total, then apply the suggested values to the expense form.
            </p>
            <form className="stack" onSubmit={handleAnalyzeBill}>
              <label>
                Bill Image
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  onChange={(event) => {
                    const file = event.target.files?.[0] || null
                    setBillImageFile(file)
                  }}
                  required
                />
              </label>
              <button type="submit" disabled={busy === 'parse'}>
                {busy === 'parse' ? 'Analyzing Bill...' : 'Analyze Bill'}
              </button>
            </form>

            {billParseResult && (
              <div className="stack">
                {confidenceSummary && (
                  <div
                    className={`confidence-indicator ${confidenceSummary.tone}`}
                    aria-label="Parser confidence"
                  >
                    Parser confidence: {confidenceSummary.percent}%
                  </div>
                )}

                <div className="form-grid four">
                  <label>
                    Parsed Total
                    <input type="text" value={billParseResult.totals?.total || ''} readOnly />
                  </label>
                  <label>
                    Parsed Date
                    <input type="text" value={billParseResult.suggested_expense?.expense_date || ''} readOnly />
                  </label>
                  <label>
                    Currency
                    <input type="text" value={billParseResult.totals?.currency || ''} readOnly />
                  </label>
                  <label>
                    Party Size
                    <input type="text" value={billParseResult.party_size || ''} readOnly />
                  </label>
                </div>

                <div className="form-grid four">
                  <label>
                    Subtotal
                    <input type="text" value={billParseResult.totals?.subtotal || ''} readOnly />
                  </label>
                  <label>
                    Tax
                    <input type="text" value={billParseResult.totals?.tax || ''} readOnly />
                  </label>
                  <label>
                    Tip
                    <input type="text" value={billParseResult.totals?.tip || ''} readOnly />
                  </label>
                  <label>
                    Discounts
                    <input type="text" value={billParseResult.totals?.discounts || ''} readOnly />
                  </label>
                </div>

                {(billParseResult.extracted_charges || []).length > 0 && (
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th>Qty</th>
                        <th>Unit Price</th>
                        <th>Line Total</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(billParseResult.extracted_charges || []).map((charge, index) => (
                        <tr key={`${charge.name}-${index}`}>
                          <td>{charge.name}</td>
                          <td>{charge.quantity}</td>
                          <td>{formatMoney(charge.unit_price)}</td>
                          <td>{formatMoney(charge.line_total)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}

                {(billParseResult.warnings || []).length > 0 && (
                  <div className="alert error">
                    {(billParseResult.warnings || []).join(' | ')}
                  </div>
                )}

                <button type="button" onClick={applyParsedExpenseSuggestion}>
                  Apply Parsed Suggestion To Expense Form
                </button>
              </div>
            )}
          </section>

          <form className="panel stack" onSubmit={handleSubmit}>
            <h3>Add Expense</h3>
            <div className="form-grid four">
              <label>
                Amount
                <input
                  type="number"
                  min="0.01"
                  step="0.01"
                  value={formState.amount}
                  onChange={(event) => setFormState((prev) => ({ ...prev, amount: event.target.value }))}
                  required
                />
              </label>
              <label>
                Date
                <input
                  type="date"
                  value={formState.expenseDate}
                  onChange={(event) => setFormState((prev) => ({ ...prev, expenseDate: event.target.value }))}
                  required
                />
              </label>
              <label>
                Split Type
                <select
                  value={formState.splitType}
                  onChange={(event) => setFormState((prev) => ({ ...prev, splitType: event.target.value }))}
                >
                  <option value="equal">Equal</option>
                  <option value="unequal">Unequal</option>
                </select>
              </label>
            </div>

            <label>
              Description
              <input
                type="text"
                maxLength={255}
                value={formState.description}
                onChange={(event) => setFormState((prev) => ({ ...prev, description: event.target.value }))}
                placeholder="Dinner, cab ride, groceries..."
              />
            </label>

            <label>
              Payer
              <SearchSelect
                loadOptions={loadMemberOptions}
                defaultOptions={memberOptions}
                cacheOptions={false}
                value={payer}
                onChange={setPayer}
                placeholder="Select who paid"
                noOptionsMessage={() => 'No members in this group'}
                isOptionDisabled={(option) => Boolean(option.isDisabled)}
              />
            </label>

            <label>
              Split Members
              <SearchSelect
                isMulti
                loadOptions={loadMemberOptions}
                defaultOptions={memberOptions}
                cacheOptions={false}
                value={splitUsers}
                onChange={handleSplitUsers}
                placeholder="Choose people to split with"
                isOptionDisabled={(option) => Boolean(option.isDisabled)}
              />
            </label>

            {formState.splitType === 'unequal' && splitUsers.length > 0 && (
              <div className="stack">
                <h4>Unequal Shares</h4>
                {splitUsers.map((option) => (
                  <label key={option.value}>
                    {option.label}
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={shareByUser[option.value] || ''}
                      onChange={(event) =>
                        setShareByUser((prev) => ({
                          ...prev,
                          [option.value]: event.target.value,
                        }))
                      }
                      required
                    />
                  </label>
                ))}
              </div>
            )}

            <button type="submit" disabled={busy === 'create'}>
              {busy === 'create' ? 'Creating Expense...' : 'Create Expense'}
            </button>
          </form>

          <section className="panel stack">
            <h3>Recent Expenses</h3>
            {expenses.length === 0 ? (
              <p className="muted">No expenses recorded for this group yet.</p>
            ) : (
              <table className="table">
                <thead>
                  <tr>
                    <th>Description</th>
                    <th>Payer</th>
                    <th>Amount</th>
                    <th>Date</th>
                    <th>Splits</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.map((expense) => (
                    <tr key={expense.expense_id}>
                      <td>{expense.description || 'Untitled expense'}</td>
                      <td>{expense.paid_by?.name || expense.paid_by?.user_id}</td>
                      <td>{formatMoney(expense.amount)}</td>
                      <td>{formatDate(expense.expense_date)}</td>
                      <td>
                        {(expense.splits || []).map((split) => (
                          <div key={split.expense_split_id}>
                            {split.user?.name}: {formatMoney(split.share_amount)}
                          </div>
                        ))}
                      </td>
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
