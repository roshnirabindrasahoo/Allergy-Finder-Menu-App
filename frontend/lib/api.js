export async function api(path, { method = 'GET', body, token, isFormData = false } = {}) {
    const url = (process.env.NEXT_PUBLIC_API_BASE || '') + path
    const headers = {}
    if (token) headers.Authorization = `Bearer ${token}`
    if (!isFormData) headers['Content-Type'] = 'application/json'
  
    const res = await fetch(url, {
      method,
      headers,
      body: isFormData ? body : body ? JSON.stringify(body) : undefined,
      cache: 'no-store'
    })
    if (!res.ok) {
      let j; try { j = await res.json() } catch { j = null }
      const msg = j?.detail || j?.error || res.statusText
      throw new Error(msg)
    }
    if (res.status === 204) return null
    return res.json()
  }
  