"""
Custom exceptions for Cluvo.ai
"""


class CluvoBaseException(Exception):
    """Base exception for Cluvo.ai"""
    pass


class CompetitorDiscoveryError(CluvoBaseException):
    """Raised when competitor discovery fails"""
    pass


class DataScrapingError(CluvoBaseException):
    """Raised when data scraping fails"""
    pass


class AnalysisError(CluvoBaseException):
    """Raised when analysis fails"""
    pass


class ReportGenerationError(CluvoBaseException):
    """Raised when report generation fails"""
    pass


class APIKeyError(CluvoBaseException):
    """Raised when API keys are missing or invalid"""
    pass


class RateLimitError(CluvoBaseException):
    """Raised when rate limits are exceeded"""
    pass