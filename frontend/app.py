# frontend/app.py
import streamlit as st
import sys
import os

# Add backend to path so we can import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

st.set_page_config(page_title="GEO Audit AI", layout="centered")

st.title("🔍 GEO Audit AI Tool")

# --- BACKEND LOGIC (INCLUDED DIRECTLY) ---

import asyncio
import json
import re
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup

# Windows fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import your existing backend modules
from backend.app.core.config import get_groq_client
from backend.app.services.scraper import scrape_page
from backend.app.services.geo_analyzer import geo_analyze
from backend.app.services.schema_generator import generate_schema

# --- FRONTEND UI ---

url = st.text_input("Enter Website URL")

if st.button("Analyze"):
    if not url:
        st.warning("Please enter a URL")
    else:
        try:
            with st.spinner("Analyzing..."):
                # Call backend functions directly (no HTTP needed!)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                scraped_data = loop.run_until_complete(scrape_page(url))
                schema = generate_schema(scraped_data, url)
                geo_analysis = geo_analyze(scraped_data)
                
                data = {
                    **scraped_data,
                    "json_ld": schema,
                    "geo_analysis": geo_analysis
                }

            # Display results (your existing UI)
            st.subheader("📄 Page Info")
            st.write("**Title:**", data.get("title"))
            st.write("**Meta Description:**", data.get("meta_description"))

            if data.get("is_dynamic"):
                st.warning("⚠️ Page may rely on JavaScript rendering")

            st.write("**Confidence Score:**", data.get("confidence_score"))
            
            signal = data.get("signal_strength", {})
            st.write("**Source:**", signal.get("source", "unknown"))
            st.write("**Tier:**", signal.get("tier", "unknown"))

            st.subheader("🧱 Headings")
            for h in data.get("headings", []):
                level = h.get("level", "") if isinstance(h, dict) else ""
                text = h.get("text", "") if isinstance(h, dict) else str(h)
                st.write(f"**{level.upper()}:** {text}")

            st.subheader("🖼 Image")
            img = data.get("image", "")
            if img and img != "0" and isinstance(img, str):
                st.image(img)

            # GEO Analysis
            geo = data.get("geo_analysis", {})
            st.subheader("📊 GEO Analysis (Rule-based)")
            st.write("**Rule Score:**", geo.get("rule_score"))

            st.subheader("🤖 AI GEO Critique")
            llm = geo.get("llm_analysis", {})
            st.write("**Summary:**", llm.get("summary"))

            st.write("**✅ Strengths**")
            for s in llm.get("strengths", []):
                st.write(f"- {s}")

            st.write("**❌ Weaknesses**")
            for w in llm.get("weaknesses", []):
                st.write(f"- {w}")

            st.write("**🔧 Improvements**")
            for i in llm.get("improvements", []):
                st.write(f"- {i}")

            st.write("**AI GEO Score:**", llm.get("geo_score"))

            st.subheader("⚙️ JSON-LD Schema")
            st.json(data.get("json_ld"))

        except Exception as e:
            st.error(f"Error: {str(e)}")
            import traceback
            st.code(traceback.format_exc())