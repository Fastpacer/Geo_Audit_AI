# backend/app/services/extractors/llm_enricher.py
from typing import Dict, List, Optional
import json

class LLMContentEnricher:
    """Tier 3: Reconstruct content from metadata when extraction fails"""
    
    def __init__(self, groq_client):
        self.llm = groq_client
    
    async def enrich(self, metadata: Dict, raw_html: str = "") -> Dict:
        prompt = f"""Given this webpage metadata, reconstruct the likely article structure:

Title: {metadata.get('title', 'N/A')}
Description: {metadata.get('description', 'N/A')}
URL: {metadata.get('url', 'N/A')}

Generate realistic headings and content summary. Output JSON:
{{"headings": [{{"level": "h2", "text": "Heading"}}], "summary": "...", "completeness": 0.6}}"""

        try:
            response = self.llm.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            
            raw_content = response.choices[0].message.content
            
            # Parse JSON
            try:
                enriched = json.loads(raw_content)
            except:
                # Try to extract JSON
                start = raw_content.find('{')
                end = raw_content.rfind('}')
                if start != -1 and end != -1:
                    enriched = json.loads(raw_content[start:end+1])
                else:
                    raise
            
            return {
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
                'content': enriched.get('summary', metadata.get('description', '')),
                'headings': enriched.get('headings', []),
                'image': metadata.get('image', ''),
                'source': 'llm_enriched',
                'confidence': enriched.get('completeness', 0.5) * 0.7,
                'is_dynamic': False,
                'is_inferred': True
            }
            
        except Exception as e:
            print(f"LLM enrichment error: {e}")
            return {
                'title': metadata.get('title', ''),
                'description': metadata.get('description', ''),
                'content': metadata.get('description', ''),
                'headings': [],
                'image': metadata.get('image', ''),
                'source': 'metadata_only',
                'confidence': 0.3,
                'is_dynamic': False,
                'is_inferred': True
            }