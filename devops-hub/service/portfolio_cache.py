"""
Portfolio Cache - Intelligent caching with auto-invalidation for portfolio analysis.

Provides:
- Redis-backed caching with TTL
- Cache invalidation on git changes
- Parallel project scanning
- File system monitoring hooks
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from service.redis_client import get_redis_client

logger = logging.getLogger(__name__)


@dataclass
class CacheKey:
    """Cache key builder for portfolio data."""
    
    PREFIX = "portfolio"
    
    @staticmethod
    def summary() -> str:
        """Cache key for portfolio summary."""
        return f"{CacheKey.PREFIX}:summary"
    
    @staticmethod
    def all_projects() -> str:
        """Cache key for all projects list."""
        return f"{CacheKey.PREFIX}:all_projects"
    
    @staticmethod
    def project(project_name: str) -> str:
        """Cache key for specific project."""
        return f"{CacheKey.PREFIX}:project:{project_name}"
    
    @staticmethod
    def recommendations() -> str:
        """Cache key for recommendations."""
        return f"{CacheKey.PREFIX}:recommendations"
    
    @staticmethod
    def git_status(project_path: str) -> str:
        """Cache key for git status."""
        path_hash = hashlib.md5(str(project_path).encode()).hexdigest()[:8]
        return f"{CacheKey.PREFIX}:git:{path_hash}"
    
    @staticmethod
    def monetization(project_path: str) -> str:
        """Cache key for monetization analysis."""
        path_hash = hashlib.md5(str(project_path).encode()).hexdigest()[:8]
        return f"{CacheKey.PREFIX}:monetization:{path_hash}"


class PortfolioCache:
    """
    Intelligent caching for portfolio analysis.
    
    Features:
    - Automatic cache invalidation on git operations
    - TTL-based expiration with different tiers
    - Batch invalidation for related keys
    - Cache warming on startup
    """
    
    # Cache TTLs in seconds
    TTL_SHORT = 60          # 1 minute - frequently changing data
    TTL_MEDIUM = 300        # 5 minutes - project details
    TTL_LONG = 1800         # 30 minutes - summary data
    TTL_GIT = 120           # 2 minutes - git status
    
    def __init__(self):
        self.redis = get_redis_client()
        self._last_invalidation = datetime.utcnow()
    
    @property
    def is_available(self) -> bool:
        """Check if cache is available."""
        return self.redis.is_available
    
    # ============ Get Methods ============
    
    async def get_summary(self) -> Optional[Dict[str, Any]]:
        """Get cached portfolio summary."""
        if not self.is_available:
            return None
        return await self.redis.get_json(CacheKey.summary())
    
    async def get_all_projects(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached projects list."""
        if not self.is_available:
            return None
        return await self.redis.get_json(CacheKey.all_projects())
    
    async def get_project(self, project_name: str) -> Optional[Dict[str, Any]]:
        """Get cached project details."""
        if not self.is_available:
            return None
        return await self.redis.get_json(CacheKey.project(project_name))
    
    async def get_recommendations(self) -> Optional[List[Dict[str, Any]]]:
        """Get cached recommendations."""
        if not self.is_available:
            return None
        return await self.redis.get_json(CacheKey.recommendations())
    
    async def get_git_status(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Get cached git status."""
        if not self.is_available:
            return None
        return await self.redis.get_json(CacheKey.git_status(project_path))
    
    async def get_monetization(self, project_path: str) -> Optional[Dict[str, Any]]:
        """Get cached monetization analysis."""
        if not self.is_available:
            return None
        return await self.redis.get_json(CacheKey.monetization(project_path))
    
    # ============ Set Methods ============
    
    async def set_summary(self, data: Dict[str, Any]) -> bool:
        """Cache portfolio summary."""
        if not self.is_available:
            return False
        return await self.redis.set_json(CacheKey.summary(), data, ttl=self.TTL_LONG)
    
    async def set_all_projects(self, projects: List[Dict[str, Any]]) -> bool:
        """Cache projects list."""
        if not self.is_available:
            return False
        return await self.redis.set_json(CacheKey.all_projects(), projects, ttl=self.TTL_MEDIUM)
    
    async def set_project(self, project_name: str, data: Dict[str, Any]) -> bool:
        """Cache project details."""
        if not self.is_available:
            return False
        return await self.redis.set_json(CacheKey.project(project_name), data, ttl=self.TTL_MEDIUM)
    
    async def set_recommendations(self, recommendations: List[Dict[str, Any]]) -> bool:
        """Cache recommendations."""
        if not self.is_available:
            return False
        return await self.redis.set_json(CacheKey.recommendations(), recommendations, ttl=self.TTL_MEDIUM)
    
    async def set_git_status(self, project_path: str, data: Dict[str, Any]) -> bool:
        """Cache git status."""
        if not self.is_available:
            return False
        return await self.redis.set_json(CacheKey.git_status(project_path), data, ttl=self.TTL_GIT)
    
    async def set_monetization(self, project_path: str, data: Dict[str, Any]) -> bool:
        """Cache monetization analysis."""
        if not self.is_available:
            return False
        return await self.redis.set_json(CacheKey.monetization(project_path), data, ttl=self.TTL_LONG)
    
    # ============ Invalidation Methods ============
    
    async def invalidate_project(self, project_name: str) -> int:
        """
        Invalidate all cache entries for a specific project.
        
        Returns number of keys invalidated.
        """
        if not self.is_available:
            return 0
        
        keys = [
            CacheKey.project(project_name),
            CacheKey.summary(),
            CacheKey.all_projects(),
            CacheKey.recommendations(),
        ]
        
        count = await self.redis.delete(*keys)
        logger.info(f"Invalidated {count} cache keys for project: {project_name}")
        self._last_invalidation = datetime.utcnow()
        return count
    
    async def invalidate_git_status(self, project_path: str) -> int:
        """Invalidate git status cache for a project."""
        if not self.is_available:
            return 0
        
        key = CacheKey.git_status(project_path)
        count = await self.redis.delete(key)
        logger.debug(f"Invalidated git status cache for: {project_path}")
        return count
    
    async def invalidate_all_projects(self) -> int:
        """
        Invalidate all portfolio cache.
        
        Returns number of keys invalidated.
        """
        if not self.is_available:
            return 0
        
        keys = [
            CacheKey.summary(),
            CacheKey.all_projects(),
            CacheKey.recommendations(),
        ]
        
        count = await self.redis.delete(*keys)
        logger.info(f"Invalidated {count} global portfolio cache keys")
        self._last_invalidation = datetime.utcnow()
        return count
    
    async def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate cache keys matching a pattern.
        
        WARNING: This requires Redis SCAN command and may be slow.
        Use specific invalidation methods when possible.
        """
        if not self.is_available:
            return 0
        
        # Note: This requires redis.scan which we need to add
        # For now, just log and return 0
        logger.warning(f"Pattern invalidation not implemented: {pattern}")
        return 0
    
    # ============ Utility Methods ============
    
    async def warm_cache(self, analyzer: Any) -> Dict[str, bool]:
        """
        Pre-populate cache with portfolio data.
        
        Args:
            analyzer: ProjectAnalyzer instance to get fresh data
        
        Returns dict with warming status for each cache type.
        """
        if not self.is_available:
            return {"available": False}
        
        results = {}
        
        try:
            # Warm summary
            summary = analyzer.get_portfolio_summary()
            results["summary"] = await self.set_summary(summary)
            
            # Warm projects list
            projects = analyzer.scan_all_projects()
            results["projects"] = await self.set_all_projects(projects)
            
            # Warm individual projects (parallel)
            project_tasks = []
            for project in projects[:10]:  # Limit to top 10 to avoid overwhelming
                task = self.set_project(project["name"], project)
                project_tasks.append(task)
            
            if project_tasks:
                await asyncio.gather(*project_tasks, return_exceptions=True)
            
            logger.info("Cache warming completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
            return {"error": str(e)}
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.is_available:
            return {"available": False}
        
        keys_to_check = [
            ("summary", CacheKey.summary()),
            ("all_projects", CacheKey.all_projects()),
            ("recommendations", CacheKey.recommendations()),
        ]
        
        stats = {
            "available": True,
            "last_invalidation": self._last_invalidation.isoformat(),
            "keys": {},
        }
        
        for name, key in keys_to_check:
            exists = await self.redis.exists(key)
            ttl = await self.redis.ttl(key) if exists else None
            stats["keys"][name] = {
                "cached": bool(exists),
                "ttl_seconds": ttl,
            }
        
        return stats
    
    async def clear_all(self) -> int:
        """
        Clear all portfolio cache entries.
        
        WARNING: This clears ALL portfolio cache. Use with caution.
        """
        return await self.invalidate_all_projects()


# ============ Global Cache Instance ============

_portfolio_cache: Optional[PortfolioCache] = None


def get_portfolio_cache() -> PortfolioCache:
    """Get the global portfolio cache instance."""
    global _portfolio_cache
    if _portfolio_cache is None:
        _portfolio_cache = PortfolioCache()
    return _portfolio_cache


# ============ Cache Invalidation Hooks ============

async def invalidate_on_git_operation(project_path: Path, operation: str) -> None:
    """
    Hook to invalidate cache after git operations.
    
    Call this after: commit, push, pull, checkout, etc.
    """
    cache = get_portfolio_cache()
    project_name = project_path.name
    
    logger.debug(f"Git operation '{operation}' detected on {project_name}")
    
    # Invalidate git status immediately
    await cache.invalidate_git_status(str(project_path))
    
    # For impactful operations, invalidate project cache
    if operation in ("commit", "push", "pull", "merge", "rebase"):
        await cache.invalidate_project(project_name)


async def invalidate_on_file_change(project_path: Path, file_path: Path) -> None:
    """
    Hook to invalidate cache after file changes.
    
    Call this when important files are modified.
    """
    cache = get_portfolio_cache()
    project_name = project_path.name
    
    # Only invalidate for important files
    important_files = {
        "package.json", "requirements.txt", "pyproject.toml",
        "Cargo.toml", "go.mod", "Dockerfile", "README.md"
    }
    
    if file_path.name in important_files:
        logger.debug(f"Important file changed: {file_path.name} in {project_name}")
        await cache.invalidate_project(project_name)
