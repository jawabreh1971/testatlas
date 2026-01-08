
import React, { useEffect, useState } from "react";
import { health, getSettings, setSettings, streamChat, v4Plan, v4Run, v41Plan, v41Run, webFetch, tailLogs, type UUISettings } from "./lib/api";
import { openPopout } from "./lib/popout";

type Msg = { role: "system"|"user"|"assistant"; content: string };

function Panel({title, tag, children, onPop}:{title:string; tag?:string; children:React.ReactNode; onPop?:()=>void}){
  return (
    <div className="panel">
      <div className="panelHeader">
        <div className="panelTitle">
          <span className="dot" />
          <span>{title}</span>
          {tag ? <span className="tag">{tag}</span> : null}
        </div>
        <div className="row">
          {onPop ? <button className="btn btnCopper" onClick={onPop}>Pop-out</button> : null}
        </div>
      </div>
      <div className="panelBody">{children}</div>
    </div>
  );
}

export default function App(){
  const [h, setH] = useState<any>(null);
  const [settings, setS] = useState<UUISettings>({openaiBaseUrl:"https://api.openai.com", openaiModel:"gpt-4o-mini", temperature:0.2, v4BasePath:"/api/addons/v4", v41BasePath:"/api/addons/v4_1"});
  const [status, setStatus] = useState<string>("");
  const [active, setActive] = useState<string>("Workbench");
  const [msgs, setMsgs] = useState<Msg[]>([{role:"system", content:"You are Atlas UUI assistant."}]);
  const [chatInput, setChatInput] = useState("");
  const [chatStreaming, setChatStreaming] = useState(false);
  const [goal, setGoal] = useState("");
  const [context, setContext] = useState("{}");
  const [constraints, setConstraints] = useState("{}");
  const [engine, setEngine] = useState<"v4"|"v4_1">("v4");
  const [runnerOut, setRunnerOut] = useState<any>(null);
  const [webUrl, setWebUrl] = useState("");
  const [webOut, setWebOut] = useState<any>(null);
  const [logsOut, setLogsOut] = useState<any>(null);

  useEffect(()=>{
    (async()=>{
      try{ setH(await health()); }catch(e:any){ setH({ok:false, error:String(e?.message||e)}); }
      try{ setS(prev => ({...prev, ...(await getSettings())})); }catch{}
    })();
  },[]);

  async function saveSettings(){
    setStatus("Saving settings...");
    try{ await setSettings(settings); setStatus("Settings saved."); }
    catch(e:any){ setStatus("Save failed: " + String(e?.message||e)); }
  }

  async function sendChat(){
    const input = chatInput.trim();
    if (!input || chatStreaming) return;
    const newMsgs: Msg[] = [...msgs, {role:"user", content: input}, {role:"assistant", content:""}];
    setMsgs(newMsgs);
    setChatInput("");
    setChatStreaming(true);
    try{
      let acc = "";
      await streamChat(newMsgs.filter(m=>m.role!=="assistant" || m.content!==""), (chunk)=>{
        acc += chunk;
        setMsgs(ms => {
          const copy = [...ms];
          const last = copy[copy.length-1];
          if (last?.role === "assistant") last.content = acc;
          return copy;
        });
      });
    }catch(e:any){
      setMsgs(ms => {
        const copy = [...ms];
        const last = copy[copy.length-1];
        if (last?.role === "assistant") last.content = "ERROR: " + String(e?.message||e);
        return copy;
      });
    } finally {
      setChatStreaming(false);
    }
  }

  function safeJson(s:string){
    try{ return JSON.parse(s || "{}"); }catch{ return {"_parse_error": true, "_raw": s}; }
  }

  async function runPlan(){
    setRunnerOut(null);
    const payload = {goal, context: safeJson(context), constraints: safeJson(constraints)};
    const r = engine === "v4" ? await v4Plan(payload) : await v41Plan(payload);
    setRunnerOut(r);
  }
  async function runExec(){
    setRunnerOut(null);
    const payload = {goal, context: safeJson(context), constraints: safeJson(constraints)};
    const r = engine === "v4" ? await v4Run(payload) : await v41Run(payload);
    setRunnerOut(r);
  }

  async function doWebFetch(){ setWebOut(await webFetch(webUrl)); }
  async function doLogs(){ setLogsOut(await tailLogs(200)); }

  function popPanel(title:string, elementId:string){
    const el = document.getElementById(elementId);
    if (!el) return;
    openPopout(title, `<div style="background:#0b1220;color:#e7eefc;font-family:Segoe UI;padding:12px;">${el.innerHTML}</div>`);
  }

  return (
    <>
      <div className="topbar">
        <div className="brand">
          <div className="dot"></div>
          <div>
            <div style={{fontWeight:700}}>Atlas UUI</div>
            <div className="small">Windows-style • Blue/Copper • Dockable Panels</div>
          </div>
          <span className="badge">Render: testatlas.onrender.com</span>
        </div>
        <div className="row">
          <span className="badge">UUI Health: {h?.ok ? "OK" : "N/A"}</span>
          <span className="badge">Engine: {engine}</span>
          <span className="badge">{status || "Ready"}</span>
        </div>
      </div>

      <div className="layout">
        <div className="sidebar">
          {["Workbench","Runner","Hooks & Keys","Web","Logs","Camera","Mic/STT"].map(x => (
            <div key={x} className={"navItem " + (active===x ? "active": "")} onClick={()=>setActive(x)}>{x}</div>
          ))}
          <div className="hr" />
          <div className="small">Panels support <b>Pop-out</b>. Docking is layout-based in this v1.</div>
        </div>

        <div className="main">
          <div className="grid">

            {(active==="Workbench" || active==="Runner") && (
              <Panel title="v4 / v4.1 Runner" tag="Plan • Run • Artifact" onPop={()=>popPanel("Runner","panel-runner")}>
                <div id="panel-runner">
                  <div className="row">
                    <label className="small">Engine</label>
                    <select className="select" style={{maxWidth:200}} value={engine} onChange={e=>setEngine(e.target.value as any)}>
                      <option value="v4">v4</option>
                      <option value="v4_1">v4.1</option>
                    </select>
                  </div>
                  <div className="field">
                    <div className="small">Goal</div>
                    <textarea className="input" style={{minHeight:70}} value={goal} onChange={e=>setGoal(e.target.value)} placeholder="Describe what you want Atlas to produce..."/>
                  </div>
                  <div className="split">
                    <div className="field">
                      <div className="small">Context (JSON)</div>
                      <textarea className="textarea" value={context} onChange={e=>setContext(e.target.value)} />
                    </div>
                    <div className="field">
                      <div className="small">Constraints (JSON)</div>
                      <textarea className="textarea" value={constraints} onChange={e=>setConstraints(e.target.value)} />
                    </div>
                  </div>
                  <div className="row">
                    <button className="btn btnPrimary" onClick={runPlan}>Plan</button>
                    <button className="btn btnCopper" onClick={runExec}>Run</button>
                  </div>
                  <div className="hr"/>
                  <div className="small">Output</div>
                  <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{runnerOut ? JSON.stringify(runnerOut, null, 2) : "—"}</pre>
                </div>
              </Panel>
            )}

            {(active==="Workbench") && (
              <Panel title="Chat (Streaming)" tag="/api/uui/chat/stream" onPop={()=>popPanel("Chat","panel-chat")}>
                <div id="panel-chat" className="chatBox">
                  <div className="chatMsgs">
                    {msgs.map((m, i)=>(
                      <div key={i} className="msg">
                        <div className="msgRole">{m.role}</div>
                        <div className="msgText">{m.content}</div>
                      </div>
                    ))}
                  </div>
                  <div className="row">
                    <input className="input" value={chatInput} onChange={e=>setChatInput(e.target.value)} placeholder="Type message..." />
                    <button className="btn btnPrimary" disabled={chatStreaming} onClick={sendChat}>Send</button>
                  </div>
                  <div className="small">Set API key in "Hooks & Keys" first.</div>
                </div>
              </Panel>
            )}

            {(active==="Hooks & Keys" || active==="Workbench") && (
              <Panel title="Hooks & Keys" tag="server JSON store" onPop={()=>popPanel("Hooks","panel-hooks")}>
                <div id="panel-hooks">
                  <div className="kv">
                    <div className="small">Project Key</div>
                    <input className="input" value={settings.projectKey || ""} onChange={e=>setS({...settings, projectKey:e.target.value})} />
                    <div className="small">OpenAI Base URL</div>
                    <input className="input" value={settings.openaiBaseUrl || ""} onChange={e=>setS({...settings, openaiBaseUrl:e.target.value})} />
                    <div className="small">API Key</div>
                    <input className="input" value={settings.openaiApiKey || ""} onChange={e=>setS({...settings, openaiApiKey:e.target.value})} placeholder="sk-..." />
                    <div className="small">Model</div>
                    <input className="input" value={settings.openaiModel || ""} onChange={e=>setS({...settings, openaiModel:e.target.value})} />
                    <div className="small">Temperature</div>
                    <input className="input" value={String(settings.temperature ?? 0.2)} onChange={e=>setS({...settings, temperature:Number(e.target.value)})} />
                    <div className="small">v4 Base Path</div>
                    <input className="input" value={settings.v4BasePath || ""} onChange={e=>setS({...settings, v4BasePath:e.target.value})} />
                    <div className="small">v4.1 Base Path</div>
                    <input className="input" value={settings.v41BasePath || ""} onChange={e=>setS({...settings, v41BasePath:e.target.value})} />
                    <div className="small">Logs Path</div>
                    <input className="input" value={settings.logsPath || ""} onChange={e=>setS({...settings, logsPath:e.target.value})} placeholder="backend/logs/app.log" />
                  </div>
                  <div className="row">
                    <button className="btn btnPrimary" onClick={saveSettings}>Save</button>
                  </div>
                  <div className="small">Saved on server as `backend/data/uui_settings.json` (default).</div>
                </div>
              </Panel>
            )}

            {(active==="Web" || active==="Workbench") && (
              <Panel title="Web Bridge" tag="SSRF-guarded">
                <div>
                  <div className="row">
                    <input className="input" value={webUrl} onChange={e=>setWebUrl(e.target.value)} placeholder="https://example.com/article" />
                    <button className="btn btnPrimary" onClick={doWebFetch}>Fetch</button>
                  </div>
                  <div className="hr"/>
                  <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{webOut ? JSON.stringify(webOut, null, 2) : "—"}</pre>
                </div>
              </Panel>
            )}

            {(active==="Logs" || active==="Workbench") && (
              <Panel title="Logs / Console" tag="tail">
                <div>
                  <div className="row">
                    <button className="btn btnPrimary" onClick={doLogs}>Refresh</button>
                  </div>
                  <div className="hr"/>
                  <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{logsOut ? JSON.stringify(logsOut, null, 2) : "—"}</pre>
                </div>
              </Panel>
            )}

            {(active==="Camera") && (
              <Panel title="Camera" tag="capture + vision">
                <CameraPanel />
              </Panel>
            )}

            {(active==="Mic/STT") && (
              <Panel title="Mic / STT" tag="record + upload">
                <MicPanel />
              </Panel>
            )}

          </div>
        </div>
      </div>
    </>
  );
}

