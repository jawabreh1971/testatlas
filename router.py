from fastapi import APIRouter, HTTPException
from .engine import export_from_payload, list_exports, download_export, list_presets, spec_schema

router = APIRouter(prefix="/api/factory", tags=["factory"])

@router.get("/spec-schema")
def get_schema():
    return spec_schema()

@router.get("/presets")
def presets():
    return {"items": list_presets()}

@router.post("/export")
def export(payload: dict):
    # payload can be: {"preset_id": "..."} OR full {"spec": {...}}
    return export_from_payload(payload)

@router.get("/exports")
def exports():
    return {"items": list_exports()}

@router.get("/download/{artifact}")
def download(artifact: str):
    return download_export(artifact)
