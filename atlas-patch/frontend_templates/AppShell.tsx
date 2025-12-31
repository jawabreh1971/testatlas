import * as React from "react";
import {
  FluentProvider, webDarkTheme, webLightTheme, tokens,
  Button, Input, Text, Subtitle2, Caption1, Divider, Textarea
} from "@fluentui/react-components";
import {
  Home24Regular, PlugDisconnected24Regular, Sparkle24Regular, Library24Regular,
  Camera24Regular, Chat24Regular, Mic24Regular, Globe24Regular, Video24Regular, Wrench24Regular, Link24Regular
} from "@fluentui/react-icons";

type NavKey = "home" | "chat" | "mic" | "camera" | "web" | "video" | "plugins" | "engines" | "foundry" | "builder" | "hooks";

async function apiGet(path: string, headers?: Record<string,string>) {
  const r = await fetch(path, { headers: headers || {} });
  const ct = r.headers.get("content-type") || "";
  if (ct.includes("application/json")) return await r.json();
  return { ok: false, status: r.status, text: await r.text() };
}
async function apiPost(path: string, body: any, headers?: Record<string,string>) {
  const r = await fetch(path, { method: "POST", headers: { "Content-Type": "application/json", ...(headers || {}) }, body: JSON.stringify(body) });
  const ct = r.headers.get("content-type") || "";
  if (ct.includes("application/json")) return await r.json();
  return { ok: false, status: r.status, text: await r.text() };
}

export default function AppShell() {
  const [dark, setDark] = React.useState(true);
  const [nav, setNav] = React.useState<NavKey>("home");
  const [health, setHealth] = React.useState<any>(null);

  React.useEffect(() => { apiGet("/api/factory/health").then(setHealth).catch(() => setHealth({ ok:false })); }, []);
  const theme = dark ? webDarkTheme : webLightTheme;

  return (
    <FluentProvider theme={theme}>
      <div style={styles.root}>
        <div style={styles.titlebar}>
          <div style={styles.brand}>
            <div style={styles.dot} />
            <Text weight="semibold">Atlas Unified</Text>
            <Caption1 style={{ opacity: 0.75, marginLeft: 10 }}>Factory v5</Caption1>
          </div>
          <div style={styles.titlebarRight}>
            <Button appearance="subtle" onClick={() => setDark(!dark)}>{dark ? "Light" : "Dark"}</Button>
          </div>
        </div>

        <div style={styles.body}>
          <aside style={styles.nav}>
            <NavItem icon={<Home24Regular />} label="Home" active={nav==="home"} onClick={()=>setNav("home")} />
            <NavItem icon={<Chat24Regular />} label="Chat" active={nav==="chat"} onClick={()=>setNav("chat")} />
            <NavItem icon={<Mic24Regular />} label="Mic" active={nav==="mic"} onClick={()=>setNav("mic")} />
            <NavItem icon={<Camera24Regular />} label="Camera" active={nav==="camera"} onClick={()=>setNav("camera")} />
            <Divider />
            <NavItem icon={<Globe24Regular />} label="Web Hub" active={nav==="web"} onClick={()=>setNav("web")} />
            <NavItem icon={<Video24Regular />} label="Video API" active={nav==="video"} onClick={()=>setNav("video")} />
            <Divider />
            <NavItem icon={<PlugDisconnected24Regular />} label="Plugins" active={nav==="plugins"} onClick={()=>setNav("plugins")} />
            <NavItem icon={<Sparkle24Regular />} label="Engines" active={nav==="engines"} onClick={()=>setNav("engines")} />
            <NavItem icon={<Library24Regular />} label="Foundry" active={nav==="foundry"} onClick={()=>setNav("foundry")} />
            <NavItem icon={<Wrench24Regular />} label="Builder" active={nav==="builder"} onClick={()=>setNav("builder")} />
            <NavItem icon={<Link24Regular />} label="Hooks" active={nav==="hooks"} onClick={()=>setNav("hooks")} />
          </aside>

          <main style={styles.main}>
            <div style={styles.headerRow}>
              <Subtitle2>{titleOf(nav)}</Subtitle2>
              <div style={{ display:"flex", gap:8 }}>
                <Button appearance="primary" onClick={()=>location.reload()}>Refresh</Button>
              </div>
            </div>

            {nav==="home" && <Panel title="System Health" subtitle="Backend overlay status."><pre style={styles.pre}>{JSON.stringify(health,null,2)}</pre></Panel>}
            {nav==="chat" && <ChatPage apiGet={apiGet} apiPost={apiPost} />}
            {nav==="mic" && <MicPage apiPost={apiPost} />}
            {nav==="camera" && <CameraPage />}
            {nav==="web" && <WebHubPage apiGet={apiGet} apiPost={apiPost} />}
            {nav==="video" && <VideoPage apiPost={apiPost} />}
            {nav==="plugins" && <JsonPanel title="Plugins" subtitle="Registry." loader={()=>apiGet("/api/plugins")} />}
            {nav==="engines" && <JsonPanel title="Engines Artifacts" subtitle="Artifacts list." loader={()=>apiGet("/api/engines/artifacts")} />}
            {nav==="foundry" && <FoundryPage apiGet={apiGet} apiPost={apiPost} />}
            {nav==="builder" && <BuilderPage apiPost={apiPost} />}
            {nav==="hooks" && <HooksPage apiGet={apiGet} apiPost={apiPost} />}
          </main>
        </div>
      </div>
    </FluentProvider>
  );
}

