'use client'
import { useState } from 'react'
import { getToken } from '@/lib/auth'
import Link from 'next/link'

export default function UploadPage() {
  const token = getToken()
  const [file, setFile] = useState(null)
  const [fileId, setFileId] = useState(null)
  const [preview, setPreview] = useState([])
  const [issues, setIssues] = useState([])
  const [err, setErr] = useState('')

  const upload = async (endpoint) => {
    setErr('')
    const fd = new FormData()
    fd.append('file', file)
    try {
      const url = (process.env.NEXT_PUBLIC_API_BASE || '') + endpoint
      const res = await fetch(url, { method:'POST', headers: { Authorization:`Bearer ${token}` }, body: fd })
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Upload failed')
      setFileId(json.fileId || null)
      setPreview(json.preview || [])
      setIssues(json.issues || [])
    } catch (e) { setErr(e.message) }
  }

  const commit = async () => {
    if (!fileId) { alert('No preview to commit'); return }
    try {
      const url = (process.env.NEXT_PUBLIC_API_BASE || '') + `/api/ingest/commit?fileId=${fileId}`
      const res = await fetch(url, { method:'POST', headers: { Authorization:`Bearer ${token}` }})
      const json = await res.json()
      if (!res.ok) throw new Error(json.detail || 'Commit failed')
      alert(`Committed ${json.created} items`)
      setPreview([]); setIssues([]); setFile(null); setFileId(null)
    } catch (e) { alert(e.message) }
  }

  if (!token) return <p>Please <Link href="/login">login</Link> as a restaurant.</p>

  return (
    <div>
      <h2>Bulk Upload (Restaurant)</h2>
      {err && <div style={{color:'red'}}>{err}</div>}
      <input type="file" accept=".csv,.pdf" onChange={e=>setFile(e.target.files?.[0] || null)} />
      <div style={{display:'flex', gap:8}}>
        <button disabled={!file} onClick={()=>upload('/api/ingest/csv')}>Preview CSV</button>
        <button disabled={!file} onClick={()=>upload('/api/ingest/pdf')}>Preview PDF</button>
      </div>

      {issues.length > 0 && (
        <div style={{background:'#fff5e6', padding:8, margin:'12px 0'}}>
          <b>Issues:</b>
          <ul>{issues.map((i,k)=><li key={k}>{i}</li>)}</ul>
        </div>
      )}

      {preview.length > 0 && (
        <>
          <table>
            <thead><tr><th>Name</th><th>Description</th><th>Price</th><th>Auto-predicted allergens</th></tr></thead>
            <tbody>
              {preview.map((r,idx)=>(
                <tr key={idx}>
                  <td>{r.item_name}</td>
                  <td>{r.description}</td>
                  <td>{r.price}</td>
                  <td>{(r.predicted_allergens||[]).join(', ') || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <button onClick={commit} style={{ marginTop: 12 }}>Commit</button>
        </>
      )}
    </div>
  )
}
