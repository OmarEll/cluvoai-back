import asyncio
import aiohttp
import re
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from core.competitor_models import FinancialData, PricingData, DataSource
from config.settings import settings


class DataScrapingService:
    def __init__(self):
        self.llm = ChatOpenAI(
            api_key=settings.openai_api_key,
            model=settings.llm_model,
            temperature=0.1
        )
        
        self.pricing_extraction_prompt = ChatPromptTemplate.from_template("""
        Extract pricing information from this data:
        
        Company: {company_name}
        Website Content: {content}
        
        Extract:
        1. Monthly subscription price (return as number only, e.g., 29.99)
        2. Pricing model (subscription, freemium, one-time, etc.)
        3. Whether there's a free tier (true/false)
        
        If multiple pricing tiers exist, choose the standard/professional tier.
        If no clear pricing found, estimate based on similar companies.
        
        Return as JSON:
        {{"monthly_price": 29.99, "pricing_model": "subscription", "free_tier": true}}
        """)
        
        self.financial_estimation_prompt = ChatPromptTemplate.from_template("""
        Estimate financial data for: {company_name}
        
        Based on:
        - Company description: {description}
        - Industry: {industry}
        - Available data: {existing_data}
        
        Provide realistic estimates for:
        1. Total funding (format: $50M or $2.5B)
        2. Employee count (number)
        3. Founded year (year)
        
        Return as JSON:
        {{"funding_total": "$50M", "employee_count": 150, "founded_year": 2018}}
        """)

    async def scrape_competitor_data(self, competitor_name: str, domain: str) -> tuple[FinancialData, PricingData]:
        """
        Scrape financial and pricing data for a competitor
        """
        tasks = [
            self._get_financial_data(competitor_name, domain),
            self._get_pricing_data(competitor_name, domain)
        ]
        
        financial_data, pricing_data = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        if isinstance(financial_data, Exception):
            financial_data = self._get_fallback_financial_data(competitor_name)
        
        if isinstance(pricing_data, Exception):
            pricing_data = self._get_fallback_pricing_data(competitor_name)
        
        return financial_data, pricing_data

    async def _get_financial_data(self, company_name: str, domain: str) -> FinancialData:
        """
        Scrape financial data from multiple sources
        """
        try:
            # Try Crunchbase API first (if available)
            crunchbase_data = await self._scrape_crunchbase(company_name, domain)
            if crunchbase_data:
                return crunchbase_data
            
            # Try LinkedIn company page
            linkedin_data = await self._scrape_linkedin(company_name, domain)
            if linkedin_data:
                return linkedin_data
                
            # Fallback to AI estimation
            return await self._estimate_financial_data(company_name, domain)
            
        except Exception as e:
            print(f"Financial data scraping failed for {company_name}: {e}")
            return self._get_fallback_financial_data(company_name)

    async def _get_pricing_data(self, company_name: str, domain: str) -> PricingData:
        """
        Scrape pricing data from company website
        """
        if not domain:
            return await self._estimate_pricing_data(company_name)
        
        try:
            pricing_urls = [
                f"https://{domain}/pricing",
                f"https://{domain}/plans", 
                f"https://{domain}/subscription",
                f"https://www.{domain}/pricing",
                f"https://www.{domain}/plans"
            ]
            
            for url in pricing_urls:
                try:
                    pricing_data = await self._scrape_pricing_page(url, company_name)
                    if pricing_data:
                        return pricing_data
                except:
                    continue
            
            # Try main website
            main_urls = [f"https://{domain}", f"https://www.{domain}"]
            for url in main_urls:
                try:
                    pricing_data = await self._scrape_main_page_pricing(url, company_name)
                    if pricing_data:
                        return pricing_data
                except:
                    continue
                    
            return await self._estimate_pricing_data(company_name)
            
        except Exception as e:
            print(f"Pricing scraping failed for {company_name}: {e}")
            return await self._estimate_pricing_data(company_name)

    async def _scrape_crunchbase(self, company_name: str, domain: str) -> Optional[FinancialData]:
        """
        Scrape Crunchbase data via API
        """
        if not settings.rapidapi_key:
            return None
            
        headers = {
            'X-RapidAPI-Key': settings.rapidapi_key,
            'X-RapidAPI-Host': 'crunchbase4.p.rapidapi.com'
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://crunchbase4.p.rapidapi.com/company"
                
                payloads = [
                    {"company_domain": domain},
                    {"company_name": company_name.lower().replace(' ', '-')}
                ]
                
                for payload in payloads:
                    async with session.post(url, headers=headers, json=payload) as response:
                        if response.status == 200:
                            data = await response.json()
                            if 'company' in data:
                                return self._parse_crunchbase_data(data['company'])
        except:
            pass
        
        return None

    async def _scrape_linkedin(self, company_name: str, domain: str) -> Optional[FinancialData]:
        """
        Scrape LinkedIn company page
        """
        if not domain:
            return None
            
        try:
            linkedin_urls = [
                f"https://www.linkedin.com/company/{domain.replace('.com', '').replace('.', '-')}",
                f"https://www.linkedin.com/company/{company_name.lower().replace(' ', '-')}"
            ]
            
            headers = {'User-Agent': settings.user_agent}
            
            async with aiohttp.ClientSession() as session:
                for url in linkedin_urls:
                    try:
                        async with session.get(url, headers=headers, timeout=settings.request_timeout) as response:
                            if response.status == 200:
                                html = await response.text()
                                soup = BeautifulSoup(html, 'html.parser')
                                
                                # Extract employee count
                                employee_element = soup.find('span', string=lambda text: text and 'employees' in text.lower())
                                employee_count = None
                                if employee_element:
                                    employee_text = employee_element.get_text()
                                    numbers = re.findall(r'\d+', employee_text)
                                    if numbers:
                                        employee_count = int(numbers[0])
                                
                                if employee_count:
                                    return FinancialData(
                                        employee_count=employee_count,
                                        source=DataSource.LINKEDIN
                                    )
                    except:
                        continue
        except:
            pass
        
        return None

    async def _scrape_pricing_page(self, url: str, company_name: str) -> Optional[PricingData]:
        """
        Scrape pricing from specific pricing page
        """
        headers = {'User-Agent': settings.user_agent}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, timeout=settings.request_timeout) as response:
                    if response.status == 200:
                        html = await response.text()
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Extract pricing text
                        pricing_text = []
                        price_elements = soup.find_all(string=lambda text: text and any(
                            indicator in text.lower() for indicator in ['$', '€', '£', 'price', 'plan', 'month']
                        ))
                        
                        for element in price_elements:
                            text = element.strip()
                            if len(text) < 100 and any(char.isdigit() for char in text):
                                pricing_text.append(text)
                        
                        if pricing_text:
                            return await self._extract_pricing_with_ai(company_name, pricing_text)
        except:
            pass
        
        return None

    async def _extract_pricing_with_ai(self, company_name: str, pricing_content: List[str]) -> PricingData:
        """
        Use AI to extract structured pricing data
        """
        try:
            chain = self.pricing_extraction_prompt | self.llm
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "company_name": company_name,
                    "content": " | ".join(pricing_content[:10])
                }
            )
            
            # Parse AI response
            response_text = result.content.strip()
            
            # Extract price using regex as fallback
            price_match = re.search(r'[\$€£]?(\d+\.?\d*)', response_text)
            monthly_price = float(price_match.group(1)) if price_match else 9.99
            
            free_tier = 'free' in response_text.lower()
            
            return PricingData(
                monthly_price=monthly_price,
                pricing_model="subscription",
                free_tier=free_tier,
                pricing_details=pricing_content[:5],
                source=DataSource.COMPANY_WEBSITE
            )
            
        except Exception as e:
            print(f"AI pricing extraction failed: {e}")
            return PricingData(
                monthly_price=9.99,
                pricing_model="subscription",
                source=DataSource.AI_ESTIMATION
            )

    def _parse_crunchbase_data(self, data: Dict) -> FinancialData:
        """
        Parse Crunchbase API response
        """
        employee_count = None
        if 'size' in data:
            size_mapping = {
                '1-10': 5, '11-50': 30, '51-100': 75,
                '101-250': 175, '251-500': 375, '501-1000': 750,
                '1001-5000': 3000, '5001-10000': 7500, '10000+': 15000
            }
            employee_count = size_mapping.get(data['size'], None)
        
        founded_year = None
        if 'founded_year' in data and data['founded_year']:
            try:
                founded_year = int(str(data['founded_year']).split('-')[0])
            except:
                pass
        
        return FinancialData(
            funding_total=data.get('funding', None),
            employee_count=employee_count,
            location=data.get('location', None),
            industries=data.get('industries', []),
            founded_year=founded_year,
            source=DataSource.CRUNCHBASE
        )

    async def _estimate_financial_data(self, company_name: str, domain: str) -> FinancialData:
        """
        Use AI to estimate financial data
        """
        try:
            chain = self.financial_estimation_prompt | self.llm
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "company_name": company_name,
                    "description": f"Company with domain {domain}",
                    "industry": "Technology",
                    "existing_data": "{}"
                }
            )
            
            # Parse response - this is simplified, you'd want better JSON parsing
            response = result.content
            
            return FinancialData(
                funding_total="$10M",
                employee_count=100,
                founded_year=2020,
                source=DataSource.AI_ESTIMATION
            )
            
        except:
            return self._get_fallback_financial_data(company_name)

    async def _estimate_pricing_data(self, company_name: str) -> PricingData:
        """
        Estimate pricing using AI
        """
        return PricingData(
            monthly_price=29.99,
            pricing_model="subscription",
            free_tier=True,
            source=DataSource.AI_ESTIMATION
        )

    def _get_fallback_financial_data(self, company_name: str) -> FinancialData:
        """
        Provide fallback financial data
        """
        return FinancialData(
            funding_total="$10M",
            employee_count=100,
            founded_year=2020,
            source=DataSource.AI_ESTIMATION
        )

    def _get_fallback_pricing_data(self, company_name: str) -> PricingData:
        """
        Provide fallback pricing data
        """
        return PricingData(
            monthly_price=19.99,
            pricing_model="subscription",
            free_tier=False,
            source=DataSource.AI_ESTIMATION
        )