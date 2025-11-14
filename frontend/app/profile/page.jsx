// app/profile/page.jsx
"use client";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";

export default function ProfilePage() {
  const [allergens, setAllergens] = useState([]);
  const [myIds, setMyIds] = useState([]);
  const [msg, setMsg] = useState("");

  async function load() {
    setMsg("");
    try {
      const [all, mine] = await Promise.all([
        api("/api/allergens"),
        api("/api/allergens/me", { headers: { ...authHeader() } }),
      ]);
      setAllergens(all || []);
      setMyIds(mine?.allergyIds || []);
    } catch (e) {
      setMsg(`Load failed: ${e.message}. (Are you logged in?)`);
    }
  }

  useEffect(() => { load(); }, []);

  function toggle(id) {
    setMyIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  async function save() {
    setMsg("");
    try {
      await api("/api/allergens/me", {
        method: "PUT",
        headers: { ...authHeader() },
        body: { allergyIds: myIds },
      });
      setMsg("Saved your allergy preferences.");
    } catch (e) {
      setMsg(`Save failed: ${e.message}`);
    }
  }

  return (
    <section className="card" aria-labelledby="profile-h">
      <h2 id="profile-h" className="section-title">My Allergy Profile</h2>
      <p className="small">Select allergens to avoid. The “Safe for me” filter on the Menu page will use this.</p>

      <div role="group" aria-labelledby="profile-h" style={{display:"grid", gap:8, gridTemplateColumns:"repeat(auto-fill, minmax(180px, 1fr))"}}>
        {allergens.map(a => (
          <label key={a.id} className="chip">
            <input
              type="checkbox"
              checked={myIds.includes(a.id)}
              onChange={() => toggle(a.id)}
            />
            <span>{a.name}</span>
          </label>
        ))}
      </div>

      <div style={{marginTop:12, display:"flex", gap:8}}>
        <button className="btn" onClick={save}>Save</button>
        <button className="btn secondary" onClick={load}>Reload</button>
      </div>

      {msg && <div role="status" aria-live="polite" className="alert success" style={{marginTop:12}}>{msg}</div>}
    </section>
  );
}
