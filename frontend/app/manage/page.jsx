"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";

export default function ManagePage() {
  const [items, setItems] = useState([]);
  const [msg, setMsg] = useState("");

  async function load() {
    setMsg("");
    try {
      const data = await api("/api/menus/mine", { headers: { ...authHeader() } });
      setItems(data);
    } catch (e) {
      setMsg(`Load failed: ${e.message}. (Are you logged in as a restaurant?)`);
    }
  }

  useEffect(() => { load(); }, []);

  async function del(id) {
    setMsg("");
    const ok = confirm("Delete this item? This cannot be undone.");
    if (!ok) return;
    try {
      await api(`/api/menus/${id}`, { method: "DELETE", headers: { ...authHeader() } });
      setMsg("Deleted.");
      // remove locally without full reload for snappy UX
      setItems(prev => prev.filter(x => x.id !== id));
    } catch (e) {
      setMsg(`Delete failed: ${e.message}`);
    }
  }

  return (
    <section className="card" aria-labelledby="manage-h">
      <h2 id="manage-h" className="section-title">Manage My Menu</h2>
      <p className="small">Only your restaurant’s items are shown here.</p>

      <table className="table" role="table" aria-label="My menu items">
        <thead>
          <tr>
            <th>Item</th><th>Description</th><th>Price</th><th>Allergens</th><th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {items.map(mi => (
            <tr key={mi.id}>
              <td>{mi.item_name}</td>
              <td className="small">{mi.description}</td>
              <td>${mi.price?.toFixed?.(2) ?? mi.price}</td>
              <td>{mi.allergens?.map(a => <span key={a} className="badge">{a}</span>)}</td>
              <td>
                <button className="btn danger" onClick={() => del(mi.id)}>Delete</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      {items.length === 0 && <p className="small" aria-live="polite">No items yet. Upload via the Upload page.</p>}
      {msg && <div role="status" aria-live="polite" className="alert success" style={{marginTop:12}}>{msg}</div>}
    </section>
  );
}
