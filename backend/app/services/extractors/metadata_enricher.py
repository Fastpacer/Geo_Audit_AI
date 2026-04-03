# backend/app/services/extractors/metadata_enricher.py
"""Extract comprehensive metadata from multiple sources"""

from typing import Dict, Optional
import requests
from bs4 import BeautifulSoup
import json


class MetadataEnricher:
    """Extract comprehensive metadata from multiple sources"""
    
    def extract(self, url: str) -> Dict:
        """Extract comprehensive metadata from a webpage"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'DNT': '1'
            }
            
            response = requests.get(url, headers=headers, timeout=20, allow_redirects=True, verify=False)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            metadata = {
                'url': url,
                'title': '',
                'description': '',
                'keywords': '',
                'author': '',
                'published_date': '',
                'modified_date': '',
                'image': '',
                'canonical_url': '',
                'language': '',
                'open_graph': {},
                'twitter_cards': {},
                'json_ld': {},
                'structured_data': []
            }
            
            # Basic meta tags
            metadata['title'] = self._extract_title(soup)
            metadata['description'] = self._extract_description(soup)
            
            # Keywords
            keywords_meta = soup.find('meta', attrs={'name': 'keywords'})
            if keywords_meta and keywords_meta.get('content'):
                metadata['keywords'] = keywords_meta.get('content')
            
            # Author
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta and author_meta.get('content'):
                metadata['author'] = author_meta.get('content')
            
            # Dates
            published_meta = soup.find('meta', attrs={'property': 'article:published_time'})
            if published_meta and published_meta.get('content'):
                metadata['published_date'] = published_meta.get('content')
            
            modified_meta = soup.find('meta', attrs={'property': 'article:modified_time'})
            if modified_meta and modified_meta.get('content'):
                metadata['modified_date'] = modified_meta.get('content')
            
            # Canonical URL
            canonical = soup.find('link', rel='canonical')
            if canonical and canonical.get('href'):
                metadata['canonical_url'] = canonical.get('href')
            
            # Language
            html_tag = soup.find('html')
            if html_tag and html_tag.get('lang'):
                metadata['language'] = html_tag.get('lang')
            
            # Open Graph data
            og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
            for tag in og_tags:
                prop = tag.get('property', '').replace('og:', '')
                content = tag.get('content', '')
                metadata['open_graph'][prop] = content
            
            # Twitter Cards
            twitter_tags = soup.find_all('meta', attrs={'name': lambda x: x and x.startswith('twitter:')})
            for tag in twitter_tags:
                prop = tag.get('name', '').replace('twitter:', '')
                content = tag.get('content', '')
                metadata['twitter_cards'][prop] = content
            
            # JSON-LD structured data
            json_scripts = soup.find_all('script', type='application/ld+json')
            for script in json_scripts:
                if script.string:
                    try:
                        data = json.loads(script.string)
                        metadata['structured_data'].append(data)
                        if isinstance(data, dict):
                            metadata['json_ld'].update(data)
                    except:
                        pass
            
            # Extract image
            metadata['image'] = self._extract_image(soup, url)
            
            return metadata
        
        except Exception as e:
            print(f"Metadata extraction failed: {e}")
            return {
                'url': url,
                'title': '',
                'description': '',
                'error': str(e)
            }
    
    def _extract_title(self, soup) -> str:
        """Extract title from multiple sources"""
        if soup.title and soup.title.string:
            return soup.title.string.strip()
        
        og_title = soup.find('meta', property='og:title')
        if og_title and og_title.get('content'):
            return og_title.get('content').strip()
        
        return ''
    
    def _extract_description(self, soup) -> str:
        """Extract description from multiple sources"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc.get('content').strip()
        
        og_desc = soup.find('meta', property='og:description')
        if og_desc and og_desc.get('content'):
            return og_desc.get('content').strip()
        
        return ''
    
    def _extract_image(self, soup, url: str) -> str:
        """Extract image"""
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            return og_image.get('content')
        
        twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
        if twitter_image and twitter_image.get('content'):
            return twitter_image.get('content')
        
        return ''
