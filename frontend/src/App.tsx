import React, { useMemo, useState } from "react";

type Tab = "Chat" | "Settings" | "AdminFactory";

async function apiGet(path: string) {
  const r = await fetch(path);
  return r.json();
}
async function apiPost(path: string, body: any, headers?: Record<string,string>) {
  const r = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(headers||{}) },
    body: JSON.stringify(body)
  });
  return r.json();
}

export default function App() {
  const [tab, setTab] = useState<Tab>("Chat");

  // Settings
  const [baseUrl, setBaseUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");

  // Chat
  const [prompt, setPrompt] = useState("Hello Atlas v6. Respond briefly.");
  const [chatOut, setChatOut] = useState<any>(null);
  const [busy, setBusy] = useState(false);

  // Admin factory
  const [adminToken, setAdminToken] = useState("");
  const [specJson, setSpecJson] = useState(JSON.stringify({
    plugin_slug: "construction",
    title: "Construction Pack",
    notes: "Generated plugin example"
  }, null, 2));
  const [factoryOut, setFactoryOut] = useState<any>(null);

  const tabs: Tab[] = useMemo(() => ["Chat","Settings","AdminFactory"], []);

  async function saveSetting(k: string, v: string) {
    return apiPost("/api/settings", { key: k, value: v });
  }

  async function loadSettings() {
    const res = await apiGet("/api/settings");
    if (res?.ok) {
      const map: Record<string,string> = {};
      for (const it of res.items || []) map[it.key] = it.value;
      setBaseUrl(map["llm.base_url"] || "");
      setApiKey(map["llm.api_key"] || "");
      setModel(map["llm.model"] || "");
    }
  }

  async function doChat() {
    setBusy(true);
    try {
      const res = await apiPost("/api/chat", {
        messages: [{ role: "user", content: prompt }],
        temperature: 0.2
      });
      setChatOut(res);
    } finally {
      setBusy(false);
    }
  }

  async function doGeneratePlugin() {
    let spec: any;
    try { spec = JSON.parse(specJson); }
    catch (e:any) { setFactoryOut({ ok:false, error:"Invalid JSON", details: String(e) }); return; }

    const res = await apiPost("/api/admin/factory/generate-plugin", { spec }, { "X-Atlas-Admin-Token": adminToken });
    setFactoryOut(res);
  }

  async function doListPlugins() {
    const res = await apiGet("/api/admin/factory/list");
    setFactoryOut(res);
  }

  return (
    <div className="window">
      <div className="titlebar">
        <div className="dot" /><div className="dot" /><div className="dot" />
        <div className="title">Atlas v6 Unified (Runtime + Internal Factory)</div>
        <div style={{marginLeft:"auto"}} className="small">/healthz</div>
      </div>

      <div className="content">
        <div className="card">
          <div className="tabs">
            {tabs.map(t => (
              <div key={t} className={"tab " + (tab===t ? "active":"")} onClick={() => setTab(t)}>
                {t}
              </div>
            ))}
          </div>

          {tab === "Settings" && (
            <>
              <div className="label">External LLM Settings (saved to SQLite)</div>
              <div className="label">Base URL</div>
              <input value={baseUrl} onChange={e=>setBaseUrl(e.target.value)} placeholder="https://api.openai.com" />
              <div className="label" style={{marginTop:8}}>API Key</div>
              <input value={apiKey} onChange={e=>setApiKey(e.target.value)} placeholder="sk-..." />
              <div className="label" style={{marginTop:8}}>Model</div>
              <input value={model} onChange={e=>setModel(e.target.value)} placeholder="gpt-4o-mini" />
              <div className="row" style={{marginTop:10}}>
                <button className="btn" onClick={() => saveSetting("llm.base_url", baseUrl)}>Save Base</button>
                <button className="btn" onClick={() => saveSetting("llm.api_key", apiKey)}>Save Key</button>
                <button className="btn" onClick={() => saveSetting("llm.model", model)}>Save Model</button>
              </div>
              <div className="row" style={{marginTop:10}}>
                <button className="btn" onClick={loadSettings}>Reload</button>
              </div>

              <div className="label" style={{marginTop:12}}>UUI Integrations (placeholders)</div>
              <div className="small">Fields are reserved in settings DB: tts.*, ocr.*, hooks.*, whatsapp.*, email.*, github.*, render.*</div>
            </>
          )}

          {tab === "Chat" && (
            <>
              <div className="label">Chat</div>
              <textarea value={prompt} onChange={e=>setPrompt(e.target.value)} />
              <div className="row" style={{marginTop:10}}>
                <button className="btn" onClick={doChat} disabled={busy}>Send</button>
                <button className="btn" onClick={()=>setChatOut(null)} disabled={busy}>Clear</button>
              </div>
              <div className="small" style={{marginTop:10}}>
                If env vars are set, they override DB settings: EXTERNAL_LLM_BASE_URL / EXTERNAL_LLM_API_KEY / EXTERNAL_LLM_MODEL
              </div>
            </>
          )}

          {tab === "AdminFactory" && (
            <>
              <div className="label">Admin Factory (requires ATLAS_ADMIN_TOKEN)</div>
              <div className="label">Admin Token</div>
              <input value={adminToken} onChange={e=>setAdminToken(e.target.value)} placeholder="ATLAS_ADMIN_TOKEN" />
              <div className="label" style={{marginTop:8}}>Plugin Spec (JSON)</div>
              <textarea value={specJson} onChange={e=>setSpecJson(e.target.value)} />
              <div className="row" style={{marginTop:10}}>
                <button className="btn" onClick={doGeneratePlugin}>Generate Plugin</button>
                <button className="btn" onClick={doListPlugins}>List Generated</button>
              </div>
              <div className="small" style={{marginTop:8}}>
                Generated plugins are loaded automatically on restart (Render redeploy). Each plugin exposes /api/plugins/&lt;slug&gt;/ping
              </div>
            </>
          )}
        </div>

        <div className="card">
          <div className="label">Output</div>
          {tab==="Chat" && <pre>{chatOut ? JSON.stringify(chatOut, null, 2) : "No chat output yet."}</pre>}
          {tab==="Settings" && <pre>{"Settings saved in backend SQLite (ATLAS_DB_PATH)."} </pre>}
          {tab==="AdminFactory" && <pre>{factoryOut ? JSON.stringify(factoryOut, null, 2) : "No factory output yet."}</pre>}
        </div>
      </div>
    </div>
  );
}
