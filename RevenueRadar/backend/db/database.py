"""SQLite database setup and management."""
import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

DATABASE_PATH = Path(__file__).parent.parent / "data" / "projects.db"

def get_connection() -> sqlite3.Connection:
    """Get database connection with row factory."""
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL UNIQUE,
            description TEXT,
            tech_stack TEXT,
            maturity_score INTEGER DEFAULT 0,
            revenue_score INTEGER DEFAULT 0,
            effort_score INTEGER DEFAULT 50,
            overall_score INTEGER DEFAULT 0,
            tier TEXT DEFAULT 'tier3',
            status TEXT DEFAULT 'discovery',
            revenue_potential_min INTEGER DEFAULT 0,
            revenue_potential_max INTEGER DEFAULT 0,
            last_scanned TEXT,
            metadata TEXT,
            created_at TEXT,
            updated_at TEXT
        );

        CREATE TABLE IF NOT EXISTS opportunities (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id),
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            priority TEXT DEFAULT 'medium',
            effort_hours INTEGER DEFAULT 8,
            revenue_impact INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            completed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS actions (
            id TEXT PRIMARY KEY,
            opportunity_id TEXT REFERENCES opportunities(id),
            title TEXT NOT NULL,
            action_type TEXT DEFAULT 'manual',
            command TEXT,
            completed INTEGER DEFAULT 0,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS metrics (
            id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(id),
            date TEXT,
            metric_type TEXT,
            value REAL,
            created_at TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_projects_tier ON projects(tier);
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
        CREATE INDEX IF NOT EXISTS idx_opportunities_project ON opportunities(project_id);
        CREATE INDEX IF NOT EXISTS idx_opportunities_status ON opportunities(status);
    """)

    conn.commit()
    conn.close()

def dict_from_row(row: sqlite3.Row) -> Dict[str, Any]:
    """Convert sqlite3.Row to dict, parsing JSON fields."""
    d = dict(row)
    for key in ['tech_stack', 'metadata']:
        if key in d and d[key]:
            try:
                d[key] = json.loads(d[key])
            except:
                pass
    return d

# Project operations
def get_all_projects() -> List[Dict]:
    """Get all projects."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects ORDER BY overall_score DESC")
    projects = [dict_from_row(row) for row in cursor.fetchall()]
    conn.close()
    return projects

def get_project_by_id(project_id: str) -> Optional[Dict]:
    """Get project by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row) if row else None

def get_project_by_path(path: str) -> Optional[Dict]:
    """Get project by path."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM projects WHERE path = ?", (path,))
    row = cursor.fetchone()
    conn.close()
    return dict_from_row(row) if row else None

def upsert_project(project: Dict) -> str:
    """Insert or update a project."""
    conn = get_connection()
    cursor = conn.cursor()

    now = datetime.utcnow().isoformat()
    project_id = project.get('id') or str(uuid.uuid4())

    # Check if exists by path
    existing = get_project_by_path(project['path'])
    if existing:
        project_id = existing['id']

    tech_stack = json.dumps(project.get('tech_stack', []))
    metadata = json.dumps(project.get('metadata', {}))

    cursor.execute("""
        INSERT INTO projects (id, name, path, description, tech_stack,
            maturity_score, revenue_score, effort_score, overall_score,
            tier, status, revenue_potential_min, revenue_potential_max,
            last_scanned, metadata, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            name = excluded.name,
            description = excluded.description,
            tech_stack = excluded.tech_stack,
            maturity_score = excluded.maturity_score,
            revenue_score = excluded.revenue_score,
            effort_score = excluded.effort_score,
            overall_score = excluded.overall_score,
            tier = excluded.tier,
            status = excluded.status,
            revenue_potential_min = excluded.revenue_potential_min,
            revenue_potential_max = excluded.revenue_potential_max,
            last_scanned = excluded.last_scanned,
            metadata = excluded.metadata,
            updated_at = excluded.updated_at
    """, (
        project_id,
        project['name'],
        project['path'],
        project.get('description', ''),
        tech_stack,
        project.get('maturity_score', 0),
        project.get('revenue_score', 0),
        project.get('effort_score', 50),
        project.get('overall_score', 0),
        project.get('tier', 'tier3'),
        project.get('status', 'discovery'),
        project.get('revenue_potential_min', 0),
        project.get('revenue_potential_max', 0),
        now,
        metadata,
        existing['created_at'] if existing else now,
        now
    ))

    conn.commit()
    conn.close()
    return project_id

