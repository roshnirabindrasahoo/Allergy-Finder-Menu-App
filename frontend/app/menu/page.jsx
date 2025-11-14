// frontend/app/menu/page.jsx
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";

const PAGE_SIZE = 20;

export default function MenuPage() {
  const [items, setItems] = useState([]);
  const [safe, setSafe] = useState(false);
  const [q, setQ] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);

  async function load({ reset = false } = {}) {
    setLoading(true);
    const params = new URLSearchParams();
    if (safe) params.set("safeForUser", "true");
    if (q) params.set("q", q);
    params.set("limit", PAGE_SIZE.toString());
    params.set("offset", (reset ? 0 : offset).toString());

    const data = await api(`/api/menus?${params.toString()}`, { headers: { ...authHeader() }});
    setItems((prev) => (reset ? data : [...prev, ...data]));
    setOffset((prev) => (reset ? PAGE_SIZE : prev + PAGE_SIZE));
    setLoading(false);
  }

  useEffect(() => { load({ reset: true }); }, []); // first load

  return (
    <section className="card" aria-labelledby="menu-h">
      <h2 id="menu-h" className="section-title">Menu</h2>

      <div style={{display:"grid", gridTemplateColumns:"1fr auto auto", gap:8, alignItems:"center"}}>
        <div>
          <label htmlFor="q" className="small">Search</label>
          <input
            id="q"
            className="input"
            placeholder="e.g., tofu, pasta…"
            value={q}
            onChange={(e)=>setQ(e.target.value)}
            onKeyDown={(e)=>e.key==="Enter" && load({ reset: true })}
          />
        </div>
        <label className="small" style={{display:"flex", alignItems:"center", gap:8, marginTop:18}}>
          <input
            type="checkbox"
            checked={safe}
            onChange={(e)=>{ setSafe(e.target.checked); setOffset(0); load({ reset: true }); }}
          />
          Safe for me
        </label>
        <button className="btn" style={{marginTop:18}} onClick={()=>{ setOffset(0); load({ reset: true }); }}>
          Apply
        </button>
      </div>

      <table className="table" role="table" aria-label="Menu items">
        <thead>
          <tr><th>Item</th><th>Description</th><th>Price</th><th>Allergens</th></tr>
        </thead>
        <tbody>
          {items.map(mi => (
            <tr key={mi.id}>
              <td>{mi.item_name}</td>
              <td className="small">{mi.description}</td>
              <td>${mi.price?.toFixed?.(2) ?? mi.price}</td>
              <td>{mi.allergens?.map(a => <span key={a} className="badge">{a}</span>)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {items.length === 0 && !loading && (
        <p className="small" role="status" aria-live="polite">No items found.</p>
      )}

      <div style={{display:"flex", gap:8, marginTop:12}}>
        <button className="btn" onClick={()=>load()} disabled={loading}>Load more</button>
        {loading && <span className="small" aria-live="polite">Loading…</span>}
      </div>
    </section>
  );
}
