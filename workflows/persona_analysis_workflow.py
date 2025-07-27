import asyncio
import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from core.persona_models import PersonaAnalysisState, PersonaReport
from services.persona_analysis.social_media_service import SocialMediaAnalysisService
from services.persona_analysis.persona_generator_service import PersonaGeneratorService
from services.persona_analysis.persona_report_service import PersonaReportService
from services.persona_analysis.competitor_context_service import competitor_context_service


class PersonaAnalysisWorkflow:
    def __init__(self):
        self.social_media_service = SocialMediaAnalysisService()
        self.persona_generator = PersonaGeneratorService()
        self.report_service = PersonaReportService()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow for persona analysis
        """
        workflow = StateGraph(PersonaAnalysisState)
        
        # Add nodes
        workflow.add_node("check_competitor_context", self._check_competitor_context_node)
        workflow.add_node("analyze_social_media", self._analyze_social_media_node)
        workflow.add_node("generate_personas", self._generate_personas_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # Add edges
        workflow.add_edge("check_competitor_context", "analyze_social_media")
        workflow.add_edge("analyze_social_media", "generate_personas")
        workflow.add_edge("generate_personas", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Set entry point
        workflow.set_entry_point("check_competitor_context")
        
        return workflow.compile()

    async def _check_competitor_context_node(self, state: PersonaAnalysisState) -> dict:
        """
        Node 0: Check for existing competitor analysis to enhance persona generation
        """
        try:
            print("🔍 Checking for competitor analysis context...")
            
            # Get user_id and idea_id from the state if available
            user_id = getattr(state, 'user_id', None)
            idea_id = getattr(state, 'idea_id', None)
            
            competitor_context = None
            if user_id and idea_id:
                competitor_context = await competitor_context_service.get_competitor_context_for_idea(
                    user_id, idea_id
                )
                
                if competitor_context:
                    print("✅ Found competitor analysis context - will enhance persona generation")
                else:
                    print("ℹ️ No competitor analysis found - using standard persona generation")
            else:
                print("ℹ️ No user/idea context - using standard persona generation")
            
            return {
                "competitor_context": competitor_context
            }
            
        except Exception as e:
            print(f"⚠️ Error checking competitor context: {e}")
            return {
                "competitor_context": None,
                "errors": state.errors + [f"Competitor context check failed: {str(e)}"]
            }

    async def _analyze_social_media_node(self, state: PersonaAnalysisState) -> dict:
        """
        Node 1: Analyze social media platforms for persona insights
        """
        try:
            print("📱 Analyzing social media platforms...")
            
            social_data = await self.social_media_service.analyze_social_platforms(
                state.analysis_input
            )
            
            print("✅ Social media analysis completed")
            return {"social_media_data": social_data}
            
        except Exception as e:
            error_msg = f"Social media analysis failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    async def _generate_personas_node(self, state: PersonaAnalysisState) -> dict:
        """
        Node 2: Generate detailed personas based on social media insights
        """
        try:
            print("👥 Generating target personas...")
            
            # Format competitor context for persona generation
            competitor_context_str = ""
            if hasattr(state, 'competitor_context') and state.competitor_context:
                competitor_context_str = competitor_context_service.format_context_for_prompt(
                    state.competitor_context
                )
            
            personas = await self.persona_generator.generate_personas(
                state.analysis_input,
                state.social_media_data,
                competitor_context_str
            )
            
            print(f"✅ Generated {len(personas)} personas")
            for persona in personas:
                print(f"  - {persona.name}")
            
            return {"generated_personas": personas}
            
        except Exception as e:
            error_msg = f"Persona generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    async def _generate_report_node(self, state: PersonaAnalysisState) -> dict:
        """
        Node 3: Generate comprehensive persona analysis report
        """
        try:
            print("📝 Generating persona analysis report...")
            
            report = await self.report_service.generate_persona_report(
                analysis_input=state.analysis_input,
                personas=state.generated_personas,
                social_media_data=state.social_media_data,
                errors=state.errors
            )
            
            print(f"✅ Report generated with {len(state.generated_personas)} personas")
            return {"final_report": report}
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    async def run_analysis(self, analysis_input) -> PersonaReport:
        """
        Run the complete persona analysis workflow
        """
        start_time = time.time()
        
        print("🚀 Starting persona analysis...")
        print(f"Business Idea: {analysis_input.business_idea}")
        
        # Initialize state
        initial_state = PersonaAnalysisState(analysis_input=analysis_input)
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state.dict())
        
        execution_time = time.time() - start_time
        
        # Convert final_state dict back to PersonaAnalysisState object
        final_analysis_state = PersonaAnalysisState(**final_state)
        
        if final_analysis_state.final_report:
            final_analysis_state.final_report.execution_time = execution_time
            print(f"✅ Persona analysis completed in {execution_time:.2f} seconds")
            return final_analysis_state.final_report
        else:
            # Create emergency fallback report
            print("⚠️ Creating fallback report due to errors")
            
            fallback_report = PersonaReport(
                business_idea=analysis_input.business_idea,
                total_personas=0,
                personas=[],
                market_insights=["Analysis failed - please try again"],
                targeting_recommendations=["Unable to generate recommendations"],
                content_strategy_recommendations=["Unable to generate strategy"],
                execution_time=execution_time
            )
            return fallback_report