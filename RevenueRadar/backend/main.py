"""RevenueRadar - Monetization Opportunity Dashboard API."""
import os
import logging
import subprocess
import shlex
from enum import Enum
from pathlib import Path
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator


# ============ Enums for Validation ============

class ProjectTier(str, Enum):
    """Project tier classification."""
    TIER1 = "tier1"
    TIER2 = "tier2"
    TIER3 = "tier3"


class ProjectStatus(str, Enum):
    """Project lifecycle status."""
    DISCOVERY = "discovery"
    DEVELOPMENT = "development"
    READY = "ready"
    LAUNCHED = "launched"


class OpportunityStatus(str, Enum):
    """Opportunity pipeline status."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


class OpportunityPriority(str, Enum):
    """Opportunity priority level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpportunityCategory(str, Enum):
    """Opportunity category type."""
    PAYMENT = "payment"
    DEPLOYMENT = "deployment"
    FEATURE = "feature"
    MARKETING = "marketing"

from db.database import (
    get_all_projects, get_project_by_id, upsert_project,
    get_opportunities_for_project, get_all_opportunities,
    create_opportunity, update_opportunity_status, get_statistics
)
from scanner import scan_directory, get_quick_wins, get_tier_summary

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "Health",
        "description": "Service health and status checks.",
    },
    {
        "name": "Projects",
        "description": "Manage portfolio projects. Scan, list, filter, and update projects.",
    },
    {
        "name": "Analytics",
        "description": "Portfolio analytics and insights. KPIs, tier distribution, and quick wins.",
    },
    {
        "name": "Opportunities",
        "description": "Monetization opportunities management. Track progress through the pipeline.",
    },
    {
        "name": "Actions",
        "description": "Execute predefined actions on projects. Deploy, test, and install dependencies.",
    },
]

