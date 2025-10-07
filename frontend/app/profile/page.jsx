'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { getToken } from '@/lib/auth'
import Link from 'next/link'

export default function ProfilePage() {
  const [allergens, setAllergens] = useState([])
  const [sel, setSel] = useState(new Set())
  const [msg, setMsg] = useState('')
  const token = getToken()

  useEffect(() => {
    if (!token) return
    api('/api/allergens', { token }).then(setAllergens)
  }, [token])

  const toggle = (id) => {
    const s = new Set(sel)
    s.has(id) ? s.delete(id) : s.add(id)
    setSel(s)
  }

  const save = async () => {
    await api('/api/allergens/me', { method:'PUT', body:{ allergyIds:[...sel] }, token })
    setMsg('Saved!'); setTimeout(()=>setMsg(''), 1200)
  }

  if (!token) return <p>Please <Link href="/login">login</Link>.</p>

  return (
    <div>
      <h2>My Allergies</h2>
      {msg && <div style={{color:'green'}}>{msg}</div>}
      <ul>
        {allergens.map(a => (
          <li key={a.id}>
            <label>
              <input type="checkbox" checked={sel.has(a.id)} onChange={()=>toggle(a.id)} />
              {' '}{a.name}
            </label>
          </li>
        ))}
      </ul>
      <button onClick={save}>Save</button>
    </div>
  )
}
