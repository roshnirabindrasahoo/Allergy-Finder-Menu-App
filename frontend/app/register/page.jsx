'use client'
import { useState } from 'react'
import { api } from '@/lib/api'
import { setToken } from '@/lib/auth'
import Link from 'next/link'

export default function RegisterPage() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [role, setRole] = useState('customer')
  const [err, setErr] = useState('')

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    try {
      const r = await api('/api/auth/register', { method:'POST', body:{ name, email, password, role } })
      setToken(r.token)
      location.href = role === 'restaurant' ? '/upload' : '/menu'
    } catch (e) { setErr(e.message) }
  }

  return (
    <div>
      <h2>Register</h2>
      {err && <div style={{color:'red'}}>{err}</div>}
      <form onSubmit={submit}>
        <div><input placeholder="Name" value={name} onChange={e=>setName(e.target.value)} /></div>
        <div><input placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)} /></div>
        <div><input placeholder="Password" type="password" value={password} onChange={e=>setPassword(e.target.value)} /></div>
        <div>
          <label>Role: </label>
          <select value={role} onChange={e=>setRole(e.target.value)}>
            <option value="customer">Customer</option>
            <option value="restaurant">Restaurant</option>
          </select>
        </div>
        <button>Create Account</button>
      </form>
      <p>Already have an account? <Link href="/login">Login</Link></p>
    </div>
  )
}
