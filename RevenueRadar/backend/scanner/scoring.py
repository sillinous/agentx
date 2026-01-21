"""Monetization scoring engine."""
from typing import Any, Dict, Tuple

# Known high-value projects with manual overrides
TIER1_PROJECTS = {
    'FlipFlow': {'min': 5000, 'max': 30000, 'status': 'development'},
    'market-research-ai-webapp': {'min': 3000, 'max': 15000, 'status': 'ready'},
    'PinescriptAutogenLab': {'min': 5000, 'max': 50000, 'status': 'development'},
    'synapse-core': {'min': 10000, 'max': 50000, 'status': 'development'},
    'UnifiedMediaAssetManager': {'min': 3000, 'max': 30000, 'status': 'development'},
}

TIER2_PROJECTS = {
    'AgentOperationsHub': {'min': 10000, 'max': 100000, 'status': 'discovery'},
    'EnhancedGrantSystem': {'min': 5000, 'max': 20000, 'status': 'development'},
    'devops-hub': {'min': 5000, 'max': 25000, 'status': 'ready'},
    'ApiaryFundingAndResearch': {'min': 3000, 'max': 15000, 'status': 'development'},
}

TIER3_PROJECTS = {
    'market-research-agentic-ecosystem': {'min': 10000, 'max': 50000, 'status': 'discovery'},
    'mcp-marketplace': {'min': 5000, 'max': 30000, 'status': 'discovery'},
    'multiAgentStandardsProtocol': {'min': 3000, 'max': 15000, 'status': 'discovery'},
    'AgentFactoryNine': {'min': 5000, 'max': 30000, 'status': 'development'},
}


def calculate_maturity_score(metadata: Dict) -> int:
    """Calculate maturity score (0-100)."""
    score = 0

    if metadata.get('has_tests'):
        score += 20
    if metadata.get('has_docker'):
        score += 15
    if metadata.get('has_readme'):
        score += 10
    if metadata.get('has_ci_cd'):
        score += 15
    if metadata.get('loc_estimate', 0) > 1000:
        score += 10
    if metadata.get('has_typescript'):
        score += 10
    if metadata.get('has_package_json') or metadata.get('has_requirements'):
        score += 10

    # Bonus for having both frontend and backend indicators
    has_frontend = any(t.lower() in ['next.js', 'react', 'vue']
                       for t in metadata.get('tech_stack', []))
    has_backend = any(t.lower() in ['fastapi', 'express', 'django', 'flask']
                      for t in metadata.get('tech_stack', []))
    if has_frontend and has_backend:
        score += 10

    return min(score, 100)


def calculate_revenue_score(metadata: Dict) -> int:
    """Calculate revenue readiness score (0-100)."""
    score = 0

    if metadata.get('has_stripe'):
        score += 30
    if metadata.get('has_auth'):
        score += 15
    if metadata.get('has_api'):
        score += 20
    if metadata.get('has_database'):
        score += 15
    if metadata.get('has_docker'):  # Deployment ready
        score += 10

    # Bonus for AI/ML capabilities (high value)
    ai_tech = ['openai', 'anthropic claude', 'pytorch', 'tensorflow']
    if any(t.lower() in ai_tech for t in metadata.get('tech_stack', [])):
        score += 10

    return min(score, 100)


def calculate_effort_score(metadata: Dict) -> int:
    """Calculate effort score (100 = easy, 0 = hard)."""
    score = 100

    if not metadata.get('has_tests'):
        score -= 10
    if not metadata.get('has_readme'):
        score -= 5
    if not metadata.get('has_auth'):
        score -= 15
    if not metadata.get('has_stripe'):
        score -= 20
    if not metadata.get('has_docker'):
        score -= 10
    if not metadata.get('has_database'):
        score -= 10

    return max(score, 0)


def calculate_overall_score(maturity: int, revenue: int, effort: int) -> int:
    """Calculate overall ROI-focused score."""
    # Weight: revenue potential highest, then effort (ROI focus), then maturity
    return int((maturity * 0.25) + (revenue * 0.40) + (effort * 0.35))


def determine_tier(name: str, overall_score: int) -> str:
    """Determine project tier."""
    # Check manual overrides first
    if name in TIER1_PROJECTS:
        return 'tier1'
    if name in TIER2_PROJECTS:
        return 'tier2'
    if name in TIER3_PROJECTS:
        return 'tier3'

    # Auto-classify based on score
    if overall_score >= 70:
        return 'tier1'
    elif overall_score >= 50:
        return 'tier2'
    else:
        return 'tier3'


