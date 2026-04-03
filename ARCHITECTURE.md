# GEO Audit AI - Architecture Documentation

## 🏗️ Project Structure (Production-Grade)

```
geo_audit_ai/
├── backend/                           # FastAPI Backend (Business Logic)
│   ├── app/
│   │   ├── main.py                   # FastAPI application entry
│   │   ├── core/
│   │   │   └── config.py            # Configuration & credentials
│   │   ├── models/
│   │   │   └── schemas.py           # Pydantic request/response models
│   │   ├── routes/
│   │   │   └── audit.py             # API endpoints
│   │   └── services/
│   │       ├── scraper.py           # 4-tier extraction orchestrator
│   │       ├── geo_analyzer.py      # GEO scoring logic
│   │       ├── schema_generator.py  # JSON-LD generation
│   │       └── extractors/          # Specialized extraction modules
│   │           ├── reader_mode.py           # Tier 1: Fast extraction
│   │           ├── playwright.py            # Tier 2: Browser-based
│   │           ├── playwright_sync.py       # Tier 2: Windows support
│   │           ├── multi_strategy.py        # Tier 3: Multi-UA strategy
│   │           ├── archive_org.py          # Tier 3: Archive.org fallback
│   │           ├── metadata_enricher.py    # Tier 4: Comprehensive metadata
│   │           └── llm_enricher.py         # Tier 4: LLM reconstruction
│   └── requirements.txt
│
└── frontend/                          # Streamlit Frontend (UI Only)
    └── app.py                         # Pure UI layer calling backend API
```

## 🎯 Separation of Concerns

### Backend (`backend/app/`)
**Responsibility**: All business logic, extraction, and analysis
- Extraction strategy orchestration (4-tier system)
- Web scraping and content parsing
- GEO scoring algorithms
- Schema generation
- LLM integration for content reconstruction

**Key Services**:
1. **`scraper.py`** - Unified scraper coordinating all extraction tiers
2. **`extractors/`** - Modular extraction strategies
3. **`geo_analyzer.py`** - GEO optimization scoring
4. **`schema_generator.py`** - JSON-LD schema creation

### Frontend (`frontend/`)
**Responsibility**: User interface only
- Accept user input
- Call backend API
- Display results
- Format data for visualization

**No Business Logic**: The frontend contains ZERO extraction, analysis, or processing logic

## 🔄 Data Flow

```
User (Streamlit UI)
    ↓ (URL input)
Frontend (frontend/app.py)
    ↓ (HTTP POST to /api/audit)
Backend API Gateway (backend/app/routes/audit.py)
    ↓ (orchestrates extraction)
Unified Scraper (backend/app/services/scraper.py)
    ├─ Tier 1: Reader Mode Extractor
    ├─ Tier 2: Playwright Extractor
    ├─ Tier 3: Multi-Strategy Extractor
    ├─ Tier 3: Archive.org Extractor
    └─ Tier 4: LLM with Metadata Enricher
        ↓ (extraction result)
GEO Analyzer (backend/app/services/geo_analyzer.py)
    ↓ (analysis result)
Schema Generator (backend/app/services/schema_generator.py)
    ↓ (JSON response)
Frontend (display results)
```

## 🎛️ 4-Tier Extraction System

### Tier 1: Fast Extraction (Reader Mode)
- **Module**: `backend/app/services/extractors/reader_mode.py`
- **Speed**: Ultra-fast
- **Best for**: Clean, non-JavaScript content
- **Confidence threshold**: > 70% + content > 500 words

### Tier 2: Browser-Based Extraction (Playwright)
- **Module**: `backend/app/services/extractors/playwright.py` / `playwright_sync.py`
- **Speed**: Medium
- **Best for**: JavaScript-heavy pages
- **Confidence threshold**: > 40% + content > 400 words

### Tier 3a: Multi-Strategy Extraction
- **Module**: `backend/app/services/extractors/multi_strategy.py`
- **Strategies**: Desktop UA, Mobile UA, Minimal Headers
- **Best for**: Pages blocking standard requests
- **Confidence threshold**: Content > 300 words

