import { useCallback, useEffect, useMemo, useState } from 'react'
import { useOutletContext } from 'react-router-dom'
import { useAuth } from '../context/useAuth'
import SearchSelect from '../components/SearchSelect'
import { apiRequest, endpoints } from '../lib/api'
import { formatDate } from '../lib/format'

export default function GroupsPage() {
  const { accessToken, selectedGroupId, updateSelectedGroup } = useAuth()
  const { groups, reloadGroups } = useOutletContext()

  const [groupName, setGroupName] = useState('')
  const [isJoinable, setIsJoinable] = useState(true)
  const [joinTarget, setJoinTarget] = useState(null)
  const [members, setMembers] = useState([])
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState('')

  const selectedGroup = useMemo(
    () => groups.find((group) => String(group.group_id) === String(selectedGroupId)),
    [groups, selectedGroupId],
  )

  const loadMembers = useCallback(async () => {
    if (!selectedGroupId) {
      setMembers([])
      return
    }

    const payload = await apiRequest(endpoints.groupMembers(selectedGroupId), {
      token: accessToken,
    })
    setMembers(payload.results || [])
  }, [accessToken, selectedGroupId])

  useEffect(() => {
    loadMembers().catch(() => setMembers([]))
  }, [loadMembers])

  const loadDiscoverOptions = useCallback(async (query) => {
    const payload = await apiRequest(endpoints.discoverGroups, {
      token: accessToken,
      params: {
        q: query,
        limit: 30,
      },
    })

    return (payload.results || []).map((group) => ({
      value: String(group.group_id),
      label: group.group_name,
      meta: group,
    }))
  }, [accessToken])

  async function handleCreate(event) {
    event.preventDefault()
    setBusy('create')
    setError('')
    setMessage('')

    try {
      const payload = await apiRequest(endpoints.groups, {
        method: 'POST',
        token: accessToken,
        body: {
          group_name: groupName,
          is_joinable: isJoinable,
        },
      })

      await reloadGroups()
      setGroupName('')
      setIsJoinable(true)
      setMessage(payload.message || 'Group created successfully.')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function handleJoin(event) {
    event.preventDefault()
    if (!joinTarget) {
      setError('Pick a group from the searchable dropdown before joining.')
      return
    }

    setBusy('join')
    setError('')
    setMessage('')

    try {
      const payload = await apiRequest(endpoints.groupJoin(joinTarget.value), {
        method: 'POST',
        token: accessToken,
      })

      await reloadGroups()
      updateSelectedGroup(joinTarget.value)
      setJoinTarget(null)
      setMessage(payload.message || 'Joined group.')
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
          <p className="section-eyebrow">Group Management</p>
          <h2>Create, discover, and join groups</h2>
        </div>
      </div>

      {(error || message) && <div className={error ? 'alert error' : 'alert ok'}>{error || message}</div>}

      <div className="cards-grid split-2">
        <form className="panel stack" onSubmit={handleCreate}>
          <h3>Create Group</h3>
          <label>
            Group Name
            <input
              type="text"
              value={groupName}
              onChange={(event) => setGroupName(event.target.value)}
              required
            />
          </label>
          <label className="check-row">
            <input
              type="checkbox"
              checked={isJoinable}
              onChange={(event) => setIsJoinable(event.target.checked)}
            />
            Group is discoverable for join requests
          </label>
          <button type="submit" disabled={busy === 'create'}>
            {busy === 'create' ? 'Creating...' : 'Create Group'}
          </button>
        </form>

        <form className="panel stack" onSubmit={handleJoin}>
          <h3>Join Group</h3>
          <label>
            Search Public Groups
            <SearchSelect
              loadOptions={loadDiscoverOptions}
              value={joinTarget}
              onChange={setJoinTarget}
              placeholder="Type group name"
              noOptionsMessage={() => 'No joinable groups found'}
            />
          </label>
          <button type="submit" disabled={busy === 'join'}>
            {busy === 'join' ? 'Joining...' : 'Join Group'}
          </button>
        </form>
      </div>

      <section className="panel stack">
        <div className="section-header">
          <h3>My Groups</h3>
          <button type="button" className="ghost-btn" onClick={reloadGroups}>Refresh</button>
        </div>

        {groups.length === 0 ? (
          <p className="muted">No groups yet. Create one or join an existing public group.</p>
        ) : (
          <div className="list-grid">
            {groups.map((group) => (
              <button
                type="button"
                key={group.group_id}
                className={String(selectedGroupId) === String(group.group_id) ? 'mini-card selected' : 'mini-card'}
                onClick={() => updateSelectedGroup(group.group_id)}
              >
                <h4>{group.group_name}</h4>
                <p>Created {formatDate(group.created_at)}</p>
              </button>
            ))}
          </div>
        )}
      </section>

      <section className="panel stack">
        <h3>Members in Current Group</h3>
        {!selectedGroup ? (
          <p className="muted">Select one of your groups to view members.</p>
        ) : members.length === 0 ? (
          <p className="muted">No members found in this group.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Email</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => (
                <tr key={member.group_member_id}>
                  <td>{member.user?.name}</td>
                  <td>{member.user?.email}</td>
                  <td>{formatDate(member.joined_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </section>
  )
}