function Panel(props: { title: string; subtitle?: string; children: React.ReactNode }) {
  return (
    <div style={styles.panel}>
      <Subtitle2>{props.title}</Subtitle2>
      {props.subtitle && <Caption1 style={{ opacity: 0.8 }}>{props.subtitle}</Caption1>}
      <div style={{ marginTop: 10 }}>{props.children}</div>
    </div>
  );
}

function JsonPanel({ title, subtitle, loader }: any) {
  const [data, setData] = React.useState<any>(null);
  React.useEffect(()=>{ loader().then(setData); }, []);
  return <Panel title={title} subtitle={subtitle}><pre style={styles.pre}>{JSON.stringify(data,null,2)}</pre></Panel>;
}

function ChatPage({ apiGet, apiPost }: any) {
  const [role, setRole] = React.useState<"user"|"owner">("user");
  const [text, setText] = React.useState("");
  const [hist, setHist] = React.useState<any>(null);
  const load = async () => setHist(await apiGet("/api/chat/history?limit=80"));
  React.useEffect(()=>{ load(); }, []);
  async function send() {
    if (!text.trim()) return;
    await apiPost("/api/chat", { messages: [{ role, content: text }] });
    setText("");
    await load();
  }
  return (
    <Panel title="Chat Console" subtitle="Stored chat. Optional LLM if EXTAPI_KEY configured on server.">
      <div style={{ display:"flex", gap:10, alignItems:"center", flexWrap:"wrap" }}>
        <Button appearance={role==="user"?"primary":"secondary"} onClick={()=>setRole("user")}>User</Button>
        <Button appearance={role==="owner"?"primary":"secondary"} onClick={()=>setRole("owner")}>Owner</Button>
        <Button onClick={load}>Reload</Button>
      </div>
      <div style={{ marginTop:10, display:"grid", gap:10 }}>
        <Textarea value={text} onChange={(_,d)=>setText((d as any).value)} placeholder="Type message..." />
        <Button appearance="primary" onClick={send}>Send</Button>
      </div>
      <Divider style={{ margin:"12px 0" }} />
      <pre style={styles.pre}>{JSON.stringify(hist, null, 2)}</pre>
    </Panel>
  );
}

