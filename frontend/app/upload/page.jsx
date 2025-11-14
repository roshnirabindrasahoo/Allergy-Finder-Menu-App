"use client";
import { useState } from "react";
import { api } from "@/lib/api";
import { authHeader } from "@/lib/auth";

export default function UploadPage() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [fileId, setFileId] = useState(null);
  const [msg, setMsg] = useState("");

  async function upload() {
    setMsg("");
    if (!file) return setMsg("Choose a CSV first.");

    const fd = new FormData();
    fd.append("file", file);

    try {
      const res = await api("/api/ingest/csv", {
        method: "POST",
        headers: { ...authHeader() }, // MUST be a restaurant token
        formData: fd,
      });
      setPreview(res.preview || []);
      setFileId(res.fileId);
      setMsg(`Uploaded. fileId=${res.fileId}`);
    } catch (e) {
      console.error("Upload failed:", e);
      setMsg(`Upload failed: ${e.message}. 
Hint: Are you logged in as a restaurant? Is CORS allowing http://localhost:5173?`);
    }
  }

  async function commit() {
    setMsg("");
    if (!fileId) return setMsg("Nothing to commit. Upload and preview first.");
    try {
      const res = await api(`/api/ingest/commit?fileId=${fileId}`, {
        method: "POST",
        headers: { ...authHeader() },
      });
      setMsg(`Commit complete. Created ${res.created} items.`);
    } catch (e) {
      console.error("Commit failed:", e);
      setMsg(`Commit failed: ${e.message}`);
    }
  }

  return (
    <section className="card" aria-labelledby="upload-h">
      <h2 id="upload-h" className="section-title">Upload Menu (CSV)</h2>

      <div style={{display:"grid", gridTemplateColumns:"1fr auto auto", gap:8, alignItems:"end"}}>
        <div>
          <label htmlFor="csv" className="small">CSV file</label>
          <input
            id="csv"
            className="file"
            type="file"
            accept=".csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
          />
        </div>
        <button className="btn" onClick={upload}>Preview</button>
        <button className="btn" onClick={commit} disabled={!fileId} aria-disabled={!fileId}>
          Commit
        </button>
      </div>

      {preview && (
        <>
          <h3 className="section-title" style={{marginTop:16}}>Preview</h3>
          <table className="table" role="table" aria-label="Parsed menu preview">
            <thead>
              <tr>
                <th>Item</th><th>Description</th><th>Price</th><th>Predicted Allergens</th>
              </tr>
            </thead>
            <tbody>
              {preview.map((r, i) => (
                <tr key={i}>
                  <td>{r.item_name}</td>
                  <td className="small">{r.description}</td>
                  <td>{r.price}</td>
                  <td>
                    {(r.predicted_allergens || []).map(a => (
                      <span key={a} className="badge">{a}</span>
                    ))}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )}

      {msg && (
        <div role="status" aria-live="polite" className="alert success" style={{marginTop:12}}>
          {msg}
        </div>
      )}

      <p className="small" style={{marginTop:12}}>
        Note: Only <strong>restaurant</strong>-role users can upload and commit.
      </p>
    </section>
  );
}
