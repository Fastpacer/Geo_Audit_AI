# backend/app/services/scraper.py
import sys
import asyncio
from typing import Dict, Optional
from concurrent.futures import ThreadPoolExecutor

from app.core.config import get_groq_client
from .extractors import ReaderModeExtractor, PlaywrightExtractor, LLMContentEnricher

_use_sync_playwright = sys.platform == "win32"

class UnifiedScraper:
    def __init__(self, groq_client=None):
        self.reader = ReaderModeExtractor()
        self.groq_client = groq_client or get_groq_client()
        self.llm_enricher = LLMContentEnricher(self.groq_client)
        self.playwright = PlaywrightExtractor()
        
        if _use_sync_playwright:
            self._thread_pool = ThreadPoolExecutor(max_workers=3, thread_name_prefix="scraper_")
    
    async def extract(self, url: str) -> Dict:
        url_str = str(url)
        
        # Tier 1: Reader Mode
        result = self.reader.extract(url_str)
        if result and result.get('confidence', 0) > 0.7 and len(result.get('content', '')) > 500:
            print(f"[Tier 1] Reader mode success: {url_str[:60]}...")
            return self._normalize(result, url_str)
        
        # Tier 2: Playwright
        print(f"[Tier 2] Attempting Playwright: {url_str[:60]}...")
        try:
            if _use_sync_playwright:
                pw_result = await asyncio.get_event_loop().run_in_executor(
                    self._thread_pool, 
                    self.playwright.extract, 
                    url_str
                )
            else:
                pw_result = await self.playwright.extract(url_str)
            
            if pw_result and len(pw_result.get('content', '')) > 400:
                print(f"[Tier 2] Playwright success: {len(pw_result.get('content', ''))} chars")
                return self._normalize(pw_result, url_str)
            else:
                print(f"[Tier 2] Playwright insufficient content, falling back")
                
        except Exception as e:
            print(f"[Tier 2] Playwright failed: {e}")
        
        # Tier 3: LLM Enrichment
        print(f"[Tier 3] LLM enrichment fallback: {url_str[:60]}...")
        basic_meta = self._extract_metadata_fallback(url_str)
        enriched = await self.llm_enricher.enrich(basic_meta, "")
        return self._normalize(enriched, url_str)
    
    def _extract_metadata_fallback(self, url: str) -> Dict:
        import requests
        from bs4 import BeautifulSoup
        import json
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            og_title = soup.find('meta', property='og:title')
            og_desc = soup.find('meta', property='og:description')
            og_image = soup.find('meta', property='og:image')
            
            json_ld = {}
            scripts = soup.find_all('script', type='application/ld+json')
            for script in scripts:
                if script and script.string:
                    try:
                        data = json.loads(script.string)
                        if isinstance(data, dict):
                            json_ld = data
                            break
                        elif isinstance(data, list) and len(data) > 0:
                            json_ld = data[0]
                            break
                    except:
                        continue
            
            title = ''
            if og_title and og_title.get('content'):
                title = og_title.get('content')
            elif isinstance(json_ld, dict) and json_ld.get('headline'):
                title = json_ld.get('headline')
            elif soup.title and soup.title.string:
                title = soup.title.string
            
            description = ''
            if og_desc and og_desc.get('content'):
                description = og_desc.get('content')
            elif isinstance(json_ld, dict) and json_ld.get('description'):
                description = json_ld.get('description')
            
            image = ''
            if og_image and og_image.get('content'):
                image = og_image.get('content')
            elif isinstance(json_ld, dict) and json_ld.get('image'):
                image = json_ld.get('image')
            
            return {
                'url': url,
                'title': title,
                'description': description,
                'image': image,
                'json_ld': json_ld if isinstance(json_ld, dict) else {},
                'raw_html': response.text[:5000]
            }
            
        except Exception as e:
            print(f"Metadata fallback failed: {e}")
            return {
                'url': url, 
                'title': '', 
                'description': '', 
                'image': '',
                'json_ld': {},
                'raw_html': ''
            }
    
    def _normalize(self, result: Dict, url: str) -> Dict:
        url_str = str(url)
        
        confidence = result.get('confidence', 0.3)
        if isinstance(confidence, float):
            confidence_int = int(confidence * 100)
        else:
            confidence_int = int(confidence)
        
        source = result.get('source', 'unknown')
        signal_strength_dict = {
            'source': source,
            'method': 'sync_thread' if _use_sync_playwright and 'playwright' in source else 'async',
            'tier': self._get_tier_from_source(source),
            'platform': sys.platform,
            'confidence_raw': confidence
        }
        
        # Handle image - ensure it's a string
        image_val = result.get('image', '')
        if image_val is None:
            image_val = ''
        elif not isinstance(image_val, str):
            image_val = str(image_val)
        
        return {
            'url': url_str,
            'title': str(result.get('title', ''))[:200],
            'meta_description': str(result.get('description', ''))[:500],
            'headings': result.get('headings', [])[:10],
            'content': str(result.get('content', ''))[:10000],
            'image': image_val,
            'og_image': image_val,
            'confidence_score': confidence_int,
            'signal_strength': signal_strength_dict,
            'is_dynamic': bool(result.get('is_dynamic', False)),
            'is_inferred': bool(result.get('is_inferred', False)),
            'json_ld': {},
            'geo_analysis': {}
        }
    
    def _get_tier_from_source(self, source: str) -> str:
        tiers = {
            'reader_mode': '1_fast',
            'playwright': '2_browser',
            'playwright_sync': '2_browser',
            'llm_enriched': '3_ai_enhanced',
            'metadata_only': '3_fallback'
        }
        return tiers.get(source, 'unknown')
    
    def shutdown(self):
        if _use_sync_playwright and hasattr(self, '_thread_pool'):
            self._thread_pool.shutdown(wait=True)
        if hasattr(self.playwright, 'shutdown'):
            self.playwright.shutdown()

_scraper_instance = None

async def scrape_page(url: str) -> Dict:
    global _scraper_instance
    if _scraper_instance is None:
        _scraper_instance = UnifiedScraper()
    return await _scraper_instance.extract(url)