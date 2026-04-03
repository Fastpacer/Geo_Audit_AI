# backend/app/services/extractors/archive_org.py
"""Extract from Archive.org for restricted websites"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import json


class ArchiveOrgExtractor:
    """Extract content from web.archive.org for restricted websites"""
    
    def extract(self, url: str) -> Optional[Dict]:
        """Extract from Archive.org snapshot"""
        try:
            archive_url = f"https://web.archive.org/web/2/{url}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'DNT': '1'
            }
            
            response = requests.get(archive_url, headers=headers, timeout=30, allow_redirects=True, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract from archived page
            content = self._extract_from_archived_page(soup)
            
            if content and len(content) > 200:
                return {
                    'title': self._extract_title(soup),
                    'description': self._extract_description(soup),
                    'content': content,
                    'headings': self._extract_headings(soup),
                    'image': self._extract_image(soup, url),
                    'source': 'archive_org',
                    'confidence': 0.6,  # Lower confidence for archived content
                    'is_dynamic': False
                }
            
            return None
        
        except Exception as e:
            print(f"Archive.org extraction failed: {e}")
            return None
    
    def _extract_from_archived_page(self, soup) -> str:
        """Extract content specifically from archive.org pages"""
        # Try to find the archived content
        content_div = soup.find('div', id='CONTENT')
        if content_div:
            for unwanted in content_div.find_all(['script', 'style', 'div'], class_=['navbar', 'footer']):
                unwanted.decompose()
            
            text = content_div.get_text(separator=' ', strip=True)
            if len(text) > 100:
                return ' '.join(text.split())
        
        # Fallback: look for main content
        for selector in ['#main', '.content', 'article', 'main']:
            element = soup.select_one(selector)
            if element:
                for unwanted in element.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    unwanted.decompose()
                text = element.get_text(separator=' ', strip=True)
                if len(text) > 100:
                    return ' '.join(text.split())
        
        return ''
    
    def _extract_title(self, soup) -> str:
        """Extract title from archived page"""
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title.get('content').strip()
        
        return ''
    
    def _extract_description(self, soup) -> str:
        """Extract description from archived page"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()
        
        return ''
    
    def _extract_headings(self, soup) -> list:
        """Extract headings"""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3']):
            text = tag.get_text().strip()
            if len(text) > 3:
                headings.append({'level': tag.name, 'text': text})
        return headings[:10]
    
    def _extract_image(self, soup, url: str) -> str:
        """Extract image"""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image.get('content')
        return ''
