from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os, sqlite3, uuid, time, json

APP_NAME = os.getenv("ATLAS_PRODUCT_NAME", "Atlas PMX — Project Management eXported Platform")
DB_PATH = os.getenv("ATLAS_DB_PATH", "/data/app.db")
UPLOAD_DIR = os.getenv("ATLAS_UPLOAD_DIR", "/data/uploads")
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    con = db()
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, name TEXT, description TEXT, created_at INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS tasks(id TEXT PRIMARY KEY, project_id TEXT, title TEXT, status TEXT, due_date TEXT, created_at INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS files(id TEXT PRIMARY KEY, project_id TEXT, filename TEXT, path TEXT, mime TEXT, size INTEGER, created_at INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS chat_logs(id TEXT PRIMARY KEY, project_id TEXT, role TEXT, content TEXT, created_at INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT, role TEXT, created_at INTEGER)")
    con.commit()
    con.close()

init_db()

app = FastAPI(title=APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProjectIn(BaseModel):
    name: str
    description: Optional[str] = ""

class TaskIn(BaseModel):
    project_id: str
    title: str
    status: str = "todo"
    due_date: Optional[str] = None

class ChatIn(BaseModel):
    project_id: str
    messages: List[Dict[str, Any]]
    temperature: float = 0.2

def require_role(min_role: str = "viewer"):
    # Minimal RBAC stub: expects header X-Role
    # roles: viewer < engineer < pm < admin < owner
    order = {"viewer":1,"engineer":2,"pm":3,"admin":4,"owner":5}
    def _dep(x_role: Optional[str] = None):
        # FastAPI doesn't auto inject headers without Header(), keep simple for scaffold.
        return True
    return _dep

@app.get("/healthz")
def healthz():
    return {"ok": True, "product": APP_NAME}

@app.get("/api/projects")
def list_projects():
    con = db()
    rows = con.execute("SELECT * FROM projects ORDER BY created_at DESC").fetchall()
    con.close()
    return {"items": [dict(r) for r in rows]}

@app.post("/api/projects")
def create_project(p: ProjectIn):
    pid = str(uuid.uuid4())
    con = db()
    con.execute("INSERT INTO projects(id,name,description,created_at) VALUES(?,?,?,?)", (pid, p.name, p.description or "", int(time.time())))
    con.commit()
    con.close()
    return {"id": pid}

@app.get("/api/tasks")
def list_tasks(project_id: Optional[str] = None):
    con = db()
    if project_id:
        rows = con.execute("SELECT * FROM tasks WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
    con.close()
    return {"items": [dict(r) for r in rows]}

@app.post("/api/tasks")
def create_task(t: TaskIn):
    tid = str(uuid.uuid4())
    con = db()
    con.execute("INSERT INTO tasks(id,project_id,title,status,due_date,created_at) VALUES(?,?,?,?,?,?)",
                (tid, t.project_id, t.title, t.status, t.due_date, int(time.time())))
    con.commit()
    con.close()
    return {"id": tid}

@app.post("/api/files/upload")
async def upload_file(project_id: str, file: UploadFile = File(...)):
    fid = str(uuid.uuid4())
    target = os.path.join(UPLOAD_DIR, f"{fid}_{file.filename}")
    data = await file.read()
    with open(target, "wb") as f:
        f.write(data)
    con = db()
    con.execute("INSERT INTO files(id,project_id,filename,path,mime,size,created_at) VALUES(?,?,?,?,?,?,?)",
                (fid, project_id, file.filename, target, file.content_type or "", len(data), int(time.time())))
    con.commit()
    con.close()
    return {"id": fid, "filename": file.filename}

@app.get("/api/files")
def list_files(project_id: Optional[str] = None):
    con = db()
    if project_id:
        rows = con.execute("SELECT * FROM files WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
    else:
        rows = con.execute("SELECT * FROM files ORDER BY created_at DESC").fetchall()
    con.close()
    items = [dict(r) for r in rows]
    # Do not expose absolute path by default
    for it in items:
        it["path"] = None
    return {"items": items}

@app.post("/api/chat")
def chat(c: ChatIn):
    # Factory-safe stub: persists messages, returns echo and hook point for LLM
    now = int(time.time())
    con = db()
    for m in c.messages[-10:]:
        role = str(m.get("role","user"))
        content = str(m.get("content",""))
        cid = str(uuid.uuid4())
        con.execute("INSERT INTO chat_logs(id,project_id,role,content,created_at) VALUES(?,?,?,?,?)",
                    (cid, c.project_id, role, content, now))
    con.commit()
    con.close()
    last = c.messages[-1]["content"] if c.messages else ""
    return {"reply": f"[Atlas PMX] Received: {last}", "mode": "stub", "next": "wire LLM provider via settings"}

@app.get("/api/admin/rbac/roles")
def roles():
    return {"roles": ["viewer","engineer","pm","admin","owner"]}

# Static SPA placeholder (for client build)
SPA_DIR = os.getenv("ATLAS_SPA_DIR", "")
if SPA_DIR and os.path.isdir(SPA_DIR):
    app.mount("/", StaticFiles(directory=SPA_DIR, html=True), name="spa")
