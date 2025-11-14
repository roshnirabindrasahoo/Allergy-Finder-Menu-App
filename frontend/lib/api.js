const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:4000";

/**
 * Minimal fetch wrapper that:
 *  - automatically sets JSON headers
 *  - supports multipart via formData
 *  - throws readable errors
 */
export async function api(path, { method = "GET", headers = {}, body, formData } = {}) {
  const url = `${BASE}${path}`;
  let opts = { method, headers: { ...headers } };

  if (formData) {
    // Let the browser set multipart boundary automatically
    opts.body = formData;
  } else if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }

  const res = await fetch(url, opts);
  if (!res.ok) {
    let msg;
    try { msg = await res.json(); } catch { msg = await res.text(); }
    const detail = typeof msg === "string" ? msg : msg?.detail || `HTTP ${res.status}`;
    throw new Error(detail);
  }
  const ct = res.headers.get("content-type") || "";
  return ct.includes("application/json") ? res.json() : res.text();
}