# Opportunity operations
def get_opportunities_for_project(project_id: str) -> List[Dict]:
    """Get all opportunities for a project."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM opportunities WHERE project_id = ? ORDER BY priority, created_at",
        (project_id,)
    )
    opportunities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return opportunities

def get_all_opportunities() -> List[Dict]:
    """Get all opportunities with project info."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT o.*, p.name as project_name
        FROM opportunities o
        JOIN projects p ON o.project_id = p.id
        ORDER BY o.priority, o.created_at
    """)
    opportunities = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return opportunities

def create_opportunity(opp: Dict) -> str:
    """Create a new opportunity."""
    conn = get_connection()
    cursor = conn.cursor()

    opp_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    cursor.execute("""
        INSERT INTO opportunities (id, project_id, title, description, category,
            priority, effort_hours, revenue_impact, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        opp_id,
        opp['project_id'],
        opp['title'],
        opp.get('description', ''),
        opp.get('category', 'feature'),
        opp.get('priority', 'medium'),
        opp.get('effort_hours', 8),
        opp.get('revenue_impact', 0),
        opp.get('status', 'pending'),
        now
    ))

    conn.commit()
    conn.close()
    return opp_id

def update_opportunity_status(opp_id: str, status: str) -> bool:
    """Update opportunity status."""
    conn = get_connection()
    cursor = conn.cursor()

    completed_at = datetime.utcnow().isoformat() if status == 'completed' else None

    cursor.execute("""
        UPDATE opportunities SET status = ?, completed_at = ?
        WHERE id = ?
    """, (status, completed_at, opp_id))

    conn.commit()
    success = cursor.rowcount > 0
    conn.close()
    return success

# Analytics
def get_statistics() -> Dict:
    """Get portfolio statistics."""
    conn = get_connection()
    cursor = conn.cursor()

    stats = {}

    # Total projects
    cursor.execute("SELECT COUNT(*) FROM projects")
    stats['total_projects'] = cursor.fetchone()[0]

    # By tier
    cursor.execute("SELECT tier, COUNT(*) FROM projects GROUP BY tier")
    stats['by_tier'] = {row[0]: row[1] for row in cursor.fetchall()}

    # By status
    cursor.execute("SELECT status, COUNT(*) FROM projects GROUP BY status")
    stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

    # Revenue potential
    cursor.execute("""
        SELECT
            SUM(revenue_potential_min) as min_total,
            SUM(revenue_potential_max) as max_total
        FROM projects
    """)
    row = cursor.fetchone()
    stats['revenue_potential'] = {
        'min': row[0] or 0,
        'max': row[1] or 0
    }

    # Average scores
    cursor.execute("""
        SELECT
            AVG(maturity_score) as avg_maturity,
            AVG(revenue_score) as avg_revenue,
            AVG(overall_score) as avg_overall
        FROM projects
    """)
    row = cursor.fetchone()
    stats['avg_scores'] = {
        'maturity': round(row[0] or 0, 1),
        'revenue': round(row[1] or 0, 1),
        'overall': round(row[2] or 0, 1)
    }

    # Opportunities stats
    cursor.execute("SELECT status, COUNT(*) FROM opportunities GROUP BY status")
    stats['opportunities_by_status'] = {row[0]: row[1] for row in cursor.fetchall()}

    conn.close()
    return stats

# Initialize on import
init_db()
