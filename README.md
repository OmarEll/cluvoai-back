# Cluvo.ai - Competitor Analysis Backend

AI-powered competitive intelligence platform designed to help entrepreneurs analyze their competition and identify market opportunities.

## 🚀 Features

- **AI-Powered Competitor Discovery**: Automatically identify direct, indirect, and substitute competitors
- **Comprehensive Data Scraping**: Financial data, pricing information, and market presence
- **SWOT Analysis**: AI-generated strengths, weaknesses, opportunities, and threats for each competitor
- **Market Gap Analysis**: Identify underserved segments and positioning opportunities
- **Fast Parallel Processing**: Concurrent data collection for maximum speed
- **RESTful API**: Easy integration with frontend applications

## 🏗️ Architecture

```
cluvo-backend/
├── requirements.txt          # Dependencies
├── config/                   # Configuration
│   ├── __init__.py
│   └── settings.py          # App settings and environment variables
├── core/                    # Core data models
│   ├── __init__.py
│   ├── models.py           # Pydantic models for data structures
│   └── exceptions.py       # Custom exceptions
├── services/               # Business logic services
│   ├── __init__.py
│   ├── competitor_discovery.py  # AI-powered competitor discovery
│   ├── data_scraper.py          # Web scraping and data collection
│   ├── market_analyzer.py       # Market analysis and SWOT generation
│   └── report_generator.py      # Final report generation
├── workflows/              # LangGraph workflows
│   ├── __init__.py
│   └── competitor_analysis_workflow.py  # Main analysis orchestration
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── web_scraper.py      # Web scraping utilities
│   └── data_processor.py   # Data processing helpers
├── api/                    # FastAPI routes and schemas
│   ├── __init__.py
│   ├── routes.py           # API endpoints
│   └── schemas.py          # Request/response schemas
└── main.py                 # FastAPI application entry point
```

## 🛠️ Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **LangChain & LangGraph**: LLM orchestration and workflow management
- **OpenAI GPT-4**: AI analysis and insights generation
- **aiohttp**: Async HTTP client for web scraping
- **BeautifulSoup**: HTML parsing and data extraction
- **Pydantic**: Data validation and serialization
- **asyncio**: Asynchronous processing for parallel execution

## 📋 Prerequisites

- Python 3.8+
- OpenAI API key
- RapidAPI key (optional, for enhanced data sources)

## 🚦 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Set Environment Variables**
```bash
export OPENAI_API_KEY="your_openai_api_key"
export RAPIDAPI_KEY="your_rapidapi_key"  # Optional
```

3. **Run the API**
```bash
python main.py
```

4. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 📡 API Usage

### Analyze Competitors (Synchronous)

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "idea_description": "AI-powered HR recruitment tool for small businesses",
    "target_market": "SMBs with 10-100 employees",
    "business_model": "SaaS subscription",
    "geographic_focus": "North America",
    "industry": "HR Technology"
  }'
```

### Analyze Competitors (Asynchronous)

```bash
# Start analysis
curl -X POST "http://localhost:8000/api/v1/analyze/competitors/async" \
  -H "Content-Type: application/json" \
  -d '{
    "idea_description": "AI-powered HR recruitment tool for small businesses"
  }'

# Check status
curl "http://localhost:8000/api/v1/analyze/competitors/{analysis_id}"
```

## 📊 Example Response

```json
{
  "status": "completed",
  "report": {
    "business_idea": "AI-powered HR recruitment tool for small businesses",
    "total_competitors": 3,
    "competitors": [
      {
        "basic_info": {
          "name": "BambooHR",
          "domain": "bamboohr.com",
          "type": "indirect",
          "description": "HR software for growing companies"
        },
        "financial_data": {
          "funding_total": "$57M",
          "employee_count": 1200,
          "founded_year": 2008
        },
        "pricing_data": {
          "monthly_price": 99.0,
          "pricing_model": "subscription",
          "free_tier": false
        },
        "strengths": [
          "Well-established market presence",
          "Comprehensive HR feature set",
          "Strong customer base"
        ],
        "weaknesses": [
          "Higher pricing for small businesses",
          "Complex setup process",
          "Limited AI capabilities"
        ]
      }
    ],
    "market_gaps": [
      {
        "category": "PRICING GAPS",
        "description": "Affordable AI-powered solutions for micro-businesses",
        "opportunity_score": 8.5,
        "recommended_action": "Create a simplified, low-cost tier"
      }
    ],
    "key_insights": [
      "Market validation exists with 3 established competitors",
      "Average competitor pricing is $67/month",
      "AI automation features are underrepresented",
      "Small business segment appears underserved",
      "Freemium models are rare in this space"
    ],
    "positioning_recommendations": [
      "Focus on AI-first approach to differentiate",
      "Target micro-businesses (under 20 employees)",
      "Position pricing below $50/month",
      "Emphasize ease of setup and use",
      "Develop freemium tier for market entry"
    ],
    "execution_time": 12.3
  }
}
```

## 🎯 Key Features in Detail

### 1. AI-Powered Competitor Discovery
- Uses OpenAI GPT-4 to intelligently identify competitors
- Categorizes competitors as direct, indirect, or substitute
- Fallback mechanisms for robust discovery

### 2. Comprehensive Data Collection
- **Financial Data**: Funding, employee count, valuation, founding year
- **Pricing Data**: Subscription costs, pricing models, free tiers
- **Market Presence**: Domain analysis, social media presence

### 3. Parallel Processing
- Concurrent web scraping for maximum speed
- Async data collection from multiple sources
- Rate limiting to respect website policies

### 4. Intelligent Analysis
- SWOT analysis for each competitor
- Market gap identification
- Strategic positioning recommendations
- Actionable insights generation

### 5. Data Sources
- **Primary**: Company websites, pricing pages
- **Secondary**: Crunchbase API, LinkedIn
- **Fallback**: AI estimation when data unavailable

## 🔧 Configuration

Key settings in `config/settings.py`:

```python
# LLM Configuration
llm_model: str = "gpt-4o-mini"
llm_temperature: float = 0.3
max_tokens: int = 2000

