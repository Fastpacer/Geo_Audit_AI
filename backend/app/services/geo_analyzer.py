# backend/app/services/geo_analyzer.py
import json
import re
from typing import Dict, List, Any
from app.core.config import get_groq_client

def calculate_rule_score(data: Dict) -> int:
    """Calculate rule-based GEO score"""
    score = 0
    max_score = 100
    
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
    
    return min(score, max_score)

def geo_analyze(data: Dict) -> Dict:
    """
    Hybrid GEO analysis: Rule-based + LLM critique
    Always returns both rule_score and llm_analysis with geo_score
    """
    # Calculate rule score FIRST (this is always available)
    rule_score = calculate_rule_score(data)
    
    # Get LLM analysis (with fallback to rule_score)
    llm_analysis = None
    try:
        llm_analysis = _get_llm_critique(data, rule_score)
    except Exception as e:
        print(f"LLM critique failed: {e}, using rule_score as fallback")
        llm_analysis = {
            'summary': f'Using rule-based scoring: {rule_score}/100. LLM analysis temporarily unavailable.',
            'strengths': ['Content structure analyzed', 'Extraction quality assessed'],
            'weaknesses': ['LLM critique temporarily unavailable - resume with it returns'],
            'geo_score': rule_score,  # ALWAYS set to rule_score if LLM fails
            'improvements': ['Ensure GROQ_API_KEY is valid', 'Check API rate limits', 'Verify internet connection']
        }
    
    # Final safety check: ensure geo_score exists
    if not llm_analysis:
        llm_analysis = {}
    
    if llm_analysis.get('geo_score') is None:
        llm_analysis['geo_score'] = rule_score
    
    return {
        'rule_score': rule_score,
        'llm_analysis': llm_analysis
    }

def _get_llm_critique(data: Dict, rule_score: int) -> Dict:  # Accept rule_score as parameter
    """Get LLM critique with robust JSON parsing"""
    groq_client = get_groq_client()
    
    # Prepare content sample (first 2000 chars to save tokens)
    content_sample = data.get('content', '')[:2000]
    headings_sample = json.dumps(data.get('headings', [])[:5])
    
    prompt = f"""You are a GEO (Generative Engine Optimization) expert. Analyze this webpage for AI search readiness.

PAGE DATA:
Title: {data.get('title', 'N/A')}
Description: {data.get('meta_description', 'N/A')}
Word Count: {len(data.get('content', '').split())}
Headings: {headings_sample}
Content Sample: {content_sample[:500]}...

EXTRACTION QUALITY: {data.get('signal_strength', {}).get('tier', 'unknown')}
RULE SCORE: {rule_score}/100

Analyze and respond with ONLY this JSON format:
{{
    "summary": "2-3 sentence assessment of AI citation readiness",
    "strengths": ["strength 1", "strength 2", "strength 3"],
    "weaknesses": ["weakness 1", "weakness 2"],
    "geo_score": 75,
    "improvements": ["actionable fix 1", "actionable fix 2", "actionable fix 3"]
}}

Rules:
- geo_score: 0-100 integer based on how well AI can cite this content
- strengths/weaknesses: specific, technical SEO/GEO points
- improvements: concrete, actionable recommendations
- Return ONLY valid JSON, no markdown, no explanation"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You are a GEO expert. Output only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=800
        )
        
        raw_content = response.choices[0].message.content.strip()
        print(f"LLM raw response: {raw_content[:200]}...")  # Debug logging
        
        # Parse JSON with multiple fallback strategies
        analysis = _parse_llm_json(raw_content)
        
        # Ensure all required fields exist with proper types
        geo_score = analysis.get('geo_score')
        if geo_score is None:
            geo_score = rule_score
        else:
            try:
                geo_score = int(geo_score)
            except (ValueError, TypeError):
                geo_score = rule_score
        
        return {
            'summary': analysis.get('summary', 'Analysis completed'),
            'strengths': analysis.get('strengths', [])[:5] if isinstance(analysis.get('strengths'), list) else [],
            'weaknesses': analysis.get('weaknesses', [])[:5] if isinstance(analysis.get('weaknesses'), list) else [],
            'geo_score': min(100, max(0, geo_score)),  # Clamp between 0-100
            'improvements': analysis.get('improvements', [])[:5] if isinstance(analysis.get('improvements'), list) else []
        }
        
    except Exception as e:
        print(f"LLM API error: {e}")
        raise

def _parse_llm_json(raw_content: str) -> Dict:
    """Robust JSON parsing with multiple fallback strategies"""
    
    # Strategy 1: Direct parse
    try:
        return json.loads(raw_content)
    except json.JSONDecodeError:
        pass
    
    # Strategy 2: Extract from markdown code block
    try:
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{.*\}'  # Greedy match for JSON object
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, raw_content, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except:
                    continue
    except:
        pass
    
    # Strategy 3: Line-by-line repair
    try:
        start = raw_content.find('{')
        end = raw_content.rfind('}')
        if start != -1 and end != -1:
            cleaned = raw_content[start:end+1]
            return json.loads(cleaned)
    except:
        pass
    
    # Strategy 4: Extract key-value pairs manually
    try:
        return {
            'summary': raw_content[:200] if raw_content else 'Could not parse LLM response',
            'strengths': [],
            'weaknesses': ['JSON parsing failed'],
            'geo_score': 50,
            'improvements': ['Retry analysis']
        }
    except:
        pass
    
    # Ultimate fallback
    return {
        'summary': 'Failed to parse LLM response',
        'strengths': [],
        'weaknesses': ['Response parsing error'],
        'geo_score': 0,
        'improvements': ['Contact support']
    }