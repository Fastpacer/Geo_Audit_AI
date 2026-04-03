"""
GEO Audit AI - Frontend UI
Self-contained Streamlit app with integrated backend logic.
Clean architecture maintained through direct module imports.
"""

import streamlit as st
import asyncio
import sys
import os
from typing import Dict

# Import backend modules directly
import sys
import os

# Add backend to path
backend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend')
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import functions with error handling
scrape_page = None
geo_analyze = None
generate_schema = None

try:
    from app.services.scraper import scrape_page as _scrape_page
    from app.services.geo_analyzer import geo_analyze as _geo_analyze
    from app.services.schema_generator import generate_schema as _generate_schema
    scrape_page = _scrape_page
    geo_analyze = _geo_analyze
    generate_schema = _generate_schema
    print("✅ Backend modules imported successfully")
except ImportError as e:
    print(f"❌ Failed to import backend modules: {e}")
    st.error(f"Backend import failed: {e}")
    st.error("The app cannot run without backend modules.")
    st.stop()

# Configure page
st.set_page_config(
    page_title="GEO Audit AI",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styling - Dark theme
st.markdown("""
<style>
    .metric-container {
        background-color: #161b22;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border: 1px solid #30363d;
    }
    
    /* Dark theme customization */
    [data-testid="stMetricValue"] {
        color: #00d4ff;
    }
    
    [data-testid="stMarkdownContainer"] {
        color: #c9d1d9;
    }
</style>
""", unsafe_allow_html=True)

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
    - **App**: Self-contained Streamlit
    - **Backend Logic**: Direct module imports
    - **AI Model**: Groq (llama-3.1-8b-instant)
    """)
    
    # Module availability check
    try:
        # Test if backend modules are importable
        import app.services.scraper
        import app.services.geo_analyzer
        import app.services.schema_generator
        st.success("✅ Backend modules loaded")
        st.caption("All extraction & analysis ready")
    except ImportError as e:
        st.error("❌ Backend modules missing")
        st.caption(f"Import error: {str(e)}")
        st.stop()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def run_audit_analysis(url: str) -> Dict:
    """Run complete audit analysis using direct backend function calls"""
    try:
        # Create event loop for async scraping
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Extract content (async function)
        scraped_data = loop.run_until_complete(scrape_page(url))
        
        # Generate schema (sync function)
        schema = generate_schema(scraped_data, url)
        
        # GEO analysis (sync function)
        geo_analysis = geo_analyze(scraped_data)
        
        # Build response matching the original API format
        response = {
            "url": scraped_data.get("url", url),
            "title": scraped_data.get("title", ""),
            "meta_description": scraped_data.get("meta_description", ""),
            "headings": scraped_data.get("headings", []),
            "content": scraped_data.get("content", ""),
            "image": scraped_data.get("image", ""),
            "og_image": scraped_data.get("og_image", ""),
            "confidence_score": scraped_data.get("confidence_score", 0),
            "signal_strength": scraped_data.get("signal_strength", {
                "source": "unknown",
                "method": "unknown", 
                "tier": "unknown",
                "platform": "unknown"
            }),
            "is_dynamic": scraped_data.get("is_dynamic", False),
            "is_inferred": scraped_data.get("is_inferred", False),
            "json_ld": schema,
            "geo_analysis": geo_analysis
        }
        
        loop.close()
        return response
        
    except Exception as e:
        import traceback
        print(f"ERROR in audit analysis: {str(e)}")
        print(traceback.format_exc())
        st.error(f"❌ Analysis Error: {str(e)}")
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
            result = run_audit_analysis(url)
        
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
    "Self-contained Streamlit app • "
    "Direct backend integration"
)
