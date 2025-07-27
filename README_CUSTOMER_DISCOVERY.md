# Customer Discovery Feature

## Overview

The Customer Discovery feature enables entrepreneurs to systematically collect, analyze, and act on customer feedback through audio, video, and transcript uploads. It uses AI to extract actionable insights, automatically updates your Business Model Canvas, and provides objective scoring to guide business decisions.

## Key Features

### 🎤 Multi-Format Input Support
- **Audio Files**: MP3, M4A, WAV, WEBM, MPGA, MPEG
- **Video Files**: MP4, WEBM (audio extraction)
- **Text Transcripts**: Direct text input
- **Live Transcription**: Real-time audio processing

### 🧠 AI-Powered Analysis
- **Pain Point Extraction**: Identifies customer frustrations and problems
- **Validation Signal Detection**: Finds evidence supporting/refuting your idea
- **Feature Request Identification**: Captures specific customer needs
- **Competitive Intelligence**: Analyzes mentions of existing solutions
- **Pricing Feedback**: Extracts budget and willingness-to-pay signals

### 📊 Objective Scoring System
- **Frequency Analysis**: How often insights appear across interviews
- **Intensity Scoring**: Emotional weight of customer language
- **Specificity Assessment**: Concrete details vs vague statements
- **Consistency Tracking**: Agreement across similar customers
- **Evidence Quality**: Supporting proof for insights
- **Recency Weighting**: Recent feedback vs older data

### 🔄 Automatic BMC Updates
- **Smart Integration**: Updates Business Model Canvas based on insights
- **Confidence-Based**: Only applies high-confidence updates
- **Evidence-Backed**: Every change supported by customer quotes
- **Preservation Logic**: Maintains validated existing content

### 📈 Discovery Dashboard
- **Progress Tracking**: Interview completion vs targets
- **Quality Metrics**: Insight quality and confidence scores
- **Validation Scores**: Problem confirmation and solution interest
- **Segment Analysis**: Performance by customer segments
- **AI Recommendations**: Next steps based on data

## API Endpoints

### Interview Management

#### Create Interview
```http
POST /api/v1/customer-discovery/interviews
Authorization: Bearer {token}

{
  "customer_profile": {
    "name": "Sarah Johnson",
    "email": "sarah@email.com",
    "segment": "busy_parents",
    "characteristics": ["Working mother", "Time-constrained"],
    "pain_points": ["Meal planning stress", "Food waste"],
    "goals": ["Save time", "Reduce waste"]
  },
  "interview_type": "problem_validation",
  "idea_id": "uuid",
  "platform": "Zoom",
  "notes": "Initial validation interview"
}
```

#### Get Interviews
```http
GET /api/v1/customer-discovery/interviews?idea_id={id}&status=completed&segment=busy_parents
Authorization: Bearer {token}
```

#### Update Interview
```http
PUT /api/v1/customer-discovery/interviews/{interview_id}
Authorization: Bearer {token}

{
  "status": "completed",
  "completed_at": "2025-01-20T15:30:00Z",
  "notes": "Great insights on pain points"
}
```

### File Upload & Transcription

#### Upload Interview File
```http
POST /api/v1/customer-discovery/interviews/{interview_id}/upload
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: [audio/video/transcript file]
file_type: "audio" | "video" | "transcript"
```

#### Transcribe File
```http
POST /api/v1/customer-discovery/transcribe
Authorization: Bearer {token}

{
  "file_id": "uuid",
  "language": "en",
  "enable_speaker_labels": true,
  "enable_timestamps": true
}
```

### AI Analysis

#### Analyze Interview
```http
POST /api/v1/customer-discovery/analyze
Authorization: Bearer {token}

{
  "interview_id": "uuid",
  "force_reanalysis": false
}
```

#### Get Insights
```http
GET /api/v1/customer-discovery/insights?idea_id={id}&insight_type=pain_point&confidence=high&min_impact_score=7.0
Authorization: Bearer {token}
```

### BMC Integration

#### Update BMC from Insights
```http
POST /api/v1/customer-discovery/bmc-update
Authorization: Bearer {token}

{
  "insight_ids": ["uuid1", "uuid2"],
  "apply_updates": true,
  "preview_only": false
}
```

### Dashboard & Analytics

#### Get Discovery Dashboard
```http
GET /api/v1/customer-discovery/dashboard/{idea_id}
Authorization: Bearer {token}
```

### AI Assistant

#### Generate Interview Questions
```http
POST /api/v1/customer-discovery/generate-questions?interview_type=problem_validation&customer_segment=busy_parents&context=meal planning
Authorization: Bearer {token}
```

## Data Models

