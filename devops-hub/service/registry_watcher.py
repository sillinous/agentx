"""
Registry Watcher - File system monitoring for agent registry hot-reloading.

Monitors registry.json for changes and triggers reload without server restart.
"""

import asyncio
import hashlib
import logging
from pathlib import Path
from typing import Callable, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RegistryWatcher:
    """
    Watch agent registry file for changes and trigger hot-reload.
    
    Uses file modification time and content hash to detect changes.
    """
    
    def __init__(
        self,
        registry_path: Path,
        on_change: Optional[Callable[[], None]] = None,
        check_interval: float = 5.0,
    ):
        self.registry_path = registry_path
        self.on_change = on_change
        self.check_interval = check_interval
        self._last_hash: Optional[str] = None
        self._last_modified: Optional[float] = None
        self._watch_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _compute_file_hash(self) -> Optional[str]:
        """Compute MD5 hash of registry file content."""
        if not self.registry_path.exists():
            return None
        
        try:
            content = self.registry_path.read_bytes()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"Failed to compute registry hash: {e}")
            return None
    
    def _get_modified_time(self) -> Optional[float]:
        """Get file modification timestamp."""
        if not self.registry_path.exists():
            return None
        
        try:
            return self.registry_path.stat().st_mtime
        except Exception as e:
            logger.error(f"Failed to get registry modification time: {e}")
            return None
    
    def has_changed(self) -> bool:
        """Check if registry file has changed since last check."""
        current_hash = self._compute_file_hash()
        current_modified = self._get_modified_time()
        
        if current_hash is None:
            return False
        
        # First check
        if self._last_hash is None:
            self._last_hash = current_hash
            self._last_modified = current_modified
            return False
        
        # Check if changed
        changed = (
            current_hash != self._last_hash or
            current_modified != self._last_modified
        )
        
        if changed:
            logger.info(f"Registry change detected: {self.registry_path.name}")
            self._last_hash = current_hash
            self._last_modified = current_modified
        
        return changed
    
    async def watch(self) -> None:
        """
        Start watching the registry file for changes.
        
        Runs in a background task and calls on_change callback when changes detected.
        """
        self._running = True
        logger.info(f"Started watching registry: {self.registry_path}")
        
        while self._running:
            try:
                if self.has_changed():
                    logger.info("Triggering registry reload")
                    if self.on_change:
                        if asyncio.iscoroutinefunction(self.on_change):
                            await self.on_change()
                        else:
                            self.on_change()
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in registry watcher: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info("Registry watcher stopped")
    
    def start(self) -> None:
        """Start the watcher in a background task."""
        if self._watch_task is None or self._watch_task.done():
            self._watch_task = asyncio.create_task(self.watch())
            logger.info("Registry watcher task started")
    
    def stop(self) -> None:
        """Stop the watcher."""
        self._running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
            logger.info("Registry watcher task cancelled")
    
    async def stop_async(self) -> None:
        """Stop the watcher and wait for task to complete."""
        self.stop()
        if self._watch_task and not self._watch_task.done():
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass


class GitWatcher:
    """
    Watch for git changes in project directories.
    
    Monitors .git/index and .git/refs/heads/* for changes.
    """
    
    def __init__(
        self,
        project_path: Path,
        on_git_change: Optional[Callable[[str], None]] = None,
        check_interval: float = 10.0,
    ):
        self.project_path = project_path
        self.on_git_change = on_git_change
        self.check_interval = check_interval
        self._git_path = project_path / ".git"
        self._index_hash: Optional[str] = None
        self._refs_hash: Optional[str] = None
        self._watch_task: Optional[asyncio.Task] = None
        self._running = False
    
    def _compute_git_hash(self) -> Optional[str]:
        """Compute combined hash of git index and refs."""
        if not self._git_path.exists():
            return None
        
        try:
            hashes = []
            
            # Hash git index
            index_file = self._git_path / "index"
            if index_file.exists():
                hashes.append(hashlib.md5(index_file.read_bytes()).hexdigest())
            
            # Hash HEAD
            head_file = self._git_path / "HEAD"
            if head_file.exists():
                hashes.append(hashlib.md5(head_file.read_bytes()).hexdigest())
            
            # Combine hashes
            combined = "".join(hashes)
            return hashlib.md5(combined.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to compute git hash: {e}")
            return None
    
    def has_changed(self) -> bool:
        """Check if git state has changed."""
        current_hash = self._compute_git_hash()
        
        if current_hash is None:
            return False
        
        # First check
        if self._index_hash is None:
            self._index_hash = current_hash
            return False
        
        # Check if changed
        changed = current_hash != self._index_hash
        
        if changed:
            logger.debug(f"Git change detected in: {self.project_path.name}")
            self._index_hash = current_hash
        
        return changed
    
    async def watch(self) -> None:
        """Watch for git changes."""
        self._running = True
        logger.info(f"Started watching git changes: {self.project_path.name}")
        
        while self._running:
            try:
                if self.has_changed():
                    if self.on_git_change:
                        if asyncio.iscoroutinefunction(self.on_git_change):
                            await self.on_git_change(str(self.project_path))
                        else:
                            self.on_git_change(str(self.project_path))
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in git watcher: {e}")
                await asyncio.sleep(self.check_interval)
        
        logger.info(f"Git watcher stopped: {self.project_path.name}")
    
    def start(self) -> None:
        """Start the watcher."""
        if self._watch_task is None or self._watch_task.done():
            self._watch_task = asyncio.create_task(self.watch())
    
    def stop(self) -> None:
        """Stop the watcher."""
        self._running = False
        if self._watch_task and not self._watch_task.done():
            self._watch_task.cancel()
    
    async def stop_async(self) -> None:
        """Stop and wait for completion."""
        self.stop()
        if self._watch_task and not self._watch_task.done():
            try:
                await self._watch_task
            except asyncio.CancelledError:
                pass


# ============ Global Watcher Instances ============

_registry_watcher: Optional[RegistryWatcher] = None
_git_watchers: Dict[str, GitWatcher] = {}


def get_registry_watcher(
    registry_path: Path,
    on_change: Optional[Callable[[], None]] = None,
) -> RegistryWatcher:
    """Get or create the global registry watcher."""
    global _registry_watcher
    if _registry_watcher is None:
        _registry_watcher = RegistryWatcher(registry_path, on_change)
    return _registry_watcher


def start_registry_watching(
    registry_path: Path,
    on_change: Optional[Callable[[], None]] = None,
) -> None:
    """Start watching the agent registry file."""
    watcher = get_registry_watcher(registry_path, on_change)
    watcher.start()


async def stop_registry_watching() -> None:
    """Stop the registry watcher."""
    global _registry_watcher
    if _registry_watcher:
        await _registry_watcher.stop_async()
        _registry_watcher = None


def start_git_watching(
    project_path: Path,
    on_git_change: Optional[Callable[[str], None]] = None,
) -> None:
    """Start watching a project's git repository."""
    global _git_watchers
    key = str(project_path)
    
    if key not in _git_watchers:
        _git_watchers[key] = GitWatcher(project_path, on_git_change)
    
    _git_watchers[key].start()


async def stop_all_git_watchers() -> None:
    """Stop all git watchers."""
    global _git_watchers
    for watcher in _git_watchers.values():
        await watcher.stop_async()
    _git_watchers.clear()
