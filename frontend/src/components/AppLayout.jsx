import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useCallback, useEffect, useMemo, useState } from 'react'
import SearchSelect from './SearchSelect'
import { useAuth } from '../context/useAuth'
import { apiRequest, endpoints } from '../lib/api'

const navItems = [
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/groups', label: 'Groups' },
  { to: '/expenses', label: 'Expenses' },
  { to: '/balances', label: 'Balances' },
  { to: '/settlements', label: 'Settlements' },
  { to: '/profile', label: 'Profile' },
]

export default function AppLayout() {
  const navigate = useNavigate()
  const {
    accessToken,
    me,
    selectedGroupId,
    updateSelectedGroup,
    logout,
  } = useAuth()
  const [groups, setGroups] = useState([])
  const [loadingGroups, setLoadingGroups] = useState(false)

  const loadMyGroups = useCallback(async () => {
    setLoadingGroups(true)
    try {
      const payload = await apiRequest(endpoints.groups, { token: accessToken })
      const nextGroups = payload.results || []
      setGroups(nextGroups)

      if (
        selectedGroupId &&
        !nextGroups.some((group) => String(group.group_id) === String(selectedGroupId))
      ) {
        updateSelectedGroup('')
      }
    } finally {
      setLoadingGroups(false)
    }
  }, [accessToken, selectedGroupId, updateSelectedGroup])

  useEffect(() => {
    loadMyGroups().catch(() => {
      setGroups([])
    })
  }, [loadMyGroups])

  const groupValue = useMemo(() => {
    const currentGroup = groups.find((group) => String(group.group_id) === String(selectedGroupId))
    if (!currentGroup) {
      return null
    }

    return {
      value: String(currentGroup.group_id),
      label: currentGroup.group_name,
      meta: currentGroup,
    }
  }, [groups, selectedGroupId])

  const loadGroupOptions = useCallback(async (inputValue) => {
    const query = (inputValue || '').trim().toLowerCase()
    return groups
      .filter((group) => group.group_name.toLowerCase().includes(query))
      .slice(0, 50)
      .map((group) => ({
        value: String(group.group_id),
        label: group.group_name,
        meta: group,
      }))
  }, [groups])

  const handleGroupChange = useCallback((nextValue) => {
    updateSelectedGroup(nextValue?.value || '')
  }, [updateSelectedGroup])

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="brand-eyebrow">SplitRight</p>
          <h1 className="brand-title">Expense Workspace</h1>
        </div>
        <div className="topbar-actions">
          <div className="topbar-field">
            <label>Current Group</label>
            <SearchSelect
              loadOptions={loadGroupOptions}
              value={groupValue}
              onChange={handleGroupChange}
              placeholder={loadingGroups ? 'Loading groups...' : 'Search your groups'}
              noOptionsMessage={() => 'No groups yet'}
            />
          </div>
          <button className="ghost-btn" type="button" onClick={() => navigate('/profile')}>
            {me ? `${me.name} (${me.email})` : 'Current User'}
          </button>
          <button className="danger-btn" type="button" onClick={logout}>
            Logout
          </button>
        </div>
      </header>

      <nav className="nav-grid">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
          >
            {item.label}
          </NavLink>
        ))}
      </nav>

      <main className="page-wrap">
        <Outlet context={{ groups, reloadGroups: loadMyGroups }} />
      </main>
    </div>
  )
}
