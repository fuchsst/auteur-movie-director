"""
Template Registry Manager

Central registry for function templates with hot-reload and versioning support.
"""

import asyncio
import logging
import threading
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime
from packaging.version import Version
from pydantic import BaseModel
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent

from .base import FunctionTemplate
from .validation import TemplateValidator
from .exceptions import TemplateNotFoundError, TemplateLoadError

logger = logging.getLogger(__name__)


class TemplateInfo(BaseModel):
    """Summary information about a template"""
    id: str
    name: str
    version: str
    category: str
    description: str
    author: str
    tags: List[str]
    requires_gpu: bool
    loaded_at: datetime
    file_path: str


class TemplateFileHandler(FileSystemEventHandler):
    """Handle template file changes for hot-reload"""
    
    def __init__(self, registry: 'TemplateRegistry'):
        self.registry = registry
        self._pending_reloads: Set[Path] = set()
        self._reload_timer = None
    
    def on_created(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_template_file(event.src_path):
            self._schedule_reload(Path(event.src_path))
    
    def on_modified(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_template_file(event.src_path):
            self._schedule_reload(Path(event.src_path))
    
    def on_deleted(self, event: FileSystemEvent) -> None:
        if not event.is_directory and self._is_template_file(event.src_path):
            asyncio.create_task(
                self.registry._handle_template_deletion(Path(event.src_path))
            )
    
    def _is_template_file(self, path: str) -> bool:
        """Check if file is a template definition"""
        path_obj = Path(path)
        return path_obj.suffix in ['.yaml', '.yml', '.json']
    
    def _schedule_reload(self, file_path: Path) -> None:
        """Schedule template reload with debouncing"""
        self._pending_reloads.add(file_path)
        
        # Cancel existing timer
        if self._reload_timer:
            self._reload_timer.cancel()
        
        # Schedule new reload in 1 second
        self._reload_timer = threading.Timer(
            1.0, 
            lambda: asyncio.create_task(self._process_reloads())
        )
        self._reload_timer.start()
    
    async def _process_reloads(self) -> None:
        """Process pending template reloads"""
        reloads = list(self._pending_reloads)
        self._pending_reloads.clear()
        
        for file_path in reloads:
            try:
                await self.registry.load_template_file(file_path)
                logger.info(f"Hot-reloaded template: {file_path}")
            except Exception as e:
                logger.error(f"Failed to hot-reload {file_path}: {e}")


class TemplateRegistry:
    """Central registry for all function templates"""
    
    def __init__(self, template_dirs: List[Path]):
        """
        Initialize template registry.
        
        Args:
            template_dirs: List of directories containing template definitions
        """
        self.template_dirs = template_dirs
        self.templates: Dict[str, FunctionTemplate] = {}
        self.template_versions: Dict[str, List[str]] = {}
        self.template_files: Dict[str, Path] = {}  # Maps template_key to file path
        self._lock = threading.RLock()
        self._file_observer = None
        self._validator = TemplateValidator()
        self._initialized = False
    
    async def initialize(self) -> None:
        """Load all templates and start file watcher"""
        if self._initialized:
            return
        
        logger.info("Initializing template registry...")
        
        # Load templates from all directories
        for template_dir in self.template_dirs:
            if template_dir.exists():
                await self.load_templates_from_directory(template_dir)
            else:
                logger.warning(f"Template directory not found: {template_dir}")
        
        # Start file watcher for hot-reload
        self._start_file_watcher()
        
        self._initialized = True
        logger.info(
            f"Template registry initialized with {len(self.templates)} templates"
        )
    
    async def load_templates_from_directory(self, directory: Path) -> None:
        """Load all templates from a directory"""
        template_files = list(directory.glob("**/*.yaml")) + \
                        list(directory.glob("**/*.yml")) + \
                        list(directory.glob("**/*.json"))
        
        for file_path in template_files:
            try:
                await self.load_template_file(file_path)
            except Exception as e:
                logger.error(f"Failed to load template {file_path}: {e}")
    
    async def load_template_file(self, file_path: Path) -> None:
        """Load and validate a single template file"""
        try:
            # Read file content
            content = file_path.read_text()
            
            # Parse based on file extension
            if file_path.suffix == '.json':
                definition = json.loads(content)
            else:
                definition = yaml.safe_load(content)
            
            # Validate template definition
            errors = self._validator.validate(definition)
            if errors:
                raise TemplateLoadError(
                    f"Validation errors in {file_path}:\n" + 
                    '\n'.join(f"  - {error}" for error in errors)
                )
            
            # Create template instance
            template = FunctionTemplate(definition)
            
            # Register template
            await self._register_template(template, file_path)
            
        except Exception as e:
            logger.error(f"Error loading template from {file_path}: {e}")
            raise TemplateLoadError(f"Failed to load {file_path}: {str(e)}")
    
    async def _register_template(self, template: FunctionTemplate, file_path: Path) -> None:
        """Register a template in the registry"""
        with self._lock:
            template_key = f"{template.id}@{template.version}"
            
            # Check if replacing existing template
            if template_key in self.templates:
                logger.info(f"Replacing existing template: {template_key}")
            
            # Store template
            self.templates[template_key] = template
            self.template_files[template_key] = file_path
            
            # Update version tracking
            if template.id not in self.template_versions:
                self.template_versions[template.id] = []
            
            if template.version not in self.template_versions[template.id]:
                self.template_versions[template.id].append(template.version)
                # Sort versions
                self.template_versions[template.id].sort(
                    key=lambda v: Version(v), reverse=True
                )
            
            logger.info(f"Registered template: {template_key} from {file_path}")
    
    async def _handle_template_deletion(self, file_path: Path) -> None:
        """Handle deletion of a template file"""
        with self._lock:
            # Find templates loaded from this file
            templates_to_remove = []
            for key, path in self.template_files.items():
                if path == file_path:
                    templates_to_remove.append(key)
            
            # Remove templates
            for key in templates_to_remove:
                template = self.templates.pop(key, None)
                if template:
                    logger.info(f"Removed template {key} due to file deletion")
                    
                    # Update version tracking
                    versions = self.template_versions.get(template.id, [])
                    if template.version in versions:
                        versions.remove(template.version)
                    if not versions:
                        self.template_versions.pop(template.id, None)
                
                self.template_files.pop(key, None)
    
    def get_template(self, template_id: str, version: Optional[str] = None) -> FunctionTemplate:
        """
        Get template by ID and optional version.
        
        Args:
            template_id: Template identifier
            version: Specific version (latest if not specified)
            
        Returns:
            FunctionTemplate instance
            
        Raises:
            TemplateNotFoundError: If template not found
        """
        with self._lock:
            if version:
                # Get specific version
                template_key = f"{template_id}@{version}"
                if template_key not in self.templates:
                    raise TemplateNotFoundError(
                        f"Template '{template_id}' version '{version}' not found"
                    )
                return self.templates[template_key]
            else:
                # Get latest version
                if template_id not in self.template_versions:
                    raise TemplateNotFoundError(f"Template '{template_id}' not found")
                
                versions = self.template_versions[template_id]
                if not versions:
                    raise TemplateNotFoundError(f"No versions found for '{template_id}'")
                
                latest_version = versions[0]  # Already sorted, first is latest
                return self.get_template(template_id, latest_version)
    
    def list_templates(
        self, 
        category: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[TemplateInfo]:
        """
        List all available templates.
        
        Args:
            category: Filter by category
            tags: Filter by tags (templates must have all specified tags)
            
        Returns:
            List of template information
        """
        with self._lock:
            templates = []
            
            for key, template in self.templates.items():
                # Apply filters
                if category and template.category != category:
                    continue
                
                if tags:
                    template_tags = set(template.tags)
                    if not all(tag in template_tags for tag in tags):
                        continue
                
                # Get file info
                file_path = self.template_files.get(key, Path("unknown"))
                
                templates.append(TemplateInfo(
                    id=template.id,
                    name=template.name,
                    version=template.version,
                    category=template.category,
                    description=template.description,
                    author=template.author,
                    tags=template.tags,
                    requires_gpu=template.resources.gpu,
                    loaded_at=datetime.fromtimestamp(file_path.stat().st_mtime),
                    file_path=str(file_path)
                ))
            
            # Sort by name and version
            templates.sort(key=lambda t: (t.name, Version(t.version)))
            
            return templates
    
    def get_template_versions(self, template_id: str) -> List[str]:
        """Get all available versions of a template"""
        with self._lock:
            if template_id not in self.template_versions:
                raise TemplateNotFoundError(f"Template '{template_id}' not found")
            
            return self.template_versions[template_id].copy()
    
    def template_exists(self, template_id: str, version: Optional[str] = None) -> bool:
        """Check if a template exists"""
        with self._lock:
            if version:
                return f"{template_id}@{version}" in self.templates
            else:
                return template_id in self.template_versions
    
    def reload_template(self, template_id: str, version: str) -> None:
        """Force reload a specific template"""
        with self._lock:
            template_key = f"{template_id}@{version}"
            if template_key not in self.template_files:
                raise TemplateNotFoundError(f"Template {template_key} not found")
            
            file_path = self.template_files[template_key]
            
        # Reload outside lock to avoid blocking
        asyncio.create_task(self.load_template_file(file_path))
    
    def get_categories(self) -> List[str]:
        """Get all unique template categories"""
        with self._lock:
            categories = set()
            for template in self.templates.values():
                categories.add(template.category)
            return sorted(categories)
    
    def get_all_tags(self) -> List[str]:
        """Get all unique tags across templates"""
        with self._lock:
            tags = set()
            for template in self.templates.values():
                tags.update(template.tags)
            return sorted(tags)
    
    def _start_file_watcher(self) -> None:
        """Start watching template directories for changes"""
        if self._file_observer:
            return
        
        self._file_observer = Observer()
        handler = TemplateFileHandler(self)
        
        for template_dir in self.template_dirs:
            if template_dir.exists():
                self._file_observer.schedule(
                    handler, 
                    str(template_dir), 
                    recursive=True
                )
                logger.info(f"Watching template directory: {template_dir}")
        
        self._file_observer.start()
    
    def shutdown(self) -> None:
        """Shutdown the registry and stop file watching"""
        if self._file_observer:
            self._file_observer.stop()
            self._file_observer.join()
            self._file_observer = None
        
        logger.info("Template registry shutdown complete")