def get_revenue_potential(name: str, revenue_score: int) -> Tuple[int, int]:
    """Estimate monthly revenue potential."""
    # Check manual overrides
    if name in TIER1_PROJECTS:
        return TIER1_PROJECTS[name]['min'], TIER1_PROJECTS[name]['max']
    if name in TIER2_PROJECTS:
        return TIER2_PROJECTS[name]['min'], TIER2_PROJECTS[name]['max']
    if name in TIER3_PROJECTS:
        return TIER3_PROJECTS[name]['min'], TIER3_PROJECTS[name]['max']

    # Auto-estimate based on revenue score
    base_min = revenue_score * 30
    base_max = revenue_score * 150
    return base_min, base_max


def get_project_status(name: str, metadata: Dict) -> str:
    """Determine project status."""
    # Check manual overrides
    for tier_dict in [TIER1_PROJECTS, TIER2_PROJECTS, TIER3_PROJECTS]:
        if name in tier_dict:
            return tier_dict[name]['status']

    # Auto-detect
    if metadata.get('has_stripe') and metadata.get('has_docker'):
        return 'ready'
    elif metadata.get('has_api') or metadata.get('has_database'):
        return 'development'
    else:
        return 'discovery'


def score_project(name: str, metadata: Dict) -> Dict[str, Any]:
    """Calculate all scores for a project."""
    maturity = calculate_maturity_score(metadata)
    revenue = calculate_revenue_score(metadata)
    effort = calculate_effort_score(metadata)
    overall = calculate_overall_score(maturity, revenue, effort)
    tier = determine_tier(name, overall)
    rev_min, rev_max = get_revenue_potential(name, revenue)
    status = get_project_status(name, metadata)

    return {
        'maturity_score': maturity,
        'revenue_score': revenue,
        'effort_score': effort,
        'overall_score': overall,
        'tier': tier,
        'status': status,
        'revenue_potential_min': rev_min,
        'revenue_potential_max': rev_max,
    }


def generate_opportunities(name: str, metadata: Dict, scores: Dict) -> list:
    """Generate monetization opportunities for a project."""
    opportunities = []

    if not metadata.get('has_stripe') and scores['revenue_score'] > 30:
        opportunities.append({
            'title': 'Add Stripe payment integration',
            'description': 'Integrate Stripe for subscription billing or one-time payments',
            'category': 'payment',
            'priority': 'high',
            'effort_hours': 16,
            'revenue_impact': 5000,
        })

    if not metadata.get('has_auth') and scores['maturity_score'] > 30:
        opportunities.append({
            'title': 'Implement user authentication',
            'description': 'Add user login/signup with NextAuth or similar',
            'category': 'feature',
            'priority': 'high',
            'effort_hours': 12,
            'revenue_impact': 2000,
        })

    if not metadata.get('has_docker') and scores['maturity_score'] > 40:
        opportunities.append({
            'title': 'Add Docker deployment',
            'description': 'Create Dockerfile and docker-compose for easy deployment',
            'category': 'deployment',
            'priority': 'medium',
            'effort_hours': 8,
            'revenue_impact': 1000,
        })

    if not metadata.get('has_tests') and scores['maturity_score'] > 50:
        opportunities.append({
            'title': 'Add test coverage',
            'description': 'Implement unit and integration tests',
            'category': 'feature',
            'priority': 'medium',
            'effort_hours': 24,
            'revenue_impact': 500,
        })

    if scores['tier'] == 'tier1' and scores['status'] != 'launched':
        opportunities.append({
            'title': 'Deploy to production',
            'description': 'Deploy to Vercel/Railway/AWS for public access',
            'category': 'deployment',
            'priority': 'high',
            'effort_hours': 4,
            'revenue_impact': 3000,
        })

    if not metadata.get('has_readme'):
        opportunities.append({
            'title': 'Create documentation',
            'description': 'Write comprehensive README with setup instructions',
            'category': 'marketing',
            'priority': 'low',
            'effort_hours': 4,
            'revenue_impact': 200,
        })

    # Sort by ROI (revenue_impact / effort_hours)
    opportunities.sort(key=lambda x: x['revenue_impact'] / max(x['effort_hours'], 1), reverse=True)

    return opportunities
