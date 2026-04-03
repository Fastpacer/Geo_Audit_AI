from playwright.async_api import async_playwright
from typing import Optional, Dict, List

class PlaywrightExtractor:
    """Tier 2: Headless browser for JS-heavy sites"""
    
    async def extract(self, url: str) -> Optional[Dict]:
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = await browser.new_context(
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    viewport={'width': 1280, 'height': 800}
                )
                
                page = await context.new_page()
                
                # Block heavy resources
                await page.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2,js}", 
                               lambda route: route.abort() if route.request.resource_type in ['image', 'stylesheet', 'font'] else route.continue_())
                
                await page.goto(url, wait_until='networkidle', timeout=15000)
                
                # Extract content
                content_selectors = ['article', '[role="main"]', '.post-content', '.entry-content', 'main', '#content', '.article']
                main_text = ''
                
                for selector in content_selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=3000)
                        if element:
                            main_text = await element.inner_text()
                            break
                    except:
                        continue
                
                if not main_text:
                    body = await page.query_selector('body')
                    main_text = await body.inner_text() if body else ''
                
                # Get headings
                headings = await page.evaluate('''() => {
                    return Array.from(document.querySelectorAll('h1, h2, h3'))
                        .map(h => ({level: h.tagName.toLowerCase(), text: h.innerText.trim()}))
                        .filter(h => h.text.length > 10 && h.text.length < 200);
                }''')
                
                title = await page.title()
                
                await browser.close()
                
                return {
                    'title': title,
                    'content': main_text[:8000],
                    'headings': headings[:8],
                    'source': 'playwright',
                    'confidence': 0.85 if len(main_text) > 1000 else 0.5,
                    'is_dynamic': True
                }
                
        except Exception:
            return None