"""
Revenue Automation Service - Autonomous revenue generation and project optimization.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import subprocess
import sys
import logging

# Ensure service directory is in path for imports
sys.path.insert(0, str(Path(__file__).parent))

from service.portfolio_analyzer import ProjectAnalyzer

logger = logging.getLogger(__name__)


class RevenueActionExecutor:
    """Execute revenue-generating actions autonomously."""
    
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.analyzer = ProjectAnalyzer(root_path)
    
    def get_executable_actions(self) -> List[Dict[str, Any]]:
        """Get list of actions that can be executed autonomously."""
        projects = self.analyzer.scan_all_projects()
        
        executable_actions = []
        
        for project in projects:
            project_path = Path(self.root_path.parent / project["name"])
            
            for rec in project["recommendations"]:
                action_type = self._classify_action(rec)
                
                if action_type in ["git_commit", "git_push", "git_init"]:
                    executable_actions.append({
                        "id": f"{project['name']}_{len(executable_actions)}",
                        "project": project["name"],
                        "project_path": str(project_path),
                        "type": action_type,
                        "recommendation": rec,
                        "monetization_score": project["monetization"]["score"],
                        "estimated_impact": self._estimate_impact(rec),
                        "risk_level": self._assess_risk(action_type),
                        "auto_executable": self._is_safe_to_auto_execute(action_type),
                    })
        
        # Sort by impact and risk
        executable_actions.sort(
            key=lambda x: (x["estimated_impact"], -x["risk_level"]),
            reverse=True
        )
        
        return executable_actions
    
    def _classify_action(self, recommendation: Dict[str, Any]) -> str:
        """Classify recommendation into actionable type."""
        action = recommendation["action"].lower()
        
        if "commit" in action and "changes" in action:
            return "git_commit"
        elif "push" in action and "commit" in action:
            return "git_push"
        elif "initialize git" in action:
            return "git_init"
        elif "add remote" in action:
            return "git_add_remote"
        elif "create readme" in action:
            return "create_readme"
        elif "implement payment" in action or "launch beta" in action:
            return "revenue_launch"
        elif "create api pricing" in action:
            return "api_monetization"
        elif "launch saas" in action:
            return "saas_launch"
        else:
            return "manual_review"
    
    def _estimate_impact(self, recommendation: Dict[str, Any]) -> int:
        """Estimate impact score (0-100)."""
        impact_scores = {
            "revenue": 90,
            "critical": 70,
            "high": 50,
            "medium": 30,
            "low": 10,
        }
        return impact_scores.get(recommendation["type"], 0)
    
    def _assess_risk(self, action_type: str) -> int:
        """Assess risk level (0-100)."""
        risk_levels = {
            "git_commit": 10,
            "git_push": 20,
            "git_init": 5,
            "git_add_remote": 5,
            "create_readme": 5,
            "revenue_launch": 80,
            "api_monetization": 60,
            "saas_launch": 90,
            "manual_review": 100,
        }
        return risk_levels.get(action_type, 100)
    
    def _is_safe_to_auto_execute(self, action_type: str) -> bool:
        """Determine if action can be safely auto-executed."""
        safe_actions = {"git_commit", "git_push", "git_init", "git_add_remote"}
        return action_type in safe_actions
    
    def execute_action(
        self,
        action_id: str,
        dry_run: bool = True
    ) -> Dict[str, Any]:
        """Execute a specific action."""
        actions = self.get_executable_actions()
        action = next((a for a in actions if a["id"] == action_id), None)
        
        if not action:
            return {"success": False, "error": "Action not found"}
        
        if not action["auto_executable"] and not dry_run:
            return {
                "success": False,
                "error": "Action requires manual approval",
                "action": action,
            }
        
        project_path = Path(action["project_path"])
        action_type = action["type"]
        
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "action": action,
                "preview": self._get_action_preview(action_type, project_path),
            }
        
        # Execute the action
        result = self._execute_git_action(action_type, project_path)
        
        return {
            "success": result["success"],
            "action": action,
            "result": result,
            "executed_at": datetime.now().isoformat(),
        }
    
    def _get_action_preview(self, action_type: str, project_path: Path) -> str:
        """Get preview of what the action would do."""
        if action_type == "git_commit":
            status = self._run_git(project_path, "status", "--short")
            return f"Would commit:\n{status}"
        elif action_type == "git_push":
            branch = self._run_git(project_path, "rev-parse", "--abbrev-ref", "HEAD")
            ahead = self._run_git(project_path, "rev-list", "--count", f"{branch}@{{u}}..{branch}")
            return f"Would push {ahead} commits to {branch}"
        elif action_type == "git_init":
            return f"Would initialize Git repository in {project_path.name}"
        else:
            return "Preview not available"
    
    def _execute_git_action(
        self,
        action_type: str,
        project_path: Path
    ) -> Dict[str, Any]:
        """Execute a Git action and invalidate cache."""
        try:
            if action_type == "git_commit":
                # Stage all changes
                self._run_git(project_path, "add", ".")
                
                # Commit with automated message
                commit_msg = f"chore: automated commit - portfolio sync\n\nGenerated by DevOps Hub Portfolio Automation"
                self._run_git(project_path, "commit", "-m", commit_msg)
                
                # Invalidate cache asynchronously
                asyncio.create_task(self._invalidate_cache(project_path, "commit"))
                
                return {"success": True, "message": "Changes committed"}
            
            elif action_type == "git_push":
                branch = self._run_git(project_path, "rev-parse", "--abbrev-ref", "HEAD")
                self._run_git(project_path, "push", "origin", branch)
                
                # Invalidate cache asynchronously
                asyncio.create_task(self._invalidate_cache(project_path, "push"))
                
                return {"success": True, "message": f"Pushed to {branch}"}
            
            elif action_type == "git_init":
                self._run_git(project_path, "init")
                
                # Invalidate cache asynchronously
                asyncio.create_task(self._invalidate_cache(project_path, "init"))
                
                return {"success": True, "message": "Git repository initialized"}
            
            else:
                return {"success": False, "error": "Action type not implemented"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    async def _invalidate_cache(self, project_path: Path, operation: str) -> None:
        """Invalidate cache after git operations."""
        try:
            from service.portfolio_cache import invalidate_on_git_operation
            await invalidate_on_git_operation(project_path, operation)
        except Exception as e:
            logger.warning(f"Failed to invalidate cache: {e}")
    
    def _run_git(self, path: Path, *args) -> str:
        """Run git command and return output."""
        result = subprocess.run(
            ["git", "-C", str(path)] + list(args),
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode != 0:
            raise Exception(f"Git command failed: {result.stderr}")
        return result.stdout.strip()
    
    def execute_revenue_workflow(
        self,
        workflow_type: str,
        target_projects: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Execute a complete revenue-generating workflow."""
        workflows = {
            "sync_all": self._workflow_sync_all,
            "prepare_top_projects": self._workflow_prepare_top_projects,
            "revenue_push": self._workflow_revenue_push,
        }
        
        workflow_func = workflows.get(workflow_type)
        if not workflow_func:
            return {"success": False, "error": "Unknown workflow type"}
        
        return workflow_func(target_projects)
    
    def _workflow_sync_all(self, target_projects: Optional[List[str]]) -> Dict[str, Any]:
        """Sync all projects with pending changes to remote."""
        actions = self.get_executable_actions()
        
        git_actions = [
            a for a in actions
            if a["type"] in ["git_commit", "git_push"] and a["auto_executable"]
        ]
        
        if target_projects:
            git_actions = [a for a in git_actions if a["project"] in target_projects]
        
        results = []
        for action in git_actions:
            result = self.execute_action(action["id"], dry_run=False)
            results.append(result)
        
        return {
            "success": True,
            "workflow": "sync_all",
            "actions_executed": len(results),
            "results": results,
        }
    
    def _workflow_prepare_top_projects(self, target_projects: Optional[List[str]]) -> Dict[str, Any]:
        """Prepare top monetization projects for launch."""
        summary = self.analyzer.get_portfolio_summary()
        top_projects = summary["top_projects"][:5]
        
        if target_projects:
            top_projects = [p for p in top_projects if p["name"] in target_projects]
        
        actions_taken = []
        for project in top_projects:
            project_path = Path(self.root_path.parent / project["name"])
            
            # Ensure git is synced
            if project["git"]["modified"] > 0 or project["git"]["staged"] > 0:
                try:
                    result = self._execute_git_action("git_commit", project_path)
                    actions_taken.append({
                        "project": project["name"],
                        "action": "git_commit",
                        "result": result,
                    })
                except Exception as e:
                    actions_taken.append({
                        "project": project["name"],
                        "action": "git_commit",
                        "result": {"success": False, "error": str(e)},
                    })
            
            if project["git"]["ahead"] > 0:
                try:
                    result = self._execute_git_action("git_push", project_path)
                    actions_taken.append({
                        "project": project["name"],
                        "action": "git_push",
                        "result": result,
                    })
                except Exception as e:
                    actions_taken.append({
                        "project": project["name"],
                        "action": "git_push",
                        "result": {"success": False, "error": str(e)},
                    })
        
        return {
            "success": True,
            "workflow": "prepare_top_projects",
            "projects_processed": len(top_projects),
            "actions_taken": actions_taken,
        }
    
    def _workflow_revenue_push(self, target_projects: Optional[List[str]]) -> Dict[str, Any]:
        """Focus on high-revenue projects and prepare them for monetization."""
        projects = self.analyzer.scan_all_projects()
        
        high_revenue_projects = [
            p for p in projects
            if p["monetization"]["score"] >= 60
        ]
        
        if target_projects:
            high_revenue_projects = [p for p in high_revenue_projects if p["name"] in target_projects]
        
        recommendations = []
        for project in high_revenue_projects:
            revenue_recs = [
                r for r in project["recommendations"]
                if r["type"] == "revenue"
            ]
            
            for rec in revenue_recs:
                recommendations.append({
                    "project": project["name"],
                    "recommendation": rec,
                    "monetization_score": project["monetization"]["score"],
                    "revenue_streams": project["monetization"]["revenue_streams"],
                })
        
        return {
            "success": True,
            "workflow": "revenue_push",
            "high_revenue_projects": len(high_revenue_projects),
            "revenue_recommendations": recommendations,
            "message": "Review and execute revenue recommendations manually",
        }
