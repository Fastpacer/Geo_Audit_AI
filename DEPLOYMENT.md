# GEO Audit AI - Deployment Guide

## 📋 Prerequisites

- Python 3.8+
- Groq API Key (get from https://console.groq.com)
- Backend server (8000) and Frontend server (8501) ports available

## 🚀 Local Development

### 1. Setup Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Setup Frontend

```bash
cd frontend
pip install streamlit requests
```

### 3. Set Environment Variables

**Windows (PowerShell)**:
```powershell
$env:GROQ_API_KEY = "your_groq_api_key"
$env:BACKEND_URL = "http://localhost:8000"
```

**Linux/macOS**:
```bash
export GROQ_API_KEY="your_groq_api_key"
export BACKEND_URL="http://localhost:8000"
```

### 4. Run Backend

```bash
cd backend
python -m uvicorn app.main:app --reload --port 8000
```

### 5. Run Frontend

```bash
cd frontend
streamlit run app.py
```

Visit: http://localhost:8501

## 🐳 Docker Deployment

### Backend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

ENV GROQ_API_KEY=""
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install streamlit requests

COPY frontend/app.py .

ENV BACKEND_URL="http://backend:8000"
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: backend.Dockerfile
    ports:
      - "8000:8000"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./backend:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: .
      dockerfile: frontend.Dockerfile
    ports:
      - "8501:8501"
    environment:
      - BACKEND_URL=http://backend:8000
    volumes:
      - ./frontend:/app
    depends_on:
      - backend
    command: streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

**Run with Docker Compose**:
```bash
docker-compose up
```

## ☁️ Streamlit Cloud Deployment

### 1. Push to GitHub

```bash
git add .
git commit -m "Production-ready GEO audit AI"
git push origin main
```

### 2. Deploy Frontend

1. Go to https://streamlit.io/cloud
2. Click "New app"
3. Select repository and branch
4. Set main file to `frontend/app.py`
5. Click "Deploy"

### 3. Set Secrets

In Streamlit Cloud dashboard:
```
GROQ_API_KEY = "your_groq_api_key"
BACKEND_URL = "https://your-backend-url.com"
```

## 🚀 Railway.app Deployment

### Backend

```bash
railway init
railway add
railway variables set GROQ_API_KEY=your_key
railway up
```

### Frontend

Link GitHub repo in Railway dashboard, set environment variables.

## 🌐 Render Deployment

### Backend Service

1. New → Web Service
2. Connect GitHub repo
3. Command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
4. Set environment variables
5. Deploy

### Frontend Service

1. New → Web Service
2. Connect GitHub repo
3. Build Command: `pip install -r frontend_requirements.txt`
4. Start Command: `streamlit run frontend/app.py --server.port 10000`
5. Set BACKEND_URL environment variable
6. Deploy

## 📊 AWS Deployment

### Backend (Lambda + API Gateway)

1. Create Lambda function in Python 3.11
2. Upload FastAPI code
3. Use Zappa for easy deployment:

```bash
pip install zappa
zappa init
zappa deploy production
```

### Frontend (Streamlit App Runner)  

1. Create ECR repository
2. Build and push Docker image
3. Create App Runner service
4. Set environment variables

## 🔍 Health Checks

### Backend Health
```bash
curl http://localhost:8000/health
# Response: {"status": "ok", "version": "2.0-content-aware"}
```

### Frontend Connection
- Check sidebar status indicator
- Should show "✅ Backend Connected"

## 📝 Monitoring

### Backend Logs
```bash
# Local
tail -f logs/backend.log

# Production (Render/Railway)
View in dashboard → Logs
```

### Frontend Logs
```bash
# Streamlit Cloud
View in dashboard → Logs
```

## 🔐 Production Checklist

- [ ] Environment variables properly set
- [ ] GROQ_API_KEY secured in secrets manager
- [ ] Backend URL configured in frontend
- [ ] CORS enabled if cross-origin
- [ ] Rate limiting implemented
- [ ] Error logging configured
- [ ] SSL/TLS certificates valid
- [ ] API keys rotated regularly
- [ ] Database backups scheduled (if using DB)
- [ ] Monitoring alerts configured

## 🐛 Troubleshooting

### Backend not connecting
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check firewall
netstat -an | grep 8000
```

### Slow extraction
- Check network connection
- Monitor Groq API rate limits
- Consider caching results
- Check server resources (CPU, memory)

### LLM not working
- Verify GROQ_API_KEY is valid
- Check Groq API status
- Monitor token usage
- Ensure sufficient API credits

## 📈 Scaling

### Horizontal Scaling

1. **Backend**: Deploy multiple instances behind load balancer (nginx, HAProxy)
2. **Frontend**: Streamlit Cloud handles this automatically
3. **Cache**: Add Redis for extraction caching
4. **Database**: PostgreSQL for result persistence

### Performance Optimization

1. Implement response caching
2. Use CDN for static assets
3. Enable gzip compression
4. Optimize extraction tiers
5. Use async/await throughout

## 🔄 CI/CD Pipeline

### GitHub Actions Example

```yaml
name: Deploy GEO Audit AI

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/

  deploy-backend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Backend
        run: |
          # Add your deployment script here
          echo "Deploying backend..."

  deploy-frontend:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Deploy Frontend
        run: |
          # Streamlit Cloud auto-deploys on push
          echo "Frontend deploying via Streamlit Cloud..."
```

---

**Need Help?** Check the [Architecture Documentation](./ARCHITECTURE.md) for system overview.
