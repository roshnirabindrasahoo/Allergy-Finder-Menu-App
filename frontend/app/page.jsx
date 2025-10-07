'use client'
import Link from 'next/link'
import { getToken, clearToken } from '@/lib/auth'
import { useEffect, useState } from 'react'

export default function HomePage() {
  const [authed, setAuthed] = useState(false)
  useEffect(() => { setAuthed(!!getToken()) }, [])
  return (
    <div>
      <nav>
        {!authed && <Link href="/login"><button>Login</button></Link>}
        {!authed && <Link href="/register"><button>Register</button></Link>}
        {authed && <Link href="/menu"><button>Menu</button></Link>}
        {authed && <Link href="/profile"><button>My Allergies</button></Link>}
        {authed && <Link href="/upload"><button>Bulk Upload</button></Link>}
        {authed && <button onClick={() => { clearToken(); location.href='/' }}>Logout</button>}
      </nav>
      <p>Welcome! Please log in or register to continue.</p>
    </div>
  )
}
