import asyncio
import aiohttp
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from config.settings import settings


class WebScrapingUtils:
    """
    Utility class for web scraping operations
    """
    
    @staticmethod
    async def fetch_url(url: str, headers: Optional[Dict] = None) -> Optional[str]:
        """
        Fetch content from a URL with error handling
        """
        if not headers:
            headers = {'User-Agent': settings.user_agent}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, 
                    headers=headers, 
                    timeout=settings.request_timeout
                ) as response:
                    if response.status == 200:
                        return await response.text()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        
        return None
    
    @staticmethod
    def extract_text_by_patterns(html: str, patterns: List[str]) -> List[str]:
        """
        Extract text matching specific patterns from HTML
        """
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        for pattern in patterns:
            elements = soup.find_all(string=lambda text: text and pattern.lower() in text.lower())
            for element in elements:
                text = element.strip()
                if len(text) < 200 and len(text) > 5:  # Reasonable text length
                    results.append(text)
        
        return list(set(results))  # Remove duplicates
    
    @staticmethod
    def extract_pricing_text(html: str) -> List[str]:
        """
        Extract potential pricing information from HTML
        """
        patterns = ['$', '€', '£', 'price', 'plan', 'month', 'year', 'subscription', 'free', 'premium']
        return WebScrapingUtils.extract_text_by_patterns(html, patterns)
    
    @staticmethod
    def clean_domain(domain: str) -> str:
        """
        Clean and normalize domain names
        """
        if not domain:
            return ""
        
        domain = domain.lower().strip()
        domain = re.sub(r'^https?://', '', domain)
        domain = re.sub(r'^www\.', '', domain)
        domain = domain.strip('/')
        
        return domain
    
    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """
        Extract numeric values from text
        """
        pattern = r'\d+\.?\d*'
        matches = re.findall(pattern, text)
        return [float(match) for match in matches if match]
    
    @staticmethod
    def generate_url_variations(domain: str, paths: List[str]) -> List[str]:
        """
        Generate URL variations for scraping
        """
        if not domain:
            return []
        
        variations = []
        base_urls = [f"https://{domain}", f"https://www.{domain}"]
        
        for base_url in base_urls:
            for path in paths:
                variations.append(f"{base_url}/{path.lstrip('/')}")
        
        return variations
    
    @staticmethod
    async def scrape_multiple_urls(urls: List[str], max_concurrent: int = 5) -> Dict[str, str]:
        """
        Scrape multiple URLs concurrently with rate limiting
        """
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(url: str) -> tuple:
            async with semaphore:
                content = await WebScrapingUtils.fetch_url(url)
                await asyncio.sleep(settings.rate_limit_delay)  # Rate limiting
                return url, content
        
        tasks = [fetch_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = {}
        for result in results:
            if isinstance(result, tuple) and result[1] is not None:
                successful_results[result[0]] = result[1]
        
        return successful_results
    
    @staticmethod
    def extract_social_media_handles(html: str) -> Dict[str, str]:
        """
        Extract social media handles from HTML
        """
        soup = BeautifulSoup(html, 'html.parser')
        social_links = {}
        
        # Common social media patterns
        patterns = {
            'twitter': r'twitter\.com/([^/\s"]+)',
            'linkedin': r'linkedin\.com/company/([^/\s"]+)',
            'facebook': r'facebook\.com/([^/\s"]+)',
            'instagram': r'instagram\.com/([^/\s"]+)'
        }
        
        html_text = str(soup)
        
        for platform, pattern in patterns.items():
            matches = re.findall(pattern, html_text, re.IGNORECASE)
            if matches:
                social_links[platform] = matches[0]
        
        return social_links
    
    @staticmethod
    def is_valid_url(url: str) -> bool:
        """
        Validate if a string is a proper URL
        """
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False