# Analysis Configuration
max_competitors: int = 5
min_competitors: int = 3

# Scraping Configuration
request_timeout: int = 15
max_concurrent_requests: int = 5
rate_limit_delay: float = 1.0
```

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["python", "main.py"]
```

### Environment Variables for Production

```bash
# Required
OPENAI_API_KEY=your_openai_key

# Optional
RAPIDAPI_KEY=your_rapidapi_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret

# Configuration
LLM_MODEL=gpt-4o-mini
MAX_COMPETITORS=5
REQUEST_TIMEOUT=15
```

## 📈 Performance

- **Average Analysis Time**: 10-30 seconds
- **Concurrent Requests**: Up to 5 simultaneous scraping operations
- **Rate Limiting**: 1 second delay between requests
- **Timeout Handling**: 15-second timeout per web request

## 🔐 Security Considerations

- API rate limiting (implement in production)
- Input validation and sanitization
- Environment variable protection
- CORS configuration for production
- Error handling without exposing sensitive data

## 🧪 Testing

### Run Example Analysis

```bash
python example_usage.py
```

### API Testing with curl

```bash
# Health check
curl http://localhost:8000/health

# Test competitor analysis
curl -X POST "http://localhost:8000/api/v1/analyze/competitors" \
  -H "Content-Type: application/json" \
  -d '{
    "idea_description": "AI chatbot for customer service",
    "target_market": "E-commerce businesses",
    "industry": "Customer Service Technology"
  }'
```

## 🔄 Workflow Details

The competitor analysis follows this LangGraph workflow:

1. **Discover Competitors** (`discover_competitors_node`)
   - AI-powered competitor identification
   - Categorization (direct/indirect/substitute)
   - Domain validation and cleaning

2. **Scrape Data** (`scrape_data_node`)
   - Parallel data collection
   - Financial data (Crunchbase, LinkedIn)
   - Pricing data (company websites)
   - Fallback mechanisms

3. **Analyze Market** (`analyze_market_node`)
   - SWOT analysis generation
   - Market gap identification
   - Sentiment analysis

4. **Generate Report** (`generate_report_node`)
   - Strategic insights synthesis
   - Positioning recommendations
   - Final report compilation

## 📋 Data Models

### Core Models

- **BusinessInput**: User's business idea and parameters
- **CompetitorBasic**: Basic competitor information
- **FinancialData**: Funding, employees, valuation data
- **PricingData**: Subscription costs and models
- **MarketSentiment**: Social media and review sentiment
- **CompetitorAnalysis**: Complete competitor profile
- **MarketGap**: Identified market opportunities
- **CompetitorReport**: Final analysis output

### API Schemas

- **CompetitorAnalysisRequest**: Input validation
- **CompetitorAnalysisResponse**: Structured output
- **AnalysisStatusResponse**: Async status tracking

## 🎯 Future Enhancements

- [ ] Database integration for caching results
- [ ] Advanced sentiment analysis with social media APIs
- [ ] Competitive positioning visualization
- [ ] Email alerts for competitor changes
- [ ] Multi-language support
- [ ] Industry-specific analysis templates
- [ ] Integration with additional data sources
- [ ] Real-time competitor monitoring
- [ ] Export capabilities (PDF, Excel)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the API documentation at `/docs`

## 🔗 Related Projects

- Frontend Dashboard (coming soon)
- Mobile App (planned)
- Chrome Extension (planned)

---

Built with ❤️ for entrepreneurs worldwide