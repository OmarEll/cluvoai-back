import asyncio
import time
from typing import Dict, Any
from langgraph.graph import StateGraph, END

from core.competitor_models import AnalysisState, CompetitorAnalysis, CompetitorReport
from services.competitor_analysis.competitor_discovery import CompetitorDiscoveryService
from services.competitor_analysis.data_scraper import DataScrapingService  
from services.competitor_analysis.market_analyzer import MarketAnalysisService
from services.competitor_analysis.report_generator import ReportGenerationService


class CompetitorAnalysisWorkflow:
    def __init__(self):
        self.discovery_service = CompetitorDiscoveryService()
        self.scraping_service = DataScrapingService()
        self.market_service = MarketAnalysisService()
        self.report_service = ReportGenerationService()
        
        # Build the workflow graph
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """
        Build the LangGraph workflow for competitor analysis
        """
        workflow = StateGraph(AnalysisState)
        
        # Add nodes
        workflow.add_node("discover_competitors", self._discover_competitors_node)
        workflow.add_node("scrape_data", self._scrape_data_node)
        workflow.add_node("analyze_market", self._analyze_market_node)
        workflow.add_node("generate_report", self._generate_report_node)
        
        # Add edges
        workflow.add_edge("discover_competitors", "scrape_data")
        workflow.add_edge("scrape_data", "analyze_market")
        workflow.add_edge("analyze_market", "generate_report")
        workflow.add_edge("generate_report", END)
        
        # Set entry point
        workflow.set_entry_point("discover_competitors")
        
        return workflow.compile()

    async def _discover_competitors_node(self, state: AnalysisState) -> dict:
        """
        Node 1: Discover competitors using AI
        """
        try:
            print("🔍 Discovering competitors...")
            
            competitors = await self.discovery_service.discover_competitors(state.business_input)
            
            print(f"✅ Found {len(competitors)} competitors")
            for comp in competitors:
                print(f"  - {comp.name} ({comp.type.value})")
            
            return {"discovered_competitors": competitors}
            
        except Exception as e:
            error_msg = f"Competitor discovery failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    async def _scrape_data_node(self, state: AnalysisState) -> dict:
        """
        Node 2: Scrape financial and pricing data for all competitors in parallel
        """
        try:
            print("📊 Scraping competitor data...")
            
            # Create tasks for parallel data scraping
            scraping_tasks = []
            for competitor in state.discovered_competitors:
                task = self._scrape_single_competitor(competitor)
                scraping_tasks.append(task)
            
            # Execute all scraping tasks in parallel
            competitor_analyses = await asyncio.gather(*scraping_tasks, return_exceptions=True)
            # Filter out exceptions and build competitor analyses
            valid_analyses = []
            errors = list(state.errors)  # Copy existing errors
            
            for i, result in enumerate(competitor_analyses):
                if isinstance(result, Exception):
                    error_msg = f"Data scraping failed for {state.discovered_competitors[i].name}: {str(result)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    
                    # Create fallback analysis
                    fallback_analysis = self._create_fallback_analysis(state.discovered_competitors[i])
                    valid_analyses.append(fallback_analysis)
                else:
                    valid_analyses.append(result)
                    print(f"✅ Scraped data for {result.basic_info.name}")
            
            return {
                "competitor_analyses": valid_analyses,
                "errors": errors
            }
            
        except Exception as e:
            error_msg = f"Data scraping node failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    async def _scrape_single_competitor(self, competitor) -> CompetitorAnalysis:
        """
        Scrape data for a single competitor
        """
        # Get financial and pricing data
        financial_data, pricing_data = await self.scraping_service.scrape_competitor_data(
            competitor.name, 
            competitor.domain or ""
        )

        # Create competitor analysis
        return CompetitorAnalysis(
            basic_info=competitor,
            financial_data=financial_data,
            pricing_data=pricing_data,
            #market_sentiment=None  # Will be filled in market analysis
        )

    async def _analyze_market_node(self, state: AnalysisState) -> dict:
        """
        Node 3: Perform market analysis and SWOT for all competitors
        """
        try:
            print("🎯 Analyzing market and performing SWOT...")
            
            # Analyze each competitor with SWOT
            analysis_tasks = []
            for competitor_analysis in state.competitor_analyses:
                task = self.market_service.analyze_competitor_swot(competitor_analysis)
                analysis_tasks.append(task)
            
            # Execute SWOT analyses in parallel
            updated_analyses = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Update state with SWOT results
            valid_analyses = []
            errors = list(state.errors)  # Copy existing errors
            
            for i, result in enumerate(updated_analyses):
                if isinstance(result, Exception):
                    error_msg = f"SWOT analysis failed for {state.competitor_analyses[i].basic_info.name}: {str(result)}"
                    print(f"❌ {error_msg}")
                    errors.append(error_msg)
                    valid_analyses.append(state.competitor_analyses[i])  # Keep original
                else:
                    valid_analyses.append(result)
                    print(f"✅ SWOT completed for {result.basic_info.name}")
            
            # Identify market gaps
            print("🔍 Identifying market gaps...")
            market_gaps = await self.market_service.identify_market_gaps(
                state.business_input, 
                valid_analyses
            )
            print(f"✅ Identified {len(market_gaps)} market gaps")
            
            return {
                "competitor_analyses": valid_analyses,
                "market_gaps": market_gaps,
                "errors": errors
            }
            
        except Exception as e:
            error_msg = f"Market analysis failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    async def _generate_report_node(self, state: AnalysisState) -> dict:
        """
        Node 4: Generate final competitive intelligence report
        """
        try:
            print("📝 Generating competitive intelligence report...")
            
            report = await self.report_service.generate_report(
                business_input=state.business_input,
                competitors=state.competitor_analyses,
                market_gaps=state.market_gaps,
                errors=state.errors
            )
            
            print(f"✅ Report generated with {len(state.competitor_analyses)} competitors analyzed")
            
            return {"final_report": report}
            
        except Exception as e:
            error_msg = f"Report generation failed: {str(e)}"
            print(f"❌ {error_msg}")
            return {"errors": state.errors + [error_msg]}

    def _create_fallback_analysis(self, competitor) -> CompetitorAnalysis:
        """
        Create a fallback analysis when scraping fails
        """
        from core.competitor_models import FinancialData, PricingData, MarketSentiment, DataSource
        
        return CompetitorAnalysis(
            basic_info=competitor,
            financial_data=FinancialData(
                funding_total="Unknown",
                employee_count=None,
                source=DataSource.AI_ESTIMATION
            ),
            pricing_data=PricingData(
                monthly_price=None,
                pricing_model="Unknown",
                source=DataSource.AI_ESTIMATION
            ),
            market_sentiment=MarketSentiment(
                overall_score=0.0,
                reddit_mentions=0,
                twitter_mentions=0,
                key_complaints=["Data not available"],
                key_praises=["Data not available"]
            ),
            strengths=["Market presence"],
            weaknesses=["Limited data available"],
            opportunities=["Data collection needed"],
            threats=["Competitive analysis incomplete"]
        )

    async def run_analysis(self, business_input) -> CompetitorReport:
        """
        Run the complete competitor analysis workflow
        """
        start_time = time.time()
        
        print("🚀 Starting competitive intelligence analysis...")
        print(f"Business Idea: {business_input.idea_description}")
        
        # Initialize state
        initial_state = AnalysisState(business_input=business_input)
        
        # Run the workflow
        final_state = await self.workflow.ainvoke(initial_state.dict())
        
        execution_time = time.time() - start_time
        
        # Convert final_state dict back to AnalysisState object
        final_analysis_state = AnalysisState(**final_state)
        
        if final_analysis_state.final_report:
            final_analysis_state.final_report.execution_time = execution_time
            print(f"✅ Analysis completed in {execution_time:.2f} seconds")
            return final_analysis_state.final_report
        else:
            # Create emergency fallback report
            print("⚠️ Creating fallback report due to errors")
            from core.competitor_models import FinancialData, PricingData, MarketSentiment, DataSource
            
            fallback_report = CompetitorReport(
                business_idea=business_input.idea_description,
                total_competitors=0,
                competitors=[],
                market_gaps=[],
                key_insights=["Analysis failed - please try again"],
                positioning_recommendations=["Unable to generate recommendations"],
                execution_time=execution_time
            )
            return fallback_report