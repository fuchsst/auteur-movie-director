"""
Workspace service implementing programmatically enforced project structure.
This is the core implementation of the Project-as-Repository model.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from uuid import uuid4

import git
from pydantic import ValidationError

from app.schemas.project import (
    ChapterInfo,
    CharacterAsset,
    GitConfig,
    NarrativeConfig,
    NarrativeStructure,
    ProjectCreate,
    ProjectManifest,
    ProjectMetadata,
    ProjectStructureValidation,
)

logger = logging.getLogger(__name__)


class WorkspaceService:
    """
    Service for managing workspace and project structure.
    Enforces the numbered directory structure as API contract.
    """

    # Numbered directories as API contract - ANY DEVIATION IS A BREAKING CHANGE
    REQUIRED_STRUCTURE = [
        "01_Assets/Characters",
        "01_Assets/Styles",
        "01_Assets/Locations",
        "02_Story",
        "03_Renders",
        "04_Compositions",
        "05_Audio",
        "06_Exports"
    ]

    # Files/directories to ignore in Git by default
    GIT_IGNORE_PATTERNS = [
        # Python
        "__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.so",
        ".Python",
        "venv/",
        "ENV/",
        # Node
        "node_modules/",
        "npm-debug.log*",
        "yarn-debug.log*",
        "yarn-error.log*",
        # IDE
        ".vscode/",
        ".idea/",
        "*.swp",
        "*.swo",
        "*~",
        # OS
        ".DS_Store",
        ".DS_Store?",
        "._*",
        ".Spotlight-V100",
        ".Trashes",
        "ehthumbs.db",
        "Thumbs.db",
        # Project specific
        "*.log",
        ".env.local",
        "# Temporary files",
        "*.tmp",
        "*.bak",
        "*.cache"
    ]

    # Narrative structure templates
    NARRATIVE_STRUCTURES = {
        NarrativeStructure.THREE_ACT: [
            ("act-1", "Act I: Setup"),
            ("act-2", "Act II: Confrontation"),
            ("act-3", "Act III: Resolution"),
        ],
        NarrativeStructure.HERO_JOURNEY: [
            ("ordinary-world", "Ordinary World"),
            ("call-to-adventure", "Call to Adventure"),
            ("ordeal", "Ordeal"),
            ("return", "Return"),
        ],
        NarrativeStructure.BEAT_SHEET: [
            ("opening-image", "Opening Image"),
            ("setup", "Setup"),
            ("catalyst", "Catalyst"),
            ("debate", "Debate"),
            ("break-into-two", "Break Into Two"),
            ("b-story", "B Story"),
            ("fun-and-games", "Fun and Games"),
            ("midpoint", "Midpoint"),
            ("bad-guys-close-in", "Bad Guys Close In"),
            ("all-is-lost", "All Is Lost"),
            ("dark-night", "Dark Night of the Soul"),
            ("break-into-three", "Break Into Three"),
            ("finale", "Finale"),
            ("final-image", "Final Image"),
        ],
        NarrativeStructure.STORY_CIRCLE: [
            ("you", "You"),
            ("need", "Need"),
            ("go", "Go"),
            ("search", "Search"),
            ("find", "Find"),
            ("take", "Take"),
            ("return", "Return"),
            ("change", "Change"),
        ],
    }

    def __init__(self, workspace_root: str):
        self.workspace_root = Path(workspace_root)
        self._ensure_workspace_exists()

    def _ensure_workspace_exists(self) -> None:
        """Ensure workspace directory exists"""
        self.workspace_root.mkdir(parents=True, exist_ok=True)

    def create_project(self, project_data: ProjectCreate) -> tuple[Path, ProjectManifest]:
        """
        Create a new project with enforced structure.
        Returns tuple of (project_path, manifest).
        """
        # Performance timer
        import time
        start_time = time.time()
        
        # Sanitize project name for directory
        safe_name = self._sanitize_project_name(project_data.name)
        project_path = self.workspace_root / safe_name

        # Check if project already exists
        if project_path.exists():
            raise ValueError(f"Project '{safe_name}' already exists")

        try:
            # Create project directory
            project_path.mkdir(parents=True)

            # Create enforced directory structure
            self._create_directory_structure(project_path)

            # Initialize Git with LFS
            self._initialize_git_with_lfs(project_path)

            # Create project manifest
            manifest = self._create_project_manifest(project_path, project_data)

            # Save project.json
            self._save_project_manifest(project_path, manifest)

            # Create initial Git commit
            self._create_initial_commit(project_path)

            # Validate the created structure
            validation = self.validate_project_structure(project_path)
            if not validation.valid:
                raise RuntimeError(f"Project creation validation failed: {validation.errors}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"Project '{project_data.name}' created at {project_path} in {elapsed_time:.2f}s")
            
            # Send WebSocket notification
            self._send_project_created_notification(manifest.id, str(project_path))
            
            return project_path, manifest

        except Exception as e:
            # Clean up on failure
            if project_path.exists():
                shutil.rmtree(project_path)
            raise e

    def _sanitize_project_name(self, name: str) -> str:
        """Sanitize project name for use as directory name"""
        # Replace spaces and special characters with underscores
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in name)
        # Remove leading/trailing underscores
        safe_name = safe_name.strip("_")
        # Ensure not empty
        if not safe_name:
            safe_name = "untitled_project"
        return safe_name

    def _create_directory_structure(self, project_path: Path) -> None:
        """Create the enforced directory structure"""
        for dir_path in self.REQUIRED_STRUCTURE:
            full_path = project_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            # Add .gitkeep to empty directories
            gitkeep = full_path / ".gitkeep"
            gitkeep.touch()

    def _initialize_git_with_lfs(self, project_path: Path) -> None:
        """Initialize Git repository with LFS configuration"""
        # Use our async Git service synchronously for now
        # TODO: Make workspace service async in the future
        import asyncio

        from app.services.git import git_service

        # Run async initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            success = loop.run_until_complete(git_service.initialize_repository(project_path))
            if not success:
                raise RuntimeError("Failed to initialize Git repository")
        finally:
            loop.close()

        # Create .gitignore and .gitattributes
        self._generate_gitignore(project_path)
        self._generate_gitattributes(project_path)

    def _generate_gitignore(self, project_path: Path) -> None:
        """Generate .gitignore file"""
        gitignore_path = project_path / ".gitignore"

        with open(gitignore_path, "w") as f:
            f.write("# Auto-generated .gitignore for Auteur Movie Director\n\n")

            for pattern in self.GIT_IGNORE_PATTERNS:
                f.write(f"{pattern}\n")
                
    def _generate_gitattributes(self, project_path: Path) -> None:
        """Generate .gitattributes file with LFS patterns"""
        gitattributes_path = project_path / ".gitattributes"
        
        # Import LFS patterns from git service
        from app.services.git import GitService
        
        with open(gitattributes_path, "w") as f:
            f.write("# Auto-generated .gitattributes for Auteur Movie Director\n")
            f.write("# Configure Git LFS for media files\n\n")
            
            # Add all LFS patterns
            for pattern in sorted(GitService.LFS_EXTENSIONS):
                f.write(f"{pattern} filter=lfs diff=lfs merge=lfs -text\n")
            
            f.write("\n# Additional patterns\n")
            f.write("# Ensure consistent line endings\n")
            f.write("*.py text eol=lf\n")
            f.write("*.js text eol=lf\n")
            f.write("*.json text eol=lf\n")
            f.write("*.md text eol=lf\n")

    def _create_project_manifest(
        self, project_path: Path, project_data: ProjectCreate
    ) -> ProjectManifest:
        """Create project manifest according to STORY-025 specification"""
        from datetime import datetime, timezone
        
        # Create the manifest according to the exact specification
        manifest_data = {
            "id": str(uuid4()),
            "name": project_data.name,
            "version": "1.0.0",
            "structure_version": "1.0",
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "created_by": project_data.director or os.environ.get("USER", "unknown"),
            "metadata": {
                "description": project_data.description or "",
                "tags": [],
                "settings": {}
            },
            "canvas_state": None
        }
        
        # Convert to ProjectManifest for compatibility
        # Generate narrative chapters based on structure
        chapters = []
        structure_template = self.NARRATIVE_STRUCTURES[project_data.narrative_structure]

        for i, (chapter_id, chapter_name) in enumerate(structure_template):
            chapters.append(ChapterInfo(id=chapter_id, name=chapter_name, order=i + 1, scenes=[]))

        # Create narrative config
        narrative = NarrativeConfig(structure=project_data.narrative_structure, chapters=chapters)

        # Create project manifest using the schema
        manifest = ProjectManifest(
            id=manifest_data["id"],
            name=manifest_data["name"],
            version=manifest_data["version"],
            quality=project_data.quality,
            narrative=narrative,
            metadata=ProjectMetadata(
                director=manifest_data["created_by"],
                description=manifest_data["metadata"]["description"]
            ),
            git=GitConfig(
                initialized=True,
                lfs_enabled=True
            )
        )

        return manifest

    def _save_project_manifest(self, project_path: Path, manifest: ProjectManifest) -> None:
        """Save project manifest to project.json"""
        manifest_path = project_path / "project.json"
        
        # Save the full manifest for compatibility with validation
        with open(manifest_path, "w") as f:
            json.dump(manifest.model_dump() if hasattr(manifest, 'model_dump') else manifest.dict(), f, indent=2, default=str)

    def _create_initial_commit(self, project_path: Path) -> None:
        """Create initial Git commit"""
        repo = git.Repo(project_path)
        repo.index.add("*")
        repo.index.commit("Initial project structure")

    def validate_project_structure(self, project_path: Path) -> ProjectStructureValidation:
        """
        Validate project structure integrity.
        Any deviation is considered a breaking change.
        """
        # Initialize with all required fields
        result = ProjectStructureValidation(
            valid=True, git_initialized=False, git_lfs_enabled=False, project_json_valid=False
        )

        # Check if project path exists
        if not project_path.exists():
            result.valid = False
            result.errors.append(f"Project path does not exist: {project_path}")
            return result

        # Check required directories
        for required_dir in self.REQUIRED_STRUCTURE:
            dir_path = project_path / required_dir
            if not dir_path.exists():
                result.valid = False
                result.missing_directories.append(required_dir)

        # Check for Git repository
        try:
            git.Repo(project_path)
            result.git_initialized = True

            # Check if Git LFS is enabled
            gitattributes = project_path / ".gitattributes"
            if gitattributes.exists():
                with open(gitattributes) as f:
                    content = f.read()
                    result.git_lfs_enabled = "filter=lfs" in content
            else:
                result.git_lfs_enabled = False

        except git.InvalidGitRepositoryError:
            result.git_initialized = False
            result.git_lfs_enabled = False
            result.valid = False
            result.errors.append("Not a valid Git repository")

        # Validate project.json
        manifest_path = project_path / "project.json"
        if manifest_path.exists():
            try:
                with open(manifest_path) as f:
                    data = json.load(f)
                    ProjectManifest(**data)
                result.project_json_valid = True
            except (json.JSONDecodeError, ValidationError) as e:
                result.project_json_valid = False
                result.valid = False
                result.errors.append(f"Invalid project.json: {str(e)}")
        else:
            result.project_json_valid = False
            result.valid = False
            result.errors.append("Missing project.json")

        return result

    def create_hierarchical_path(
        self, project_path: Path, chapter: str, scene: str, shot: str
    ) -> Path:
        """
        Generate Takes system path: 03_Renders/{chapter}/{scene}/{shot}/
        """
        renders_path = project_path / "03_Renders" / chapter / scene / shot
        renders_path.mkdir(parents=True, exist_ok=True)
        return renders_path

    def create_character_structure(self, project_path: Path, character_name: str) -> Path:
        """
        Create character-specific directory structure for assets.
        Returns the character directory path.
        """
        # Sanitize character name
        safe_name = self._sanitize_project_name(character_name)
        char_path = project_path / "01_Assets" / "Characters" / safe_name

        # Create subdirectories
        (char_path / "lora").mkdir(parents=True, exist_ok=True)
        (char_path / "variations").mkdir(exist_ok=True)

        # Add .gitkeep files
        (char_path / "lora" / ".gitkeep").touch()
        (char_path / "variations" / ".gitkeep").touch()

        return char_path

    def list_projects(self) -> list[dict[str, any]]:
        """List all projects in workspace"""
        projects = []

        for item in self.workspace_root.iterdir():
            if item.is_dir() and (item / "project.json").exists():
                try:
                    with open(item / "project.json") as f:
                        manifest = json.load(f)
                        projects.append(
                            {
                                "path": str(item),
                                "manifest": manifest,
                                "validation": self.validate_project_structure(item),
                            }
                        )
                except Exception as e:
                    logger.error(f"Error reading project {item}: {e}")

        return projects

    def get_project_manifest(self, project_path: Path) -> ProjectManifest | None:
        """Load project manifest from project.json"""
        manifest_path = project_path / "project.json"

        if not manifest_path.exists():
            return None

        try:
            with open(manifest_path) as f:
                data = json.load(f)
                return ProjectManifest(**data)
        except Exception as e:
            logger.error(f"Error loading project manifest: {e}")
            return None

    def get_project_path(self, project_id: str) -> Path | None:
        """Get project path by ID or name"""
        # First try to find by manifest ID
        for item in self.workspace_root.iterdir():
            if item.is_dir() and (item / "project.json").exists():
                manifest = self.get_project_manifest(item)
                if manifest and manifest.id == project_id:
                    return item

        # Try by directory name
        project_path = self.workspace_root / project_id
        if project_path.exists() and project_path.is_dir():
            return project_path

        return None

    def update_project_manifest(self, project_path: Path, manifest: ProjectManifest) -> bool:
        """Update the project manifest in project.json"""
        try:
            self._save_project_manifest(project_path, manifest)
            return True
        except Exception as e:
            logger.error(f"Error updating project manifest: {e}")
            return False

    def add_character_to_project(
        self, project_path: Path, character_name: str, description: str = ""
    ) -> CharacterAsset | None:
        """Add a character to the project manifest with basic structure"""
        try:
            # Load current manifest
            manifest = self.get_project_manifest(project_path)
            if not manifest:
                logger.error("Project manifest not found")
                return None

            # Create character structure
            self.create_character_structure(project_path, character_name)

            # Create character asset
            character_id = str(uuid4())
            character = CharacterAsset(
                # AssetReference fields
                id=character_id,
                name=character_name,
                type="Character",
                path=f"01_Assets/Characters/{self._sanitize_project_name(character_name)}",
                # CharacterAsset specific fields
                assetId=character_id,
                assetType="Character",
                description=description,
                triggerWord=None,  # Placeholder for future LoRA
                baseFaceImagePath=None,  # Placeholder
                loraModelPath=None,  # Placeholder for future
                loraTrainingStatus="untrained",
                variations={},  # Empty, will be populated later
                usage=[],  # Will track shot IDs in future
            )

            # Add to manifest
            if "characters" not in manifest.assets:
                manifest.assets["characters"] = []

            # Check if character already exists
            for existing in manifest.assets["characters"]:
                # Handle both dict and object forms
                existing_name = existing.name if hasattr(existing, "name") else existing.get("name")
                if existing_name == character_name:
                    logger.warning(f"Character '{character_name}' already exists")
                    return None

            manifest.assets["characters"].append(character)

            # Save updated manifest
            if self.update_project_manifest(project_path, manifest):
                logger.info(f"Added character '{character_name}' to project")
                return character

            return None

        except Exception as e:
            logger.error(f"Error adding character to project: {e}")
            return None
    
    def _send_project_created_notification(self, project_id: str, project_path: str) -> None:
        """Send WebSocket notification that project was created"""
        try:
            # Import here to avoid circular imports
            import asyncio
            from datetime import datetime, timezone
            from app.api.websocket import manager
            
            # Create notification message
            message = {
                "type": "project_created",
                "project_id": project_id,
                "project_path": project_path,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Run async broadcast synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(manager.broadcast(message))
            finally:
                loop.close()
        except Exception as e:
            # Don't fail project creation if notification fails
            logger.warning(f"Failed to send WebSocket notification: {e}")


# Global workspace service instance - will be initialized in the endpoint
workspace_service = None


def get_workspace_service():
    """Get or create workspace service instance"""
    global workspace_service
    if workspace_service is None:
        from app.config import settings

        workspace_service = WorkspaceService(str(settings.workspace_root))
    return workspace_service