function MicPage({ apiPost }: any) {
  const [supported, setSupported] = React.useState(false);
  const [listening, setListening] = React.useState(false);
  const [text, setText] = React.useState("");
  const recRef = React.useRef<any>(null);

  React.useEffect(()=>{
    const SR: any = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    setSupported(!!SR);
    if (SR) {
      const rec = new SR();
      rec.lang = "ar-SA";
      rec.continuous = true;
      rec.interimResults = true;
      rec.onresult = (e: any) => {
        let out = "";
        for (let i=0;i<e.results.length;i++){
          out += e.results[i][0].transcript + " ";
        }
        setText(out.trim());
      };
      rec.onerror = () => setListening(false);
      rec.onend = () => setListening(false);
      recRef.current = rec;
    }
  }, []);

  function start() {
    if (!recRef.current) return;
    setListening(true);
    recRef.current.start();
  }
  function stop() {
    if (!recRef.current) return;
    recRef.current.stop();
    setListening(false);
  }
  async function sendToSttStub() {
    // If you record audio file, you can upload via /api/media/stt; here we just store recognized text in chat.
    await apiPost("/api/chat", { messages: [{ role:"user", content: text || "(empty mic)" }] });
    alert("Sent to chat (stored).");
  }

  return (
    <Panel title="Mic" subtitle="Browser Speech Recognition (if supported). For raw audio upload: /api/media/stt (stub).">
      <Caption1 style={{ opacity:0.8 }}>SpeechRecognition supported: {String(supported)}</Caption1>
      <div style={{ display:"flex", gap:10, marginTop:10, flexWrap:"wrap" }}>
        {!listening ? <Button appearance="primary" onClick={start} disabled={!supported}>Start</Button> : <Button onClick={stop}>Stop</Button>}
        <Button onClick={sendToSttStub} disabled={!text.trim()}>Send Text to Chat</Button>
      </div>
      <Textarea value={text} onChange={(_,d)=>setText((d as any).value)} placeholder="Transcript..." style={{ marginTop: 10 }} />
    </Panel>
  );
}

function CameraPage() {
  const videoRef = React.useRef<HTMLVideoElement | null>(null);
  const [on, setOn] = React.useState(false);
  const [err, setErr] = React.useState("");
  async function start() {
    setErr("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
      if (videoRef.current) videoRef.current.srcObject = stream;
      setOn(true);
    } catch (e: any) { setErr(String(e?.message || e)); }
  }
  function stop() {
    const v = videoRef.current;
    const s = (v?.srcObject as MediaStream | null);
    s?.getTracks().forEach(t=>t.stop());
    if (v) v.srcObject = null;
    setOn(false);
  }
  return (
    <Panel title="Camera" subtitle="WebRTC preview.">
      <div style={{ display:"flex", gap:10 }}>
        {!on ? <Button appearance="primary" onClick={start}>Start</Button> : <Button onClick={stop}>Stop</Button>}
      </div>
      {err && <Caption1 style={{ color: tokens.colorPaletteRedForeground1, marginTop:8 }}>{err}</Caption1>}
      <div style={{ marginTop:12 }}>
        <video ref={videoRef} autoPlay playsInline style={{ width:"100%", maxWidth: 760, borderRadius: 12, border: `1px solid ${tokens.colorNeutralStroke2}` }} />
      </div>
    </Panel>
  );
}

function WebHubPage({ apiGet, apiPost }: any) {
  const [url, setUrl] = React.useState("https://example.com");
  const [fetchRes, setFetchRes] = React.useState<any>(null);
  const [wiki, setWiki] = React.useState("Artificial_intelligence");
  const [wikiRes, setWikiRes] = React.useState<any>(null);
  const [arxiv, setArxiv] = React.useState("retrieval augmented generation");
  const [arxivRes, setArxivRes] = React.useState<any>(null);
  const [cr, setCr] = React.useState("machine learning");
  const [crRes, setCrRes] = React.useState<any>(null);

  return (
    <Panel title="Web Hub" subtitle="Specialized providers: URL fetch, Wikipedia summary, arXiv, Crossref, RSS.">
      <div style={{ display:"grid", gap:10 }}>
        <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
          <Input value={url} onChange={(_,d)=>setUrl(d.value)} style={{ width: 520 }} />
          <Button appearance="primary" onClick={async()=>setFetchRes(await apiPost("/api/web/fetch",{url}))}>Fetch URL</Button>
        </div>
        <pre style={styles.pre}>{JSON.stringify(fetchRes,null,2)}</pre>

        <Divider />

        <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
          <Input value={wiki} onChange={(_,d)=>setWiki(d.value)} style={{ width: 320 }} />
          <Button appearance="primary" onClick={async()=>setWikiRes(await apiGet(`/api/web/wikipedia/summary?title=${encodeURIComponent(wiki)}`))}>Wiki Summary</Button>
        </div>
        <pre style={styles.pre}>{JSON.stringify(wikiRes,null,2)}</pre>

        <Divider />

        <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
          <Input value={arxiv} onChange={(_,d)=>setArxiv(d.value)} style={{ width: 420 }} />
          <Button appearance="primary" onClick={async()=>setArxivRes(await apiGet(`/api/web/arxiv/search?q=${encodeURIComponent(arxiv)}&limit=5`))}>arXiv Search</Button>
        </div>
        <pre style={styles.pre}>{JSON.stringify(arxivRes,null,2)}</pre>

        <Divider />

        <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
          <Input value={cr} onChange={(_,d)=>setCr(d.value)} style={{ width: 420 }} />
          <Button appearance="primary" onClick={async()=>setCrRes(await apiGet(`/api/web/crossref/works?q=${encodeURIComponent(cr)}&rows=5`))}>Crossref Works</Button>
        </div>
        <pre style={styles.pre}>{JSON.stringify(crRes,null,2)}</pre>
      </div>
    </Panel>
  );
}

