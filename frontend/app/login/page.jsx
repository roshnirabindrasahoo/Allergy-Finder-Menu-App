"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { setToken, clearToken } from "@/lib/auth";

export default function LoginPage() {
  const [form, setForm] = useState({ email: "", password: "" });
  const [msg, setMsg] = useState({ type: "", text: "" });

  async function submit(e) {
    e.preventDefault();
    setMsg({type:"", text:""});
    try {
      const data = await api("/api/auth/login", { method: "POST", body: form });
      setToken(data.token);
      setMsg({ type: "success", text: "Logged in. Token saved." });
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  }

  return (
    <section className="card" aria-labelledby="login-h">
      <h2 id="login-h" className="section-title">Login</h2>
      <form onSubmit={submit} noValidate>
        <label htmlFor="lemail">Email</label>
        <input id="lemail" className="input" type="email" autoComplete="email" required
               value={form.email} onChange={e=>setForm({...form, email:e.target.value})} />
        <label htmlFor="lpass">Password</label>
        <input id="lpass" className="input" type="password" autoComplete="current-password" required
               value={form.password} onChange={e=>setForm({...form, password:e.target.value})} />
        <div style={{display:"flex", gap:8}}>
          <button className="btn" type="submit">Login</button>
          <button className="btn secondary" type="button" onClick={()=>{ clearToken(); setMsg({type:"success", text:"Logged out. Token cleared."}); }}>
            Logout
          </button>
        </div>
      </form>
      {msg.text && (
        <div role="status" aria-live="polite" className={`alert ${msg.type === "error" ? "error" : "success"}`} style={{marginTop:12}}>
          {msg.text}
        </div>
      )}
    </section>
  );
}
