import json
from typing import Optional, Dict, List
import trafilatura

class ReaderModeExtractor:
    """Tier 1: Fast content extraction using Trafilatura"""
    
    def extract(self, url: str) -> Optional[Dict]:
        try:
            downloaded = trafilatura.fetch_url(url)
            if not downloaded:
                return None
                
            result = trafilatura.extract(
                downloaded,
                output_format='json',
                include_comments=False,
                deduplicate=True,
                url=url
            )
            
            if not result:
                return None
                
            data = json.loads(result)
            
            return {
                'title': data.get('title', ''),
                'description': data.get('description', ''),
                'author': data.get('author', ''),
                'date': data.get('date', ''),
                'content': data.get('raw_text', '') or data.get('text', ''),
                'headings': self._extract_headings(data.get('text', '')),
                'image': data.get('image', ''),
                'source': 'reader_mode',
                'confidence': 0.9 if data.get('text') else 0.5,
                'is_dynamic': False
            }
            
        except Exception:
            return None
    
    def _extract_headings(self, text: str) -> List[Dict]:
        if not text:
            return []
        lines = text.split('\n')[:30]
        headings = []
        for line in lines:
            clean = line.strip()
            if 15 < len(clean) < 120 and clean[0].isupper() and not clean.endswith('.'):
                headings.append({'level': 'h2', 'text': clean})
        return headings[:5]  # Limit to top 5