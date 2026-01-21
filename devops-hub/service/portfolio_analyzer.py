"""
Solution Portfolio Analyzer - Comprehensive project intelligence and monetization analysis.
"""

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import json
import re
import logging

logger = logging.getLogger(__name__)


class GitStatus:
    """Git repository status information."""
    def __init__(self, path: Path):
        self.path = path
        self.is_repo = (path / ".git").exists()
        self.branch = ""
        self.ahead = 0
        self.behind = 0
        self.modified = 0
        self.untracked = 0
        self.staged = 0
        self.remote = ""
        self.last_commit = ""
        self.last_commit_date = ""
        
        if self.is_repo:
            self._analyze()
    
    def _run_git(self, *args) -> str:
        """Run git command and return output."""
        try:
            result = subprocess.run(
                ["git", "-C", str(self.path)] + list(args),
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip()
        except Exception:
            return ""
    
    def _analyze(self):
        """Analyze git repository status."""
        self.branch = self._run_git("rev-parse", "--abbrev-ref", "HEAD")
        
        # Get remote info
        remote_url = self._run_git("config", "--get", f"branch.{self.branch}.remote")
        if remote_url:
            full_url = self._run_git("remote", "get-url", remote_url)
            self.remote = full_url
        
        # Get ahead/behind count
        tracking = self._run_git("rev-list", "--left-right", "--count", f"{self.branch}...@{{u}}")
        if tracking and "\t" in tracking:
            parts = tracking.split("\t")
            self.ahead = int(parts[0])
            self.behind = int(parts[1])
        
        # Get status
        status = self._run_git("status", "--porcelain")
        if status:
            for line in status.split("\n"):
                if line.startswith("??"):
                    self.untracked += 1
                elif line[0] in "MARC":
                    self.staged += 1
                elif line[1] in "M":
                    self.modified += 1
        
        # Get last commit
        self.last_commit = self._run_git("log", "-1", "--format=%s")
        self.last_commit_date = self._run_git("log", "-1", "--format=%ci")


class MonetizationAnalyzer:
    """Analyze monetization potential of projects."""
    
    # Revenue indicators with weighted scores
    REVENUE_SIGNALS = {
        "stripe": 40,
        "payment": 35,
        "subscription": 35,
        "checkout": 30,
        "pricing": 25,
        "billing": 30,
        "api": 20,
        "saas": 40,
        "marketplace": 35,
        "e-commerce": 40,
        "affiliate": 30,
        "ad": 15,
        "analytics": 20,
        "dashboard": 15,
        "admin": 10,
        "auth": 15,
        "user": 10,
        "database": 10,
    }
    
    # Technology stack indicators
    TECH_SCORES = {
        "nextjs": 25,
        "react": 20,
        "typescript": 15,
        "python": 15,
        "fastapi": 20,
        "stripe": 40,
        "postgresql": 15,
        "redis": 15,
        "docker": 10,
        "kubernetes": 15,
        "ai": 30,
        "ml": 25,
        "agent": 25,
    }
    
    @staticmethod
    def analyze(path: Path) -> Dict[str, Any]:
        """Analyze monetization potential of a project."""
        score = 0
        signals = []
        tech_stack = []
        revenue_streams = []
        
        # Scan package files
        package_json = path / "package.json"
        pyproject = path / "pyproject.toml"
        requirements = path / "requirements.txt"
        
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                    
                    for dep in deps.keys():
                        dep_lower = dep.lower()
                        for signal, points in MonetizationAnalyzer.REVENUE_SIGNALS.items():
                            if signal in dep_lower:
                                score += points
                                if signal not in signals:
                                    signals.append(signal)
                        
                        for tech, points in MonetizationAnalyzer.TECH_SCORES.items():
                            if tech in dep_lower:
                                if tech not in tech_stack:
                                    tech_stack.append(tech)
            except Exception:
                pass
        
        if requirements.exists():
            try:
                with open(requirements) as f:
                    for line in f:
                        line_lower = line.lower()
                        for signal, points in MonetizationAnalyzer.REVENUE_SIGNALS.items():
                            if signal in line_lower:
                                score += points
                                if signal not in signals:
                                    signals.append(signal)
                        
                        for tech, points in MonetizationAnalyzer.TECH_SCORES.items():
                            if tech in line_lower:
                                if tech not in tech_stack:
                                    tech_stack.append(tech)
            except Exception:
                pass
        
        # Scan source files for revenue indicators
        source_dirs = ["src", "app", "pages", "components", "lib", "service", "api"]
        for src_dir in source_dirs:
            src_path = path / src_dir
            if src_path.exists():
                try:
                    for file_path in src_path.rglob("*"):
                        if file_path.is_file() and file_path.suffix in [".ts", ".tsx", ".js", ".jsx", ".py"]:
                            file_lower = file_path.name.lower()
                            for signal, points in MonetizationAnalyzer.REVENUE_SIGNALS.items():
                                if signal in file_lower:
                                    score += points * 0.5
                                    if signal not in signals:
                                        signals.append(signal)
                except Exception:
                    pass
        
        # Determine revenue streams based on signals
        if "stripe" in signals or "payment" in signals or "checkout" in signals:
            revenue_streams.append("Direct Payments")
        if "subscription" in signals or "billing" in signals:
            revenue_streams.append("Subscription Model")
        if "api" in signals:
            revenue_streams.append("API Access")
        if "marketplace" in signals:
            revenue_streams.append("Marketplace Fees")
        if "affiliate" in signals:
            revenue_streams.append("Affiliate Revenue")
        if "ad" in signals:
            revenue_streams.append("Advertising")
        if "saas" in signals:
            revenue_streams.append("SaaS Model")
        
        # Normalize score to 0-100
        normalized_score = min(100, score)
        
        # Determine category
        if normalized_score >= 70:
            category = "High Potential"
        elif normalized_score >= 40:
            category = "Medium Potential"
        elif normalized_score >= 20:
            category = "Low Potential"
        else:
            category = "Exploratory"
        
        return {
            "score": normalized_score,
            "category": category,
            "signals": signals,
            "tech_stack": tech_stack,
            "revenue_streams": revenue_streams,
        }


class ProjectMetadata:
    """Read and parse PROJECT_META.json files from projects."""

    METADATA_FILENAME = "PROJECT_META.json"

    @staticmethod
    def read(path: Path) -> Optional[Dict[str, Any]]:
        """Read PROJECT_META.json from a project directory."""
        meta_file = path / ProjectMetadata.METADATA_FILENAME
        if not meta_file.exists():
            return None

        try:
            with open(meta_file) as f:
                data = json.load(f)
                # Validate required fields
                if "name" not in data or "status" not in data:
                    logger.warning(f"Invalid PROJECT_META.json in {path.name}: missing required fields")
                    return None
                return data
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in {path.name}/PROJECT_META.json: {e}")
            return None
        except Exception as e:
            logger.warning(f"Error reading PROJECT_META.json from {path.name}: {e}")
            return None

    @staticmethod
    def merge_with_analysis(metadata: Dict[str, Any], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Merge project metadata with automated analysis, metadata takes precedence."""
        merged = analysis.copy()

        # Override with metadata values
        if metadata.get("name"):
            merged["display_name"] = metadata["name"]

        if metadata.get("description"):
            merged["description"] = metadata["description"]

        if metadata.get("status"):
            merged["project_status"] = metadata["status"]

        if metadata.get("priority"):
            merged["priority"] = metadata["priority"]

        if metadata.get("completion"):
            merged["completion"] = metadata["completion"]

        if metadata.get("time_to_launch"):
            merged["time_to_launch"] = metadata["time_to_launch"]

        if metadata.get("tech_stack"):
            merged["tech_stack_override"] = metadata["tech_stack"]

        if metadata.get("stakeholder_notes"):
            merged["stakeholder_notes"] = metadata["stakeholder_notes"]

        # Revenue data
        if metadata.get("revenue"):
            rev = metadata["revenue"]
            merged["revenue_metadata"] = {
                "model": rev.get("model", "unknown"),
                "current_mrr": rev.get("current_mrr", 0),
                "mrr_potential": rev.get("mrr_potential", "Unknown"),
                "launch_date": rev.get("launch_date"),
            }

        # Blockers
        if metadata.get("blockers"):
            merged["blockers"] = metadata["blockers"]
            merged["blocker_count"] = len(metadata["blockers"])

        # Links
        if metadata.get("links"):
            merged["links"] = metadata["links"]

        # Mark that this project has explicit metadata
        merged["has_metadata"] = True
        merged["metadata_updated_at"] = metadata.get("updated_at")

        return merged


class ProjectAnalyzer:
    """Comprehensive project analysis with intelligent caching."""

    def __init__(self, root_path: Path, use_cache: bool = True):
        self.root_path = root_path
        self.use_cache = use_cache
        self._cache = None
    
    @property
    def cache(self):
        """Lazy load cache to avoid circular imports."""
        if self._cache is None and self.use_cache:
            try:
                from service.portfolio_cache import get_portfolio_cache
                self._cache = get_portfolio_cache()
            except ImportError:
                logger.warning("Portfolio cache not available")
                self._cache = None
        return self._cache
    
    async def analyze_project_async(self, path: Path) -> Dict[str, Any]:
        """
        Analyze a single project with caching support.
        
        Checks cache first, then performs analysis if needed.
        """
        # Try cache first
        if self.cache and self.cache.is_available:
            cached = await self.cache.get_project(path.name)
            if cached:
                logger.debug(f"Cache hit for project: {path.name}")
                return cached
        
        # Perform analysis
        project_data = self.analyze_project(path)
        
        # Cache the result
        if self.cache and self.cache.is_available:
            await self.cache.set_project(path.name, project_data)
        
        return project_data
    
    def analyze_project(self, path: Path) -> Dict[str, Any]:
        """Analyze a single project (synchronous)."""
        git_status = GitStatus(path)
        monetization = MonetizationAnalyzer.analyze(path)

        # Determine project type
        project_type = self._detect_project_type(path)

        # Calculate health score
        health_score = self._calculate_health(path, git_status)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            path, git_status, monetization, health_score
        )

        # Base analysis result
        analysis = {
            "name": path.name,
            "path": str(path.relative_to(self.root_path.parent)),
            "type": project_type,
            "git": {
                "is_repo": git_status.is_repo,
                "branch": git_status.branch,
                "remote": git_status.remote,
                "ahead": git_status.ahead,
                "behind": git_status.behind,
                "modified": git_status.modified,
                "untracked": git_status.untracked,
                "staged": git_status.staged,
                "last_commit": git_status.last_commit,
                "last_commit_date": git_status.last_commit_date,
            },
            "monetization": monetization,
            "health": {
                "score": health_score,
                "status": self._health_status(health_score),
            },
            "recommendations": recommendations,
            "updated_at": datetime.now().isoformat(),
            # Defaults for projects without metadata
            "has_metadata": False,
            "priority": 5,  # Default low priority
            "project_status": "in_progress" if monetization["score"] >= 40 else "planning",
            "completion": health_score,
            "blocker_count": len([r for r in recommendations if r["type"] in ["critical", "high"]]),
        }

        # Read and merge PROJECT_META.json if it exists
        metadata = ProjectMetadata.read(path)
        if metadata:
            analysis = ProjectMetadata.merge_with_analysis(metadata, analysis)
            logger.debug(f"Merged metadata for project: {path.name}")

        return analysis
    
    def _detect_project_type(self, path: Path) -> str:
        """Detect project type based on files present."""
        if (path / "package.json").exists():
            pkg_data = {}
            try:
                with open(path / "package.json") as f:
                    pkg_data = json.load(f)
            except Exception:
                pass
            
            deps = {**pkg_data.get("dependencies", {}), **pkg_data.get("devDependencies", {})}
            if "next" in deps:
                return "Next.js Application"
            elif "react" in deps:
                return "React Application"
            elif "vue" in deps:
                return "Vue Application"
            else:
                return "Node.js Application"
        
        if (path / "requirements.txt").exists() or (path / "pyproject.toml").exists():
            if (path / "fastapi").exists() or any((path / "service").glob("*api*.py")):
                return "FastAPI Application"
            elif (path / "manage.py").exists():
                return "Django Application"
            elif (path / "app.py").exists() or (path / "main.py").exists():
                return "Python Application"
            else:
                return "Python Project"
        
        if (path / "Dockerfile").exists():
            return "Containerized Application"
        
        return "Unknown"
    
    def _calculate_health(self, path: Path, git_status: GitStatus) -> int:
        """Calculate project health score (0-100)."""
        score = 50
        
        # Git health
        if git_status.is_repo:
            score += 10
            if git_status.remote:
                score += 10
            if git_status.modified == 0 and git_status.untracked == 0:
                score += 5
            if git_status.ahead == 0 and git_status.behind == 0:
                score += 5
        else:
            score -= 20
        
        # Documentation
        if (path / "README.md").exists():
            score += 5
        
        # Configuration
        if (path / ".env.example").exists() or (path / ".env.template").exists():
            score += 5
        
        # Testing
        if (path / "tests").exists() or (path / "__tests__").exists():
            score += 10
        
        # Docker support
        if (path / "Dockerfile").exists():
            score += 5
        
        return max(0, min(100, score))
    
    def _health_status(self, score: int) -> str:
        """Convert health score to status."""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        else:
            return "Needs Attention"
    
    def _generate_recommendations(
        self,
        path: Path,
        git_status: GitStatus,
        monetization: Dict[str, Any],
        health_score: int,
    ) -> List[Dict[str, str]]:
        """Generate actionable recommendations."""
        recommendations = []
        
        # Git recommendations
        if not git_status.is_repo:
            recommendations.append({
                "type": "critical",
                "category": "Version Control",
                "action": "Initialize Git repository",
                "impact": "Enable version control and collaboration",
            })
        elif not git_status.remote:
            recommendations.append({
                "type": "high",
                "category": "Version Control",
                "action": "Add remote repository (GitHub)",
                "impact": "Enable backup and collaboration",
            })
        
        if git_status.modified > 0 or git_status.staged > 0:
            recommendations.append({
                "type": "medium",
                "category": "Version Control",
                "action": f"Commit {git_status.modified + git_status.staged} pending changes",
                "impact": "Preserve work and track progress",
            })
        
        if git_status.ahead > 0:
            recommendations.append({
                "type": "medium",
                "category": "Version Control",
                "action": f"Push {git_status.ahead} commits to remote",
                "impact": "Sync with remote and backup changes",
            })
        
        # Monetization recommendations
        if monetization["score"] >= 40:
            if "stripe" in monetization["signals"] or "payment" in monetization["signals"]:
                recommendations.append({
                    "type": "revenue",
                    "category": "Monetization",
                    "action": "Implement payment flow and launch beta",
                    "impact": "Start generating revenue from existing infrastructure",
                })
            
            if "api" in monetization["signals"]:
                recommendations.append({
                    "type": "revenue",
                    "category": "Monetization",
                    "action": "Create API pricing tiers and documentation",
                    "impact": "Enable API-based revenue stream",
                })
            
            if "dashboard" in monetization["signals"] and "auth" in monetization["signals"]:
                recommendations.append({
                    "type": "revenue",
                    "category": "Monetization",
                    "action": "Launch SaaS offering with tiered pricing",
                    "impact": "Convert application into revenue-generating SaaS",
                })
        elif monetization["score"] < 20:
            recommendations.append({
                "type": "low",
                "category": "Monetization",
                "action": "Explore monetization opportunities",
                "impact": "Identify potential revenue streams",
            })
        
        # Health recommendations
        if health_score < 60:
            if not (path / "README.md").exists():
                recommendations.append({
                    "type": "medium",
                    "category": "Documentation",
                    "action": "Create comprehensive README",
                    "impact": "Improve project clarity and onboarding",
                })
            
            if not ((path / "tests").exists() or (path / "__tests__").exists()):
                recommendations.append({
                    "type": "medium",
                    "category": "Quality",
                    "action": "Add test suite",
                    "impact": "Increase code quality and reliability",
                })
        
        return recommendations
    
    async def scan_all_projects_async(self) -> List[Dict[str, Any]]:
        """
        Scan all projects in parallel with caching.
        
        Returns list of projects sorted by monetization score.
        """
        # Try cache first
        if self.cache and self.cache.is_available:
            cached = await self.cache.get_all_projects()
            if cached:
                logger.debug("Cache hit for all projects")
                return cached
        
        # Get list of project directories
        project_dirs = self._discover_projects()
        
        # Analyze projects in parallel
        tasks = [self.analyze_project_async(path) for path in project_dirs]
        projects = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out errors and None values
        valid_projects = [
            p for p in projects
            if p and not isinstance(p, Exception)
        ]

        # Sort by: 1) has_metadata (True first), 2) priority (lower first), 3) monetization score (higher first)
        valid_projects.sort(key=lambda x: (
            not x.get("has_metadata", False),  # Projects with metadata first
            x.get("priority", 5),               # Lower priority number = higher priority
            -x["monetization"]["score"],        # Higher score = higher rank
        ))
        
        # Cache the result
        if self.cache and self.cache.is_available:
            await self.cache.set_all_projects(valid_projects)
        
        return valid_projects
    
    def _discover_projects(self) -> List[Path]:
        """
        Discover all project directories.
        
        Returns list of Path objects for each project.
        """
        projects = []
        parent_dir = self.root_path.parent
        
        for item in parent_dir.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                # Skip common non-project directories
                skip_dirs = {"node_modules", "__pycache__", "venv", ".venv", "dist", "build"}
                if item.name in skip_dirs:
                    continue
                
                # Check if it's a project (has common project files)
                is_project = any([
                    (item / ".git").exists(),
                    (item / "package.json").exists(),
                    (item / "requirements.txt").exists(),
                    (item / "pyproject.toml").exists(),
                    (item / "Dockerfile").exists(),
                ])
                
                if is_project:
                    projects.append(item)
        
        return projects
    
    def scan_all_projects(self) -> List[Dict[str, Any]]:
        """Scan all projects in the root directory (synchronous)."""
        projects = []
        project_dirs = self._discover_projects()

        for path in project_dirs:
            try:
                project_data = self.analyze_project(path)
                projects.append(project_data)
            except Exception as e:
                logger.error(f"Error analyzing {path.name}: {e}")

        # Sort by: 1) has_metadata (True first), 2) priority (lower first), 3) monetization score (higher first)
        projects.sort(key=lambda x: (
            not x.get("has_metadata", False),  # Projects with metadata first
            x.get("priority", 5),               # Lower priority number = higher priority
            -x["monetization"]["score"],        # Higher score = higher rank
        ))

        return projects
    
    async def get_portfolio_summary_async(self) -> Dict[str, Any]:
        """
        Get high-level portfolio summary with caching.
        
        Returns cached summary if available, otherwise generates fresh.
        """
        # Try cache first
        if self.cache and self.cache.is_available:
            cached = await self.cache.get_summary()
            if cached:
                logger.debug("Cache hit for portfolio summary")
                return cached
        
        # Generate fresh summary
        projects = await self.scan_all_projects_async()
        summary = self._compute_summary(projects)
        
        # Cache the result
        if self.cache and self.cache.is_available:
            await self.cache.set_summary(summary)
        
        return summary
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get high-level portfolio summary (synchronous)."""
        projects = self.scan_all_projects()
        return self._compute_summary(projects)
    
    def _compute_summary(self, projects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Compute portfolio summary from projects list."""
        total_projects = len(projects)
        high_potential = sum(1 for p in projects if p["monetization"]["score"] >= 70)
        medium_potential = sum(1 for p in projects if 40 <= p["monetization"]["score"] < 70)
        low_potential = sum(1 for p in projects if 20 <= p["monetization"]["score"] < 40)
        
        revenue_ready = sum(1 for p in projects if p["monetization"]["revenue_streams"])
        
        total_recommendations = sum(len(p["recommendations"]) for p in projects)
        critical_actions = sum(
            1 for p in projects
            for r in p["recommendations"]
            if r["type"] == "critical"
        )
        revenue_opportunities = sum(
            1 for p in projects
            for r in p["recommendations"]
            if r["type"] == "revenue"
        )
        
        return {
            "total_projects": total_projects,
            "by_potential": {
                "high": high_potential,
                "medium": medium_potential,
                "low": low_potential,
            },
            "revenue_ready": revenue_ready,
            "total_recommendations": total_recommendations,
            "critical_actions": critical_actions,
            "revenue_opportunities": revenue_opportunities,
            "top_projects": projects[:5],
            "updated_at": datetime.now().isoformat(),
        }