function VideoPage({ apiPost }: any) {
  const [url, setUrl] = React.useState("https://example.com/video");
  const [res, setRes] = React.useState<any>(null);
  return (
    <Panel title="Video API" subtitle="v5 provides a safe stub + artifact storage. Provider plugins can extend later.">
      <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
        <Input value={url} onChange={(_,d)=>setUrl(d.value)} style={{ width: 520 }} />
        <Button appearance="primary" onClick={async()=>setRes(await apiPost("/api/media/video/analyze",{url}))}>Analyze</Button>
      </div>
      <pre style={styles.pre}>{JSON.stringify(res,null,2)}</pre>
    </Panel>
  );
}

function FoundryPage({ apiGet, apiPost }: any) {
  const [catalog, setCatalog] = React.useState<any>(null);
  const [tree, setTree] = React.useState<any>(null);
  const load = async () => { setCatalog(await apiGet("/api/foundry/catalog")); setTree(await apiGet("/api/foundry/tree")); };
  React.useEffect(()=>{ load(); }, []);
  return (
    <Panel title="Foundry" subtitle="Catalog + Tree.">
      <Button onClick={load}>Reload</Button>
      <Divider style={{ margin:"12px 0" }} />
      <Subtitle2>Catalog</Subtitle2>
      <pre style={styles.pre}>{JSON.stringify(catalog,null,2)}</pre>
      <Subtitle2 style={{ marginTop:10 }}>Tree</Subtitle2>
      <pre style={styles.pre}>{JSON.stringify(tree,null,2)}</pre>
    </Panel>
  );
}

function BuilderPage({ apiPost }: any) {
  const [token, setToken] = React.useState("");
  const [name, setName] = React.useState("atlas_product_demo");
  const [kind, setKind] = React.useState<"app"|"plugin">("app");
  const [res, setRes] = React.useState<any>(null);

  const headers = token ? { "X-Atlas-Admin-Token": token } : undefined;

  async function gen() {
    const r = await apiPost("/api/builder/generate-zip", { spec: { name, kind, stack: "fastapi+react", target: "render" } }, headers);
    setRes(r);
  }

  return (
    <Panel title="Builder" subtitle="Generate product/plugin ZIP as artifact (admin if token enabled).">
      <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
        <Input value={token} onChange={(_,d)=>setToken(d.value)} placeholder="X-Atlas-Admin-Token (if enabled)" style={{ width: 320 }} />
        <Input value={name} onChange={(_,d)=>setName(d.value)} style={{ width: 260 }} />
        <Button appearance={kind==="app"?"primary":"secondary"} onClick={()=>setKind("app")}>App</Button>
        <Button appearance={kind==="plugin"?"primary":"secondary"} onClick={()=>setKind("plugin")}>Plugin</Button>
        <Button appearance="primary" onClick={gen}>Generate ZIP</Button>
      </div>
      <pre style={styles.pre}>{JSON.stringify(res,null,2)}</pre>
    </Panel>
  );
}

