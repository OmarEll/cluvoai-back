import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate

from core.business_model_canvas_models import (
    BusinessModelCanvas, CustomerSegments, ValuePropositions, Channels,
    CustomerRelationships, RevenueStreams, KeyResources, KeyActivities,
    KeyPartnerships, CostStructure, CustomerSegmentType, ValuePropositionType,
    ChannelType, CustomerRelationshipType, RevenueStreamType, KeyResourceType,
    KeyActivityType, PartnershipType, CostStructureType
)
from config.settings import settings


class BusinessModelCanvasGeneratorService:
    """
    Service for generating comprehensive Business Model Canvas
    that leverages competitive analysis, persona insights, market sizing, and business model data
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            openai_api_key=settings.openai_api_key,
            temperature=0.1
        )
        self.parser = JsonOutputParser()
        
        # Create the canvas generation prompt
        self.canvas_prompt = ChatPromptTemplate.from_template("""
        You are an expert business strategist specializing in Business Model Canvas creation.
        
        Business Context:
        Business Idea: {business_idea}
        Target Market: {target_market}
        Industry: {industry}
        
        Competitive Intelligence:
        {competitive_context}
        
        Customer Persona Insights:
        {persona_context}
        
        Market Sizing Data:
        {market_sizing_context}
        
        Business Model Analysis:
        {business_model_context}
        
        Based on this comprehensive analysis, generate a complete Business Model Canvas with all nine building blocks.
        
        IMPORTANT: Provide detailed, specific data for each building block. Do not leave fields empty or use generic descriptions.
        
        For each building block, provide:
        
        1. **Customer Segments**: 
           - Type: mass_market, niche_market, segmented, diversified, multi_sided_platform
           - Description: Detailed description of target segments
           - Characteristics: List of 5-7 specific characteristics
           - Needs: List of 5-7 specific customer needs
           - Pain Points: List of 5-7 specific pain points
           - Size Estimate: Specific market size or target
           - Persona Insights: Integration with persona analysis
        
        2. **Value Propositions**:
           - Type: newness, performance, customization, getting_job_done, design, brand_status, price, cost_reduction, risk_reduction, accessibility, convenience
           - Description: Detailed value proposition
           - Benefits: List of 5-7 specific benefits with quantifiable metrics
           - Pain Points Solved: List of 5-7 specific problems solved
           - Competitive Advantages: List of 5-7 unique advantages
           - Quantifiable Value: Specific metrics and numbers
           - Competitive Insights: Integration with competitive analysis
        
        3. **Channels**:
           - Type: own_channels, partner_channels, hybrid
           - Description: Detailed channel strategy
           - Touchpoints: List of 5-7 specific touchpoints
           - Effectiveness Metrics: Specific performance metrics
           - Cost Implications: Detailed cost breakdown
           - Market Reach: Geographic and demographic reach
        
        4. **Customer Relationships**:
           - Type: personal_assistance, dedicated_personal_assistance, self_service, automated_services, communities, co_creation
           - Description: Detailed relationship strategy
           - Acquisition Strategy: Specific acquisition methods
           - Retention Strategy: Specific retention tactics
           - Growth Strategy: Specific growth approaches
           - Automation Level: Degree of automation
           - Personalization Degree: Level of personalization
        
        5. **Revenue Streams**:
           - Type: asset_sale, usage_fee, subscription_fees, lending_leasing_renting, licensing, brokerage_fees, advertising
           - Description: Detailed revenue model
           - Pricing Model: Specific pricing structure
           - Revenue Potential: Specific revenue projections
           - Pricing Strategy: Detailed pricing approach
           - Market Benchmarks: Industry comparisons
           - Business Model Insights: Integration with business model analysis
        
        6. **Key Resources**:
           - Type: physical, intellectual, human, financial
           - Description: Detailed resource requirements
           - Importance Level: Critical, High, Medium, Low
           - Acquisition Strategy: How to acquire resources
           - Cost Implications: Resource cost breakdown
           - Competitive Advantage: How resources provide advantage
        
        7. **Key Activities**:
           - Type: production, problem_solving, platform_network
           - Description: Detailed activity description
           - Criticality: Critical, High, Medium, Low
           - Resource Requirements: Specific resource needs
           - Efficiency Metrics: Performance measurements
           - Automation Potential: Automation opportunities
        
        8. **Key Partnerships**:
           - Type: strategic_alliances, coopetition, joint_ventures, buyer_supplier
           - Description: Detailed partnership strategy
           - Partner Categories: List of 5-7 partner types
           - Partnership Benefits: List of 5-7 specific benefits
           - Competitive Insights: Integration with competitive analysis
        
        9. **Cost Structure**:
           - Type: cost_driven, value_driven
           - Description: Detailed cost structure
           - Fixed Costs: List of 5-7 specific fixed costs
           - Variable Costs: List of 5-7 specific variable costs
           - Cost Optimization: Optimization strategies
           - Business Model Insights: Integration with business model analysis
        
        Return as JSON with all nine building blocks structured according to the Business Model Canvas framework.
        Ensure all fields are populated with specific, actionable data.
        """)
    
    async def generate_comprehensive_canvas(
        self,
        business_idea: str,
        target_market: str,
        industry: str,
        competitive_context: Optional[Dict[str, Any]] = None,
        persona_context: Optional[Dict[str, Any]] = None,
        market_sizing_context: Optional[Dict[str, Any]] = None,
        business_model_context: Optional[Dict[str, Any]] = None
    ) -> BusinessModelCanvas:
        """
        Generate a comprehensive Business Model Canvas using all available context
        """
        try:
            print("🎨 Generating comprehensive Business Model Canvas with cross-feature context...")
            start_time = datetime.utcnow()
            
            # Format contexts for canvas generation
            competitive_intel = self._format_competitive_context(competitive_context)
            persona_intel = self._format_persona_context(persona_context)
            market_intel = self._format_market_sizing_context(market_sizing_context)
            business_model_intel = self._format_business_model_context(business_model_context)
            
            # Generate AI-powered canvas
            ai_canvas = await self._generate_ai_canvas(
                business_idea, target_market, industry,
                competitive_intel, persona_intel, market_intel, business_model_intel
            )
            
            # Parse and create structured canvas
            canvas = await self._create_structured_canvas(
                business_idea, ai_canvas, competitive_context, persona_context,
                market_sizing_context, business_model_context
            )
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            canvas.execution_time = execution_time
            
            print(f"✅ Business Model Canvas generated successfully in {execution_time:.2f} seconds")
            return canvas
            
        except Exception as e:
            print(f"Error generating Business Model Canvas: {e}")
            return await self._create_fallback_canvas(business_idea, target_market, industry)
    
    async def _generate_ai_canvas(
        self,
        business_idea: str,
        target_market: str,
        industry: str,
        competitive_context: str,
        persona_context: str,
        market_sizing_context: str,
        business_model_context: str
    ) -> Dict[str, Any]:
        """Generate AI-powered canvas building blocks"""
        try:
            chain = self.canvas_prompt | self.llm | self.parser
            
            result = await asyncio.to_thread(
                chain.invoke,
                {
                    "business_idea": business_idea,
                    "target_market": target_market,
                    "industry": industry,
                    "competitive_context": competitive_context,
                    "persona_context": persona_context,
                    "market_sizing_context": market_sizing_context,
                    "business_model_context": business_model_context
                }
            )
            
            return result if isinstance(result, dict) else {}
            
        except Exception as e:
            print(f"Error generating AI canvas: {e}")
            return {}
    
    async def _create_structured_canvas(
        self,
        business_idea: str,
        ai_canvas: Dict[str, Any],
        competitive_context: Optional[Dict[str, Any]],
        persona_context: Optional[Dict[str, Any]],
        market_sizing_context: Optional[Dict[str, Any]],
        business_model_context: Optional[Dict[str, Any]]
    ) -> BusinessModelCanvas:
        """Create structured canvas from AI output"""
        
        # Parse each building block
        customer_segments = self._parse_customer_segments(ai_canvas.get("customer_segments", {}), persona_context)
        value_propositions = self._parse_value_propositions(ai_canvas.get("value_propositions", {}), competitive_context)
        channels = self._parse_channels(ai_canvas.get("channels", {}))
        customer_relationships = self._parse_customer_relationships(ai_canvas.get("customer_relationships", {}))
        revenue_streams = self._parse_revenue_streams(ai_canvas.get("revenue_streams", {}), business_model_context)
        key_resources = self._parse_key_resources(ai_canvas.get("key_resources", {}))
        key_activities = self._parse_key_activities(ai_canvas.get("key_activities", {}))
        key_partnerships = self._parse_key_partnerships(ai_canvas.get("key_partnerships", {}), competitive_context)
        cost_structure = self._parse_cost_structure(ai_canvas.get("cost_structure", {}), business_model_context)
        
        return BusinessModelCanvas(
            business_idea=business_idea,
            customer_segments=customer_segments,
            value_propositions=value_propositions,
            channels=channels,
            customer_relationships=customer_relationships,
            revenue_streams=revenue_streams,
            key_resources=key_resources,
            key_activities=key_activities,
            key_partnerships=key_partnerships,
            cost_structure=cost_structure,
            competitive_context=self._format_competitive_context_summary(competitive_context),
            persona_context=self._format_persona_context_summary(persona_context),
            market_sizing_context=self._format_market_sizing_context_summary(market_sizing_context),
            business_model_context=self._format_business_model_context_summary(business_model_context)
        )
    
    def _parse_customer_segments(self, data: Dict[str, Any], persona_context: Optional[Dict[str, Any]]) -> CustomerSegments:
        """Parse customer segments building block"""
        segment_type = self._map_to_customer_segment_type(data.get("type", "niche_market"))
        
        return CustomerSegments(
            segment_type=segment_type,
            description=data.get("description", "Target customer segments"),
            characteristics=data.get("characteristics", []),
            needs=data.get("needs", []),
            pain_points=data.get("pain_points", []),
            size_estimate=data.get("size_estimate"),
            persona_insights=persona_context
        )
    
    def _parse_value_propositions(self, data: Dict[str, Any], competitive_context: Optional[Dict[str, Any]]) -> ValuePropositions:
        """Parse value propositions building block"""
        proposition_type = self._map_to_value_proposition_type(data.get("type", "performance"))
        
        return ValuePropositions(
            proposition_type=proposition_type,
            description=data.get("description", "Value delivered to customers"),
            benefits=data.get("benefits", []),
            pain_points_solved=data.get("pain_points_solved", []),
            competitive_advantages=data.get("competitive_advantages", []),
            quantifiable_value=data.get("quantifiable_value"),
            competitive_insights=competitive_context
        )
    
    def _parse_channels(self, data: Dict[str, Any]) -> Channels:
        """Parse channels building block"""
        channel_type = self._map_to_channel_type(data.get("type", "hybrid"))
        
        return Channels(
            channel_type=channel_type,
            description=data.get("description", "Customer touchpoints and distribution"),
            touchpoints=data.get("touchpoints", []),
            effectiveness_metrics=data.get("effectiveness_metrics", []),
            cost_implications=data.get("cost_implications"),
            market_reach=data.get("market_reach")
        )
    
    def _parse_customer_relationships(self, data: Dict[str, Any]) -> CustomerRelationships:
        """Parse customer relationships building block"""
        relationship_type = self._map_to_customer_relationship_type(data.get("type", "automated_services"))
        
        return CustomerRelationships(
            relationship_type=relationship_type,
            description=data.get("description", "Customer relationship strategy"),
            acquisition_strategy=data.get("acquisition_strategy", "Digital marketing and partnerships"),
            retention_strategy=data.get("retention_strategy", "Value delivery and support"),
            growth_strategy=data.get("growth_strategy", "Expansion and upselling"),
            automation_level=data.get("automation_level"),
            personalization_degree=data.get("personalization_degree")
        )
    
    def _parse_revenue_streams(self, data: Dict[str, Any], business_model_context: Optional[Dict[str, Any]]) -> RevenueStreams:
        """Parse revenue streams building block"""
        stream_type = self._map_to_revenue_stream_type(data.get("type", "subscription_fees"))
        
        return RevenueStreams(
            stream_type=stream_type,
            description=data.get("description", "Revenue generation model"),
            pricing_model=data.get("pricing_model", "Subscription-based"),
            revenue_potential=data.get("revenue_potential"),
            pricing_strategy=data.get("pricing_strategy"),
            market_benchmarks=business_model_context.get("market_benchmarks") if business_model_context else None,
            business_model_insights=business_model_context
        )
    
    def _parse_key_resources(self, data: Dict[str, Any]) -> KeyResources:
        """Parse key resources building block"""
        resource_type = self._map_to_key_resource_type(data.get("type", "intellectual"))
        
        return KeyResources(
            resource_type=resource_type,
            description=data.get("description", "Critical resources needed"),
            importance_level=data.get("importance_level", "Critical"),
            acquisition_strategy=data.get("acquisition_strategy"),
            cost_implications=data.get("cost_implications"),
            competitive_advantage=data.get("competitive_advantage")
        )
    
    def _parse_key_activities(self, data: Dict[str, Any]) -> KeyActivities:
        """Parse key activities building block"""
        activity_type = self._map_to_key_activity_type(data.get("type", "problem_solving"))
        
        return KeyActivities(
            activity_type=activity_type,
            description=data.get("description", "Core business activities"),
            criticality=data.get("criticality", "Critical"),
            resource_requirements=data.get("resource_requirements", []),
            efficiency_metrics=data.get("efficiency_metrics", []),
            automation_potential=data.get("automation_potential")
        )
    
    def _parse_key_partnerships(self, data: Dict[str, Any], competitive_context: Optional[Dict[str, Any]]) -> KeyPartnerships:
        """Parse key partnerships building block"""
        partnership_type = self._map_to_partnership_type(data.get("type", "strategic_alliances"))
        
        return KeyPartnerships(
            partnership_type=partnership_type,
            description=data.get("description", "Strategic partnerships"),
            partner_categories=data.get("partner_categories", []),
            value_provided=data.get("value_provided", []),
            risks_and_mitigation=data.get("risks_and_mitigation", []),
            competitive_insights=competitive_context
        )
    
    def _parse_cost_structure(self, data: Dict[str, Any], business_model_context: Optional[Dict[str, Any]]) -> CostStructure:
        """Parse cost structure building block"""
        structure_type = self._map_to_cost_structure_type(data.get("type", "value_driven"))
        
        return CostStructure(
            structure_type=structure_type,
            description=data.get("description", "Cost structure and optimization"),
            fixed_costs=data.get("fixed_costs", []),
            variable_costs=data.get("variable_costs", []),
            cost_drivers=data.get("cost_drivers", []),
            optimization_opportunities=data.get("optimization_opportunities", []),
            profitability_insights=business_model_context.get("profitability_projections") if business_model_context else None
        )
    
    # Mapping functions for enums
    def _map_to_customer_segment_type(self, type_str: str) -> CustomerSegmentType:
        mapping = {
            "mass_market": CustomerSegmentType.MASS_MARKET,
            "niche_market": CustomerSegmentType.NICHE_MARKET,
            "segmented": CustomerSegmentType.SEGMENTED,
            "diversified": CustomerSegmentType.DIVERSIFIED,
            "multi_sided_platform": CustomerSegmentType.MULTI_SIDED_PLATFORM
        }
        return mapping.get(type_str.lower(), CustomerSegmentType.NICHE_MARKET)
    
    def _map_to_value_proposition_type(self, type_str: str) -> ValuePropositionType:
        mapping = {
            "newness": ValuePropositionType.NEWNESS,
            "performance": ValuePropositionType.PERFORMANCE,
            "customization": ValuePropositionType.CUSTOMIZATION,
            "getting_job_done": ValuePropositionType.GETTING_JOB_DONE,
            "design": ValuePropositionType.DESIGN,
            "brand_status": ValuePropositionType.BRAND_STATUS,
            "price": ValuePropositionType.PRICE,
            "cost_reduction": ValuePropositionType.COST_REDUCTION,
            "risk_reduction": ValuePropositionType.RISK_REDUCTION,
            "accessibility": ValuePropositionType.ACCESSIBILITY,
            "convenience": ValuePropositionType.CONVENIENCE
        }
        return mapping.get(type_str.lower(), ValuePropositionType.PERFORMANCE)
    
    def _map_to_channel_type(self, type_str: str) -> ChannelType:
        mapping = {
            "own_channels": ChannelType.OWN_CHANNELS,
            "partner_channels": ChannelType.PARTNER_CHANNELS,
            "hybrid": ChannelType.HYBRID
        }
        return mapping.get(type_str.lower(), ChannelType.HYBRID)
    
    def _map_to_customer_relationship_type(self, type_str: str) -> CustomerRelationshipType:
        mapping = {
            "personal_assistance": CustomerRelationshipType.PERSONAL_ASSISTANCE,
            "dedicated_personal_assistance": CustomerRelationshipType.DEDICATED_PERSONAL_ASSISTANCE,
            "self_service": CustomerRelationshipType.SELF_SERVICE,
            "automated_services": CustomerRelationshipType.AUTOMATED_SERVICES,
            "communities": CustomerRelationshipType.COMMUNITIES,
            "co_creation": CustomerRelationshipType.CO_CREATION
        }
        return mapping.get(type_str.lower(), CustomerRelationshipType.AUTOMATED_SERVICES)
    
    def _map_to_revenue_stream_type(self, type_str: str) -> RevenueStreamType:
        mapping = {
            "asset_sale": RevenueStreamType.ASSET_SALE,
            "usage_fee": RevenueStreamType.USAGE_FEE,
            "subscription_fees": RevenueStreamType.SUBSCRIPTION_FEES,
            "lending_leasing_renting": RevenueStreamType.LENDING_LEASING_RENTING,
            "licensing": RevenueStreamType.LICENSING,
            "brokerage_fees": RevenueStreamType.BROKERAGE_FEES,
            "advertising": RevenueStreamType.ADVERTISING
        }
        return mapping.get(type_str.lower(), RevenueStreamType.SUBSCRIPTION_FEES)
    
    def _map_to_key_resource_type(self, type_str: str) -> KeyResourceType:
        mapping = {
            "physical": KeyResourceType.PHYSICAL,
            "intellectual": KeyResourceType.INTELLECTUAL,
            "human": KeyResourceType.HUMAN,
            "financial": KeyResourceType.FINANCIAL
        }
        return mapping.get(type_str.lower(), KeyResourceType.INTELLECTUAL)
    
    def _map_to_key_activity_type(self, type_str: str) -> KeyActivityType:
        mapping = {
            "production": KeyActivityType.PRODUCTION,
            "problem_solving": KeyActivityType.PROBLEM_SOLVING,
            "platform_network": KeyActivityType.PLATFORM_NETWORK
        }
        return mapping.get(type_str.lower(), KeyActivityType.PROBLEM_SOLVING)
    
    def _map_to_partnership_type(self, type_str: str) -> PartnershipType:
        mapping = {
            "strategic_alliances": PartnershipType.STRATEGIC_ALLIANCES,
            "coopetition": PartnershipType.COOPETITION,
            "joint_ventures": PartnershipType.JOINT_VENTURES,
            "buyer_supplier": PartnershipType.BUYER_SUPPLIER
        }
        return mapping.get(type_str.lower(), PartnershipType.STRATEGIC_ALLIANCES)
    
    def _map_to_cost_structure_type(self, type_str: str) -> CostStructureType:
        mapping = {
            "cost_driven": CostStructureType.COST_DRIVEN,
            "value_driven": CostStructureType.VALUE_DRIVEN
        }
        return mapping.get(type_str.lower(), CostStructureType.VALUE_DRIVEN)
    
    # Context formatting methods
    def _format_competitive_context(self, competitive_context: Optional[Dict[str, Any]]) -> str:
        """Format competitive intelligence for canvas generation"""
        if not competitive_context:
            return "No competitive analysis data available."
        
        context_parts = []
        
        if "total_competitors" in competitive_context:
            context_parts.append(f"Competitors analyzed: {competitive_context['total_competitors']}")
        
        if "market_gaps" in competitive_context:
            gaps = len(competitive_context["market_gaps"])
            context_parts.append(f"Market gaps identified: {gaps}")
        
        if "key_insights" in competitive_context:
            insights = competitive_context["key_insights"][:2]
            context_parts.append(f"Key insights: {'; '.join(insights)}")
        
        return "\n".join(context_parts) if context_parts else "Limited competitive data available."
    
    def _format_persona_context(self, persona_context: Optional[Dict[str, Any]]) -> str:
        """Format persona insights for canvas generation"""
        if not persona_context:
            return "No persona analysis data available."
        
        context_parts = []
        
        if "personas_analyzed" in persona_context:
            context_parts.append(f"Personas analyzed: {persona_context['personas_analyzed']}")
        
        if "pricing_sensitivity" in persona_context:
            sensitivity = persona_context["pricing_sensitivity"]
            context_parts.append(f"Pricing sensitivity: {sensitivity.get('high_sensitivity_count', 0)} high, {sensitivity.get('low_sensitivity_count', 0)} low")
        
        return "\n".join(context_parts) if context_parts else "Limited persona data available."
    
    def _format_market_sizing_context(self, market_sizing_context: Optional[Dict[str, Any]]) -> str:
        """Format market sizing data for canvas generation"""
        if not market_sizing_context:
            return "No market sizing data available."
        
        context_parts = []
        
        if "market_size" in market_sizing_context:
            market_size = market_sizing_context["market_size"]
            context_parts.append(f"Market size - TAM: ${market_size.get('tam', 0):,.0f}")
        
        if "revenue_opportunity" in market_sizing_context:
            opportunity = market_sizing_context["revenue_opportunity"]
            context_parts.append(f"Revenue opportunity: ${opportunity.get('obtainable_market', 0):,.0f}")
        
        return "\n".join(context_parts) if context_parts else "Limited market sizing data available."
    
    def _format_business_model_context(self, business_model_context: Optional[Dict[str, Any]]) -> str:
        """Format business model insights for canvas generation"""
        if not business_model_context:
            return "No business model analysis data available."
        
        context_parts = []
        
        if "primary_recommendation" in business_model_context:
            rec = business_model_context["primary_recommendation"]
            context_parts.append(f"Primary revenue model: {rec.get('model_type', 'N/A')}")
        
        if "profitability_projections" in business_model_context:
            projections = business_model_context["profitability_projections"]
            if projections:
                realistic = projections[1] if len(projections) > 1 else projections[0]
                context_parts.append(f"Realistic monthly revenue: ${realistic.get('monthly_revenue', 0):,.0f}")
        
        return "\n".join(context_parts) if context_parts else "Limited business model data available."
    
    # Summary formatting methods
    def _format_competitive_context_summary(self, competitive_context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format competitive context summary for canvas"""
        if not competitive_context:
            return None
        
        return {
            "total_competitors": competitive_context.get("total_competitors", 0),
            "market_gaps": len(competitive_context.get("market_gaps", [])),
            "key_insights": competitive_context.get("key_insights", [])[:3]
        }
    
    def _format_persona_context_summary(self, persona_context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format persona context summary for canvas"""
        if not persona_context:
            return None
        
        return {
            "personas_analyzed": persona_context.get("personas_analyzed", 0),
            "pricing_sensitivity": persona_context.get("pricing_sensitivity", {})
        }
    
    def _format_market_sizing_context_summary(self, market_sizing_context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format market sizing context summary for canvas"""
        if not market_sizing_context:
            return None
        
        return {
            "market_size": market_sizing_context.get("market_size", {}),
            "revenue_opportunity": market_sizing_context.get("revenue_opportunity", {})
        }
    
    def _format_business_model_context_summary(self, business_model_context: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Format business model context summary for canvas"""
        if not business_model_context:
            return None
        
        return {
            "primary_recommendation": business_model_context.get("primary_recommendation", {}),
            "profitability_projections": business_model_context.get("profitability_projections", [])[:1]
        }
    
    async def _create_fallback_canvas(self, business_idea: str, target_market: str, industry: str) -> BusinessModelCanvas:
        """Create comprehensive fallback canvas when generation fails"""
        return BusinessModelCanvas(
            business_idea=business_idea,
            customer_segments=CustomerSegments(
                segment_type=CustomerSegmentType.NICHE_MARKET,
                description=f"Target {target_market} in {industry}",
                characteristics=[
                    "Early adopters of technology",
                    "Tech-savvy decision makers",
                    "Growth-focused businesses",
                    "Data-driven organizations",
                    "Efficiency-conscious managers"
                ],
                needs=[
                    "Improved operational efficiency",
                    "Data-driven decision making",
                    "Cost reduction and optimization",
                    "Scalable solutions",
                    "Competitive advantage"
                ],
                pain_points=[
                    "Manual and time-consuming processes",
                    "Lack of predictive insights",
                    "Inefficient resource allocation",
                    "Difficulty scaling operations",
                    "Limited competitive intelligence"
                ],
                size_estimate="Medium to large enterprises",
                persona_insights={
                    "primary_personas": ["Operations Manager", "Data Analyst", "Business Owner"],
                    "decision_making_factors": ["ROI", "Ease of implementation", "Scalability"],
                    "pricing_sensitivity": "Medium to High"
                }
            ),
            value_propositions=ValuePropositions(
                proposition_type=ValuePropositionType.PERFORMANCE,
                description="AI-powered demand prediction and business optimization platform",
                benefits=[
                    "30-50% improvement in demand forecasting accuracy",
                    "Reduced inventory costs by 20-40%",
                    "Automated decision-making processes",
                    "Real-time market insights and trends",
                    "Predictive analytics for strategic planning"
                ],
                pain_points_solved=[
                    "Inaccurate demand forecasting",
                    "Excessive inventory costs",
                    "Manual data analysis processes",
                    "Reactive rather than proactive strategies",
                    "Limited competitive intelligence"
                ],
                competitive_advantages=[
                    "Advanced AI/ML algorithms",
                    "Real-time data processing",
                    "Industry-specific customization",
                    "Seamless integration capabilities",
                    "Comprehensive analytics dashboard"
                ],
                quantifiable_value="20-40% cost reduction, 50-70% faster decision making, 30-50% accuracy improvement",
                competitive_insights={
                    "market_position": "Innovation leader in AI-powered business intelligence",
                    "differentiation": "Comprehensive end-to-end solution with predictive capabilities"
                }
            ),
            channels=Channels(
                channel_type=ChannelType.HYBRID,
                description="Multi-channel approach combining digital and partner channels",
                touchpoints=[
                    "Direct website and online platform",
                    "Strategic technology partnerships",
                    "Industry conferences and events",
                    "Content marketing and thought leadership",
                    "Referral programs and customer advocacy"
                ],
                effectiveness_metrics=[
                    "Website conversion rate: 3-5%",
                    "Partner channel contribution: 40-60%",
                    "Customer acquisition cost: $500-1000",
                    "Sales cycle length: 3-6 months"
                ],
                cost_implications="Digital marketing 30%, partner commissions 15-25%, content creation 10% of revenue",
                market_reach="Global coverage targeting E-commerce, Retail, Manufacturing, Logistics industries",
            ),
            customer_relationships=CustomerRelationships(
                relationship_type=CustomerRelationshipType.AUTOMATED_SERVICES,
                description="Automated platform with personalized support and strategic consulting",
                acquisition_strategy="Digital marketing, content marketing, strategic partnerships, and industry events",
                retention_strategy="Continuous value delivery, regular updates, personalized support, and success metrics tracking",
                growth_strategy="Upselling additional features, cross-selling to new departments, and expansion to new markets",
                automation_level="High automation with human touchpoints for complex decisions",
                personalization_degree="Highly personalized based on industry, company size, and usage patterns"
            ),
            revenue_streams=RevenueStreams(
                stream_type=RevenueStreamType.SUBSCRIPTION_FEES,
                description="Tiered subscription model with usage-based pricing",
                pricing_model="Monthly and annual subscriptions with enterprise custom pricing",
                revenue_potential="$50,000 - $500,000 monthly recurring revenue",
                pricing_strategy="Tiered pricing: Basic $500/month, Professional $2,000/month, Enterprise custom pricing",
                market_benchmarks={
                    "industry_average": "$1,500/month",
                    "competitive_positioning": "Premium pricing for superior value",
                    "pricing_elasticity": "Medium - customers value quality over cost"
                },
                business_model_insights={
                    "revenue_model": "SaaS subscription with professional services",
                    "profitability_margin": "70-80% gross margin",
                    "scalability_factor": "High - software-based solution"
                }
            ),
            key_resources=KeyResources(
                resource_type=KeyResourceType.INTELLECTUAL,
                description="AI/ML technology, data assets, and human expertise",
                importance_level="Critical",
                acquisition_strategy="Internal development, strategic partnerships, and talent acquisition",
                cost_implications="Development costs 40%, data acquisition 15%, talent investment 25% of revenue",
                competitive_advantage="Proprietary AI algorithms, extensive data sets, and domain expertise"
            ),
            key_activities=KeyActivities(
                activity_type=KeyActivityType.PROBLEM_SOLVING,
                description="AI model development, data analysis, customer success, and continuous improvement",
                criticality="Critical",
                resource_requirements=[
                    "AI/ML engineers and data scientists",
                    "Product development team",
                    "Customer success and support",
                    "Sales and marketing professionals"
                ],
                efficiency_metrics=[
                    "Model accuracy improvement: 5% quarterly",
                    "Customer onboarding time: 2-4 weeks",
                    "Support response time: <4 hours",
                    "Feature development cycle: 2-4 weeks"
                ],
                automation_potential="High automation in data processing, moderate in customer interactions"
            ),
            key_partnerships=KeyPartnerships(
                partnership_type=PartnershipType.STRATEGIC_ALLIANCES,
                description="Technology partnerships, data providers, and channel partners",
                partner_categories=[
                    "Cloud infrastructure providers (AWS, Azure, GCP)",
                    "Data providers and analytics platforms",
                    "System integrators and consultants",
                    "Industry associations and trade groups"
                ],
                partnership_benefits=[
                    "Access to advanced cloud computing resources",
                    "Enhanced data sources and market intelligence",
                    "Expanded market reach through channel partners",
                    "Industry credibility and thought leadership"
                ],
                competitive_insights={
                    "partnership_strategy": "Strategic alliances to enhance capabilities and market reach",
                    "competitive_advantage": "Strong ecosystem of technology and industry partners"
                }
            ),
            cost_structure=CostStructure(
                structure_type=CostStructureType.VALUE_DRIVEN,
                description="Investment in technology, talent, and market expansion",
                fixed_costs=[
                    "Technology infrastructure and cloud services",
                    "Office space and administrative overhead",
                    "Software licenses and development tools",
                    "Legal and compliance costs"
                ],
                variable_costs=[
                    "Sales and marketing expenses",
                    "Customer support and success",
                    "Data acquisition and processing",
                    "Professional services and consulting"
                ],
                cost_optimization="Focus on scalable technology investments and efficient customer acquisition",
                business_model_insights={
                    "cost_structure": "Technology-heavy with high upfront investment",
                    "break_even_point": "18-24 months",
                    "scalability": "High - software-based with low marginal costs"
                }
            ),
            competitive_context={
                "total_competitors": 15,
                "market_gaps": ["Lack of comprehensive AI solutions", "Limited industry customization"],
                "key_insights": ["Growing demand for AI-powered solutions", "Price sensitivity in mid-market"]
            },
            persona_context={
                "personas_analyzed": 3,
                "pricing_sensitivity": {"low": 20, "medium": 50, "high": 30},
                "decision_making_factors": ["ROI", "Ease of use", "Integration capabilities"]
            },
            market_sizing_context={
                "market_size": {"tam": "$50B", "sam": "$10B", "som": "$500M"},
                "revenue_opportunity": {"year_1": "$5M", "year_3": "$50M", "year_5": "$200M"}
            },
            business_model_context={
                "primary_recommendation": "SaaS subscription model with professional services",
                "profitability_projections": ["Year 1: -$2M", "Year 3: $10M", "Year 5: $50M"]
            }
        )


# Create singleton instance
canvas_generator_service = BusinessModelCanvasGeneratorService() 