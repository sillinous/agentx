"""Repository scanner for detecting and analyzing projects."""
import os
from pathlib import Path
from typing import List, Dict, Any, Set
from .metadata import extract_metadata, detect_project_type
from .scoring import score_project, generate_opportunities

# Directories to skip
SKIP_DIRS = {
    'node_modules', '.git', '.venv', 'venv', '__pycache__',
    '.next', '.cache', 'dist', 'build', '.turbo', 'coverage',
    '.pytest_cache', '.mypy_cache', 'eggs', '*.egg-info',
    'RevenueRadar',  # Skip self
}

# Files that indicate a project root
PROJECT_INDICATORS = {
    'package.json', 'requirements.txt', 'setup.py', 'pyproject.toml',
    'Cargo.toml', 'go.mod', 'pom.xml', 'build.gradle',
}


def is_project_directory(path: Path) -> bool:
    """Check if directory is a project root."""
    if not path.is_dir():
        return False

    # Skip hidden directories
    if path.name.startswith('.'):
        return False

    # Skip common non-project directories
    if path.name.lower() in {s.lower() for s in SKIP_DIRS}:
        return False

    # Check for project indicator files
    for indicator in PROJECT_INDICATORS:
        if (path / indicator).exists():
            return True

    # Check for common project structures
    has_src = (path / 'src').exists()
    has_app = (path / 'app').exists()
    has_main = any(path.glob('main.*')) or any(path.glob('index.*'))

    return has_src or has_app or has_main


def scan_directory(root_path: str) -> List[Dict[str, Any]]:
    """Scan a directory for projects and extract metadata."""
    root = Path(root_path)
    projects = []
    seen_paths: Set[str] = set()

    if not root.exists():
        return projects

    # First level: direct subdirectories
    for item in root.iterdir():
        if item.name in SKIP_DIRS or item.name.startswith('.'):
            continue

        if item.is_dir() and is_project_directory(item):
            path_str = str(item)
            if path_str not in seen_paths:
                seen_paths.add(path_str)
                project = analyze_project(item)
                if project:
                    projects.append(project)

    return projects


def analyze_project(project_path: Path) -> Dict[str, Any]:
    """Analyze a single project and return full data."""
    name = project_path.name
    metadata = extract_metadata(project_path)
    project_type = detect_project_type(metadata)
    scores = score_project(name, metadata)

    # Generate opportunities
    opportunities = generate_opportunities(name, metadata, scores)

    return {
        'name': name,
        'path': str(project_path),
        'description': metadata.get('description', ''),
        'tech_stack': metadata.get('tech_stack', []),
        'project_type': project_type,
        'metadata': {
            'has_readme': metadata.get('has_readme', False),
            'has_docker': metadata.get('has_docker', False),
            'has_tests': metadata.get('has_tests', False),
            'has_ci_cd': metadata.get('has_ci_cd', False),
            'has_stripe': metadata.get('has_stripe', False),
            'has_auth': metadata.get('has_auth', False),
            'has_api': metadata.get('has_api', False),
            'has_database': metadata.get('has_database', False),
            'loc_estimate': metadata.get('loc_estimate', 0),
        },
        'opportunities': opportunities,
        **scores,
    }


def get_quick_wins(projects: List[Dict], limit: int = 10) -> List[Dict]:
    """Get top opportunities sorted by ROI."""
    all_opportunities = []

    for project in projects:
        for opp in project.get('opportunities', []):
            roi = opp['revenue_impact'] / max(opp['effort_hours'], 1)
            all_opportunities.append({
                **opp,
                'project_name': project['name'],
                'project_id': project.get('id'),
                'roi': roi,
            })

    # Sort by ROI descending
    all_opportunities.sort(key=lambda x: x['roi'], reverse=True)
    return all_opportunities[:limit]


def get_tier_summary(projects: List[Dict]) -> Dict[str, Any]:
    """Get summary by tier."""
    summary = {
        'tier1': {'count': 0, 'projects': [], 'revenue_min': 0, 'revenue_max': 0},
        'tier2': {'count': 0, 'projects': [], 'revenue_min': 0, 'revenue_max': 0},
        'tier3': {'count': 0, 'projects': [], 'revenue_min': 0, 'revenue_max': 0},
    }

    for project in projects:
        tier = project.get('tier', 'tier3')
        if tier in summary:
            summary[tier]['count'] += 1
            summary[tier]['projects'].append(project['name'])
            summary[tier]['revenue_min'] += project.get('revenue_potential_min', 0)
            summary[tier]['revenue_max'] += project.get('revenue_potential_max', 0)

    return summary
