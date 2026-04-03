# GEO Audit AI

Evaluate how well AI search engines (ChatGPT, Perplexity, Google AI) can cite your web content.

## What It Does

- Extracts article content from any URL using 3 automatic fallback strategies
- Scores AI citation readiness (0-100)
- Generates JSON-LD schema markup
- Provides actionable improvement recommendations

## The Problem

Modern websites broke traditional scraping:
- Client-side rendering (React/Vue) hides content from simple HTTP requests
- Bot detection blocks automated access
- Metadata alone is insufficient for AI understanding

**Result:** AI search engines can't cite content they can't see.

## The Solution: 3-Tier Extraction

**Tier 1 - Reader Mode (Trafilatura)**
- Static HTML, blogs, news sites
- ~0.3s, 90% confidence
- Fails? → Tier 2

**Tier 2 - Browser Rendering (Playwright)**
- JS-heavy sites (Medium, MSN)
- ~3-8s, 80% confidence
- Windows: Uses thread pool (asyncio subprocess broken)
- Fails? → Tier 3

**Tier 3 - LLM Enrichment**
- Bot-blocked sites
- Inferred from metadata
- ~1-2s, 40% confidence
- Never returns empty

## Tech Stack

- **Backend:** FastAPI + Uvicorn (async API)
- **Frontend:** Streamlit (rapid UI)
- **Extraction:** Trafilatura + Playwright
- **AI:** Groq (Llama 3.1, <500ms inference)
- **Validation:** Pydantic v2 (strict schemas)

## Key Design Decisions

- **Fail forward:** Automatic tier escalation, no dead ends
- **Cross-platform:** Thread-based Playwright on Windows, native async on Linux/Mac
- **Content cleaning:** DOM manipulation before extraction removes ads/nav
- **Robust parsing:** 4-layer JSON fallback for LLM outputs
- **Dual scoring:** Rule-based (objective) + LLM critique (qualitative)

## Quick Start

```bash
git clone https://github.com/yourusername/geo-audit-ai.git
cd geo-audit-ai

python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r backend/requirements.txt
playwright install chromium

echo GROQ_API_KEY=your_key_here > .env

uvicorn app.main:app --port 8000      # Terminal 1
streamlit run frontend/app.py          # Terminal 2


Enter any URL. System auto-selects best extraction tier.
Why GEO > SEO

SEO	GEO
Target	Google ranking algorithms	AI citation engines
Question	"Can Google index this?"	"Can ChatGPT cite this?"
Metric	PageRank, keywords	Content accessibility, semantic structure
As AI search grows, being sourceable matters as much as being findable.