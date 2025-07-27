import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
import math

from core.business_model_models import (
    BusinessModelInput, ProfitabilityProjection, RevenueModelRecommendation
)
from config.settings import settings


class ProfitabilitySimulationService:
    """
    Service for calculating profitability projections and break-even analysis
    using real market data and competitive intelligence
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.1
        )
        self.parser = JsonOutputParser()
        
        # Create the profitability analysis prompt
        self.profitability_prompt = ChatPromptTemplate.from_template("""
        You are a financial analyst specializing in business model profitability.
        
        Business Context:
        Business Idea: {business_idea}
        Target Market: {target_market}
        Industry: {industry}
        Estimated Users: {estimated_users}
        Development Cost: ${development_cost}
        Monthly Operational Cost: ${operational_cost}
        
        Revenue Model:
        Model Type: {revenue_model_type}
        Price Point: ${price_point}
        
        Market Intelligence:
        {market_intelligence}
        
        Calculate realistic profitability projections considering:
        1. Customer acquisition costs from industry benchmarks
        2. Churn rates typical for this industry and model
        3. Market penetration realistic growth rates
        4. Operational scaling costs
        5. Competitive pricing pressure
        
        Provide projections for 3 scenarios: Conservative, Realistic, Optimistic
        
        For each scenario, calculate:
        - Monthly user growth rate
        - Monthly revenue (considering churn)
        - Monthly costs (including CAC, operational, development)
        - Monthly profit/loss
        - Break-even timeline
        - Customer lifetime value
        - Return on investment
        
        Return as JSON array of 3 profitability projections.
        """)
    
    async def calculate_profitability_projections(
        self,
        business_input: BusinessModelInput,
        revenue_model: RevenueModelRecommendation,
        market_intelligence: Optional[Dict[str, Any]] = None
    ) -> List[ProfitabilityProjection]:
        """
        Calculate profitability projections using AI and market data
        """
        try:
            print("💰 Calculating profitability projections with market intelligence...")
            
            # Format market intelligence
            market_intel = self._format_market_intelligence(market_intelligence)
            
            # Generate AI-powered projections
            ai_projections = await self._generate_ai_projections(
                business_input, revenue_model, market_intel
            )
            
            # Calculate detailed financial projections
            projections = []
            scenarios = ["conservative", "realistic", "optimistic"]
            
            for i, scenario in enumerate(scenarios):
                try:
                    projection_data = ai_projections[i] if i < len(ai_projections) else {}
                    
                    projection = await self._calculate_scenario_projection(
                        business_input, revenue_model, scenario, projection_data, market_intelligence
                    )
                    projections.append(projection)
                    
                except Exception as e:
                    print(f"Error calculating {scenario} projection: {e}")
                    # Create fallback projection
                    fallback = self._create_fallback_projection(business_input, revenue_model, scenario)
                    projections.append(fallback)
            
            print(f"✅ Generated {len(projections)} profitability scenarios")
            return projections
            
        except Exception as e:
            print(f"Error calculating profitability projections: {e}")
            return self._create_fallback_projections(business_input, revenue_model)
    
    async def _generate_ai_projections(
        self,
        business_input: BusinessModelInput,
        revenue_model: RevenueModelRecommendation,
        market_intelligence: str
    ) -> List[Dict[str, Any]]:
        """Generate AI-powered profitability projections"""
        try:
            chain = self.profitability_prompt | self.llm | self.parser
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_input.business_idea,
                    "target_market": business_input.target_market,
                    "industry": business_input.industry,
                    "estimated_users": business_input.estimated_users or "Not specified",
                    "development_cost": business_input.development_cost or 50000,
                    "operational_cost": business_input.operational_cost_monthly or 5000,
                    "revenue_model_type": revenue_model.model_type.value,
                    "price_point": revenue_model.recommended_price or 29.99,
                    "market_intelligence": market_intelligence
                }
            )
            
            return result if isinstance(result, list) else []
            
        except Exception as e:
            print(f"Error generating AI projections: {e}")
            return []
    
    async def _calculate_scenario_projection(
        self,
        business_input: BusinessModelInput,
        revenue_model: RevenueModelRecommendation,
        scenario: str,
        ai_data: Dict[str, Any],
        market_intelligence: Optional[Dict[str, Any]]
    ) -> ProfitabilityProjection:
        """Calculate detailed projection for a specific scenario"""
        
        # Base parameters
        price = revenue_model.recommended_price or 29.99
        initial_users = business_input.estimated_users or 100
        dev_cost = business_input.development_cost or 50000
        monthly_operational = business_input.operational_cost_monthly or 5000
        
        # Scenario multipliers
        scenario_multipliers = {
            "conservative": {"growth": 0.5, "churn": 1.5, "cac": 1.3},
            "realistic": {"growth": 1.0, "churn": 1.0, "cac": 1.0},
            "optimistic": {"growth": 2.0, "churn": 0.7, "cac": 0.8}
        }
        
        multiplier = scenario_multipliers[scenario]
        
        # Extract market-based parameters
        market_cac = self._extract_market_cac(market_intelligence)
        market_churn = self._extract_market_churn(market_intelligence)
        
        # Calculate scenario-specific parameters
        monthly_growth_rate = ai_data.get("monthly_growth_rate", 0.1) * multiplier["growth"]
        monthly_churn_rate = market_churn * multiplier["churn"]
        customer_acquisition_cost = market_cac * multiplier["cac"]
        
        # Project 12 months out
        months = 12
        users = initial_users
        total_acquisition_cost = 0
        
        for month in range(months):
            # User growth
            new_users = users * monthly_growth_rate
            churned_users = users * monthly_churn_rate
            users = max(0, users + new_users - churned_users)
            
            # Acquisition costs
            total_acquisition_cost += new_users * customer_acquisition_cost
        
        # Calculate final projections
        monthly_revenue = users * price
        annual_revenue = monthly_revenue * 12
        
        # Costs
        monthly_costs = monthly_operational + (users * monthly_growth_rate * customer_acquisition_cost)
        annual_costs = (monthly_operational * 12) + dev_cost + total_acquisition_cost
        
        # Profits
        monthly_profit = monthly_revenue - monthly_costs
        annual_profit = annual_revenue - annual_costs
        
        # Break-even calculations
        break_even_months = self._calculate_break_even_months(
            price, monthly_operational, customer_acquisition_cost, 
            monthly_growth_rate, monthly_churn_rate, dev_cost
        )
        
        break_even_users = max(1, int(monthly_costs / price)) if price > 0 else 1000
        
        # ROI calculation
        roi_percentage = (annual_profit / max(1, annual_costs)) * 100 if annual_costs > 0 else 0
        
        return ProfitabilityProjection(
            monthly_revenue=monthly_revenue,
            annual_revenue=annual_revenue,
            monthly_costs=monthly_costs,
            annual_costs=annual_costs,
            monthly_profit=monthly_profit,
            annual_profit=annual_profit,
            break_even_months=break_even_months,
            break_even_users=break_even_users,
            roi_percentage=roi_percentage
        )
    
    def _format_market_intelligence(self, market_intelligence: Optional[Dict[str, Any]]) -> str:
        """Format market intelligence for AI prompt"""
        if not market_intelligence:
            return "No market intelligence available."
        
        intel_parts = []
        
        # Market benchmarks
        if "market_benchmarks" in market_intelligence:
            benchmarks = market_intelligence["market_benchmarks"]
            if benchmarks.get("industry_cac"):
                intel_parts.append(f"Industry CAC: ${benchmarks['industry_cac']:.2f}")
            if benchmarks.get("industry_ltv"):
                intel_parts.append(f"Industry LTV: ${benchmarks['industry_ltv']:.2f}")
            if benchmarks.get("industry_churn_rate"):
                intel_parts.append(f"Industry churn rate: {benchmarks['industry_churn_rate']:.1%}")
        
        # Competitive pricing insights
        if "pricing_intelligence" in market_intelligence:
            pricing = market_intelligence["pricing_intelligence"]
            if pricing.get("average_pricing", {}).get("monthly_subscription"):
                avg_price = pricing["average_pricing"]["monthly_subscription"]
                intel_parts.append(f"Average competitor pricing: ${avg_price:.2f}/month")
        
        return "\n".join(intel_parts) if intel_parts else "Limited market intelligence."
    
    def _extract_market_cac(self, market_intelligence: Optional[Dict[str, Any]]) -> float:
        """Extract customer acquisition cost from market data"""
        if market_intelligence and "market_benchmarks" in market_intelligence:
            benchmarks = market_intelligence["market_benchmarks"]
            return benchmarks.get("industry_cac", 50.0)
        return 50.0  # Default CAC
    
    def _extract_market_churn(self, market_intelligence: Optional[Dict[str, Any]]) -> float:
        """Extract churn rate from market data"""
        if market_intelligence and "market_benchmarks" in market_intelligence:
            benchmarks = market_intelligence["market_benchmarks"]
            return benchmarks.get("industry_churn_rate", 0.05)
        return 0.05  # Default 5% monthly churn
    
    def _calculate_break_even_months(
        self, price: float, monthly_operational: float, cac: float,
        growth_rate: float, churn_rate: float, dev_cost: float
    ) -> int:
        """Calculate break-even timeline using financial modeling"""
        try:
            # Simplified break-even calculation
            # This is a complex calculation that would need more sophisticated modeling
            # For now, using a simplified approach
            
            monthly_profit_per_user = price - (cac / 12) - (monthly_operational / 100)  # Rough estimate
            
            if monthly_profit_per_user <= 0:
                return 24  # If no profit per user, assume 2 years to break even
            
            months_to_break_even = dev_cost / monthly_profit_per_user / growth_rate
            return max(1, min(60, int(months_to_break_even)))  # Cap between 1-60 months
            
        except:
            return 12  # Default 12 months
    
    def _create_fallback_projection(
        self, business_input: BusinessModelInput, revenue_model: RevenueModelRecommendation, scenario: str
    ) -> ProfitabilityProjection:
        """Create fallback projection when AI generation fails"""
        price = revenue_model.recommended_price or 29.99
        users = business_input.estimated_users or 100
        
        # Simple scenario-based calculations
        scenario_multipliers = {
            "conservative": 0.5,
            "realistic": 1.0,
            "optimistic": 1.5
        }
        
        multiplier = scenario_multipliers.get(scenario, 1.0)
        
        monthly_revenue = users * price * multiplier
        annual_revenue = monthly_revenue * 12
        monthly_costs = (business_input.operational_cost_monthly or 5000) * (1 + multiplier * 0.2)
        annual_costs = monthly_costs * 12 + (business_input.development_cost or 50000)
        
        return ProfitabilityProjection(
            monthly_revenue=monthly_revenue,
            annual_revenue=annual_revenue,
            monthly_costs=monthly_costs,
            annual_costs=annual_costs,
            monthly_profit=monthly_revenue - monthly_costs,
            annual_profit=annual_revenue - annual_costs,
            break_even_months=int(12 / multiplier),
            break_even_users=int(monthly_costs / price) if price > 0 else 100,
            roi_percentage=(annual_revenue - annual_costs) / annual_costs * 100 if annual_costs > 0 else 0
        )
    
    def _create_fallback_projections(
        self, business_input: BusinessModelInput, revenue_model: RevenueModelRecommendation
    ) -> List[ProfitabilityProjection]:
        """Create fallback projections for all scenarios"""
        return [
            self._create_fallback_projection(business_input, revenue_model, "conservative"),
            self._create_fallback_projection(business_input, revenue_model, "realistic"),
            self._create_fallback_projection(business_input, revenue_model, "optimistic")
        ]


# Create singleton instance
profitability_service = ProfitabilitySimulationService() 