app = FastAPI(
    title="RevenueRadar API",
    description="""
## Portfolio Monetization Dashboard API

RevenueRadar helps you identify, analyze, and track monetization opportunities across your project portfolio.

### Features

* **Project Scanning** - Automatically detect and analyze projects in your repository
* **Scoring Engine** - Multi-factor scoring for maturity, revenue readiness, and implementation effort
* **Tier Classification** - Categorize projects into Tier 1 (immediate revenue), Tier 2 (high priority), Tier 3 (scalable)
* **Opportunity Tracking** - Pipeline management for monetization opportunities
* **Quick Actions** - Execute predefined deployment and setup actions

### Documentation

* **Swagger UI**: [/docs](/docs)
* **ReDoc**: [/redoc](/redoc)
* **OpenAPI JSON**: [/openapi.json](/openapi.json)
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://localhost:3003"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Default scan path
DEFAULT_SCAN_PATH = os.environ.get(
    "SCAN_PATH",
    "/mnt/c/GitHub/GitHubRoot/sillinous"
)


# ============ Models ============

class ProjectUpdate(BaseModel):
    """Update project metadata with validated fields."""
    status: Optional[ProjectStatus] = None
    tier: Optional[ProjectTier] = None
    description: Optional[str] = None

    class Config:
        use_enum_values = True


class OpportunityCreate(BaseModel):
    """Create a new monetization opportunity with validated fields."""
    project_id: str
    title: str
    description: Optional[str] = None
    category: Optional[OpportunityCategory] = OpportunityCategory.FEATURE
    priority: Optional[OpportunityPriority] = OpportunityPriority.MEDIUM
    effort_hours: Optional[int] = 8
    revenue_impact: Optional[int] = 0

    class Config:
        use_enum_values = True


class OpportunityStatusUpdate(BaseModel):
    """Update opportunity status with validated status value."""
    status: OpportunityStatus

    class Config:
        use_enum_values = True


class ActionExecute(BaseModel):
    """Request model for action execution with validation."""
    template_key: str  # Must be a valid key from ACTION_TEMPLATES
    project_path: str  # Required project path

    @field_validator('template_key')
    @classmethod
    def validate_template_key(cls, v: str) -> str:
        # Will be validated against ACTION_TEMPLATES at runtime
        if not v or not v.strip():
            raise ValueError('template_key cannot be empty')
        return v.strip()

    @field_validator('project_path')
    @classmethod
    def validate_project_path(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('project_path is required')
        # Basic path traversal prevention
        if '..' in v or v.startswith('/etc') or v.startswith('/root'):
            raise ValueError('Invalid project path')
        return v.strip()


# ============ Health ============

@app.get("/api/health", tags=["Health"])
async def health():
    """
    Health check endpoint.

    Returns the service status for monitoring and load balancers.
    """
    return {"status": "healthy", "service": "RevenueRadar"}


# ============ Projects ============

@app.get("/api/projects", tags=["Projects"])
async def list_projects(
    tier: Optional[ProjectTier] = Query(None, description="Filter by tier"),
    status: Optional[ProjectStatus] = Query(None, description="Filter by status"),
    sort_by: str = Query("overall_score", regex="^(overall_score|revenue_score|maturity_score|name)$", description="Sort field"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """
    List all projects with optional filtering and sorting.

    Returns paginated list of projects with their scores and metadata.
    """
    logger.debug(f"Listing projects: tier={tier}, status={status}, sort_by={sort_by}, order={order}")
    projects = get_all_projects()

    # Filter
    if tier:
        projects = [p for p in projects if p['tier'] == tier.value]
    if status:
        projects = [p for p in projects if p['status'] == status.value]

    # Sort
    reverse = order == "desc"
    if sort_by == "name":
        projects.sort(key=lambda x: x['name'].lower(), reverse=reverse)
    else:
        projects.sort(key=lambda x: x.get(sort_by, 0), reverse=reverse)

    logger.info(f"Listed {len(projects)} projects")
    return {"projects": projects, "total": len(projects)}


@app.get("/api/projects/{project_id}", tags=["Projects"])
async def get_project(project_id: str):
    """
    Get project details with opportunities.

    Returns full project information including scores, metadata, and associated opportunities.
    """
    logger.debug(f"Getting project: {project_id}")
    project = get_project_by_id(project_id)
    if not project:
        logger.warning(f"Project not found: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    opportunities = get_opportunities_for_project(project_id)
    logger.info(f"Retrieved project '{project['name']}' with {len(opportunities)} opportunities")
    return {**project, "opportunities": opportunities}


@app.patch("/api/projects/{project_id}", tags=["Projects"])
async def update_project(project_id: str, update: ProjectUpdate):
    """
    Update project metadata.

    Allows updating status, tier, and description.
    """
    logger.debug(f"Updating project: {project_id}")
    project = get_project_by_id(project_id)
    if not project:
        logger.warning(f"Project not found for update: {project_id}")
        raise HTTPException(status_code=404, detail="Project not found")

    changes = []
    if update.status:
        changes.append(f"status: {project['status']} -> {update.status}")
        project['status'] = update.status
    if update.tier:
        changes.append(f"tier: {project['tier']} -> {update.tier}")
        project['tier'] = update.tier
    if update.description:
        changes.append("description updated")
        project['description'] = update.description

    upsert_project(project)
    logger.info(f"Updated project '{project['name']}': {', '.join(changes) if changes else 'no changes'}")
    return {"success": True, "project": project}


@app.post("/api/projects/scan", tags=["Projects"])
async def scan_projects(path: Optional[str] = Query(None, description="Path to scan (defaults to configured SCAN_PATH)")):
    """
    Scan directory for projects and update database.

    Discovers projects, analyzes their metadata, calculates scores,
    and generates monetization opportunities.
    """
    scan_path = path or DEFAULT_SCAN_PATH
    logger.info(f"Starting project scan at: {scan_path}")

    if not Path(scan_path).exists():
        logger.error(f"Scan path does not exist: {scan_path}")
        raise HTTPException(status_code=400, detail=f"Path does not exist: {scan_path}")

    projects = scan_directory(scan_path)
    logger.info(f"Discovered {len(projects)} projects")

    # Store projects
    stored_ids = []
    total_opportunities = 0
    for project in projects:
        opportunities = project.pop('opportunities', [])
        project_id = upsert_project(project)
        stored_ids.append(project_id)

        # Create opportunities
        for opp in opportunities:
            opp['project_id'] = project_id
            create_opportunity(opp)
        total_opportunities += len(opportunities)

    logger.info(f"Scan complete: {len(projects)} projects, {total_opportunities} opportunities stored")
    return {
        "success": True,
        "scanned_path": scan_path,
        "projects_found": len(projects),
        "project_ids": stored_ids
    }


# ============ Analytics ============

@app.get("/api/analytics/overview", tags=["Analytics"])
async def get_overview():
    """
    Get portfolio overview KPIs.

    Returns total projects, tier distribution, status breakdown,
    revenue potential, and average scores.
    """
    stats = get_statistics()
    projects = get_all_projects()
    tier_summary = get_tier_summary(projects)

    return {
        "total_projects": stats['total_projects'],
        "by_tier": stats['by_tier'],
        "by_status": stats['by_status'],
        "revenue_potential": stats['revenue_potential'],
        "avg_scores": stats['avg_scores'],
        "tier_summary": tier_summary,
    }


@app.get("/api/analytics/quickwins", tags=["Analytics"])
async def get_quick_wins_api(limit: int = Query(10, description="Maximum number of results")):
    """
    Get top project opportunities sorted by ROI.

    Each project is consolidated as one opportunity with aggregated metrics.
    Sorted by ROI (revenue_impact / effort_hours) descending.
    """
    projects = get_all_projects()
    opportunities = get_all_opportunities()

    # Group opportunities by project
    project_opps = {}
    for opp in opportunities:
        pid = opp['project_id']
        if pid not in project_opps:
            project_opps[pid] = []
        project_opps[pid].append(opp)

    # Build consolidated opportunities (one per project)
    consolidated = []
    for project in projects:
        pid = project['id']
        action_items = project_opps.get(pid, [])

        # Calculate totals for this project opportunity
        total_effort = sum(a['effort_hours'] for a in action_items) or 1
        total_revenue = sum(a['revenue_impact'] for a in action_items)
        pending_count = sum(1 for a in action_items if a['status'] == 'pending')
        completed_count = sum(1 for a in action_items if a['status'] == 'completed')

        # Add revenue potential from project scores
        total_revenue += project.get('revenue_potential_min', 0)

        consolidated.append({
            'id': pid,
            'name': project['name'],
            'description': project.get('description', ''),
            'tier': project['tier'],
            'status': project['status'],
            'overall_score': project['overall_score'],
            'revenue_potential_min': project.get('revenue_potential_min', 0),
            'revenue_potential_max': project.get('revenue_potential_max', 0),
            'tech_stack': project.get('tech_stack', []),
            'total_effort_hours': total_effort,
            'total_revenue_impact': total_revenue,
            'roi': total_revenue / total_effort,
            'action_items': action_items,
            'action_count': len(action_items),
            'pending_actions': pending_count,
            'completed_actions': completed_count,
            'progress': f"{completed_count}/{len(action_items)}" if action_items else "0/0",
        })

    # Sort by ROI (highest first)
    consolidated.sort(key=lambda x: x['roi'], reverse=True)

    return {"opportunities": consolidated[:limit], "total": len(consolidated)}


@app.get("/api/analytics/tiers", tags=["Analytics"])
async def get_tier_distribution():
    """
    Get tier distribution data.

    Returns project counts and revenue potential by tier.
    """
    projects = get_all_projects()
    tier_summary = get_tier_summary(projects)
    return {"tiers": tier_summary}


# ============ Opportunities ============

@app.get("/api/opportunities", tags=["Opportunities"])
async def list_opportunities(
    status: Optional[OpportunityStatus] = Query(None, description="Filter by status"),
    priority: Optional[OpportunityPriority] = Query(None, description="Filter by priority")
):
    """
    List all opportunities with optional filtering.

    Returns opportunities with project names for easy reference.
    """
    opportunities = get_all_opportunities()

    if status:
        opportunities = [o for o in opportunities if o['status'] == status.value]
    if priority:
        opportunities = [o for o in opportunities if o['priority'] == priority.value]

    return {"opportunities": opportunities, "total": len(opportunities)}


@app.post("/api/opportunities", tags=["Opportunities"])
async def add_opportunity(opp: OpportunityCreate):
    """
    Create a new opportunity.

    Manually add a monetization opportunity to a project.
    """
    logger.info(f"Creating opportunity '{opp.title}' for project {opp.project_id}")
    opp_id = create_opportunity(opp.dict())
    logger.info(f"Created opportunity {opp_id}")
    return {"success": True, "opportunity_id": opp_id}


@app.patch("/api/opportunities/{opp_id}", tags=["Opportunities"])
async def update_opportunity(opp_id: str, update: OpportunityStatusUpdate):
    """
    Update opportunity status.

    Move opportunities through the pipeline: pending -> in_progress -> completed.
    """
    logger.info(f"Updating opportunity {opp_id} status to '{update.status}'")
    success = update_opportunity_status(opp_id, update.status)
    if not success:
        logger.warning(f"Opportunity not found: {opp_id}")
        raise HTTPException(status_code=404, detail="Opportunity not found")
    logger.info(f"Updated opportunity {opp_id} status to '{update.status}'")
    return {"success": True}


@app.get("/api/opportunities/pipeline", tags=["Opportunities"])
async def get_pipeline():
    """
    Get opportunities grouped by status for pipeline/Kanban view.

    Returns opportunities organized by status: pending, in_progress, completed, blocked.
    """
    opportunities = get_all_opportunities()

    pipeline = {
        'pending': [],
        'in_progress': [],
        'completed': [],
        'blocked': []
    }

    for opp in opportunities:
        status = opp.get('status', 'pending')
        if status in pipeline:
            pipeline[status].append(opp)

    return {"pipeline": pipeline}


# ============ Actions ============

# Allowed scan root directories (security whitelist)
ALLOWED_SCAN_ROOTS = [
    "/repos",  # Docker mount
    "/mnt/c/GitHub/GitHubRoot/sillinous",  # WSL path
    "C:\\GitHub\\GitHubRoot\\sillinous",  # Windows path
]

# Secure action templates using argument lists (no shell=True)
ACTION_TEMPLATES = {
    'deploy_vercel': {
        'title': 'Deploy to Vercel',
        'description': 'Deploy the project to Vercel production',
        'command_args': ['vercel', '--prod'],
        'requires_npm': False
    },
    'add_stripe': {
        'title': 'Add Stripe Package',
        'description': 'Install Stripe payment libraries',
        'command_args': ['npm', 'install', 'stripe', '@stripe/stripe-js'],
        'requires_npm': True
    },
    'add_docker': {
        'title': 'Initialize Docker',
        'description': 'Initialize Docker configuration',
        'command_args': ['docker', 'init'],
        'requires_npm': False
    },
    'run_tests_npm': {
        'title': 'Run Tests (npm)',
        'description': 'Run npm test suite',
        'command_args': ['npm', 'test'],
        'requires_npm': True
    },
    'run_tests_pytest': {
        'title': 'Run Tests (pytest)',
        'description': 'Run Python pytest suite',
        'command_args': ['pytest'],
        'requires_npm': False
    },
    'install_npm': {
        'title': 'Install npm Dependencies',
        'description': 'Install Node.js dependencies',
        'command_args': ['npm', 'install'],
        'requires_npm': True
    },
    'install_pip': {
        'title': 'Install pip Dependencies',
        'description': 'Install Python dependencies from requirements.txt',
        'command_args': ['pip', 'install', '-r', 'requirements.txt'],
        'requires_npm': False
    }
}


def is_path_allowed(project_path: str) -> bool:
    """Check if project path is within allowed directories."""
    normalized = os.path.normpath(os.path.abspath(project_path))
    for allowed_root in ALLOWED_SCAN_ROOTS:
        allowed_normalized = os.path.normpath(os.path.abspath(allowed_root))
        if normalized.startswith(allowed_normalized):
            return True
    return False


@app.get("/api/actions/templates", tags=["Actions"])
async def get_action_templates():
    """
    Get available action templates.

    Returns predefined action templates that can be executed on projects.
    """
    # Return sanitized templates (exclude internal fields)
    safe_templates = {
        key: {
            'title': t['title'],
            'description': t.get('description', ''),
            'requires_npm': t.get('requires_npm', False)
        }
        for key, t in ACTION_TEMPLATES.items()
    }
    return {"templates": safe_templates}


@app.post("/api/actions/execute", tags=["Actions"])
async def execute_action(action: ActionExecute):
    """
    Execute a predefined action template securely.

    **Security measures:**
    - Only predefined templates can be executed (no arbitrary commands)
    - Project paths are validated against allowed directories
    - Commands run without shell=True to prevent injection
    - Execution is logged for audit trail

    **Available templates:** deploy_vercel, add_stripe, add_docker,
    run_tests_npm, run_tests_pytest, install_npm, install_pip
    """
    # Validate template exists
    if action.template_key not in ACTION_TEMPLATES:
        logger.warning(f"Invalid action template requested: {action.template_key}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid template_key. Allowed: {list(ACTION_TEMPLATES.keys())}"
        )

    # Validate project path exists and is within allowed directories
    project_path = Path(action.project_path)
    if not project_path.exists():
        raise HTTPException(status_code=400, detail="Project path does not exist")

    if not is_path_allowed(str(project_path)):
        logger.warning(f"Blocked action execution for disallowed path: {project_path}")
        raise HTTPException(
            status_code=403,
            detail="Project path is outside allowed directories"
        )

    template = ACTION_TEMPLATES[action.template_key]
    command_args = template['command_args'].copy()

    logger.info(f"Executing action '{action.template_key}' in {project_path}")

    try:
        # Execute without shell=True for security
        result = subprocess.run(
            command_args,
            cwd=str(project_path),
            capture_output=True,
            text=True,
            timeout=120
        )

        logger.info(f"Action '{action.template_key}' completed with return code {result.returncode}")

        return {
            "success": result.returncode == 0,
            "template": action.template_key,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode
        }
    except subprocess.TimeoutExpired:
        logger.error(f"Action '{action.template_key}' timed out")
        raise HTTPException(status_code=408, detail="Command execution timed out")
    except FileNotFoundError as e:
        logger.error(f"Command not found: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Command not found. Ensure required tools are installed."
        )
    except Exception as e:
        logger.error(f"Action execution failed: {e}")
        raise HTTPException(status_code=500, detail="Action execution failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