function HooksPage({ apiGet, apiPost }: any) {
  const [list, setList] = React.useState<any>(null);
  const [token, setToken] = React.useState("");
  const [name, setName] = React.useState("notify");
  const [url, setUrl] = React.useState("https://example.com/webhook");
  const [event, setEvent] = React.useState("artifact.created");
  const [secret, setSecret] = React.useState("");
  const headers = token ? { "X-Atlas-Admin-Token": token } : undefined;

  const load = async () => setList(await apiGet("/api/hooks", headers));
  React.useEffect(()=>{ load(); }, []);

  async function save() {
    const r = await apiPost("/api/hooks", { name, url, event, secret, enabled: true }, headers);
    await load();
    alert(JSON.stringify(r,null,2));
  }

  return (
    <Panel title="Hooks" subtitle="Register outbound webhooks (registry only in v5).">
      <div style={{ display:"flex", gap:10, flexWrap:"wrap", alignItems:"center" }}>
        <Input value={token} onChange={(_,d)=>setToken(d.value)} placeholder="X-Atlas-Admin-Token" style={{ width: 260 }} />
        <Button onClick={load}>Reload</Button>
      </div>
      <div style={{ display:"grid", gap:10, marginTop:10 }}>
        <Input value={name} onChange={(_,d)=>setName(d.value)} placeholder="name" />
        <Input value={url} onChange={(_,d)=>setUrl(d.value)} placeholder="url" />
        <Input value={event} onChange={(_,d)=>setEvent(d.value)} placeholder="event" />
        <Input value={secret} onChange={(_,d)=>setSecret(d.value)} placeholder="secret" />
        <Button appearance="primary" onClick={save}>Save Hook</Button>
      </div>
      <pre style={styles.pre}>{JSON.stringify(list,null,2)}</pre>
    </Panel>
  );
}

function NavItem(props: { icon: React.ReactNode; label: string; active?: boolean; onClick: () => void }) {
  return (
    <button onClick={props.onClick} style={{ ...styles.navItem, ...(props.active ? styles.navItemActive : null) }}>
      <span style={{ display: "inline-flex", width: 20, justifyContent: "center" }}>{props.icon}</span>
      <span style={{ fontSize: 13 }}>{props.label}</span>
    </button>
  );
}
function titleOf(nav: string) {
  switch (nav) {
    case "home": return "Home";
    case "chat": return "Chat";
    case "mic": return "Mic";
    case "camera": return "Camera";
    case "web": return "Web Hub";
    case "video": return "Video API";
    case "plugins": return "Plugins";
    case "engines": return "Engines";
    case "foundry": return "Foundry";
    case "builder": return "Builder";
    case "hooks": return "Hooks";
    default: return "Atlas";
  }
}

const styles: Record<string, React.CSSProperties> = {
  root: { height: "100vh", display: "flex", flexDirection: "column", fontFamily: "Segoe UI, system-ui, -apple-system, Arial", background: tokens.colorNeutralBackground1, color: tokens.colorNeutralForeground1 },
  titlebar: { height: 52, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 14px", borderBottom: `1px solid ${tokens.colorNeutralStroke2}`, background: tokens.colorNeutralBackground2 },
  brand: { display: "flex", alignItems: "center", gap: 8 },
  dot: { width: 10, height: 10, borderRadius: 999, background: tokens.colorBrandBackground, boxShadow: `0 0 0 3px ${tokens.colorBrandBackground2}` },
  titlebarRight: { display: "flex", alignItems: "center", gap: 10 },
  body: { flex: 1, display: "flex", minHeight: 0 },
  nav: { width: 260, padding: 10, display: "flex", flexDirection: "column", gap: 6, borderRight: `1px solid ${tokens.colorNeutralStroke2}`, background: tokens.colorNeutralBackground2 },
  navItem: { width: "100%", border: "1px solid transparent", background: "transparent", color: "inherit", display: "flex", alignItems: "center", gap: 10, padding: "10px 10px", borderRadius: 10, cursor: "pointer", textAlign: "left" },
  navItemActive: { background: tokens.colorNeutralBackground3, border: `1px solid ${tokens.colorNeutralStroke2}` },
  main: { flex: 1, padding: 16, overflow: "auto" },
  headerRow: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 },
  panel: { padding: 14, borderRadius: 14, border: `1px solid ${tokens.colorNeutralStroke2}`, background: tokens.colorNeutralBackground2 },
  pre: { marginTop: 10, padding: 12, borderRadius: 12, border: `1px dashed ${tokens.colorNeutralStroke2}`, background: tokens.colorNeutralBackground1, overflow: "auto", fontSize: 12, lineHeight: 1.35 },
};