### Customer Profile
```python
{
  "name": "string",
  "email": "string",
  "age_range": "string",
  "occupation": "string",
  "location": "string",
  "income_range": "string",
  "segment": "busy_parents | remote_workers | students | seniors | entrepreneurs",
  "characteristics": ["string"],
  "pain_points": ["string"],
  "goals": ["string"],
  "current_solutions": ["string"]
}
```

### Extracted Insight
```python
{
  "id": "uuid",
  "interview_id": "uuid",
  "type": "pain_point | validation_point | feature_request | pricing_feedback | competitive_mention",
  "content": "AI summary of insight",
  "quote": "Exact customer quote",
  "context": "Surrounding conversation",
  "confidence": "low | medium | high | very_high",
  "confidence_score": 0.85,
  "impact_score": 8.5,
  "speaker": "customer | interviewer",
  "timestamp": 125.5,
  "tags": ["string"],
  "bmc_impact": {
    "sections": ["value_propositions"],
    "updates": {"specific": "changes"}
  }
}
```

### Interview Analysis
```python
{
  "id": "uuid",
  "interview_id": "uuid",
  "overall_score": 8.5,
  "category_scores": [
    {
      "category": "problem_confirmation",
      "score": 9.2,
      "reasoning": "Strong evidence of problem",
      "supporting_quotes": ["quote1", "quote2"]
    }
  ],
  "key_insights": [ExtractedInsight],
  "pain_points": ["string"],
  "validation_points": ["string"],
  "bmc_updates": {
    "customer_segments": {"updates": "object"},
    "value_propositions": {"updates": "object"}
  },
  "sentiment_analysis": {
    "enthusiasm_level": 0.7,
    "frustration_level": 0.8,
    "skepticism_level": 0.3
  }
}
```

## Scoring Methodology

### Overall Score Calculation
```python
weights = {
    "frequency": 0.25,      # How often mentioned
    "intensity": 0.20,      # Emotional intensity
    "specificity": 0.15,    # Concrete vs vague
    "consistency": 0.15,    # Agreement across interviews
    "evidence": 0.15,       # Quality of supporting evidence
    "recency": 0.10         # Recent vs older feedback
}

overall_score = sum(scores[factor] * weight for factor, weight in weights.items())
```

### Confidence Levels
- **Very High (0.9+)**: Strong evidence, specific examples, consistent patterns
- **High (0.7-0.9)**: Good evidence, some specifics, mostly consistent
- **Medium (0.5-0.7)**: Moderate evidence, general statements, some consistency
- **Low (0-0.5)**: Weak evidence, vague statements, inconsistent

### Impact Scoring (1-10)
- **9-10**: Critical business insights, immediate action required
- **7-8**: Important insights, should influence strategy
- **5-6**: Moderate insights, consider for future planning
- **3-4**: Minor insights, nice-to-know information
- **1-2**: Low-value insights, may be noise

## BMC Auto-Update Rules

### Update Triggers
1. **High Confidence** (≥ 8.0) + **High Impact** (≥ 7.0)
2. **Multiple Supporting Insights** (≥ 3 similar insights)
3. **Cross-Interview Consistency** (≥ 70% agreement)

### Update Logic
- **Additive**: New insights extend existing lists
- **Refinement**: Improved descriptions based on customer language
- **Validation**: Confirms or challenges existing assumptions
- **Evidence-Based**: Every update includes supporting quotes

### Protected Elements
- Previously validated data with high confidence
- Core business model assumptions with strong evidence
- Financial projections and market sizing
- Strategic partnerships and key resources

## Best Practices

### Interview Preparation
1. **Use AI Question Generator** for interview type and segment
2. **Review Previous Insights** to avoid duplication
3. **Set Clear Objectives** for each interview session
4. **Prepare Follow-up Questions** based on dashboard gaps

### Data Collection
1. **Record Interviews** whenever possible for accuracy
2. **Upload Multiple Formats** (audio + video + notes)
3. **Tag Interviews** with relevant keywords
4. **Document Context** around each session

### Analysis Optimization
1. **Review AI Insights** before accepting
2. **Validate High-Impact Findings** with additional interviews
3. **Look for Patterns** across customer segments
4. **Challenge Assumptions** with contradictory evidence

### BMC Integration
1. **Preview Updates** before applying to BMC
2. **Review Confidence Scores** for each change
3. **Maintain Evidence Trail** for all updates
4. **Regular BMC Reviews** after insight batches

## Workflow Example

### 1. Interview Setup
```bash
# Create customer profile
POST /customer-discovery/interviews
{
  "customer_profile": {...},
  "interview_type": "problem_validation",
  "idea_id": "uuid"
}
```

### 2. Generate Questions
```bash
# Get AI-generated questions
POST /customer-discovery/generate-questions
{
  "interview_type": "problem_validation",
  "customer_segment": "busy_parents"
}
```

