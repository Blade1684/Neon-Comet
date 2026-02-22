import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse
from .sites import SITE_SELECTORS

import os

class Scraper:
    def __init__(self):
        # Premium ScraperAPI Key checks
        self.api_key = os.getenv('SCRAPER_API_KEY')
        
        # Enforce Desktop User-Agent to avoid mobile pages
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US,en;q=0.9',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.google.com/',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'cross-site',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        }

    def _get_domain(self, url):
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www.
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

    def _clean_price(self, price_str):
        if not price_str:
            return None
        if isinstance(price_str, (int, float)):
            return float(price_str)
        # Remove non-numeric chars except .
        # Handle cases like "₹ 1,20,000" -> 120000.0
        # Remove currency symbols and commas
        clean_str = re.sub(r'[^\d.]', '', str(price_str))
        try:
            return float(clean_str)
        except ValueError:
            return None

    def _extract_flipkart_price(self, soup):
        # Flipkart often hides classes or uses dynamic ones (React Native)
        # Strategy: Find text with ₹, exclude struck-through or EMI/Exchange info
        candidates = soup.find_all(string=re.compile(r'₹'))
        
        for candidate in candidates:
            parent = candidate.parent
            if not parent:
                continue
            
            text = candidate.strip()
            parent_style = parent.get('style', '')
            
            # 1. Exclude strikethrough (original price)
            if 'text-decoration-line:line-through' in parent_style:
                continue
                
            # 2. Exclude EMI or other informational text
            if any(x in text for x in ['EMI', 'Get at', 'month', 'off', 'Extra', 'discount', 'Free', 'Store']):
                continue
                
            # 3. Exclude very long text (likely description)
            if len(text) > 30:
                continue
                
            return text
            
        return None

    def _extract_json_ld(self, soup):
        # Strategy for sites like Myntra that embed Product data in JSON-LD
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                # Some sites have multiple JSON blocks concatenated or poorly formatted
                content = script.string
                if not content:
                    continue
                data = json.loads(content)
                
                # Handle single object vs list of objects
                if isinstance(data, dict):
                    data = [data]
                
                for item in data:
                    if item.get('@type') == 'Product':
                        title = item.get('name', 'Unknown Product')
                        offers = item.get('offers', {})
                        
                        # Offers could be a dict or a list of dicts
                        price = None
                        if isinstance(offers, dict):
                            price = offers.get('price')
                        elif isinstance(offers, list) and len(offers) > 0:
                            price = offers[0].get('price')
                            
                        if price:
                            return {
                                'price': self._clean_price(price),
                                'title': title
                            }
            except Exception as e:
                print(f"JSON-LD Parsing Error: {e}")
                continue
        return None

    def get_price(self, url):
        domain = self._get_domain(url)
        selector_config = SITE_SELECTORS.get(domain)

        # Fallback for subdomains or variations if exact match fails
        if not selector_config:
            # Try matching end of domain
            for d, config in SITE_SELECTORS.items():
                if domain.endswith(d):
                    selector_config = config
                    break
        
        if not selector_config:
            print(f"Warning: No configuration found for domain {domain}. Please add selector manually.")
            return None

        # Rotate UA or use standard
        headers = self.headers.copy()
        
        try:
            if self.api_key:
                print(f"Routing request for {domain} through ScraperAPI...")
                payload = {'api_key': self.api_key, 'url': url}
                # Render JS if needed for highly dynamic SPA sites
                if 'ajio' in domain or 'myntra' in domain:
                    payload['render'] = 'true'
                # Premium proxies can take longer to handshake
                response = requests.get('http://api.scraperapi.com', params=payload, timeout=60)
            else:
                response = requests.get(url, headers=headers, timeout=10)
                
            response.raise_for_status()
            
            # Debug: Save last HTML
            with open("debug_html.html", "wb") as f:
                f.write(response.content)

            soup = BeautifulSoup(response.content, 'lxml')
            
            # Try JSON-LD parsing first if specified (e.g., Myntra)
            if selector_config.get('type') == 'json-ld':
                print(f"Using JSON-LD parsing for {domain}...")
                json_data = self._extract_json_ld(soup)
                if json_data and json_data.get('price'):
                    return json_data
                else:
                    print("Could not find Product inside JSON-LD blocks.")
                    return None

            # Special handling for Flipkart (Dynamic/React Native)
            if 'flipkart' in domain:
                price_text = self._extract_flipkart_price(soup)
                if price_text:
                    print(f"Found price text (Flipkart method): {price_text}")
                    price = self._clean_price(price_text)
                    # Title extraction fallback
                    title = "Unknown Product"
                    og_title = soup.select_one('meta[property="og:title"]')
                    if og_title and og_title.get('content'):
                        title = og_title['content'].strip()
                    elif soup.title:
                        title = soup.title.string.strip()
                        
                    return {
                        'price': price,
                        'title': title
                    }

            # Standard Extract Price using Config Selectors
            selector = selector_config.get('price')
            price_element = None
            
            if isinstance(selector, list):
                for selector_item in selector:
                    price_element = soup.select_one(selector_item)
                    if price_element:
                        break
            else:
                 price_element = soup.select_one(selector)
            
            # If fallback exists and first failed
            if not price_element and 'fallback' in selector_config:
                price_element = soup.select_one(selector_config['fallback'])

            if price_element:
                price_text = price_element.get_text(strip=True)
                print(f"Found price text: {price_text}")
                price = self._clean_price(price_text)
                
                # Get Title (generic fallback)
                title = "Unknown Product"
                if soup.title:
                    title = soup.title.string.strip()
                # Try og:title for better quality
                og_title = soup.select_one('meta[property="og:title"]')
                if og_title and og_title.get('content'):
                    title = og_title['content'].strip()
                
                return {
                    'price': price,
                    'title': title
                }
            else:
                print(f"Could not find price element with selector: {selector}")
                return None

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
