# backend/app/services/schema_generator.py
import json
from typing import Dict, Any
from app.core.config import get_groq_client

def generate_schema(data: Dict, url: str) -> Dict:
    """
    Generate JSON-LD schema based on extracted content
    """
    # Build base schema from extracted data
    base_schema = {
        "@context": "https://schema.org",
        "@type": _determine_schema_type(data),
        "headline": data.get('title', ''),
        "description": data.get('meta_description', ''),
        "url": url,
        "mainEntityOfPage": {
            "@type": "WebPage",
            "@id": url
        }
    }
    
    # Add article body if available
    content = data.get('content', '')
    if len(content) > 100:
        base_schema["articleBody"] = content[:5000]  # Limit length
    
    # Add image if available
    image = data.get('image', '')
    if image:
        base_schema["image"] = image
    
    # Add author/publisher if detected
    signal = data.get('signal_strength', {})
    if 'publisher' in signal.get('source', ''):
        base_schema["publisher"] = {
            "@type": "Organization",
            "name": signal.get('source', 'Unknown')
        }
    
    # Enhance with LLM if content is rich enough
    if len(content) > 300 and data.get('confidence_score', 0) > 50:
        try:
            enhanced = _enhance_with_llm(base_schema, data)
            return enhanced
        except Exception as e:
            print(f"Schema LLM enhancement failed: {e}")
    
    return base_schema

def _determine_schema_type(data: Dict) -> str:
    """Determine appropriate schema.org type"""
    headings = data.get('headings', [])
    content = data.get('content', '')
    
    # Check for news indicators
    if any(word in data.get('title', '').lower() for word in ['news', 'breaking', 'report']):
        return "NewsArticle"
    
    # Check for blog indicators
    if len(headings) > 2 and len(content) > 1000:
        return "BlogPosting"
    
    # Check for tech/article content
    if len(content) > 500:
        return "Article"
    
    return "WebPage"

def _enhance_with_llm(base_schema: Dict, data: Dict) -> Dict:
    """Use LLM to enhance schema with detected entities"""
    groq_client = get_groq_client()
    
    prompt = f"""Given this webpage data, enhance the JSON-LD schema.

TITLE: {data.get('title')}
DESCRIPTION: {data.get('meta_description')}
HEADINGS: {json.dumps(data.get('headings', [])[:3])}
CONTENT_SAMPLE: {data.get('content', '')[:800]}...

Current schema: {json.dumps(base_schema)}

Return ONLY the enhanced JSON-LD schema as valid JSON. Add relevant fields like:
- author (if detectable)
- datePublished (if detectable)
- keywords (3-5 relevant topics)
- articleSection (category)

Rules:
- Return ONLY valid JSON
- Do not wrap in markdown
- Ensure all strings are properly escaped"""

    try:
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": "You output only valid JSON-LD schemas."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            max_tokens=600
        )
        
        raw = response.choices[0].message.content.strip()
        
        # Parse with fallback
        try:
            enhanced = json.loads(raw)
            return enhanced
        except:
            # Try to extract JSON from response
            start = raw.find('{')
            end = raw.rfind('}')
            if start != -1 and end != -1:
                return json.loads(raw[start:end+1])
            
    except Exception as e:
        print(f"Schema enhancement error: {e}")
    
    return base_schema