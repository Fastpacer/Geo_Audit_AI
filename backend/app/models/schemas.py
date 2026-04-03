# backend/app/models/schemas.py
from pydantic import BaseModel, HttpUrl
from typing import List, Dict, Any

class AuditRequest(BaseModel):
    url: HttpUrl

class AuditResponse(BaseModel):
    url: str
    title: str
    meta_description: str
    headings: List[Dict[str, Any]]
    content: str
    image: str
    og_image: str
    confidence_score: int
    signal_strength: Dict[str, Any]
    is_dynamic: bool
    is_inferred: bool
    json_ld: Dict[str, Any]
    geo_analysis: Dict[str, Any]