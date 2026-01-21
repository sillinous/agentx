"""
Dashboard-specific data formatting for public portfolio dashboard.

Now reads from PROJECT_META.json files for accurate, project-defined metadata.
"""

from typing import Dict, List, Any


def _get_project_display_data(project: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract display data from a project, preferring explicit metadata over defaults.

    Projects with PROJECT_META.json get accurate, manually-defined values.
    Projects without metadata get values derived from automated analysis.
    """
    name = project.get("display_name", project["name"])

    # Check if project has explicit metadata
    if project.get("has_metadata"):
        # Use metadata-defined values
        revenue_meta = project.get("revenue_metadata", {})
        return {
            "name": name,
            "status": project.get("project_status", "in_progress"),
            "completion": project.get("completion", 50),
            "mrr_potential": revenue_meta.get("mrr_potential", "TBD"),
            "current_mrr": revenue_meta.get("current_mrr", 0),
            "blockers": project.get("blocker_count", 0),
            "time_to_launch": project.get("time_to_launch", "TBD"),
            "priority": project.get("priority", 5),
            "description": project.get("description", ""),
            "stakeholder_notes": project.get("stakeholder_notes", ""),
            "links": project.get("links", {}),
            "has_metadata": True,
        }
    else:
        # Derive values from automated analysis
        monetization_score = project.get("monetization", {}).get("score", 0)
        health_score = project.get("health", {}).get("score", 50)
        recommendations = project.get("recommendations", [])
        blocker_count = len([r for r in recommendations if r["type"] in ["critical", "high"]])

        # Estimate MRR potential based on monetization score
        if monetization_score >= 70:
            mrr_potential = "$500-$1,500"
        elif monetization_score >= 40:
            mrr_potential = "$200-$500"
        else:
            mrr_potential = "$50-$200"

        return {
            "name": name,
            "status": "in_progress" if monetization_score >= 40 else "planning",
            "completion": health_score,
            "mrr_potential": mrr_potential,
            "current_mrr": 0,
            "blockers": blocker_count,
            "time_to_launch": "Unknown",
            "priority": 5,
            "description": "",
            "stakeholder_notes": "",
            "links": {},
            "has_metadata": False,
        }


def format_for_dashboard(projects: List[Dict[str, Any]], summary: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format portfolio data for the public dashboard.

    Converts internal project analysis into dashboard-friendly format.
    Now uses PROJECT_META.json data when available.
    """
    formatted_projects = []

    for project in projects[:10]:  # Top 10 projects
        display_data = _get_project_display_data(project)
        formatted_projects.append(display_data)
    
    # Calculate revenue metrics dynamically from project metadata
    total_current_mrr = sum(p.get("current_mrr", 0) for p in formatted_projects)
    active_streams = sum(1 for p in formatted_projects if p.get("current_mrr", 0) > 0)

    # Count projects by status
    ready_count = sum(1 for p in formatted_projects if p.get("status") == "ready")
    launched_count = sum(1 for p in formatted_projects if p.get("status") == "launched")

    revenue_metrics = {
        "current_mrr": total_current_mrr,
        "active_streams": active_streams,
        "total_projects": summary["total_projects"],
        "ready_to_launch": ready_count,
        "launched": launched_count,
        "projects_with_metadata": sum(1 for p in formatted_projects if p.get("has_metadata")),
    }

    # Format next actions from blockers and recommendations
    next_actions = []
    seen_actions = set()

    # First: Add blockers from projects with metadata (these are manually defined, high accuracy)
    for project in projects:
        blockers = project.get("blockers", [])
        for blocker in blockers:
            action_key = f"{project['name']}:{blocker['title']}"
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                next_actions.append({
                    "title": blocker["title"],
                    "description": blocker.get("description", ""),
                    "project": project.get("display_name", project["name"]),
                    "time_estimate": "Variable",
                    "priority": blocker.get("severity", "medium"),
                })

    # Then: Add recommendations from automated analysis
    priority_map_rec = {
        "revenue": "high",
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "medium",
    }

    for project in projects[:5]:
        for rec in project.get("recommendations", [])[:2]:
            action_key = f"{rec['category']}:{rec['action']}"
            if action_key not in seen_actions:
                seen_actions.add(action_key)
                next_actions.append({
                    "title": rec["action"],
                    "description": rec["impact"],
                    "project": project.get("display_name", project["name"]),
                    "time_estimate": "Variable",
                    "priority": priority_map_rec.get(rec["type"], "medium"),
                })

    # Sort actions by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    next_actions.sort(key=lambda x: priority_order.get(x.get("priority", "medium"), 2))

    return {
        "projects": sorted(formatted_projects, key=lambda x: x["priority"]),
        "revenue": revenue_metrics,
        "next_actions": next_actions[:8],  # Top 8 actions
        "last_updated": summary["updated_at"],
    }
