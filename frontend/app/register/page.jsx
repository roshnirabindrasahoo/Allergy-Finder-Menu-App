"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { setToken } from "@/lib/auth";

export default function RegisterPage() {
  const [form, setForm] = useState({ name: "", email: "", password: "", role: "customer" });
  const [msg, setMsg] = useState({ type: "", text: "" });

  async function submit(e) {
    e.preventDefault();
    setMsg({ type: "", text: "" });
    try {
      const data = await api("/api/auth/register", { method: "POST", body: form });
      setToken(data.token);
      setMsg({ type: "success", text: "Registered! Token saved. You can now access protected pages." });
    } catch (err) {
      setMsg({ type: "error", text: err.message });
    }
  }

  return (
    <section className="card" aria-labelledby="reg-h">
      <h2 id="reg-h" className="section-title">Register</h2>
      <form onSubmit={submit} noValidate>
        <label htmlFor="name">Name</label>
        <input id="name" className="input" autoComplete="name" required
               value={form.name} onChange={e=>setForm({...form, name:e.target.value})} />

        <label htmlFor="email">Email</label>
        <input id="email" className="input" type="email" autoComplete="email" required
               value={form.email} onChange={e=>setForm({...form, email:e.target.value})} />

        <label htmlFor="password">Password</label>
        <input id="password" className="input" type="password" autoComplete="new-password" required
               value={form.password} onChange={e=>setForm({...form, password:e.target.value})} />

        <label htmlFor="role">Role</label>
        <select id="role" className="select" value={form.role}
                onChange={e=>setForm({...form, role:e.target.value})}>
          <option value="customer">Customer</option>
          <option value="restaurant">Restaurant</option>
        </select>

        <div style={{display:"flex", gap:8}}>
          <button className="btn" type="submit">Create account</button>
          <a className="btn secondary" href="/login">Already have an account?</a>
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
