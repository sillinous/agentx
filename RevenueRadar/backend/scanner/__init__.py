"""Scanner module for repository analysis."""
from .repo_scanner import scan_directory, analyze_project, get_quick_wins, get_tier_summary
from .metadata import extract_metadata, detect_project_type
from .scoring import score_project, generate_opportunities

__all__ = [
    'scan_directory',
    'analyze_project',
    'get_quick_wins',
    'get_tier_summary',
    'extract_metadata',
    'detect_project_type',
    'score_project',
    'generate_opportunities',
]
