# backend/app/core/config.py
import os
from dotenv import load_dotenv
from groq import Groq
import httpx

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing. Check your .env file.")

_groq_client = None

def get_groq_client():
    """Get or create Groq client singleton"""
    global _groq_client
    if _groq_client is None:
        http_client = httpx.Client(timeout=60.0)
        _groq_client = Groq(
            api_key=GROQ_API_KEY,
            http_client=http_client
        )
    return _groq_client