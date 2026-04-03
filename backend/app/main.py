# backend/app/main.py
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from fastapi import FastAPI
from app.routes import audit

app = FastAPI(title="GEO Audit AI")

app.include_router(audit.router, prefix="/api")

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "version": "2.0-content-aware",
        "platform": sys.platform,
        "playwright_mode": "sync_thread" if sys.platform == "win32" else "async"
    }

@app.on_event("shutdown")
async def shutdown_event():
    from app.services.scraper import get_scraper
    try:
        scraper = get_scraper()
        scraper.shutdown()
    except Exception as e:
        print(f"Shutdown error: {e}")