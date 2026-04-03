# backend/app/services/extractors/multi_strategy.py
"""Multi-strategy extraction with different user agents and headers"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import json


class MultiStrategyExtractor:
    """Extract using multiple strategies (user agents, headers, etc.)"""
    
    def __init__(self):
        self.strategies = [
            self._extract_desktop_ua,
            self._extract_mobile_ua,
            self._extract_minimal_headers,
        ]
    
    def extract(self, url: str) -> Optional[Dict]:
        """Try multiple extraction strategies and return the best result"""
        best_result = None
        best_score = 0
        
        for strategy in self.strategies:
            try:
                result = strategy(url)
                if result:
                    content_len = len(result.get('content', ''))
                    title_len = len(result.get('title', ''))
                    meta_len = len(result.get('description', ''))
                    
                    # Score based on content quality
                    score = content_len + (title_len * 2) + (meta_len * 1.5)
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
                        result['strategy'] = strategy.__name__
            except Exception as e:
                print(f"Strategy {strategy.__name__} failed: {e}")
                continue
        
        return best_result
    
    def _extract_desktop_ua(self, url: str) -> Optional[Dict]:
        """Extract with desktop browser user agent"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        }
        return self._extract_with_headers(url, headers)
    
    def _extract_mobile_ua(self, url: str) -> Optional[Dict]:
        """Extract with mobile browser user agent"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive'
        }
        return self._extract_with_headers(url, headers)
    
    def _extract_minimal_headers(self, url: str) -> Optional[Dict]:
        """Extract with minimal headers to avoid detection"""
        headers = {
            'User-Agent': 'Python-urllib/3.8',
            'Accept': '*/*'
        }
        return self._extract_with_headers(url, headers)
    
    def _extract_with_headers(self, url: str, headers: Dict) -> Optional[Dict]:
        """Extract using custom headers"""
        try:
            response = requests.get(url, headers=headers, timeout=20, allow_redirects=True, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self._extract_title_comprehensive(soup)
            meta_desc = self._extract_meta_description_comprehensive(soup)
            content = self._extract_content_advanced(soup)
            headings = self._extract_headings_advanced(soup)
            image = self._extract_image_comprehensive(soup, url)
            
            return {
                'title': title,
                'description': meta_desc,
                'content': content,
                'headings': headings,
                'image': image,
                'source': 'multi_strategy',
                'confidence': 0.7,
                'is_dynamic': False
            }
        except Exception as e:
            print(f"Headers extraction failed: {e}")
            return None
    
    def _extract_title_comprehensive(self, soup) -> str:
        """Extract title with fallbacks"""
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title.get('content').strip()
        
        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
        if twitter_title and twitter_title.get('content'):
            return twitter_title.get('content').strip()
        
        json_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_scripts:
            if script.string:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('headline'):
                        return data['headline']
                except:
                    pass
        
        h1 = soup.find('h1')
        if h1:
            return h1.get_text().strip()
        
        return ''
    
    def _extract_meta_description_comprehensive(self, soup) -> str:
        """Extract meta description with fallbacks"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()
        
        twitter_desc = soup.find('meta', attrs={'name': 'twitter:description'})
        if twitter_desc and twitter_desc.get('content'):
            return twitter_desc.get('content').strip()
        
        return ''
    
    def _extract_content_advanced(self, soup) -> str:
        """Extract main content with advanced selectors"""
        selectors = ['article', '[role="main"]', '.post-content', '.entry-content', '.content', 'main', '#content']
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer', 'noscript']):
                    unwanted.decompose()
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return ' '.join(text.split())
        
        body = soup.find('body')
        if body:
            paragraphs = body.find_all('p')
            content_parts = [p.get_text().strip() for p in paragraphs if len(p.get_text().strip()) > 20]
            if content_parts:
                return ' '.join(content_parts)
        
        return ''
    
    def _extract_headings_advanced(self, soup) -> list:
        """Extract headings"""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            text = tag.get_text().strip()
            if 3 < len(text) < 200:
                headings.append({'level': tag.name, 'text': text})
        return headings[:20]
    
    def _extract_image_comprehensive(self, soup, url: str) -> str:
        """Extract image"""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image.get('content')
        
        for img in soup.find_all('img', src=True)[:5]:
            src = img.get('src')
            if src and len(src) > 10:
                return src
        
        return ''
