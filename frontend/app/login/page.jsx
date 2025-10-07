'use client'
import { useState } from 'react'
import { api } from '@/lib/api'
import { setToken } from '@/lib/auth'
import Link from 'next/link'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      const r = await api('/api/auth/login', { method:'POST', body:{ email, password } })
      setToken(r.token)
      location.href = '/menu'
    } catch (e) { setErr(e.message) }
  }

  return (
    <div>
      <h2>Login</h2>
      {err && <div style={{color:'red'}}>{err}</div>}
      <form onSubmit={submit}>
        <div><input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div><input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
        <button>Login</button>
      </form>
      <p>New here? <Link href="/register">Create an account</Link></p>
    </div>
  )
}
