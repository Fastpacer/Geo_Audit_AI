# backend/app/services/extractors/playwright_sync.py
import sys
import threading
from typing import Optional, Dict, List
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

class PlaywrightSyncExtractor:
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=3)
        self._timeout = 45
    
    def extract(self, url: str) -> Optional[Dict]:
        future = self._executor.submit(self._run_extraction, url)
        
        try:
            return future.result(timeout=self._timeout)
        except FutureTimeoutError:
            print(f"Playwright extraction timed out for {url[:60]}...")
            future.cancel()
            return None
        except Exception as e:
            print(f"Playwright thread error: {e}")
            return None
    
    def _run_extraction(self, url: str) -> Optional[Dict]:
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                from playwright.sync_api import sync_playwright
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(
                        headless=True,
                        args=[
                            '--disable-blink-features=AutomationControlled',
                            '--no-sandbox',
                            '--disable-setuid-sandbox',
                            '--disable-dev-shm-usage',
                            '--disable-accelerated-2d-canvas',
                            '--disable-gpu',
                            '--window-size=1920,1080',
                            '--disable-extensions',
                            '--disable-plugins',
                        ]
                    )
                    
                    context = browser.new_context(
                        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        viewport={'width': 1920, 'height': 1080},
                        java_script_enabled=True,
                        bypass_csp=True
                    )
                    
                    page = context.new_page()
                    
                    # Block heavy resources
                    page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,ttf}", 
                              lambda route: route.abort())
                    
                    try:
                        response = page.goto(
                            url, 
                            wait_until='domcontentloaded',
                            timeout=25000
                        )
                    except Exception:
                        response = page.goto(
                            url,
                            wait_until='domcontentloaded',
                            timeout=35000
                        )
                    
                    if not response or response.status >= 400:
                        browser.close()
                        if attempt < max_retries - 1:
                            continue
                        return None
                    
                    # Wait for hydration
                    page.wait_for_timeout(3000 + (attempt * 2000))
                    
                    # Hide UI elements before extraction
                    try:
                        page.evaluate("""
                            const hideSelectors = [
                                'nav', 'header', 'footer', '.sidebar', '.menu',
                                '.ad', '.advertisement', '.sponsored', '.social-share',
                                '.comments', '[role="navigation"]', '[role="banner"]',
                                '.cookie-banner', '.newsletter-signup', '.related-articles',
                                '.page-settings', '.toolbar', '.sticky-header'
                            ];
                            hideSelectors.forEach(sel => {
                                document.querySelectorAll(sel).forEach(el => {
                                    el.style.display = 'none';
                                    el.setAttribute('aria-hidden', 'true');
                                });
                            });
                        """)
                        page.wait_for_timeout(500)
                    except:
                        pass
                    
                    # Extract content
                    content_data = self._extract_content(page)
                    
                    # Get metadata
                    title = page.title()
                    meta_description = self._get_meta_description(page)
                    
                    # Get headings
                    headings = self._extract_headings(page)
                    
                    browser.close()
                    
                    if len(content_data.get('text', '')) < 100 and attempt < max_retries - 1:
                        print(f"Playwright attempt {attempt + 1} content too short, retrying...")
                        continue
                    
                    confidence = self._calculate_confidence(content_data, headings, title)
                    
                    return {
                        'title': title,
                        'description': meta_description,
                        'content': content_data['text'][:10000],
                        'headings': headings,
                        'image': content_data.get('image', ''),
                        'source': 'playwright_sync',
                        'confidence': confidence,
                        'is_dynamic': True,
                        'is_inferred': False,
                        'selector_used': content_data.get('selector')
                    }
                    
            except Exception as e:
                print(f"Playwright sync extraction error (attempt {attempt + 1}): {e}")
                import traceback
                print(traceback.format_exc())
                if attempt < max_retries - 1:
                    continue
                return None
        
        return None
    
    def _extract_content(self, page) -> Dict:
        """Extract main content with cleaning"""
        
        # Try specific article selectors first
        selectors = [
            ('article[data-testid="article-body"]', 0.95),
            ('article .article-body', 0.95),
            ('[data-testid="article-body"]', 0.95),
            ('article[role="article"]', 0.9),
            ('article', 0.85),
            ('[role="main"] article', 0.9),
            ('main article', 0.9),
            ('.post-content', 0.85),
            ('.entry-content', 0.85),
            ('.article-content', 0.85),
            ('.story-body', 0.8),
            ('[role="main"]', 0.75),
            ('main', 0.7),
        ]
        
        best_content = ''
        best_selector = None
        
        for selector, weight in selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    text = element.inner_text()
                    
                    # Clean: remove short lines (likely UI)
                    lines = [line.strip() for line in text.split('\n') 
                            if len(line.strip()) > 25 and len(line.strip()) < 500]
                    cleaned_text = '\n'.join(lines)
                    
                    if len(cleaned_text) > len(best_content):
                        best_content = cleaned_text
                        best_selector = selector
            except:
                continue
        
        # Fallback to paragraphs
        if len(best_content) < 500:
            try:
                paragraphs = page.query_selector_all('article p, [role="main"] p, main p, .content p')
                if paragraphs and len(paragraphs) > 3:
                    texts = []
                    for p in paragraphs[:25]:
                        text = p.inner_text().strip()
                        # Filter out UI text
                        if (len(text) > 40 and 
                            not any(ui in text.lower() for ui in ['cookie', 'subscribe', 'sign up', 'privacy policy', 'terms of use'])):
                            texts.append(text)
                    if texts:
                        best_content = '\n\n'.join(texts)
                        best_selector = 'paragraphs_fallback'
            except:
                pass
        
        # Final fallback
        if len(best_content) < 300:
            try:
                body_text = page.evaluate("""
                    () => {
                        const clone = document.body.cloneNode(true);
                        ['script', 'style', 'nav', 'header', 'footer', 'aside',
                         '.ad', '.advertisement', '.sponsored', '.social',
                         '[role="navigation"]', '[role="banner"]'].forEach(sel => {
                            clone.querySelectorAll(sel).forEach(el => el.remove());
                        });
                        
                        const contentEls = clone.querySelectorAll('p, h1, h2, h3, article');
                        let text = '';
                        contentEls.forEach(el => {
                            const t = el.innerText.trim();
                            if (t.length > 30 && t.length < 2000 &&
                                !t.includes('Page settings') &&
                                !t.includes('Sponsored') &&
                                !t.includes('More for You')) {
                                text += t + '\\n\\n';
                            }
                        });
                        return text;
                    }
                """)
                if body_text and len(body_text) > len(best_content):
                    best_content = body_text
                    best_selector = 'body_cleaned'
            except:
                pass
        
        # Get image
        image = ''
        try:
            article_img = page.query_selector('article img, [role="main"] img, .article-content img')
            if article_img:
                src = article_img.get_attribute('src')
                if src and not src.startswith('data:'):
                    image = src
        except:
            pass
        
        if not image:
            try:
                og_image = page.query_selector('meta[property="og:image"]')
                if og_image:
                    image = og_image.get_attribute('content') or ''
            except:
                pass
        
        return {
            'text': best_content,
            'selector': best_selector,
            'image': image
        }
    
    def _extract_headings(self, page) -> List[Dict]:
        """Extract headings, filtering UI elements"""
        try:
            headings_data = page.evaluate("""
                () => {
                    const results = [];
                    const containers = document.querySelectorAll('article, [role="main"], main, .post-content');
                    const container = containers[0] || document.body;
                    
                    container.querySelectorAll('h1, h2, h3').forEach(el => {
                        const text = el.innerText.trim();
                        const level = el.tagName.toLowerCase();
                        
                        // Skip if in UI container
                        const inUI = el.closest('nav, header, footer, aside, .sidebar, .menu, .toolbar, .page-settings, .sticky-header');
                        if (inUI) return;
                        
                        // Skip UI text patterns
                        const uiPatterns = ['page settings', 'sponsored', 'more for you', 'cookie', 'subscribe', 'sign up'];
                        if (uiPatterns.some(p => text.toLowerCase().includes(p))) return;
                        
                        if (text.length > 15 && text.length < 150) {
                            results.push({level: level, text: text});
                        }
                    });
                    return results;
                }
            """)
            
            # Deduplicate
            seen = set()
            unique = []
            for h in headings_data:
                text = h.get('text', '').strip()
                if text and text not in seen:
                    seen.add(text)
                    unique.append({
                        'level': h.get('level', 'h2'),
                        'text': text
                    })
            
            return unique[:8]
            
        except Exception as e:
            print(f"Heading extraction error: {e}")
            return []
    
    def _get_meta_description(self, page) -> str:
        try:
            og_desc = page.query_selector('meta[property="og:description"]')
            if og_desc:
                content = og_desc.get_attribute('content')
                if content:
                    return content
            
            meta_desc = page.query_selector('meta[name="description"]')
            if meta_desc:
                content = meta_desc.get_attribute('content')
                if content:
                    return content
        except:
            pass
        
        return ''
    
    def _calculate_confidence(self, content_data: Dict, headings: List[Dict], title: str) -> float:
        confidence = 0.5
        
        content_len = len(content_data.get('text', ''))
        selector = content_data.get('selector', '')
        
        if content_len > 2000:
            confidence += 0.2
        elif content_len > 1000:
            confidence += 0.15
        elif content_len > 500:
            confidence += 0.1
        
        if selector in ['article', '[data-testid="article-body"]', '.post-content']:
            confidence += 0.15
        elif selector == 'body_cleaned':
            confidence -= 0.05
        
        h1_count = sum(1 for h in headings if h.get('level') == 'h1')
        h2_count = sum(1 for h in headings if h.get('level') == 'h2')
        
        if h1_count > 0:
            confidence += 0.05
        if h2_count >= 2:
            confidence += 0.05
        
        if title and len(title) > 10:
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    def shutdown(self):
        self._executor.shutdown(wait=True)