### 3. Conduct Interview
- Use generated questions as guide
- Record audio/video
- Take additional notes

### 4. Upload & Transcribe
```bash
# Upload interview recording
POST /customer-discovery/interviews/{id}/upload
Content-Type: multipart/form-data
file: interview.mp3
file_type: audio

# Automatic transcription starts
```

### 5. AI Analysis
```bash
# Analyze transcription
POST /customer-discovery/analyze
{
  "interview_id": "uuid"
}
```

### 6. Review Insights
```bash
# Get extracted insights
GET /customer-discovery/insights?interview_id={id}&min_impact_score=7.0
```

### 7. Update BMC
```bash
# Apply high-confidence insights to BMC
POST /customer-discovery/bmc-update
{
  "insight_ids": ["uuid1", "uuid2"],
  "apply_updates": true
}
```

### 8. Dashboard Review
```bash
# Check progress and metrics
GET /customer-discovery/dashboard/{idea_id}
```

## Integration Points

### With Existing Features
- **BMC Updates**: Automatic canvas refinement
- **Persona Analysis**: Enhanced persona characteristics
- **Competitive Analysis**: Validation of competitive insights
- **Market Sizing**: Customer segment validation

### External Integrations
- **Calendar Apps**: Interview scheduling
- **Video Platforms**: Direct recording upload
- **CRM Systems**: Customer profile sync
- **Analytics Tools**: Advanced reporting

## Security & Privacy

### Data Protection
- **Encrypted Storage**: All audio/video files encrypted at rest
- **Access Controls**: User-based data isolation
- **Retention Policies**: Configurable data lifecycle
- **GDPR Compliance**: Customer consent and deletion rights

### Audio Processing
- **Local Transcription**: Option for on-premise processing
- **Data Minimization**: Only necessary data stored
- **Anonymization**: Customer identity protection options
- **Audit Trails**: Complete processing history

## Performance Metrics

### Processing Times
- **Audio Transcription**: ~1-2 minutes per hour of audio
- **AI Analysis**: ~30-60 seconds per transcript
- **Insight Extraction**: ~10-20 seconds per insight type
- **BMC Updates**: ~5-10 seconds per update

### Accuracy Benchmarks
- **Transcription Accuracy**: 95%+ for clear audio
- **Insight Extraction**: 85%+ precision on high-confidence insights
- **Pain Point Detection**: 90%+ recall on explicit pain points
- **Validation Signal**: 80%+ precision on clear validation statements

## Troubleshooting

### Common Issues

#### Low Transcription Quality
- **Cause**: Poor audio quality, background noise
- **Solution**: Use noise-canceling tools, check microphone
- **Fallback**: Manual transcript upload

#### Missing Insights
- **Cause**: Vague language, short interviews
- **Solution**: Use specific probing questions, longer interviews
- **Adjustment**: Lower confidence thresholds temporarily

#### No BMC Updates
- **Cause**: Low confidence scores, conflicting insights
- **Solution**: Collect more consistent data, review thresholds
- **Manual**: Apply updates manually with justification

#### Dashboard Empty
- **Cause**: No completed interviews, analysis failures
- **Solution**: Complete interview workflow, check analysis logs
- **Verification**: Test with sample interview data

## API Rate Limits

### Endpoints
- **File Upload**: 10 files/minute
- **Transcription**: 5 requests/minute
- **Analysis**: 10 requests/minute
- **Dashboard**: 30 requests/minute

### File Limits
- **Audio/Video**: 25MB per file (OpenAI Whisper limit)
- **Transcript**: 100KB per file
- **Concurrent Uploads**: 3 files simultaneously

## Cost Considerations

### OpenAI Usage
- **Transcription**: $0.006 per minute of audio
- **Analysis**: ~$0.01-0.03 per interview (depending on length)
- **Question Generation**: ~$0.001 per request

### Storage Costs
- **Audio Files**: ~1MB per minute
- **Transcripts**: ~1KB per minute
- **Analysis Data**: ~5KB per interview

### Optimization Tips
1. **Compress Audio** before upload when possible
2. **Batch Process** multiple files together
3. **Cache Questions** for similar interview types
4. **Archive Old Files** after transcription

## Testing

### Run Complete Test Suite
```bash
python test_customer_discovery_demo.py
```

### Unit Tests
```bash
pytest tests/customer_discovery/
```

### Integration Tests
```bash
pytest tests/integration/test_customer_discovery_flow.py
```

## Support

### Documentation
- API Reference: `/docs`
- Interactive Testing: `/redoc`
- Code Examples: `examples/customer_discovery/`

### Contact
- Technical Issues: Create GitHub issue
- Feature Requests: Submit enhancement proposal
- Business Questions: Contact product team

---

**Customer Discovery Feature - Turning Customer Conversations into Business Intelligence** 🎤🧠📊 