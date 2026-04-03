# frontend/app.py
import streamlit as st
import sys
import os
import asyncio
import json
import re
from typing import Dict, Optional, List
import requests
from bs4 import BeautifulSoup
from groq import Groq
import httpx

# Load environment variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    st.error("GROQ_API_KEY environment variable is not set. Please configure it in your Streamlit Cloud secrets.")
    st.stop()

# Initialize Groq client
_groq_client = None
def get_groq_client():
    global _groq_client
    if _groq_client is None:
        http_client = httpx.Client(timeout=60.0)
        _groq_client = Groq(api_key=GROQ_API_KEY, http_client=http_client)
    return _groq_client

st.set_page_config(page_title="GEO Audit AI", layout="centered")
st.title("🔍 GEO Audit AI Tool")

# --- BACKEND FUNCTIONS (COPIED DIRECTLY) ---

def scrape_page(url: str) -> Dict:
    """Simple web scraper for basic content extraction"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract basic data
        title = soup.find('title')
        title_text = title.text.strip() if title else ""

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_text = meta_desc.get('content', '').strip() if meta_desc else ""

        # Extract headings
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append({
                'level': tag.name,
                'text': tag.get_text().strip()
            })

        # Extract main content (simple approach)
        content = ""
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            # Remove script and style elements
            for script in main_content(["script", "style"]):
                script.decompose()
            content = main_content.get_text(separator=' ', strip=True)

        # Extract image
        image = ""
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            image = img_tag['src']
            if not image.startswith('http'):
                image = url.rstrip('/') + '/' + image.lstrip('/')

        return {
            'title': title_text,
            'meta_description': meta_text,
            'content': content,
            'headings': headings,
            'image': image,
            'confidence_score': 70,
            'signal_strength': {'source': 'requests', 'tier': 'basic'},
            'is_dynamic': False
        }
    except Exception as e:
        return {
            'title': 'Error',
            'meta_description': f'Failed to scrape: {str(e)}',
            'content': '',
            'headings': [],
            'image': '',
            'confidence_score': 0,
            'signal_strength': {'source': 'error', 'tier': 'failed'},
            'is_dynamic': False
        }

def generate_schema(data: Dict, url: str) -> Dict:
    """Generate basic JSON-LD schema"""
    schema_type = "WebPage"
    content = data.get('content', '')
    if len(content) > 1000:
        schema_type = "Article"
    elif len(data.get('headings', [])) > 2:
        schema_type = "BlogPosting"

    schema = {
        "@context": "https://schema.org",
        "@type": schema_type,
        "headline": data.get('title', ''),
        "description": data.get('meta_description', ''),
        "url": url,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        }
    }

    if data.get('image'):
        schema["image"] = data['image']

    if len(content) > 100:
        schema["articleBody"] = content[:2000]

    return schema

def calculate_rule_score(data: Dict) -> int:
    """Calculate rule-based GEO score"""
    score = 0

    # Title quality (20 points)
    title = data.get('title', '')
    if len(title) > 20 and len(title) < 100:
        score += 15
    elif len(title) > 0:
        score += 5

    # Meta description (15 points)
    meta = data.get('meta_description', '')
    if len(meta) > 50 and len(meta) < 300:
        score += 15
    elif len(meta) > 0:
        score += 5

    # Headings structure (20 points)
    headings = data.get('headings', [])
    h1_count = sum(1 for h in headings if h.get('level') == 'h1')
    h2_count = sum(1 for h in headings if h.get('level') == 'h2')

    if h1_count >= 1:
        score += 10
    if h2_count >= 2:
        score += 10
    elif h2_count >= 1:
        score += 5

    # Content quality (30 points)
    content = data.get('content', '')
    word_count = len(content.split())
    if word_count > 500:
        score += 30
    elif word_count > 200:
        score += 20
    elif word_count > 100:
        score += 10

    # Schema markup (15 points)
    signal = data.get('signal_strength', {})
    if signal.get('tier') == '1_fast':
        score += 15
    elif signal.get('tier') == '2_browser':
        score += 10
    else:
        score += 5

    return min(score, 100)

def geo_analyze(data: Dict) -> Dict:
    """Hybrid GEO analysis: Rule-based + LLM critique"""
    rule_score = calculate_rule_score(data)

    # Get LLM analysis
    try:
        llm_analysis = _get_llm_critique(data, rule_score)
    except Exception as e:
        print(f"LLM critique failed: {e}")
        llm_analysis = {
            'summary': 'LLM analysis temporarily unavailable. Using rule-based scoring only.',
            'strengths': ['Content extracted successfully'],
            'weaknesses': ['LLM critique failed - check API key or connection'],
            'geo_score': rule_score,
            'improvements': ['Ensure GROQ_API_KEY is valid', 'Check internet connection']
        }

    return {
        'rule_score': rule_score,
        'llm_analysis': llm_analysis
    }

def _get_llm_critique(data: Dict, rule_score: int) -> Dict:
    """Get LLM critique with robust JSON parsing"""
    groq_client = get_groq_client()

    content_sample = data.get('content', '')[:1000]
    headings_sample = json.dumps(data.get('headings', [])[:3])

    prompt = f"""You are a GEO (Generative Engine Optimization) expert. Analyze this webpage for AI search readiness.

PAGE DATA:
Title: {data.get('title', 'N/A')}
Description: {data.get('meta_description', 'N/A')}
Word Count: {len(data.get('content', '').split())}
Headings: {headings_sample}
Content Sample: {content_sample[:300]}...

Current Rule Score: {rule_score}/100

Provide a JSON response with:
- summary: Brief assessment (2-3 sentences)
- strengths: Array of 2-3 key strengths
- weaknesses: Array of 1-3 main issues
- improvements: Array of 2-3 actionable recommendations

Return ONLY valid JSON."""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a GEO expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=400
        )

        raw = response.choices[0].message.content.strip()

        # Try to parse JSON
        try:
            return json.loads(raw)
        except:
            # Try to extract JSON from response
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1:
                return json.loads(raw[start:end+1])

    except Exception as e:
        print(f"LLM critique error: {e}")

    # Fallback response
    return {
        'summary': f'Page analysis completed with rule-based score of {rule_score}/100.',
        'strengths': ['Basic content structure detected'],
        'weaknesses': ['LLM analysis unavailable'],
        'improvements': ['Check API configuration']
    }

# --- FRONTEND UI ---

url = st.text_input("Enter Website URL")

if st.button("Analyze"):
    if not url:
        st.warning("Please enter a URL")
    else:
        try:
            with st.spinner("Analyzing..."):
                # Call backend functions directly (no HTTP needed!)
                scraped_data = scrape_page(url)
                schema = generate_schema(scraped_data, url)
                geo_analysis = geo_analyze(scraped_data)
                
                data = {
                    **scraped_data,
                    "json_ld": schema,
                    "geo_analysis": geo_analysis
                }
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