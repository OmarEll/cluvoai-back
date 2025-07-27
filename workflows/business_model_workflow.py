import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from core.business_model_models import BusinessModelInput, BusinessModelReport
from core.analysis_models import AnalysisType
from services.business_model.business_model_report_service import business_model_report_service
from services.analysis_storage_service import analysis_storage_service


class BusinessModelWorkflow:
    """
    Workflow for generating comprehensive business model analysis
    that leverages competitive, persona, and market sizing context
    """
    
    async def run_analysis(self, analysis_input: BusinessModelInput) -> BusinessModelReport:
        """
        Run comprehensive business model analysis with intelligent context integration
        """
        try:
            print("🚀 Starting business model analysis with cross-feature context...")
            start_time = datetime.utcnow()
            
            # Step 1: Collect context from previous analyses
            context = await self._collect_existing_context(analysis_input)
            
            # Step 2: Generate comprehensive business model report
            report = await business_model_report_service.generate_comprehensive_report(
                analysis_input,
                competitive_context=context.get("competitive_analysis"),
                persona_context=context.get("persona_analysis"),
                market_sizing_context=context.get("market_sizing_analysis")
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            report.execution_time = execution_time
            
            print(f"✅ Business model analysis completed successfully in {execution_time:.2f} seconds")
            return report
            
        except Exception as e:
            print(f"Error in business model analysis: {e}")
            raise Exception(f"Business model analysis failed: {str(e)}")
    
    async def _collect_existing_context(self, analysis_input: BusinessModelInput) -> Dict[str, Any]:
        """Collect existing context from competitor, persona, and market sizing analyses"""
        context = {}
        
        try:
            print("🔍 Collecting existing analysis context for enhanced business model recommendations...")
            
            user_id = getattr(analysis_input, 'user_id', None)
            idea_id = getattr(analysis_input, 'idea_id', None)
            
            if user_id and idea_id:
                # Get competitive analysis context
                try:
                    competitor_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.COMPETITOR, include_feedback=False
                    )
                    
                    if competitor_analysis and competitor_analysis.competitor_report:
                        report = competitor_analysis.competitor_report
                        
                        # Extract comprehensive competitive intelligence
                        context["competitive_analysis"] = {
                            "total_competitors": report.total_competitors,
                            "competitors": [
                                {
                                    "name": comp.basic_info.name,
                                    "type": comp.basic_info.type.value,
                                    "pricing": {
                                        "monthly_price": comp.pricing_data.monthly_price,
                                        "pricing_model": comp.pricing_data.pricing_model,
                                        "free_tier": comp.pricing_data.free_tier,
                                        "pricing_details": comp.pricing_data.pricing_details
                                    },
                                    "financial": {
                                        "funding_total": comp.financial_data.funding_total,
                                        "employee_count": comp.financial_data.employee_count,
                                        "valuation": comp.financial_data.valuation
                                    },
                                    "strengths": comp.strengths,
                                    "weaknesses": comp.weaknesses
                                }
                                for comp in report.competitors
                            ],
                            "market_gaps": report.market_gaps,
                            "key_insights": report.key_insights,
                            "positioning_recommendations": report.positioning_recommendations,
                            
                            # Derived intelligence for business model
                            "pricing_intelligence": self._extract_pricing_intelligence(report.competitors),
                            "market_size_indicators": self._extract_market_size_indicators(report.competitors),
                            "competitive_landscape": self._extract_competitive_landscape(report.competitors)
                        }
                        print(f"✅ Found competitive analysis with {len(report.competitors)} competitors")
                        
                except Exception as e:
                    print(f"Error getting competitive context: {e}")
                
                # Get persona analysis context
                try:
                    persona_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.PERSONA, include_feedback=False
                    )
                    
                    if persona_analysis and persona_analysis.persona_report:
                        report = persona_analysis.persona_report
                        
                        context["persona_analysis"] = {
                            "personas": [
                                {
                                    "basic_info": persona.basic_info.dict(),
                                    "demographics": persona.demographics.dict(),
                                    "behavioral_patterns": persona.behavioral_patterns.dict(),
                                    "psychographics": persona.psychographics.dict(),
                                    "pain_points": persona.pain_points,
                                    "goals": persona.goals
                                }
                                for persona in report.personas
                            ],
                            "target_audience_insights": report.target_audience_insights,
                            
                            # Derived intelligence for business model
                            "pricing_sensitivity": self._extract_pricing_sensitivity(report.personas),
                            "willingness_to_pay": self._extract_willingness_to_pay(report.personas),
                            "preferred_payment_models": self._extract_payment_preferences(report.personas)
                        }
                        print(f"✅ Found persona analysis with {len(report.personas)} personas")
                        
                except Exception as e:
                    print(f"Error getting persona context: {e}")
                
                # Get market sizing context
                try:
                    market_analysis = await analysis_storage_service.get_user_analysis(
                        user_id, idea_id, AnalysisType.MARKET_SIZING, include_feedback=False
                    )
                    
                    if market_analysis and market_analysis.market_sizing_report:
                        report = market_analysis.market_sizing_report
                        
                        context["market_sizing_analysis"] = {
                            "tam_sam_som_breakdown": {
                                "tam": report.tam_sam_som_breakdown.tam,
                                "sam": report.tam_sam_som_breakdown.sam,
                                "som": report.tam_sam_som_breakdown.som
                            },
                            "competitive_position": {
                                "market_gaps": report.competitive_position.market_gaps,
                                "competitive_advantages": report.competitive_position.competitive_advantages,
                                "barrier_to_entry": report.competitive_position.barrier_to_entry
                            },
                            "market_trends": report.market_trends.dict() if report.market_trends else {},
                            "revenue_projections": [proj.dict() for proj in report.revenue_projections],
                            
                            # Derived intelligence for business model
                            "market_benchmarks": self._extract_market_benchmarks(report),
                            "revenue_opportunity": self._calculate_revenue_opportunity(report)
                        }
                        print(f"✅ Found market sizing analysis with TAM: ${report.tam_sam_som_breakdown.tam:,.0f}")
                        
                except Exception as e:
                    print(f"Error getting market sizing context: {e}")
            
        except Exception as e:
            print(f"Error collecting existing context: {e}")
        
        return context
    
    def _extract_pricing_intelligence(self, competitors) -> Dict[str, Any]:
        """Extract pricing intelligence from competitors for business model recommendations"""
        pricing_data = {
            "subscription_prices": [],
            "one_time_prices": [],
            "freemium_count": 0,
            "pricing_models": set(),
            "average_price": 0
        }
        
        total_prices = []
        
        for competitor in competitors:
            pricing = competitor.pricing_data
            
            if pricing.monthly_price:
                total_prices.append(pricing.monthly_price)
                pricing_data["subscription_prices"].append(pricing.monthly_price)
            
            if pricing.free_tier:
                pricing_data["freemium_count"] += 1
            
            if pricing.pricing_model:
                pricing_data["pricing_models"].add(pricing.pricing_model)
        
        if total_prices:
            pricing_data["average_price"] = sum(total_prices) / len(total_prices)
            pricing_data["price_range"] = {"min": min(total_prices), "max": max(total_prices)}
        
        pricing_data["pricing_models"] = list(pricing_data["pricing_models"])
        
        return pricing_data
    
    def _extract_market_size_indicators(self, competitors) -> Dict[str, Any]:
        """Extract market size indicators from competitor data"""
        indicators = {
            "total_funding": 0,
            "total_employees": 0,
            "funded_companies": 0,
            "average_company_age": 0
        }
        
        total_funding = 0
        total_employees = 0
        company_ages = []
        current_year = 2024
        
        for competitor in competitors:
            financial = competitor.financial_data
            
            if financial.funding_total:
                try:
                    # Simple funding extraction
                    funding_str = financial.funding_total.lower().replace('$', '').replace(',', '')
                    if 'm' in funding_str:
                        amount = float(funding_str.split('m')[0]) * 1_000_000
                        total_funding += amount
                        indicators["funded_companies"] += 1
                except:
                    pass
            
            if financial.employee_count:
                total_employees += financial.employee_count
            
            if financial.founded_year:
                company_ages.append(current_year - financial.founded_year)
        
        indicators["total_funding"] = total_funding
        indicators["total_employees"] = total_employees
        indicators["average_company_age"] = sum(company_ages) / len(company_ages) if company_ages else 0
        
        return indicators
    
    def _extract_competitive_landscape(self, competitors) -> Dict[str, Any]:
        """Extract competitive landscape insights"""
        landscape = {
            "market_concentration": "fragmented",
            "dominant_players": [],
            "common_weaknesses": [],
            "market_opportunities": []
        }
        
        # Identify dominant players
        for competitor in competitors:
            financial = competitor.financial_data
            score = 0
            
            if financial.employee_count and financial.employee_count > 100:
                score += 2
            if financial.funding_total and 'million' in financial.funding_total.lower():
                score += 2
            
            if score >= 3:
                landscape["dominant_players"].append(competitor.basic_info.name)
        
        # Extract common weaknesses (opportunities)
        all_weaknesses = []
        for competitor in competitors:
            all_weaknesses.extend(competitor.weaknesses)
        
        # Find most common weaknesses
        weakness_counts = {}
        for weakness in all_weaknesses:
            for existing_weakness in weakness_counts:
                if any(word in weakness.lower() for word in existing_weakness.lower().split()[:3]):
                    weakness_counts[existing_weakness] += 1
                    break
            else:
                weakness_counts[weakness] = 1
        
        # Get top weaknesses as opportunities
        sorted_weaknesses = sorted(weakness_counts.items(), key=lambda x: x[1], reverse=True)
        landscape["market_opportunities"] = [weakness for weakness, count in sorted_weaknesses[:3]]
        
        return landscape
    
    def _extract_pricing_sensitivity(self, personas) -> Dict[str, Any]:
        """Extract pricing sensitivity insights from personas"""
        sensitivity_data = {
            "high_sensitivity_count": 0,
            "medium_sensitivity_count": 0,
            "low_sensitivity_count": 0,
            "price_conscious_segments": []
        }
        
        for persona in personas:
            # Simple heuristic based on demographics
            if hasattr(persona, 'demographics') and persona.demographics:
                income = persona.demographics.income_range or ""
                if "low" in income.lower() or "budget" in persona.basic_info.name.lower():
                    sensitivity_data["high_sensitivity_count"] += 1
                    sensitivity_data["price_conscious_segments"].append(persona.basic_info.name)
                elif "high" in income.lower() or "premium" in persona.basic_info.name.lower():
                    sensitivity_data["low_sensitivity_count"] += 1
                else:
                    sensitivity_data["medium_sensitivity_count"] += 1
        
        return sensitivity_data
    
    def _extract_willingness_to_pay(self, personas) -> Dict[str, Any]:
        """Extract willingness to pay insights from personas"""
        willingness_data = {
            "estimated_ranges": {},
            "payment_triggers": [],
            "value_drivers": []
        }
        
        for persona in personas:
            # Extract value drivers from goals and pain points
            if hasattr(persona, 'goals'):
                willingness_data["value_drivers"].extend(persona.goals[:2])
            
            if hasattr(persona, 'pain_points'):
                willingness_data["payment_triggers"].extend(persona.pain_points[:2])
        
        return willingness_data
    
    def _extract_payment_preferences(self, personas) -> Dict[str, Any]:
        """Extract payment model preferences from personas"""
        preferences = {
            "subscription_friendly": 0,
            "one_time_preferred": 0,
            "freemium_interested": 0
        }
        
        for persona in personas:
            # Simple heuristics based on persona characteristics
            if hasattr(persona, 'behavioral_patterns') and persona.behavioral_patterns:
                # Assume tech-savvy personas prefer subscriptions
                if "tech" in persona.basic_info.name.lower() or "digital" in persona.basic_info.title.lower():
                    preferences["subscription_friendly"] += 1
                # Budget-conscious might prefer one-time
                elif "budget" in persona.basic_info.name.lower():
                    preferences["one_time_preferred"] += 1
                else:
                    preferences["freemium_interested"] += 1
        
        return preferences
    
    def _extract_market_benchmarks(self, market_report) -> Dict[str, Any]:
        """Extract market benchmarks from market sizing report"""
        benchmarks = {
            "market_growth_potential": "medium",
            "competitive_intensity": "medium",
            "revenue_potential": "medium"
        }
        
        # Analyze TAM/SAM/SOM ratios
        breakdown = market_report.tam_sam_som_breakdown
        
        if breakdown.tam > 1_000_000_000:  # $1B+
            benchmarks["market_growth_potential"] = "high"
        elif breakdown.tam > 100_000_000:  # $100M+
            benchmarks["market_growth_potential"] = "medium"
        else:
            benchmarks["market_growth_potential"] = "low"
        
        # Analyze competitive position
        position = market_report.competitive_position
        if len(position.competitive_advantages) > len(position.barrier_to_entry):
            benchmarks["competitive_intensity"] = "low"
        elif len(position.barrier_to_entry) > 3:
            benchmarks["competitive_intensity"] = "high"
        
        return benchmarks
    
    def _calculate_revenue_opportunity(self, market_report) -> Dict[str, Any]:
        """Calculate revenue opportunity from market sizing"""
        breakdown = market_report.tam_sam_som_breakdown
        
        return {
            "addressable_market": breakdown.sam,
            "obtainable_market": breakdown.som,
            "market_penetration_potential": (breakdown.som / breakdown.sam * 100) if breakdown.sam > 0 else 0,
            "revenue_projections_available": len(market_report.revenue_projections) > 0
        }


# Create workflow instance
business_model_workflow = BusinessModelWorkflow() 