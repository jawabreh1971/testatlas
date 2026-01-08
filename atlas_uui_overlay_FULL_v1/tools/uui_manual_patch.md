
# Manual Patch

Add to your FastAPI app file (where app=FastAPI is defined):

```py
from app.uui.router import router as uui_router
app.include_router(uui_router)
```

Optional (recommended for Render): mount built UI on /atlas-uui

```py
from fastapi.staticfiles import StaticFiles
app.mount("/atlas-uui", StaticFiles(directory="uui/dist", html=True), name="atlas-uui")
```
