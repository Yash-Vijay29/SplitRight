import { useState } from 'react'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth'

const initialSignup = {
  name: '',
  email: '',
  password: '',
}

const initialLogin = {
  email: '',
  password: '',
}

export default function LoginPage() {
  const navigate = useNavigate()
  const { isAuthenticated, login, signup } = useAuth()
  const [signupForm, setSignupForm] = useState(initialSignup)
  const [loginForm, setLoginForm] = useState(initialLogin)
  const [busy, setBusy] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  async function handleSignup(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setBusy('signup')

    try {
      const payload = await signup(signupForm)
      setMessage(payload.message || 'Account created. You can now sign in.')
      setSignupForm(initialSignup)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  async function handleLogin(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setBusy('login')

    try {
      const payload = await login(loginForm)
      setMessage(payload.message || 'Login successful.')
      navigate('/dashboard')
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy('')
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-shell">
        <section className="hero-card">
          <p className="brand-eyebrow">SplitRight</p>
          <h1>Money clarity for every shared plan.</h1>
          <p>
            Use searchable workflows for group joining, expense entry, and settlements.
            No one needs to remember internal IDs.
          </p>
        </section>

        <section className="auth-grid">
          <form className="panel stack" onSubmit={handleSignup}>
            <h2>Create Account</h2>
            <label>
              Name
              <input
                type="text"
                value={signupForm.name}
                onChange={(event) => setSignupForm((prev) => ({ ...prev, name: event.target.value }))}
                required
              />
            </label>
            <label>
              Email
              <input
                type="email"
                value={signupForm.email}
                onChange={(event) => setSignupForm((prev) => ({ ...prev, email: event.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                minLength={8}
                value={signupForm.password}
                onChange={(event) => setSignupForm((prev) => ({ ...prev, password: event.target.value }))}
                required
              />
            </label>
            <button type="submit" disabled={busy === 'signup'}>
              {busy === 'signup' ? 'Creating...' : 'Create Account'}
            </button>
          </form>

          <form className="panel stack" onSubmit={handleLogin}>
            <h2>Sign In</h2>
            <label>
              Email
              <input
                type="email"
                value={loginForm.email}
                onChange={(event) => setLoginForm((prev) => ({ ...prev, email: event.target.value }))}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                value={loginForm.password}
                onChange={(event) => setLoginForm((prev) => ({ ...prev, password: event.target.value }))}
                required
              />
            </label>
            <button type="submit" disabled={busy === 'login'}>
              {busy === 'login' ? 'Signing in...' : 'Sign In'}
            </button>
          </form>
        </section>

        {(message || error) && (
          <div className={error ? 'alert error' : 'alert ok'}>
            {error || message}
          </div>
        )}
      </div>
    </div>
  )
}
