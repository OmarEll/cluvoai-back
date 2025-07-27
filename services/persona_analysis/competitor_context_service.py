from typing import Optional, Dict, Any, List
from datetime import datetime

from core.analysis_models import AnalysisType
from core.competitor_models import CompetitorReport
from services.analysis_storage_service import analysis_storage_service


class CompetitorContextService:
    """Service to extract competitor insights for enhanced persona generation"""
    
    async def get_competitor_context_for_idea(
        self, 
        user_id: str, 
        idea_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get competitor analysis context for a business idea to enhance persona generation
        """
        try:
            # Get the most recent competitor analysis for this idea
            competitor_analysis = await analysis_storage_service.get_user_analysis(
                user_id=user_id,
                idea_id=idea_id,
                analysis_type=AnalysisType.COMPETITOR,
                include_feedback=False
            )
            
            if not competitor_analysis or not competitor_analysis.competitor_report:
                return None
            
            report = competitor_analysis.competitor_report
            
            # Extract key insights for persona generation
            context = {
                "has_competitor_data": True,
                "analysis_date": competitor_analysis.created_at.isoformat() if competitor_analysis.created_at else None,
                "competitor_insights": self._extract_competitor_insights(report),
                "market_intelligence": self._extract_market_intelligence(report),
                "user_behavior_insights": self._extract_user_behavior_insights(report),
                "positioning_opportunities": self._extract_positioning_opportunities(report)
            }
            
            return context
            
        except Exception as e:
            print(f"Error getting competitor context: {e}")
            return None
    
    def _extract_competitor_insights(self, report: CompetitorReport) -> Dict[str, Any]:
        """Extract competitor-specific insights for persona generation"""
        insights = {
            "total_competitors": len(report.competitors) if report.competitors else 0,
            "competitor_targets": [],
            "competitor_strategies": [],
            "user_feedback_patterns": []
        }
        
        if report.competitors:
            for competitor in report.competitors:
                company_name = competitor.basic_info.name if competitor.basic_info else "Unknown Company"
                
                # Extract user feedback from market sentiment
                if competitor.market_sentiment:
                    if competitor.market_sentiment.key_complaints:
                        insights["user_feedback_patterns"].append({
                            "company": company_name,
                            "complaints": competitor.market_sentiment.key_complaints
                        })
                    if competitor.market_sentiment.key_praises:
                        insights["user_feedback_patterns"].append({
                            "company": company_name,
                            "praises": competitor.market_sentiment.key_praises
                        })
                
                # Extract strengths and weaknesses as strategies
                if competitor.strengths:
                    insights["competitor_strategies"].append({
                        "company": company_name,
                        "strengths": competitor.strengths
                    })
                
                # Extract company description as target audience context
                if competitor.basic_info and competitor.basic_info.description:
                    insights["competitor_targets"].append({
                        "company": company_name,
                        "description": competitor.basic_info.description,
                        "type": competitor.basic_info.type
                    })
        
        return insights
    
    def _extract_market_intelligence(self, report: CompetitorReport) -> Dict[str, Any]:
        """Extract market intelligence for persona context"""
        intelligence = {
            "market_gaps": [],
            "pricing_insights": [],
            "feature_demands": []
        }
        
        # Extract from market gaps analysis
        if hasattr(report, 'market_gaps') and report.market_gaps:
            for gap in report.market_gaps:
                intelligence["market_gaps"].append({
                    "opportunity": gap.opportunity_description if hasattr(gap, 'opportunity_description') else str(gap),
                    "target_segment": gap.target_segment if hasattr(gap, 'target_segment') else None,
                    "market_size": gap.estimated_market_size if hasattr(gap, 'estimated_market_size') else None
                })
        
        # Extract pricing patterns
        if report.competitors:
            for competitor in report.competitors:
                company_name = competitor.basic_info.name if competitor.basic_info else "Unknown Company"
                if competitor.pricing_data and (competitor.pricing_data.monthly_price or competitor.pricing_data.pricing_model):
                    intelligence["pricing_insights"].append({
                        "company": company_name,
                        "monthly_price": competitor.pricing_data.monthly_price,
                        "pricing_model": competitor.pricing_data.pricing_model,
                        "free_tier": competitor.pricing_data.free_tier
                    })
        
        return intelligence
    
    def _extract_user_behavior_insights(self, report: CompetitorReport) -> Dict[str, Any]:
        """Extract user behavior insights from competitor analysis"""
        behavior_insights = {
            "user_pain_points": [],
            "preferred_features": [],
            "engagement_patterns": [],
            "social_media_behavior": []
        }
        
        # Extract pain points from competitor market sentiment
        if report.competitors:
            for competitor in report.competitors:
                company_name = competitor.basic_info.name if competitor.basic_info else "Unknown Company"
                
                # Extract pain points from complaints
                if competitor.market_sentiment and competitor.market_sentiment.key_complaints:
                    behavior_insights["user_pain_points"].extend(competitor.market_sentiment.key_complaints)
                
                # Extract preferred features from praises
                if competitor.market_sentiment and competitor.market_sentiment.key_praises:
                    behavior_insights["preferred_features"].extend(competitor.market_sentiment.key_praises)
                
                # Extract weaknesses as additional pain points
                if competitor.weaknesses:
                    behavior_insights["user_pain_points"].extend([f"Competitor weakness: {w}" for w in competitor.weaknesses])
                
                # Extract strengths as preferred features
                if competitor.strengths:
                    behavior_insights["preferred_features"].extend([f"Competitor strength: {s}" for s in competitor.strengths])
        
        return behavior_insights
    
    def _extract_positioning_opportunities(self, report: CompetitorReport) -> Dict[str, Any]:
        """Extract positioning opportunities for persona targeting"""
        opportunities = {
            "underserved_segments": [],
            "differentiation_opportunities": [],
            "messaging_gaps": []
        }
        
        # Extract from individual competitor opportunities and threats
        if report.competitors:
            for competitor in report.competitors:
                company_name = competitor.basic_info.name if competitor.basic_info else "Unknown Company"
                
                # Extract opportunities as differentiation opportunities
                if competitor.opportunities:
                    for opp in competitor.opportunities:
                        opportunities["differentiation_opportunities"].append(f"{company_name}: {opp}")
                
                # Extract threats as potential underserved segments
                if competitor.threats:
                    for threat in competitor.threats:
                        if "underserved" in str(threat).lower() or "gap" in str(threat).lower():
                            opportunities["underserved_segments"].append(f"{company_name}: {threat}")
        
        # Extract from market gaps
        if hasattr(report, 'market_gaps') and report.market_gaps:
            for gap in report.market_gaps:
                opportunities["differentiation_opportunities"].append(f"Market gap: {gap.description}")
                opportunities["underserved_segments"].append(f"Gap in {gap.category}: {gap.description}")
        
        return opportunities
    
    def format_context_for_prompt(self, context: Optional[Dict[str, Any]]) -> str:
        """Format competitor context for use in persona generation prompts"""
        if not context or not context.get("has_competitor_data"):
            return "No competitor analysis data available. Generate personas based on business idea and market research."
        
        formatted = ["**COMPETITOR ANALYSIS CONTEXT:**"]
        
        # Add competitor insights
        competitor_insights = context.get("competitor_insights", {})
        if competitor_insights.get("total_competitors", 0) > 0:
            formatted.append(f"- Found {competitor_insights['total_competitors']} key competitors")
            
            if competitor_insights.get("competitor_targets"):
                formatted.append("- Competitor Target Audiences:")
                for target in competitor_insights["competitor_targets"]:
                    formatted.append(f"  * {target['company']}: {target['target_audience']}")
            
            if competitor_insights.get("competitor_strategies"):
                formatted.append("- Competitor Marketing Strategies:")
                for strategy in competitor_insights["competitor_strategies"]:
                    formatted.append(f"  * {strategy['company']}: {strategy['strategy']}")
        
        # Add user behavior insights
        behavior_insights = context.get("user_behavior_insights", {})
        if behavior_insights.get("user_pain_points"):
            formatted.append("- User Pain Points (from competitor feedback):")
            for pain_point in behavior_insights["user_pain_points"][:5]:  # Limit to top 5
                formatted.append(f"  * {pain_point}")
        
        if behavior_insights.get("preferred_features"):
            formatted.append("- User-Preferred Features:")
            for feature in behavior_insights["preferred_features"][:5]:  # Limit to top 5
                formatted.append(f"  * {feature}")
        
        # Add market intelligence
        market_intel = context.get("market_intelligence", {})
        if market_intel.get("market_gaps"):
            formatted.append("- Market Gaps/Opportunities:")
            for gap in market_intel["market_gaps"]:
                formatted.append(f"  * {gap['opportunity']}")
                if gap.get("target_segment"):
                    formatted.append(f"    Target: {gap['target_segment']}")
        
        # Add positioning opportunities
        positioning = context.get("positioning_opportunities", {})
        if positioning.get("differentiation_opportunities"):
            formatted.append("- Differentiation Opportunities:")
            for opp in positioning["differentiation_opportunities"][:3]:  # Limit to top 3
                formatted.append(f"  * {opp}")
        
        formatted.append("\n**USE THIS CONTEXT TO:**")
        formatted.append("1. Create more accurate personas based on real competitor data")
        formatted.append("2. Identify underserved user segments")
        formatted.append("3. Understand actual user pain points and preferences")
        formatted.append("4. Develop differentiated positioning strategies")
        formatted.append("5. Leverage gaps in competitor approaches")
        
        return "\n".join(formatted)


# Create global instance
competitor_context_service = CompetitorContextService() 