# Streamlit Cloud Deployment Guide

## ✅ Pre-Deployment Checklist

Your app is now ready for Streamlit Cloud! Here's what you need to do:

## 📋 Step-by-Step Deployment

### 1. **Verify Your GitHub Repository**

Make sure your code is pushed to GitHub:

```bash
cd c:\Users\Admin\OneDrive\Desktop\geo_audit_ai
git status
git push
```

✅ **Current repo:** `https://github.com/Fastpacer/Geo_Audit_AI.git`

---

### 2. **Go to Streamlit Cloud**

Visit: **https://streamlit.io/cloud**

1. Click **"New app"**
2. Select **"From existing repo"**
3. Select your GitHub repo: `Fastpacer/Geo_Audit_AI`
4. Set main file path: **`frontend/app.py`**
5. Click **"Deploy"**

---

### 3. **Configure Secrets (CRITICAL)**

Once deployed, your app will ask for secrets:

1. Go to your app's dashboard
2. Click ⚙️ **Settings** (bottom left)
3. Click **"Secrets"**
4. Add your secret:

```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

5. Click **"Save"**
6. **Reboot** the app (it will restart automatically)

---

### 4. **Test Your Deployment**

Once restarted, test with a URL:

1. Open your Streamlit Cloud app URL
2. Enter a website URL (e.g., `https://example.com`)
3. Click **"Analyze"**
4. Wait for results (30 seconds - 2 minutes)

---

## 🔧 Configuration Details

### **File Structure for Cloud**

```
.
├── frontend/
│   └── app.py              ← Main Streamlit file
├── backend/
│   └── app/
│       ├── __init__.py
│       ├── core/
│       ├── models/
│       ├── routes/
│       ├── services/
│       │   ├── __init__.py
│       │   ├── scraper.py
│       │   ├── geo_analyzer.py
│       │   ├── schema_generator.py
│       │   └── extractors/
│       └── main.py
├── .streamlit/
│   └── secrets.toml        ← Local secrets (ignored in git)
├── requirements.txt        ← All dependencies
└── .env                    ← Local env file
```

### **Secrets Management**

- **Local testing:** Use `.streamlit/secrets.toml` 
- **Cloud deployment:** Set in Streamlit Cloud dashboard
- **Never commit secrets** to GitHub (`.streamlit/secrets.toml` is in `.gitignore`)

---

## 📦 Dependencies in requirements.txt

All necessary packages are listed:

```
streamlit>=1.28.0
groq>=0.4.0
pydantic>=2.0.0
requests>=2.31.0
beautifulsoup4>=4.12.0
trafilatura>=1.6.0
playwright>=1.40.0
python-dotenv>=1.0.0
```

⚠️ **Note:** First deployment may run `playwright install chromium` (takes ~1-2 min)

---

## ✅ Post-Deployment Troubleshooting

### **If app crashes after deployment:**

1. **Check logs:** Click "Manage app" → "View logs"
2. **Most common issue:** `GROQ_API_KEY` not set
3. **Solution:** Go to Settings → Secrets → Add GROQ_API_KEY → Reboot

### **If analysis takes too long:**

- First run after deployment is slower (playwright setup)
- Subsequent runs will be faster (~30-90 seconds)

### **If "Backend modules not found" error:**

- This shouldn't happen with the refactored code
- If it does, push latest commits and redeploy

---

## 🚀 Deploy Button (Alternative)

If you set up this repo for community sharing:

```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://YOUR_APP_URL)

Or add to README:

```bash
streamlit run frontend/app.py
```

---

## 📊 Expected Performance

- **Tier 1 extraction:** 0.3s
- **Tier 2 extraction:** 3-8s  
- **Tier 3 extraction:** 5-10s
- **LLM analysis:** 1-2s
- **Total:** 30s - 2min

---

## ✨ You're All Set!

Your app will be live at: **https://share.streamlit.io/Fastpacer/Geo_Audit_AI/frontend/app.py**

(Exact URL appears after deployment)

**Questions?** Check [Streamlit Cloud Docs](https://docs.streamlit.io/streamlit-cloud)
