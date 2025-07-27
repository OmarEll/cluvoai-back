import re
import statistics
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import Counter, defaultdict

from core.customer_discovery_models import (
    ExtractedInsight, CustomerInterview, InterviewAnalysis, InterviewScore,
    ScoreCategory, ConfidenceLevel, InsightType, CustomerSegment
)


class ObjectiveScoringService:
    """
    Service for objective scoring and validation of customer discovery insights
    Uses data-driven algorithms to minimize bias and provide reliable assessments
    """
    
    def __init__(self):
        # Scoring weights for different factors
        self.scoring_weights = {
            "frequency": 0.25,      # How often mentioned across interviews
            "intensity": 0.20,      # Emotional intensity of language
            "specificity": 0.15,    # Specific examples vs vague statements
            "consistency": 0.15,    # Consistency across similar customers
            "evidence": 0.15,       # Supporting evidence quality
            "recency": 0.10         # Recent vs older feedback
        }
        
        # Keywords for different scoring categories
        self.intensity_keywords = {
            "high": [
                "extremely", "absolutely", "definitely", "constantly", "always",
                "terrible", "horrible", "amazing", "love", "hate", "nightmare",
                "urgent", "critical", "essential", "must have", "can't live without"
            ],
            "medium": [
                "often", "usually", "frequently", "sometimes", "quite",
                "important", "significant", "useful", "helpful", "necessary"
            ],
            "low": [
                "occasionally", "rarely", "might", "could", "maybe",
                "nice to have", "would be good", "slight", "minor"
            ]
        }
        
        # Specificity indicators
        self.specificity_indicators = {
            "high": [
                r"\$\d+", r"\d+%", r"\d+ times", r"\d+ hours", r"\d+ minutes",
                r"every day", r"every week", r"last [tuesday|wednesday|thursday|friday|monday]",
                r"at \d+", r"around \d+", r"exactly", r"specifically"
            ],
            "medium": [
                r"last week", r"this month", r"recently", r"usually",
                r"most of the time", r"often", r"typically"
            ],
            "low": [
                r"sometimes", r"occasionally", r"maybe", r"perhaps",
                r"i think", r"i believe", r"probably"
            ]
        }
        
        # Evidence quality indicators
        self.evidence_indicators = {
            "high": [
                "for example", "specifically", "last time", "yesterday",
                "this happened when", "i remember", "i tried", "i used"
            ],
            "medium": [
                "usually", "typically", "generally", "most times",
                "in my experience", "i find that"
            ],
            "low": [
                "i think", "i believe", "maybe", "probably",
                "i heard", "someone told me", "i assume"
            ]
        }
    
    def calculate_insight_score(
        self,
        insight: ExtractedInsight,
        related_insights: List[ExtractedInsight],
        interview_context: Optional[CustomerInterview] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Calculate objective score for an insight based on multiple factors
        Returns overall score (0-10) and breakdown by factor
        """
        try:
            print(f"📊 Calculating score for insight: {insight.type.value}")
            
            scores = {}
            
            # 1. Frequency Score - How often this insight appears
            scores["frequency"] = self._calculate_frequency_score(insight, related_insights)
            
            # 2. Intensity Score - Emotional intensity of the language
            scores["intensity"] = self._calculate_intensity_score(insight.quote, insight.content)
            
            # 3. Specificity Score - How specific vs vague the insight is
            scores["specificity"] = self._calculate_specificity_score(insight.quote, insight.content)
            
            # 4. Consistency Score - How consistent with other similar insights
            scores["consistency"] = self._calculate_consistency_score(insight, related_insights)
            
            # 5. Evidence Score - Quality of supporting evidence
            scores["evidence"] = self._calculate_evidence_score(insight.quote, insight.context)
            
            # 6. Recency Score - How recent the feedback is
            scores["recency"] = self._calculate_recency_score(insight, interview_context)
            
            # Calculate weighted overall score
            overall_score = sum(
                scores[factor] * weight 
                for factor, weight in self.scoring_weights.items()
            )
            
            # Ensure score is within 0-10 range
            overall_score = max(0.0, min(10.0, overall_score))
            
            print(f"✅ Insight scored: {overall_score:.2f}/10")
            print(f"   Breakdown: {scores}")
            
            return overall_score, scores
            
        except Exception as e:
            print(f"❌ Scoring failed: {e}")
            return 5.0, {"error": "Scoring calculation failed"}
    
    def calculate_validation_confidence(
        self,
        insights: List[ExtractedInsight],
        total_interviews: int,
        segment_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Calculate confidence level for validation based on statistical significance
        """
        try:
            print(f"🎯 Calculating validation confidence from {len(insights)} insights")
            
            if not insights or total_interviews == 0:
                return {
                    "confidence_level": "very_low",
                    "confidence_score": 0.0,
                    "statistical_significance": False,
                    "sample_size_adequacy": "insufficient",
                    "recommendation": "Collect more data"
                }
            
            # Calculate sample size adequacy
            sample_adequacy = self._assess_sample_size_adequacy(
                total_interviews, segment_size
            )
            
            # Calculate pattern consistency
            pattern_consistency = self._calculate_pattern_consistency(insights)
            
            # Calculate insight quality
            avg_insight_quality = sum(insight.impact_score for insight in insights) / len(insights)
            quality_score = avg_insight_quality / 10.0
            
            # Calculate statistical significance
            statistical_significance = self._assess_statistical_significance(
                insights, total_interviews
            )
            
            # Calculate overall confidence
            confidence_factors = {
                "sample_adequacy": sample_adequacy["score"],
                "pattern_consistency": pattern_consistency,
                "insight_quality": quality_score,
                "statistical_significance": statistical_significance
            }
            
            confidence_score = sum(confidence_factors.values()) / len(confidence_factors)
            
            # Determine confidence level
            if confidence_score >= 0.8:
                confidence_level = "very_high"
            elif confidence_score >= 0.65:
                confidence_level = "high"
            elif confidence_score >= 0.45:
                confidence_level = "medium"
            elif confidence_score >= 0.25:
                confidence_level = "low"
            else:
                confidence_level = "very_low"
            
            # Generate recommendations
            recommendations = self._generate_confidence_recommendations(
                confidence_score, sample_adequacy, pattern_consistency, insights
            )
            
            result = {
                "confidence_level": confidence_level,
                "confidence_score": confidence_score,
                "statistical_significance": statistical_significance >= 0.7,
                "sample_size_adequacy": sample_adequacy["level"],
                "pattern_consistency": pattern_consistency,
                "insight_quality": quality_score,
                "factor_breakdown": confidence_factors,
                "recommendations": recommendations,
                "sample_size": total_interviews,
                "insights_analyzed": len(insights)
            }
            
            print(f"✅ Validation confidence calculated: {confidence_level} ({confidence_score:.2f})")
            return result
            
        except Exception as e:
            print(f"❌ Confidence calculation failed: {e}")
            return {
                "confidence_level": "error",
                "confidence_score": 0.0,
                "error": str(e)
            }
    
    def calculate_segment_scores(
        self,
        interviews: List[CustomerInterview],
        segment: CustomerSegment
    ) -> Dict[str, Any]:
        """
        Calculate objective scores for a customer segment
        """
        try:
            print(f"📈 Calculating segment scores for: {segment.value}")
            
            # Filter interviews for this segment
            segment_interviews = [
                interview for interview in interviews
                if interview.customer_profile.segment == segment
            ]
            
            if not segment_interviews:
                return {
                    "segment": segment.value,
                    "sample_size": 0,
                    "scores": {},
                    "confidence": "insufficient_data"
                }
            
            # Aggregate scores across all categories
            category_scores = defaultdict(list)
            
            for interview in segment_interviews:
                if interview.analysis and interview.analysis.category_scores:
                    for score in interview.analysis.category_scores:
                        category_scores[score.category.value].append(score.score)
            
            # Calculate statistics for each category
            segment_scores = {}
            for category, scores in category_scores.items():
                if scores:
                    segment_scores[category] = {
                        "mean": statistics.mean(scores),
                        "median": statistics.median(scores),
                        "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                        "min": min(scores),
                        "max": max(scores),
                        "count": len(scores),
                        "confidence_interval": self._calculate_confidence_interval(scores)
                    }
            
            # Calculate overall segment score
            if segment_scores:
                overall_score = statistics.mean([
                    scores["mean"] for scores in segment_scores.values()
                ])
            else:
                overall_score = 0.0
            
            # Assess segment confidence
            segment_confidence = self._assess_segment_confidence(
                len(segment_interviews), segment_scores
            )
            
            result = {
                "segment": segment.value,
                "sample_size": len(segment_interviews),
                "overall_score": overall_score,
                "category_scores": segment_scores,
                "confidence": segment_confidence,
                "recommendations": self._generate_segment_recommendations(
                    segment, overall_score, segment_confidence, len(segment_interviews)
                )
            }
            
            print(f"✅ Segment scores calculated for {segment.value}: {overall_score:.2f}/10")
            return result
            
        except Exception as e:
            print(f"❌ Segment scoring failed: {e}")
            return {
                "segment": segment.value,
                "error": str(e)
            }
    
    def detect_insight_patterns(
        self,
        insights: List[ExtractedInsight]
    ) -> Dict[str, Any]:
        """
        Detect patterns and trends in insights using statistical analysis
        """
        try:
            print(f"🔍 Detecting patterns in {len(insights)} insights")
            
            patterns = {
                "frequent_themes": self._identify_frequent_themes(insights),
                "sentiment_trends": self._analyze_sentiment_trends(insights),
                "confidence_distribution": self._analyze_confidence_distribution(insights),
                "type_distribution": self._analyze_type_distribution(insights),
                "temporal_patterns": self._analyze_temporal_patterns(insights),
                "correlation_analysis": self._analyze_correlations(insights),
                "outlier_detection": self._detect_outliers(insights)
            }
            
            # Generate pattern insights
            pattern_insights = self._generate_pattern_insights(patterns)
            
            result = {
                "patterns": patterns,
                "insights": pattern_insights,
                "summary": {
                    "total_insights": len(insights),
                    "dominant_theme": patterns["frequent_themes"][0]["theme"] if patterns["frequent_themes"] else "None",
                    "average_confidence": patterns["confidence_distribution"]["average"],
                    "trend_direction": patterns["sentiment_trends"]["overall_trend"]
                }
            }
            
            print(f"✅ Pattern analysis completed")
            return result
            
        except Exception as e:
            print(f"❌ Pattern detection failed: {e}")
            return {"error": str(e)}
    
    def _calculate_frequency_score(
        self,
        insight: ExtractedInsight,
        related_insights: List[ExtractedInsight]
    ) -> float:
        """
        Calculate frequency score based on how often similar insights appear
        """
        try:
            if not related_insights:
                return 5.0  # Neutral score if no related insights
            
            # Count similar insights
            similar_count = 0
            total_insights = len(related_insights)
            
            for related in related_insights:
                if self._are_insights_similar(insight, related):
                    similar_count += 1
            
            # Calculate frequency percentage
            frequency_percentage = similar_count / total_insights if total_insights > 0 else 0
            
            # Convert to 0-10 scale with logarithmic scaling
            if frequency_percentage == 0:
                return 2.0
            elif frequency_percentage < 0.1:
                return 4.0
            elif frequency_percentage < 0.2:
                return 6.0
            elif frequency_percentage < 0.4:
                return 8.0
            else:
                return 10.0
                
        except Exception:
            return 5.0
    
    def _calculate_intensity_score(self, quote: str, content: str) -> float:
        """
        Calculate intensity score based on emotional language
        """
        try:
            text = f"{quote} {content}".lower()
            
            high_intensity_count = sum(
                1 for keyword in self.intensity_keywords["high"]
                if keyword in text
            )
            medium_intensity_count = sum(
                1 for keyword in self.intensity_keywords["medium"]
                if keyword in text
            )
            low_intensity_count = sum(
                1 for keyword in self.intensity_keywords["low"]
                if keyword in text
            )
            
            # Calculate weighted score
            intensity_score = (
                high_intensity_count * 3 +
                medium_intensity_count * 2 +
                low_intensity_count * 1
            )
            
            # Normalize to 0-10 scale
            max_possible_score = 3 * 3  # Assume max 3 high-intensity keywords
            normalized_score = min(10.0, (intensity_score / max_possible_score) * 10)
            
            return max(3.0, normalized_score)  # Minimum score of 3
            
        except Exception:
            return 5.0
    
    def _calculate_specificity_score(self, quote: str, content: str) -> float:
        """
        Calculate specificity score based on concrete details
        """
        try:
            text = f"{quote} {content}".lower()
            
            high_specificity_count = sum(
                1 for pattern in self.specificity_indicators["high"]
                if re.search(pattern, text)
            )
            medium_specificity_count = sum(
                1 for pattern in self.specificity_indicators["medium"]
                if re.search(pattern, text)
            )
            low_specificity_count = sum(
                1 for pattern in self.specificity_indicators["low"]
                if re.search(pattern, text)
            )
            
            # Calculate weighted score
            specificity_score = (
                high_specificity_count * 3 +
                medium_specificity_count * 2 -
                low_specificity_count * 1  # Subtract for vague language
            )
            
            # Normalize to 0-10 scale
            max_possible_score = 2 * 3  # Assume max 2 high-specificity indicators
            normalized_score = max(0, min(10.0, (specificity_score / max_possible_score) * 10))
            
            return max(2.0, normalized_score)  # Minimum score of 2
            
        except Exception:
            return 5.0
    
    def _calculate_consistency_score(
        self,
        insight: ExtractedInsight,
        related_insights: List[ExtractedInsight]
    ) -> float:
        """
        Calculate consistency score based on agreement with similar insights
        """
        try:
            if not related_insights:
                return 5.0
            
            similar_insights = [
                related for related in related_insights
                if self._are_insights_similar(insight, related)
            ]
            
            if not similar_insights:
                return 3.0  # Lower score for unique insights
            
            # Calculate consistency based on impact scores
            scores = [insight.impact_score] + [s.impact_score for s in similar_insights]
            
            if len(scores) < 2:
                return 5.0
            
            # Calculate coefficient of variation (lower is more consistent)
            mean_score = statistics.mean(scores)
            std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
            
            if mean_score == 0:
                return 5.0
            
            cv = std_dev / mean_score
            
            # Convert to 0-10 scale (lower CV = higher consistency)
            consistency_score = max(0.0, 10.0 - (cv * 10))
            
            return consistency_score
            
        except Exception:
            return 5.0
    
    def _calculate_evidence_score(self, quote: str, context: str) -> float:
        """
        Calculate evidence quality score
        """
        try:
            text = f"{quote} {context}".lower()
            
            high_evidence_count = sum(
                1 for indicator in self.evidence_indicators["high"]
                if indicator in text
            )
            medium_evidence_count = sum(
                1 for indicator in self.evidence_indicators["medium"]
                if indicator in text
            )
            low_evidence_count = sum(
                1 for indicator in self.evidence_indicators["low"]
                if indicator in text
            )
            
            # Calculate weighted score
            evidence_score = (
                high_evidence_count * 3 +
                medium_evidence_count * 2 -
                low_evidence_count * 1  # Subtract for weak evidence
            )
            
            # Normalize to 0-10 scale
            normalized_score = max(0, min(10.0, evidence_score * 2))
            
            return max(3.0, normalized_score)  # Minimum score of 3
            
        except Exception:
            return 5.0
    
    def _calculate_recency_score(
        self,
        insight: ExtractedInsight,
        interview_context: Optional[CustomerInterview]
    ) -> float:
        """
        Calculate recency score (more recent = higher score)
        """
        try:
            if not interview_context or not interview_context.completed_at:
                return 7.0  # Default score if no date info
            
            days_ago = (datetime.utcnow() - interview_context.completed_at).days
            
            if days_ago <= 7:
                return 10.0
            elif days_ago <= 30:
                return 8.0
            elif days_ago <= 90:
                return 6.0
            elif days_ago <= 180:
                return 4.0
            else:
                return 2.0
                
        except Exception:
            return 7.0
    
    def _are_insights_similar(
        self,
        insight1: ExtractedInsight,
        insight2: ExtractedInsight
    ) -> bool:
        """
        Determine if two insights are similar
        """
        try:
            # Same type is a strong indicator
            if insight1.type != insight2.type:
                return False
            
            # Check content similarity using simple keyword matching
            words1 = set(insight1.content.lower().split())
            words2 = set(insight2.content.lower().split())
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            similarity = intersection / union if union > 0 else 0
            
            return similarity > 0.3  # 30% similarity threshold
            
        except Exception:
            return False
    
    def _assess_sample_size_adequacy(
        self,
        sample_size: int,
        population_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Assess if sample size is adequate for statistical significance
        """
        # Basic sample size adequacy rules
        if sample_size >= 30:
            level = "excellent"
            score = 1.0
        elif sample_size >= 15:
            level = "good"
            score = 0.8
        elif sample_size >= 8:
            level = "adequate"
            score = 0.6
        elif sample_size >= 5:
            level = "minimal"
            score = 0.4
        else:
            level = "insufficient"
            score = 0.2
        
        return {
            "level": level,
            "score": score,
            "sample_size": sample_size,
            "recommendation": self._get_sample_size_recommendation(level, sample_size)
        }
    
    def _calculate_pattern_consistency(self, insights: List[ExtractedInsight]) -> float:
        """
        Calculate how consistent patterns are across insights
        """
        try:
            if len(insights) < 2:
                return 0.5
            
            # Group insights by type
            type_groups = defaultdict(list)
            for insight in insights:
                type_groups[insight.type].append(insight)
            
            # Calculate consistency within each type
            type_consistencies = []
            
            for insight_type, group_insights in type_groups.items():
                if len(group_insights) > 1:
                    scores = [insight.impact_score for insight in group_insights]
                    consistency = 1 - (statistics.stdev(scores) / 10.0) if len(scores) > 1 else 1.0
                    type_consistencies.append(max(0.0, consistency))
            
            return statistics.mean(type_consistencies) if type_consistencies else 0.5
            
        except Exception:
            return 0.5
    
    def _assess_statistical_significance(
        self,
        insights: List[ExtractedInsight],
        total_interviews: int
    ) -> float:
        """
        Assess statistical significance of patterns
        """
        try:
            if total_interviews < 5:
                return 0.2
            
            # Calculate significance based on sample size and pattern strength
            high_confidence_insights = sum(
                1 for insight in insights
                if insight.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
            )
            
            confidence_ratio = high_confidence_insights / len(insights) if insights else 0
            sample_factor = min(1.0, total_interviews / 15)  # 15 is ideal sample size
            
            significance = confidence_ratio * sample_factor
            
            return min(1.0, significance)
            
        except Exception:
            return 0.5
    
    def _generate_confidence_recommendations(
        self,
        confidence_score: float,
        sample_adequacy: Dict[str, Any],
        pattern_consistency: float,
        insights: List[ExtractedInsight]
    ) -> List[str]:
        """
        Generate recommendations based on confidence analysis
        """
        recommendations = []
        
        if confidence_score < 0.5:
            recommendations.append("Collect more customer interviews to increase confidence")
        
        if sample_adequacy["score"] < 0.6:
            recommendations.append(f"Increase sample size (current: {sample_adequacy['sample_size']}, recommended: 15+)")
        
        if pattern_consistency < 0.6:
            recommendations.append("Look for more consistent patterns across customer segments")
        
        low_quality_insights = sum(
            1 for insight in insights if insight.impact_score < 5.0
        )
        if low_quality_insights > len(insights) * 0.3:
            recommendations.append("Focus on higher-quality insights with stronger evidence")
        
        if confidence_score >= 0.8:
            recommendations.append("High confidence - proceed with business decisions based on these insights")
        
        return recommendations
    
    def _assess_segment_confidence(
        self,
        sample_size: int,
        segment_scores: Dict[str, Any]
    ) -> str:
        """
        Assess confidence level for segment analysis
        """
        if sample_size < 3:
            return "very_low"
        elif sample_size < 5:
            return "low"
        elif sample_size < 8:
            return "medium"
        elif sample_size < 12:
            return "high"
        else:
            return "very_high"
    
    def _generate_segment_recommendations(
        self,
        segment: CustomerSegment,
        overall_score: float,
        confidence: str,
        sample_size: int
    ) -> List[str]:
        """
        Generate recommendations for segment analysis
        """
        recommendations = []
        
        if confidence in ["very_low", "low"]:
            recommendations.append(f"Interview more {segment.value.replace('_', ' ')} customers (current: {sample_size})")
        
        if overall_score >= 8.0:
            recommendations.append(f"{segment.value.replace('_', ' ').title()} is a high-potential segment")
        elif overall_score <= 4.0:
            recommendations.append(f"Consider deprioritizing {segment.value.replace('_', ' ')} segment")
        
        return recommendations
    
    def _calculate_confidence_interval(self, scores: List[float], confidence: float = 0.95) -> Tuple[float, float]:
        """
        Calculate confidence interval for scores
        """
        try:
            if len(scores) < 2:
                return (0.0, 0.0)
            
            mean = statistics.mean(scores)
            std_dev = statistics.stdev(scores)
            n = len(scores)
            
            # Use t-distribution for small samples
            from scipy import stats
            t_value = stats.t.ppf((1 + confidence) / 2, n - 1)
            margin_error = t_value * (std_dev / (n ** 0.5))
            
            return (mean - margin_error, mean + margin_error)
            
        except Exception:
            return (0.0, 0.0)
    
    def _identify_frequent_themes(self, insights: List[ExtractedInsight]) -> List[Dict[str, Any]]:
        """
        Identify frequently mentioned themes
        """
        try:
            # Extract keywords from insights
            all_words = []
            for insight in insights:
                words = insight.content.lower().split()
                all_words.extend([word for word in words if len(word) > 3])
            
            # Count frequency
            word_counts = Counter(all_words)
            
            # Get top themes
            themes = []
            for word, count in word_counts.most_common(10):
                themes.append({
                    "theme": word,
                    "frequency": count,
                    "percentage": count / len(insights) if insights else 0
                })
            
            return themes
            
        except Exception:
            return []
    
    def _analyze_sentiment_trends(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Analyze sentiment trends in insights
        """
        try:
            # Simple sentiment analysis based on insight types and scores
            positive_insights = sum(
                1 for insight in insights
                if insight.type == InsightType.VALIDATION_POINT and insight.impact_score >= 7
            )
            negative_insights = sum(
                1 for insight in insights
                if insight.type == InsightType.PAIN_POINT and insight.impact_score >= 7
            )
            
            total_insights = len(insights)
            
            if total_insights == 0:
                return {"overall_trend": "neutral", "positive_ratio": 0, "negative_ratio": 0}
            
            positive_ratio = positive_insights / total_insights
            negative_ratio = negative_insights / total_insights
            
            if positive_ratio > negative_ratio * 1.5:
                trend = "positive"
            elif negative_ratio > positive_ratio * 1.5:
                trend = "negative"
            else:
                trend = "neutral"
            
            return {
                "overall_trend": trend,
                "positive_ratio": positive_ratio,
                "negative_ratio": negative_ratio,
                "neutral_ratio": 1 - positive_ratio - negative_ratio
            }
            
        except Exception:
            return {"overall_trend": "neutral", "positive_ratio": 0, "negative_ratio": 0}
    
    def _analyze_confidence_distribution(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Analyze distribution of confidence levels
        """
        try:
            confidence_counts = Counter(insight.confidence for insight in insights)
            total = len(insights)
            
            distribution = {}
            average_score = 0
            
            for confidence, count in confidence_counts.items():
                percentage = count / total if total > 0 else 0
                distribution[confidence.value] = {
                    "count": count,
                    "percentage": percentage
                }
                
                # Convert to numeric for average
                confidence_numeric = {
                    ConfidenceLevel.VERY_HIGH: 4,
                    ConfidenceLevel.HIGH: 3,
                    ConfidenceLevel.MEDIUM: 2,
                    ConfidenceLevel.LOW: 1
                }.get(confidence, 2)
                
                average_score += confidence_numeric * count
            
            average_confidence = average_score / total if total > 0 else 0
            
            return {
                "distribution": distribution,
                "average": average_confidence,
                "total_insights": total
            }
            
        except Exception:
            return {"distribution": {}, "average": 0, "total_insights": 0}
    
    def _analyze_type_distribution(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Analyze distribution of insight types
        """
        try:
            type_counts = Counter(insight.type for insight in insights)
            total = len(insights)
            
            distribution = {}
            for insight_type, count in type_counts.items():
                percentage = count / total if total > 0 else 0
                distribution[insight_type.value] = {
                    "count": count,
                    "percentage": percentage
                }
            
            return {
                "distribution": distribution,
                "total_insights": total,
                "dominant_type": max(type_counts, key=type_counts.get).value if type_counts else None
            }
            
        except Exception:
            return {"distribution": {}, "total_insights": 0, "dominant_type": None}
    
    def _analyze_temporal_patterns(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Analyze temporal patterns in insights
        """
        try:
            # Group insights by creation date
            insights_by_date = defaultdict(list)
            for insight in insights:
                date_key = insight.created_at.date() if insight.created_at else datetime.utcnow().date()
                insights_by_date[date_key].append(insight)
            
            # Calculate daily counts
            daily_counts = {
                date.isoformat(): len(insights_list)
                for date, insights_list in insights_by_date.items()
            }
            
            return {
                "daily_counts": daily_counts,
                "total_days": len(daily_counts),
                "average_per_day": len(insights) / len(daily_counts) if daily_counts else 0
            }
            
        except Exception:
            return {"daily_counts": {}, "total_days": 0, "average_per_day": 0}
    
    def _analyze_correlations(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Analyze correlations between different insight characteristics
        """
        try:
            if len(insights) < 3:
                return {"correlations": {}, "note": "Insufficient data for correlation analysis"}
            
            # Convert categorical data to numeric
            confidence_scores = []
            impact_scores = []
            type_scores = []
            
            type_mapping = {
                InsightType.PAIN_POINT: 1,
                InsightType.VALIDATION_POINT: 2,
                InsightType.FEATURE_REQUEST: 3,
                InsightType.PRICING_FEEDBACK: 4,
                InsightType.COMPETITIVE_MENTION: 5
            }
            
            confidence_mapping = {
                ConfidenceLevel.LOW: 1,
                ConfidenceLevel.MEDIUM: 2,
                ConfidenceLevel.HIGH: 3,
                ConfidenceLevel.VERY_HIGH: 4
            }
            
            for insight in insights:
                confidence_scores.append(confidence_mapping.get(insight.confidence, 2))
                impact_scores.append(insight.impact_score)
                type_scores.append(type_mapping.get(insight.type, 1))
            
            # Calculate correlations
            correlations = {}
            
            if len(set(confidence_scores)) > 1 and len(set(impact_scores)) > 1:
                conf_impact_corr = np.corrcoef(confidence_scores, impact_scores)[0, 1]
                correlations["confidence_impact"] = float(conf_impact_corr) if not np.isnan(conf_impact_corr) else 0
            
            return {
                "correlations": correlations,
                "sample_size": len(insights)
            }
            
        except Exception:
            return {"correlations": {}, "error": "Correlation analysis failed"}
    
    def _detect_outliers(self, insights: List[ExtractedInsight]) -> Dict[str, Any]:
        """
        Detect outlier insights that deviate significantly from patterns
        """
        try:
            if len(insights) < 5:
                return {"outliers": [], "note": "Insufficient data for outlier detection"}
            
            impact_scores = [insight.impact_score for insight in insights]
            
            # Calculate IQR method outliers
            q1 = np.percentile(impact_scores, 25)
            q3 = np.percentile(impact_scores, 75)
            iqr = q3 - q1
            
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = []
            for insight in insights:
                if insight.impact_score < lower_bound or insight.impact_score > upper_bound:
                    outliers.append({
                        "insight_id": insight.id,
                        "type": insight.type.value,
                        "impact_score": insight.impact_score,
                        "reason": "significantly_different_impact_score"
                    })
            
            return {
                "outliers": outliers,
                "outlier_count": len(outliers),
                "outlier_percentage": len(outliers) / len(insights) if insights else 0
            }
            
        except Exception:
            return {"outliers": [], "error": "Outlier detection failed"}
    
    def _generate_pattern_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """
        Generate actionable insights from pattern analysis
        """
        insights = []
        
        try:
            # Frequent themes insight
            if patterns.get("frequent_themes"):
                top_theme = patterns["frequent_themes"][0]
                insights.append(f"Most frequent theme: '{top_theme['theme']}' mentioned in {top_theme['percentage']:.1%} of insights")
            
            # Confidence insight
            confidence_dist = patterns.get("confidence_distribution", {})
            if confidence_dist.get("average", 0) >= 3:
                insights.append("High confidence in insights - data quality is strong")
            elif confidence_dist.get("average", 0) <= 2:
                insights.append("Low confidence in insights - consider gathering more specific evidence")
            
            # Type distribution insight
            type_dist = patterns.get("type_distribution", {})
            if type_dist.get("dominant_type"):
                insights.append(f"Majority of insights are {type_dist['dominant_type'].replace('_', ' ')}")
            
            # Sentiment insight
            sentiment = patterns.get("sentiment_trends", {})
            if sentiment.get("overall_trend") == "positive":
                insights.append("Overall positive sentiment - customers show validation signals")
            elif sentiment.get("overall_trend") == "negative":
                insights.append("Overall negative sentiment - focus on addressing pain points")
            
            # Outlier insight
            outliers = patterns.get("outlier_detection", {})
            if outliers.get("outlier_percentage", 0) > 0.2:
                insights.append("High number of outlier insights - investigate unusual patterns")
            
        except Exception:
            insights.append("Pattern analysis completed with limited insights")
        
        return insights
    
    def _get_sample_size_recommendation(self, level: str, current_size: int) -> str:
        """
        Get recommendation for sample size improvement
        """
        recommendations = {
            "insufficient": f"Interview at least {max(5, current_size + 3)} more customers",
            "minimal": f"Interview {max(3, 8 - current_size)} more customers for better confidence",
            "adequate": "Consider 3-5 more interviews for higher confidence",
            "good": "Sample size is good, focus on interview quality",
            "excellent": "Excellent sample size for statistical significance"
        }
        
        return recommendations.get(level, "Continue collecting customer feedback")


# Create singleton instance
scoring_service = ObjectiveScoringService() 