function CameraPanel(){
  const [img, setImg] = useState<string>("");
  const [out, setOut] = useState<any>(null);

  function capture(){
    const el = document.getElementById("camFile") as HTMLInputElement | null;
    el?.click();
  }

  async function onFile(e: React.ChangeEvent<HTMLInputElement>){
    const f = e.target.files?.[0];
    if (!f) return;
    const b64 = await fileToBase64(f);
    setImg(b64);
  }

  async function sendVision(){
    setOut(null);
    const r = await fetch("/api/uui/vision", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({image_base64: img})});
    setOut(await r.json());
  }

  return (
    <div>
      <input id="camFile" type="file" accept="image/*" capture="environment" style={{display:"none"}} onChange={onFile} />
      <div className="row">
        <button className="btn btnPrimary" onClick={capture}>Capture / Select Image</button>
        <button className="btn btnCopper" disabled={!img} onClick={sendVision}>Send to Vision</button>
      </div>
      <div className="hr"/>
      {img ? <img src={img} style={{maxWidth:"100%", borderRadius:12, border:"1px solid rgba(255,255,255,.08)"}}/> : <div className="small">No image yet.</div>}
      <div className="hr"/>
      <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{out ? JSON.stringify(out,null,2) : "—"}</pre>
    </div>
  );
}

