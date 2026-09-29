"""
Redline Document Analysis Service.
Annotates tender text with inline compliance markers:
- GREEN: Current, valid Indian Standard references
- RED: Outdated/superseded references with auto-fix suggestions
"""
from backend.app.services.redline.redline_service import RedlineService, RedlineAnalysisRequest, RedlineAnalysisResponse

__all__ = ["RedlineService", "RedlineAnalysisRequest", "RedlineAnalysisResponse"]
