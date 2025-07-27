import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.market_models import MarketSizingInput, MarketSizingReport
from services.market_sizing.market_data_service import market_data_service
from services.market_sizing.tam_sam_som_service import tam_sam_som_service
from services.market_sizing.market_sizing_report_service import market_sizing_report_service
from services.analysis_storage_service import analysis_storage_service
from core.analysis_models import AnalysisType


class SimpleMarketSizingWorkflow:
    """Simple, reliable market sizing workflow without LangGraph complexity"""
    
    async def run_analysis(self, analysis_input: MarketSizingInput) -> MarketSizingReport:
        """Run the complete market sizing analysis in a simple sequential manner"""
        
        try:
            print("🚀 Starting market sizing analysis...")
            
            # Step 1: Collect existing context from competitor and persona analysis
            competitor_context, persona_context = await self._collect_existing_context(analysis_input)
            
            # Step 2: Collect comprehensive market data
            market_data = await self._collect_market_data(analysis_input, competitor_context, persona_context)
            
            # Step 3: Calculate TAM, SAM, and SOM
            tam_sam_som = await self._calculate_tam_sam_som(analysis_input, market_data, competitor_context, persona_context)
            
            # Step 4: Generate comprehensive report
            report = await self._generate_report(analysis_input, market_data, tam_sam_som, competitor_context, persona_context)
            
            print("✅ Market sizing analysis completed successfully")
            return report
            
        except Exception as e:
            print(f"❌ Market sizing analysis failed: {e}")
            raise Exception(f"Market sizing analysis failed: {str(e)}")
    
    async def _collect_existing_context(self, analysis_input: MarketSizingInput) -> tuple:
        """Collect existing context from competitor and persona analysis"""
        
        try:
            print("🔍 Collecting existing analysis context...")
            
            user_id = getattr(analysis_input, 'user_id', None)
            idea_id = getattr(analysis_input, 'idea_id', None)
            
            competitor_context = None
            persona_context = None
            
            if user_id and idea_id:
                try:
                    # Get competitor analysis context
                    competitor_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.COMPETITOR, include_feedback=False
                    )
                    
                    if competitor_analysis and competitor_analysis.competitor_report:
                        report = competitor_analysis.competitor_report
                        
                        # Extract comprehensive competitive intelligence for market sizing
                        competitor_context = {
                            "total_competitors": report.total_competitors,
                            "competitors": report.competitors,
                            "market_gaps": report.market_gaps,
                            "key_insights": report.key_insights,
                            "positioning_recommendations": report.positioning_recommendations,
                            
                            # Extract pricing intelligence
                            "pricing_intelligence": self._extract_pricing_intelligence(report.competitors),
                            
                            # Extract market size indicators from competitor data
                            "market_size_indicators": self._extract_market_size_indicators(report.competitors),
                            
                            # Extract competitive landscape insights
                            "competitive_landscape": self._extract_competitive_landscape(report.competitors),
                            
                            # Extract market sentiment and user behavior
                            "market_sentiment_insights": self._extract_market_sentiment_insights(report.competitors),
                            
                            # Extract SWOT-based opportunities and threats
                            "swot_insights": self._extract_swot_insights(report.competitors)
                        }
                        print(f"✅ Found comprehensive competitor analysis with {len(report.competitors)} competitors")
                        print(f"   💰 Pricing data from {len([c for c in report.competitors if c.pricing_data.monthly_price])} competitors")
                        print(f"   📊 Market gaps identified: {len(report.market_gaps)}")
                        print(f"   🎯 Key insights available: {len(report.key_insights)}")
                    
                    # Get persona analysis context
                    persona_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.PERSONA, include_feedback=False
                    )
                    
                    if persona_analysis and persona_analysis.persona_report:
                        persona_context = {
                            "personas": [persona.dict() for persona in persona_analysis.persona_report.personas],
                            "target_segments": persona_analysis.persona_report.target_audience_insights
                        }
                        print(f"✅ Found persona analysis with {len(persona_analysis.persona_report.personas)} personas")
                        
                except Exception as e:
                    print(f"⚠️ Error retrieving existing context: {e}")
            
            return competitor_context, persona_context
            
        except Exception as e:
            print(f"⚠️ Context collection error: {e}")
            return None, None
    
    async def _collect_market_data(self, analysis_input: MarketSizingInput, competitor_context: Optional[Dict], persona_context: Optional[Dict]):
        """Collect comprehensive market data"""
        
        try:
            print("📊 Collecting market data...")
            
            # Prepare additional context from existing analysis
            additional_context = ""
            if competitor_context:
                additional_context += f"Competitor analysis available with {len(competitor_context.get('competitors', []))} competitors. "
            if persona_context:
                additional_context += f"Persona analysis available with {len(persona_context.get('personas', []))} personas. "
            
            # Collect market data
            market_data = await market_data_service.collect_market_data(
                analysis_input,
                additional_context
            )
            
            print(f"✅ Market data collected - Size: ${market_data.market_size_current:,.0f}, Growth: {market_data.market_growth_rate}%")
            return market_data
            
        except Exception as e:
            print(f"❌ Market data collection error: {e}")
            raise Exception(f"Market data collection failed: {str(e)}")
    
    async def _calculate_tam_sam_som(self, analysis_input: MarketSizingInput, market_data, competitor_context: Optional[Dict], persona_context: Optional[Dict]):
        """Calculate TAM, SAM, and SOM"""
        
        try:
            print("🎯 Calculating TAM/SAM/SOM...")
            
            if not market_data:
                raise Exception("Market data not available for TAM/SAM/SOM calculation")
            
            # Calculate TAM/SAM/SOM
            tam_sam_som = await tam_sam_som_service.calculate_tam_sam_som(
                analysis_input,
                market_data,
                competitor_context,
                persona_context
            )
            
            print(f"✅ TAM/SAM/SOM calculated - TAM: ${tam_sam_som.tam:,.0f}")
            return tam_sam_som
            
        except Exception as e:
            print(f"❌ TAM/SAM/SOM calculation error: {e}")
            raise Exception(f"TAM/SAM/SOM calculation failed: {str(e)}")
    
    async def _generate_report(self, analysis_input: MarketSizingInput, market_data, tam_sam_som, competitor_context: Optional[Dict], persona_context: Optional[Dict]):
        """Generate comprehensive market sizing report"""
        
        try:
            print("📝 Generating market sizing report...")
            
            if not market_data:
                raise Exception("Market data not available for report generation")
            
            if not tam_sam_som:
                raise Exception("TAM/SAM/SOM data not available for report generation")
            
            # Generate comprehensive report
            report = await market_sizing_report_service.generate_market_sizing_report(
                analysis_input,
                market_data,
                tam_sam_som,
                competitor_context,
                persona_context
            )
            
            print("✅ Market sizing report generated successfully")
            return report
            
        except Exception as e:
            print(f"❌ Report generation error: {e}")
            raise Exception(f"Report generation failed: {str(e)}")


    def _extract_pricing_intelligence(self, competitors) -> Dict[str, Any]:
        """Extract pricing intelligence from competitor data"""
        pricing_intel = {
            "pricing_models": [],
            "price_ranges": {
                "subscription_monthly": [],
                "one_time": [],
                "freemium_available": 0
            },
            "average_pricing": {},
            "pricing_strategies": []
        }
        
        for competitor in competitors:
            pricing = competitor.pricing_data
            
            # Collect pricing models
            if pricing.pricing_model:
                pricing_intel["pricing_models"].append({
                    "competitor": competitor.basic_info.name,
                    "model": pricing.pricing_model,
                    "has_free_tier": pricing.free_tier
                })
            
            # Collect pricing data
            if pricing.monthly_price:
                pricing_intel["price_ranges"]["subscription_monthly"].append({
                    "competitor": competitor.basic_info.name,
                    "price": pricing.monthly_price
                })
            
            if pricing.free_tier:
                pricing_intel["price_ranges"]["freemium_available"] += 1
            
            # Collect pricing strategies
            if pricing.pricing_details:
                pricing_intel["pricing_strategies"].extend(pricing.pricing_details)
        
        # Calculate averages
        monthly_prices = [p["price"] for p in pricing_intel["price_ranges"]["subscription_monthly"]]
        if monthly_prices:
            pricing_intel["average_pricing"]["monthly_subscription"] = sum(monthly_prices) / len(monthly_prices)
            pricing_intel["average_pricing"]["price_range"] = f"${min(monthly_prices):.2f} - ${max(monthly_prices):.2f}"
        
        return pricing_intel
    
    def _extract_market_size_indicators(self, competitors) -> Dict[str, Any]:
        """Extract market size indicators from competitor financial data"""
        indicators = {
            "funding_insights": {
                "total_funding_raised": [],
                "average_funding": 0,
                "funding_rounds": [],
                "market_maturity_score": 0
            },
            "company_size_distribution": {
                "startups": 0,
                "growth_stage": 0,
                "established": 0
            },
            "geographic_presence": [],
            "market_validation": {
                "total_employees": 0,
                "average_company_age": 0,
                "funded_companies": 0
            }
        }
        
        total_funding = 0
        total_employees = 0
        company_ages = []
        current_year = 2024
        
        for competitor in competitors:
            financial = competitor.financial_data
            
            # Funding analysis
            if financial.funding_total:
                try:
                    # Extract funding amount (handle formats like "$10M", "10 million", etc.)
                    funding_str = financial.funding_total.lower().replace('$', '').replace(',', '')
                    if 'm' in funding_str or 'million' in funding_str:
                        amount = float(funding_str.split('m')[0].split('million')[0].strip()) * 1_000_000
                    elif 'b' in funding_str or 'billion' in funding_str:
                        amount = float(funding_str.split('b')[0].split('billion')[0].strip()) * 1_000_000_000
                    else:
                        amount = float(funding_str)
                    
                    indicators["funding_insights"]["total_funding_raised"].append({
                        "competitor": competitor.basic_info.name,
                        "amount": amount
                    })
                    total_funding += amount
                    indicators["market_validation"]["funded_companies"] += 1
                except:
                    pass
            
            # Employee count analysis
            if financial.employee_count:
                total_employees += financial.employee_count
                
                # Categorize company size
                if financial.employee_count < 50:
                    indicators["company_size_distribution"]["startups"] += 1
                elif financial.employee_count < 500:
                    indicators["company_size_distribution"]["growth_stage"] += 1
                else:
                    indicators["company_size_distribution"]["established"] += 1
            
            # Company age analysis
            if financial.founded_year:
                age = current_year - financial.founded_year
                company_ages.append(age)
            
            # Geographic presence
            if financial.location:
                indicators["geographic_presence"].append(financial.location)
        
        # Calculate aggregates
        if indicators["funding_insights"]["total_funding_raised"]:
            total = sum(f["amount"] for f in indicators["funding_insights"]["total_funding_raised"])
            count = len(indicators["funding_insights"]["total_funding_raised"])
            indicators["funding_insights"]["average_funding"] = total / count
        
        if total_employees > 0:
            indicators["market_validation"]["total_employees"] = total_employees
        
        if company_ages:
            indicators["market_validation"]["average_company_age"] = sum(company_ages) / len(company_ages)
        
        # Calculate market maturity score (0-10)
        maturity_factors = [
            min(len(competitors) / 10, 1.0) * 3,  # Number of competitors (max 3 points)
            min(indicators["market_validation"]["average_company_age"] / 10, 1.0) * 2,  # Average age (max 2 points)
            min(indicators["market_validation"]["funded_companies"] / len(competitors), 1.0) * 2,  # Funding penetration (max 2 points)
            min(indicators["company_size_distribution"]["established"] / len(competitors), 1.0) * 3  # Established companies (max 3 points)
        ]
        indicators["funding_insights"]["market_maturity_score"] = sum(maturity_factors)
        
        return indicators
    
    def _extract_competitive_landscape(self, competitors) -> Dict[str, Any]:
        """Extract competitive landscape insights"""
        landscape = {
            "market_concentration": "fragmented",  # fragmented, moderately_concentrated, highly_concentrated
            "competitive_intensity": "medium",  # low, medium, high
            "barriers_to_entry": [],
            "market_leaders": [],
            "key_differentiators": [],
            "competitive_gaps": []
        }
        
        # Analyze market concentration
        established_count = sum(1 for c in competitors if c.financial_data.employee_count and c.financial_data.employee_count > 500)
        if established_count / len(competitors) > 0.6:
            landscape["market_concentration"] = "highly_concentrated"
        elif established_count / len(competitors) > 0.3:
            landscape["market_concentration"] = "moderately_concentrated"
        
        # Identify market leaders (by funding, employees, or age)
        for competitor in competitors:
            financial = competitor.financial_data
            score = 0
            
            if financial.employee_count and financial.employee_count > 100:
                score += 2
            if financial.funding_total and any(x in financial.funding_total.lower() for x in ['million', 'billion']):
                score += 2
            if financial.founded_year and (2024 - financial.founded_year) > 5:
                score += 1
            
            if score >= 3:
                landscape["market_leaders"].append({
                    "name": competitor.basic_info.name,
                    "strength_score": score,
                    "key_strengths": competitor.strengths[:3]
                })
        
        # Extract barriers to entry from competitor data
        all_threats = []
        for competitor in competitors:
            all_threats.extend(competitor.threats)
        
        # Common barriers to entry themes
        barrier_keywords = {
            "high_capital": ["funding", "capital", "investment", "money"],
            "network_effects": ["network", "platform", "users", "community"],
            "regulatory": ["regulation", "compliance", "legal", "policy"],
            "technology": ["technology", "technical", "expertise", "development"],
            "brand": ["brand", "reputation", "trust", "established"]
        }
        
        for threat in all_threats:
            threat_lower = threat.lower()
            for barrier_type, keywords in barrier_keywords.items():
                if any(keyword in threat_lower for keyword in keywords):
                    if barrier_type not in [b["type"] for b in landscape["barriers_to_entry"]]:
                        landscape["barriers_to_entry"].append({
                            "type": barrier_type,
                            "description": threat
                        })
        
        return landscape
    
    def _extract_market_sentiment_insights(self, competitors) -> Dict[str, Any]:
        """Extract market sentiment and user behavior insights"""
        sentiment_insights = {
            "overall_market_sentiment": 0.0,
            "common_user_complaints": [],
            "common_user_praises": [],
            "market_satisfaction_level": "medium",
            "user_behavior_patterns": [],
            "improvement_opportunities": []
        }
        
        sentiment_scores = []
        all_complaints = []
        all_praises = []
        
        for competitor in competitors:
            sentiment = competitor.market_sentiment
            
            if sentiment.overall_score != 0:
                sentiment_scores.append(sentiment.overall_score)
            
            all_complaints.extend(sentiment.key_complaints)
            all_praises.extend(sentiment.key_praises)
        
        # Calculate overall market sentiment
        if sentiment_scores:
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            sentiment_insights["overall_market_sentiment"] = avg_sentiment
            
            if avg_sentiment > 0.3:
                sentiment_insights["market_satisfaction_level"] = "high"
            elif avg_sentiment < -0.3:
                sentiment_insights["market_satisfaction_level"] = "low"
        
        # Find most common complaints (opportunities for new entrants)
        complaint_counts = {}
        for complaint in all_complaints:
            complaint_lower = complaint.lower()
            for existing_complaint, count in complaint_counts.items():
                if any(word in complaint_lower for word in existing_complaint.split()[:3]):
                    complaint_counts[existing_complaint] += 1
                    break
            else:
                complaint_counts[complaint] = 1
        
        # Get top complaints
        sorted_complaints = sorted(complaint_counts.items(), key=lambda x: x[1], reverse=True)
        sentiment_insights["common_user_complaints"] = [
            {"complaint": complaint, "frequency": count} 
            for complaint, count in sorted_complaints[:5]
        ]
        
        # Extract improvement opportunities from complaints
        sentiment_insights["improvement_opportunities"] = [
            f"Address user concern: {complaint}" 
            for complaint, _ in sorted_complaints[:3]
        ]
        
        return sentiment_insights
    
    def _extract_swot_insights(self, competitors) -> Dict[str, Any]:
        """Extract SWOT-based insights for market positioning"""
        swot_insights = {
            "market_strengths": [],
            "market_weaknesses": [],
            "market_opportunities": [],
            "market_threats": [],
            "positioning_gaps": [],
            "differentiation_opportunities": []
        }
        
        # Aggregate SWOT data
        all_strengths = []
        all_weaknesses = []
        all_opportunities = []
        all_threats = []
        
        for competitor in competitors:
            all_strengths.extend(competitor.strengths)
            all_weaknesses.extend(competitor.weaknesses)
            all_opportunities.extend(competitor.opportunities)
            all_threats.extend(competitor.threats)
        
        # Find common patterns in strengths (what the market is good at)
        strength_themes = self._categorize_swot_items(all_strengths)
        swot_insights["market_strengths"] = [
            {"theme": theme, "examples": examples[:3]} 
            for theme, examples in strength_themes.items()
        ]
        
        # Find common weaknesses (areas where new entrants can differentiate)
        weakness_themes = self._categorize_swot_items(all_weaknesses)
        swot_insights["market_weaknesses"] = [
            {"theme": theme, "examples": examples[:3]} 
            for theme, examples in weakness_themes.items()
        ]
        
        # Extract positioning gaps from weaknesses
        swot_insights["positioning_gaps"] = [
            f"Opportunity to excel in: {theme}" 
            for theme in weakness_themes.keys()
        ][:5]
        
        # Extract opportunities and threats
        opportunity_themes = self._categorize_swot_items(all_opportunities)
        swot_insights["market_opportunities"] = [
            {"theme": theme, "examples": examples[:2]} 
            for theme, examples in opportunity_themes.items()
        ]
        
        threat_themes = self._categorize_swot_items(all_threats)
        swot_insights["market_threats"] = [
            {"theme": theme, "examples": examples[:2]} 
            for theme, examples in threat_themes.items()
        ]
        
        return swot_insights
    
    def _categorize_swot_items(self, items) -> Dict[str, List[str]]:
        """Categorize SWOT items into themes"""
        themes = {
            "technology": [],
            "user_experience": [],
            "pricing": [],
            "market_reach": [],
            "product_features": [],
            "customer_service": [],
            "brand_reputation": [],
            "other": []
        }
        
        keywords = {
            "technology": ["tech", "platform", "software", "algorithm", "ai", "automation"],
            "user_experience": ["ux", "ui", "user", "experience", "interface", "usability"],
            "pricing": ["price", "cost", "expensive", "cheap", "affordable", "pricing"],
            "market_reach": ["market", "reach", "expansion", "geographic", "global", "local"],
            "product_features": ["feature", "functionality", "capability", "product", "service"],
            "customer_service": ["support", "service", "help", "customer", "response"],
            "brand_reputation": ["brand", "reputation", "trust", "credibility", "image"]
        }
        
        for item in items:
            item_lower = item.lower()
            categorized = False
            
            for theme, theme_keywords in keywords.items():
                if any(keyword in item_lower for keyword in theme_keywords):
                    themes[theme].append(item)
                    categorized = True
                    break
            
            if not categorized:
                themes["other"].append(item)
        
        # Remove empty themes
        return {theme: items for theme, items in themes.items() if items}


# Create workflow instance
simple_market_sizing_workflow = SimpleMarketSizingWorkflow() 