function MicPanel(){
  const [rec, setRec] = useState<MediaRecorder|null>(null);
  const [chunks, setChunks] = useState<BlobPart[]>([]);
  const [out, setOut] = useState<any>(null);

  async function start(){
    setOut(null);
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    const mr = new MediaRecorder(stream);
    mr.ondataavailable = (e)=> setChunks(prev => [...prev, e.data]);
    mr.onstop = ()=> stream.getTracks().forEach(t=>t.stop());
    mr.start();
    setChunks([]);
    setRec(mr);
  }

  async function stop(){ rec?.stop(); setRec(null); }

  async function send(){
    setOut(null);
    const blob = new Blob(chunks, {type:"audio/webm"});
    const fd = new FormData();
    fd.append("file", blob, "audio.webm");
    const r = await fetch("/api/uui/audio/stt", {method:"POST", body: fd});
    setOut(await r.json());
  }

  return (
    <div>
      <div className="row">
        {!rec ? <button className="btn btnPrimary" onClick={start}>Start Recording</button> : <button className="btn btnCopper" onClick={stop}>Stop</button>}
        <button className="btn" disabled={!chunks.length} onClick={send}>Send to STT</button>
      </div>
      <div className="hr"/>
      <div className="small">Recorder: {rec ? "ON" : "OFF"} • Chunks: {chunks.length}</div>
      <div className="hr"/>
      <pre className="mono" style={{whiteSpace:"pre-wrap"}}>{out ? JSON.stringify(out,null,2) : "—"}</pre>
    </div>
  );
}

async function fileToBase64(f: File): Promise<string>{
  return new Promise((res, rej)=>{
    const r = new FileReader();
    r.onload = ()=> res(String(r.result));
    r.onerror = ()=> rej(r.error);
    r.readAsDataURL(f);
  });
}
