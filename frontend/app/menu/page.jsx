'use client'
import { useEffect, useState } from 'react'
import { api } from '@/lib/api'
import { getToken } from '@/lib/auth'
import Link from 'next/link'

export default function MenuPage() {
  const [items, setItems] = useState([])
  const [safe, setSafe] = useState(true)
  const token = getToken()

  useEffect(() => {
    if (!token) return
    const url = safe ? '/api/menus?safeForUser=true' : '/api/menus'
    api(url, { token }).then(setItems).catch(console.error)
  }, [safe, token])

  if (!token) return <p>Please <Link href="/login">login</Link>.</p>

  return (
    <div>
      <h2>Menu</h2>
      <label>
        <input type="checkbox" checked={safe} onChange={e=>setSafe(e.target.checked)} />
        {' '}Only show items safe for me
      </label>
      <ul>
        {items.map(i => (
          <li key={i.id}>
            <b>{i.item_name}</b> - ${i.price} <br />
            <small>Allergens: {i.allergens.join(', ') || 'None'}</small>
          </li>
        ))}
      </ul>
    </div>
  )
}
