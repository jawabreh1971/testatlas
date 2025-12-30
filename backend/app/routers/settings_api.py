from fastapi import APIRouter
from pydantic import BaseModel
from ..core.settings import set_setting, get_setting, list_settings
from ..core.audit import audit

router = APIRouter(prefix="/api/settings", tags=["settings"])

class SettingIn(BaseModel):
    key: str
    value: str

@router.get("")
def list_all():
    rows = list_settings()
    return {"ok": True, "items": [{"key": k, "value": v, "updated_at": ts} for k,v,ts in rows]}

@router.get("/{key}")
def get_one(key: str):
    v = get_setting(key)
    return {"ok": True, "key": key, "value": v}

@router.post("")
def put_one(payload: SettingIn):
    set_setting(payload.key, payload.value)
    audit("settings.set", {"key": payload.key})
    return {"ok": True}
