"""
GEO Audit AI - Frontend UI
Pure Streamlit frontend that calls the FastAPI backend for all analysis.
This is a clean UI layer with zero business logic.
"""

import streamlit as st
import requests
import os
from typing import Dict

# Configure page
st.set_page_config(
    page_title="GEO Audit AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling
st.markdown("""
<style>
    .metric-container {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Backend configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Page title
st.title("🔍 GEO Audit AI")
st.markdown("_Powered by advanced multi-tier extraction & AI analysis_")

# ============================================================================
# SIDEBAR
# ============================================================================
with st.sidebar:
    st.header("⚙️ Configuration")
    
    st.markdown("""
    ### Architecture
    - **Frontend**: Streamlit UI
    - **Backend**: FastAPI with 4-tier extraction
    - **AI Model**: Groq (llama-3.1-8b-instant)
    """)
    
    # Backend health check
    try:
        response = requests.get(f"{BACKEND_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            st.success("✅ Backend Connected")
            st.caption(f"Version: {health.get('version', 'N/A')}")
        else:
            st.error("❌ Backend Offline")
    except:
        st.error("❌ Cannot reach backend")
        st.caption(f"URL: {BACKEND_URL}")

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

@st.cache_resource
def call_audit_api(url: str) -> Dict:
    """Call the backend audit API"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/audit",
            json={"url": url},
            timeout=120
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("⏱️ Request timeout - Analysis took too long")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"❌ Backend Error: {str(e)}")
        return None

# ============================================================================
# MAIN UI
# ============================================================================

# Input section
col1, col2 = st.columns([5, 1])
with col1:
    url = st.text_input(
        "Enter Website URL",
        placeholder="https://example.com",
        label_visibility="collapsed"
    )
with col2:
    analyze_btn = st.button("Analyze", use_container_width=True, type="primary")

# Separator
st.divider()

# Analysis logic
if analyze_btn:
    if not url:
        st.warning("⚠️ Please enter a URL to analyze")
    else:
        # Show progress
        with st.spinner("🔄 Analyzing website... This may take up to 2 minutes"):
            result = call_audit_api(url)
        
        if result:
            # Create tabs for different views
            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                ["📄 Page Info", "📝 Content", "🤖 GEO Analysis", "⚙️ Technical", "📊 Schema"]
            )
            
            # ================================================================
            # TAB 1: PAGE INFO
            # ================================================================
            with tab1:
                # Key metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    score = result.get("confidence_score", 0)
                    st.metric("Confidence", f"{score}%")
                
                with col2:
                    tier = result.get("signal_strength", {}).get("tier", "unknown")
                    st.metric("Extraction Tier", tier)
                
                with col3:
                    source = result.get("signal_strength", {}).get("source", "N/A")
                    st.metric("Source", source[:15])
                
                with col4:
                    is_inferred = result.get("is_inferred", False)
                    st.metric("AI Inferred", "Yes" if is_inferred else "No")
                
                st.divider()
                
                # Page metadata
                st.subheader("📰 Metadata")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Title**")
                    st.info(result.get("title", "N/A"))
                
                with col2:
                    st.write("**URL**")
                    st.info(result.get("url", "N/A"))
                
                st.write("**Meta Description**")
                st.info(result.get("meta_description", "N/A"))
                
                # Warnings
                if result.get("is_dynamic"):
                    st.warning("⚠️ This page may rely on JavaScript rendering")
                
                # Featured image
                if result.get("image"):
                    st.subheader("🖼️ Featured Image")
                    st.image(result["image"], use_column_width=True)
            
            # ================================================================
            # TAB 2: CONTENT
            # ================================================================
            with tab2:
                content = result.get("content", "")
                word_count = len(content.split()) if content else 0
                char_count = len(content)
                
                # Content stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Word Count", word_count)
                with col2:
                    st.metric("Character Count", char_count)
                with col3:
                    st.metric("Paragraph Count", len([p for p in content.split('\n\n') if p.strip()]))
                
                st.divider()
                
                # Extracted content
                st.subheader("Extracted Content")
                st.text_area(
                    "Full page content",
                    content[:5000] + ("..." if len(content) > 5000 else ""),
                    height=300,
                    disabled=True,
                    label_visibility="collapsed"
                )
                
                st.divider()
                
                # Headings structure
                st.subheader("🏗️ Heading Structure")
                headings = result.get("headings", [])
                
                if headings:
                    for idx, h in enumerate(headings, 1):
                        level = h.get("level", "").upper()
                        text = h.get("text", "")
                        indent = "▸ " * (int(level[-1]) - 1)
                        st.write(f"{indent}**{level}**: {text}")
                else:
                    st.info("No headings found in the page")
            
            # ================================================================
            # TAB 3: GEO ANALYSIS
            # ================================================================
            with tab3:
                geo = result.get("geo_analysis", {})
                
                if geo:
                    # Scores
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        rule_score = geo.get("rule_score", 0)
                        st.metric(
                            "Rule-Based Score",
                            rule_score,
                            delta=f"{rule_score - 50:+d}" if rule_score != 50 else None
                        )
                    
                    llm = geo.get("llm_analysis", {})
                    with col2:
                        ai_score = llm.get("geo_score")
                        # Fallback to rule_score if geo_score is None
                        if ai_score is None:
                            ai_score = geo.get("rule_score", 0)
                        st.metric(
                            "AI GEO Score",
                            ai_score if ai_score is not None else 0,
                            delta=f"{ai_score - rule_score:+d}" if ai_score and ai_score != rule_score else None
                        )
                    
                    st.divider()
                    
                    # Summary
                    st.subheader("📋 Summary")
                    st.info(llm.get("summary", "Analysis unavailable"))
                    
                    # Strengths and weaknesses
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("✅ Strengths")
                        strengths = llm.get("strengths", [])
                        if strengths:
                            for s in strengths:
                                st.write(f"• {s}")
                        else:
                            st.caption("No strengths detected")
                    
                    with col2:
                        st.subheader("❌ Weaknesses")
                        weaknesses = llm.get("weaknesses", [])
                        if weaknesses:
                            for w in weaknesses:
                                st.write(f"• {w}")
                        else:
                            st.caption("No weaknesses detected")
                    
                    st.divider()
                    
                    # Improvements
                    st.subheader("🔧 Improvements")
                    improvements = llm.get("improvements", [])
                    if improvements:
                        for i, improvement in enumerate(improvements, 1):
                            st.write(f"{i}. {improvement}")
                    else:
                        st.caption("No improvements suggested")
                else:
                    st.info("GEO analysis not available")
            
            # ================================================================
            # TAB 4: TECHNICAL
            # ================================================================
            with tab4:
                st.subheader("📡 Signal Strength")
                signal = result.get("signal_strength", {})
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Source**")
                    st.code(signal.get("source", "N/A"))
                
                with col2:
                    st.write("**Tier**")
                    st.code(signal.get("tier", "N/A"))
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Extraction Method**")
                    st.code(signal.get("method", "N/A"))
                
                with col2:
                    st.write("**Platform**")
                    st.code(signal.get("platform", "N/A"))
                
                st.divider()
                
                st.subheader("🔍 Full Signal Data")
                st.json(signal)
            
            # ================================================================
            # TAB 5: SCHEMA
            # ================================================================
            with tab5:
                schema = result.get("json_ld", {})
                
                if schema:
                    st.subheader("JSON-LD Structured Data")
                    st.json(schema)
                else:
                    st.info("No JSON-LD schema detected")
                
                st.divider()
                
                st.subheader("📊 Raw API Response")
                with st.expander("View complete data", expanded=False):
                    st.json(result)
else:
    # Initial state
    st.info("""
    👆 **Enter a URL above and click Analyze** to:
    - Extract page content with 4-tier fallback system
    - Analyze headings and structure
    - Calculate GEO optimization score
    - Get AI-powered improvement suggestions
    - Review JSON-LD schema
    """)
    
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🏗️ 4-Tier Extraction**")
        st.caption("Trafilatura → Playwright → Multi-Strategy → Archive.org → LLM")
    
    with col2:
        st.markdown("**🤖 AI Analysis**")
        st.caption("Rule-based + LLM hybrid scoring")
    
    with col3:
        st.markdown("**⚡ Instant Results**")
        st.caption("Fast extraction with quality assessment")

st.divider()

# Footer
st.caption(
    "🌐 GEO Audit AI • "
    "Backend-powered extraction • "
    f"Backend: {BACKEND_URL}"
)