### Tier 3b: Archive.org Fallback
- **Module**: `backend/app/services/extractors/archive_org.py`
- **Best for**: Restricted/paywalled websites
- **Confidence**: 60% (historical data)
- **Limitation**: May not have recent snapshots

### Tier 4: LLM Reconstruction
- **Module**: `backend/app/services/extractors/llm_enricher.py`
- **Input**: Comprehensive metadata (OG, Twitter, JSON-LD, etc.)
- **Output**: AI-reconstructed content
- **Best for**: Last-resort fallback
- **Confidence**: Variable based on metadata richness

## 🚀 Running the Application

### Start Backend
```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### Start Frontend
```bash
cd frontend
streamlit run app.py --server.port 8501
```

### Environment Variables
```bash
GROQ_API_KEY=your_groq_api_key_here
BACKEND_URL=http://localhost:8000  # Frontend needs this
```

## 📦 New Extractor Modules

### MultiStrategyExtractor
**File**: `backend/app/services/extractors/multi_strategy.py`

Tries multiple extraction strategies:
- Desktop Chrome user agent
- Mobile Safari user agent
- Minimal headers (to avoid detection)

Returns the best result based on content quality scoring.

### ArchiveOrgExtractor
**File**: `backend/app/services/extractors/archive_org.py`

Accesses web.archive.org snapshots for:
- Restricted/paywalled content
- Blocked websites
- Historical data access

### MetadataEnricher  
**File**: `backend/app/services/extractors/metadata_enricher.py`

Collects comprehensive metadata from:
- Open Graph tags
- Twitter Cards
- JSON-LD structured data
- Standard meta tags
- Author & publication date info

Used as input for LLM-based content reconstruction.

## 🧪 Testing the System

### Test Tier 1 (Reader Mode)
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

### Check Backend Health
```bash
curl http://localhost:8000/health
```

## 📊 Production Deployment

### Backend (FastAPI)
- Deploy to: Heroku, Railway, Render, AWS Lambda
- Database: PostgreSQL (optional, for caching)
- Cache layer: Redis (optional, for extraction results)

### Frontend (Streamlit)
- Deploy to: Streamlit Cloud (recommended)
- Or: Docker container
- Or: Self-hosted Streamlit server

## 🔒 Security Considerations

1. **API Key Management**: Store GROQ_API_KEY in environment variables
2. **Rate Limiting**: Implement per-user extraction limits
3. **Request Validation**: All URLs validated before sending to extractors
4. **Timeout Protection**: 120-second timeout on extraction requests
5. **SSL Verification**: Can be disabled for testing (not for production)

## 📈 Performance Metrics

- **Tier 1 (Reader Mode)**: ~500ms - 2s
- **Tier 2 (Playwright)**: ~3s - 10s  
- **Tier 3 (Multi-Strategy)**: ~2s - 5s
- **Tier 3 (Archive.org)**: ~3s - 8s
- **Tier 4 (LLM)**: ~5s - 15s

**Total timeout**: 120 seconds (backend request timeout)

## 🛠️ Future Enhancements

1. **Caching**: Cache extraction results for frequently accessed URLs
2. **Database**: Store extraction history for analytics
3. **Async Processing**: Support async extraction jobs
4. **WebSocket**: Real-time progress updates
5. **Multiple AI Models**: Support for Claude, GPT-4, etc.
6. **Batch Processing**: Analyze multiple URLs at once
7. **PDF Export**: Generate audit reports as PDFs
8. **Webhooks**: Notify external systems of analysis completion

## 📝 Code Standards

- **Backend**: FastAPI with async/await
- **Frontend**: Streamlit with session state
- **Type hints**: Used throughout for clarity
- **Error handling**: Graceful fallbacks at each tier
- **Logging**: Structured logging for debugging

## 🤝 Contributing

To add new extractors:
1. Create new file in `backend/app/services/extractors/`
2. Implement extraction logic
3. Add to `__init__.py` exports
4. Update `scraper.py` to include in tier system
5. Test with integration tests

---

**Version**: 2.0 (Production-Grade Architecture)  
**Last Updated**: April 2026
