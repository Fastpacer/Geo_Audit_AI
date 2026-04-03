# 🚀 Quick Start Guide

## Project Structure (Production-Grade)

Your repository is now structured like enterprise applications:

```
geo_audit_ai/
├── backend/              ← FastAPI (All Business Logic)
│   ├── app/
│   │   ├── main.py       ← API server
│   │   ├── routes/       ← Endpoints
│   │   ├── services/     ← Business logic
│   │   │   ├── scraper.py              ← 4-tier extraction
│   │   │   ├── geo_analyzer.py         ← GEO analysis
│   │   │   └── extractors/             ← Modular extractors
│   │   │       ├── multi_strategy.py   ← NEW
│   │   │       ├── archive_org.py      ← NEW
│   │   │       └── metadata_enricher.py ← NEW
│   │   └── models/       ← Data schemas
│   └── requirements.txt
│
├── frontend/             ← Streamlit (UI Only)
│   └── app.py            ← Pure UI layer (no business logic)
│
├── ARCHITECTURE.md       ← System design documentation
└── DEPLOYMENT.md        ← Cloud deployment guide
```

## 🎯 Key Improvements

### ✅ Clean Separation of Concerns
- **Backend**: Extraction, analysis, schema generation
- **Frontend**: Display, input, formatting

### ✅ Production-Ready
- Proper error handling at each tier
- Modular extractor system
- API-based communication
- Cloud deployment ready

### ✅ Scalable Architecture
```
Multiple Frontends ──┐
                     ├─→ Backend API ──→ Extractors
Multiple Services ──┘
```

### ✅ Code Organization
- Each extractor is independent
- Easy to add new extraction methods
- Clear responsibility boundaries
- Better for team collaboration

## 🏃 How to Run

### 1. Backend (Port 8000)
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

### 2. Frontend (Port 8501)
```bash
cd frontend
pip install streamlit requests
streamlit run app.py
```

### 3. Test API
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## 🛠️ New Backend Services

### `multi_strategy.py` - Multi-User-Agent Extraction
Tries extraction with:
- Desktop Chrome user agent
- Mobile Safari user agent  
- Minimal headers (stealth mode)

Returns best result based on content quality.

### `archive_org.py` - Archive.org Fallback
Accesses web.archive.org snapshots for:
- Restricted/paywalled websites
- Content behind registration walls
- Historical data access

### `metadata_enricher.py` - Comprehensive Metadata
Collects from:
- Open Graph tags
- Twitter Cards
- JSON-LD structured data
- Author & publication date
- Language & canonical URLs

Used by LLM for better content reconstruction.

## 📊 Extraction Flow (4-Tier System)

```
User URL
   ↓
[Tier 1] Reader Mode (fast, ~2s)
   ↓ (if fails or low confidence)
[Tier 2] Playwright (browser-based, ~5s)
   ↓ (if fails or insufficient content)
[Tier 3a] Multi-Strategy (different user agents, ~3s)
   ↓ (if fails)
[Tier 3b] Archive.org (historical snapshot, ~5s)
   ↓ (if fails)
[Tier 4] LLM Reconstruction (with comprehensive metadata, ~10s)
   ↓
Result returned to frontend
```

## 🔄 Data Flow

```
Frontend UI (Streamlit)
    ↓ (HTTP POST /api/audit)
Backend API (FastAPI)
    ↓ (orchestrates)
Unified Scraper
    ├─ Try Tier 1-4 extractors
    ├─ Pick best result
    └─ Return normalized data
    ↓
GEO Analyzer
    ├─ Rule-based scoring
    ├─ LLM analysis
    └─ Generate recommendations
    ↓
Frontend (display results)
```

## 📝 API Contract

### Request
```json
POST /api/audit
{
  "url": "https://example.com"
}
```

### Response
```json
{
  "url": "https://example.com",
  "title": "Example Title",
  "meta_description": "Description",
  "content": "Full page content...",
  "headings": [{"level": "h1", "text": "Heading"}],
  "image": "https://...",
  "confidence_score": 85,
  "signal_strength": {
    "source": "multi_strategy",
    "tier": "3_alternative",
    "method": "async",
    "platform": "linux"
  },
  "is_dynamic": false,
  "is_inferred": false,
  "geo_analysis": {
    "rule_score": 75,
    "llm_analysis": {
      "summary": "...",
      "strengths": ["..."],
      "weaknesses": ["..."],
      "improvements": ["..."]
    }
  }
}
```

## 🐳 Docker Deployment

```bash
docker-compose up
# Backend: http://localhost:8000
# Frontend: http://localhost:8501
```

## ☁️ Cloud Deployment

### Streamlit Cloud (Frontend)
1. Push to GitHub
2. Go to streamlit.io/cloud
3. Deploy
4. Set BACKEND_URL in secrets

### Railway/Render (Backend)
1. Connect GitHub repo
2. Set GROQ_API_KEY
3. Deploy
4. Share URL with frontend

## 📚 Documentation

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - System design & components
- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Cloud deployment guide
- **[README.md](./README.md)** - Project overview

## ✨ Features

### Frontend
- ✅ Clean, intuitive UI
- ✅ Real-time analysis
- ✅ Multiple result tabs
- ✅ Confidence metrics
- ✅ JSON schema preview
- ✅ GEO improvement suggestions

### Backend
- ✅ 4-tier extraction system
- ✅ Multi-strategy approaches
- ✅ Archive.org integration
- ✅ LLM content reconstruction
- ✅ Comprehensive metadata collection
- ✅ GEO analysis & scoring
- ✅ JSON-LD schema generation
- ✅ Error handling & fallbacks

## 🎓 Learning Path

1. Read [ARCHITECTURE.md](./ARCHITECTURE.md) to understand system design
2. Start backend: `python -m uvicorn app.main:app --reload`
3. Check API docs: http://localhost:8000/docs
4. Start frontend: `streamlit run app.py`
5. Test with sample URLs
6. Read [DEPLOYMENT.md](./DEPLOYMENT.md) for production setup

## 🤔 Common Questions

**Q: Where's the extraction logic?**
A: In `backend/app/services/extractors/` - each tier is a separate module.

**Q: Can I customize extractors?**  
A: Yes! Edit `backend/app/services/extractors/*.py` and restart the backend.

**Q: How do I add a new extraction tier?**
A: Create new file in `extractors/`, implement extraction logic, add to `__init__.py`, update `scraper.py`.

**Q: Is the frontend UI customizable?**
A: Yes! Edit `frontend/app.py` - it's pure Streamlit code.

**Q: Can I run just the API without frontend?**
A: Yes! The backend is a standalone FastAPI server with automatic docs at `/docs`.

## 🚨 Troubleshooting

**Backend won't start:**
```bash
pip install -r backend/requirements.txt
python -m uvicorn app.main:app --reload
```

**Frontend can't connect to backend:**
```bash
# Check backend is running
curl http://localhost:8000/health

# Set correct backend URL
export BACKEND_URL=http://localhost:8000
```

**LLM not working:**
- Verify GROQ_API_KEY environment variable
- Check Groq API status and credits
- Ensure valid API key format

## 📞 Support Resources

- **Streamlit Docs**: https://docs.streamlit.io
- **FastAPI Docs**: https://fastapi.tiangolo.com
- **Groq API**: https://console.groq.com/keys
- **Architecture Decisions**: See [ARCHITECTURE.md](./ARCHITECTURE.md)

---

**You now have a production-grade, enterprise-scale architecture! 🎉**

Clean separation of concerns, independent components, cloud-ready deployment.
