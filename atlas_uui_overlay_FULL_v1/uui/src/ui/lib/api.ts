
export type UUISettings = {
  projectKey?: string;
  openaiBaseUrl?: string;
  openaiApiKey?: string;
  openaiModel?: string;
  temperature?: number;
  v4BasePath?: string;
  v41BasePath?: string;
  logsPath?: string;
};

export async function getSettings(): Promise<UUISettings> {
  const r = await fetch("/api/uui/settings/get");
  if (!r.ok) throw new Error(`settings/get failed: ${r.status}`);
  return await r.json();
}

export async function setSettings(s: UUISettings): Promise<void> {
  const r = await fetch("/api/uui/settings/set", {
    method: "POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify(s)
  });
  if (!r.ok) throw new Error(`settings/set failed: ${r.status}`);
}

export async function health(): Promise<any> {
  const r = await fetch("/api/uui/health");
  return await r.json();
}

export async function v4Plan(payload: any): Promise<any> {
  const r = await fetch("/api/uui/v4/plan", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
  return await r.json();
}
export async function v4Run(payload: any): Promise<any> {
  const r = await fetch("/api/uui/v4/run", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
  return await r.json();
}
export async function v41Plan(payload: any): Promise<any> {
  const r = await fetch("/api/uui/v4_1/plan", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
  return await r.json();
}
export async function v41Run(payload: any): Promise<any> {
  const r = await fetch("/api/uui/v4_1/run", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(payload)});
  return await r.json();
}

export async function webFetch(url: string): Promise<any> {
  const r = await fetch("/api/uui/web/fetch", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({url})});
  return await r.json();
}

export async function tailLogs(lines=200): Promise<any> {
  const r = await fetch("/api/uui/logs/tail", {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify({lines})});
  return await r.json();
}

export async function streamChat(messages: {role:string; content:string}[], onChunk:(t:string)=>void): Promise<void> {
  const r = await fetch("/api/uui/chat/stream", {
    method:"POST",
    headers: {"Content-Type":"application/json"},
    body: JSON.stringify({messages})
  });
  if (!r.ok || !r.body) throw new Error(`chat stream failed: ${r.status}`);
  const reader = r.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buf = "";
  while (true){
    const {value, done} = await reader.read();
    if (done) break;
    buf += decoder.decode(value, {stream:true});
    const parts = buf.split("\n\n");
    buf = parts.pop() ?? "";
    for (const p of parts){
      const lines = p.split("\n").filter(Boolean);
      for (const ln of lines){
        if (ln.startsWith("data:")){
          onChunk(ln.slice(5).trimStart());
        }
      }
    }
  }
}
