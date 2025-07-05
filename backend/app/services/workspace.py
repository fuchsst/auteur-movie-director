"""
Workspace service implementing programmatically enforced project structure.
This is the core implementation of the Project-as-Repository model.
"""

import json
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

import git
from pydantic import ValidationError

from app.schemas.project import (
    ChapterInfo,
    NarrativeConfig,
    NarrativeStructure,
    ProjectCreate,
    ProjectManifest,
    ProjectStructureValidation,
    QualityLevel,
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
        "01_Assets/Music",
        "01_Assets/Scripts",
        "02_Source_Creative/Treatments",
        "02_Source_Creative/Scripts",
        "02_Source_Creative/Shot_Lists",
        "02_Source_Creative/Canvas",
        "03_Renders",
        "04_Project_Files/ComfyUI",
        "04_Project_Files/Blender",
        "04_Project_Files/DaVinci",
        "05_Cache/Models",
        "06_Exports/EDL",
        "06_Exports/Masters",
        "06_Exports/Deliverables",
        ".auteur",  # Project-specific config directory
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
        ".auteur/cache/",
        ".auteur/temp/",
        "*.log",
        ".env.local",
        "05_Cache/",  # Entire cache directory
        "06_Exports/",  # Large final exports
    ]

    # Git LFS patterns for large files
    GIT_LFS_PATTERNS = [
        # Images
        "*.png",
        "*.jpg",
        "*.jpeg",
        "*.tiff",
        "*.psd",
        "*.exr",
        # Video
        "*.mp4",
        "*.mov",
        "*.avi",
        "*.mkv",
        "*.webm",
        # Audio
        "*.wav",
        "*.mp3",
        "*.aiff",
        "*.flac",
        # 3D
        "*.blend",
        "*.blend1",
        "*.fbx",
        "*.obj",
        "*.abc",
        # AI Models
        "*.safetensors",
        "*.ckpt",
        "*.pt",
        "*.pth",
        "*.bin",
        # Specific directories for all files
        "04_Generated/**/*",
        "03_Renders/**/*",
        "01_Assets/Characters/*/lora/*",
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

    def create_project(self, project_data: ProjectCreate) -> Tuple[Path, ProjectManifest]:
        """
        Create a new project with enforced structure.
        Returns tuple of (project_path, manifest).
        """
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

            logger.info(f"Project '{project_data.name}' created at {project_path}")
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
        # Initialize Git repository
        repo = git.Repo.init(project_path)

        # Install Git LFS
        repo.git.lfs("install")

        # Create .gitattributes with LFS tracking rules
        self._generate_gitattributes(project_path)

        # Create .gitignore
        self._generate_gitignore(project_path)

    def _generate_gitattributes(self, project_path: Path) -> None:
        """Generate .gitattributes with LFS tracking rules"""
        gitattributes_path = project_path / ".gitattributes"

        with open(gitattributes_path, "w") as f:
            f.write("# Git LFS tracking rules for Auteur Movie Director\n")
            f.write("# This file is auto-generated - DO NOT MODIFY\n\n")

            for pattern in self.GIT_LFS_PATTERNS:
                f.write(f"{pattern} filter=lfs diff=lfs merge=lfs -text\n")

    def _generate_gitignore(self, project_path: Path) -> None:
        """Generate .gitignore file"""
        gitignore_path = project_path / ".gitignore"

        with open(gitignore_path, "w") as f:
            f.write("# Auto-generated .gitignore for Auteur Movie Director\n\n")

            for pattern in self.GIT_IGNORE_PATTERNS:
                f.write(f"{pattern}\n")

    def _create_project_manifest(
        self, project_path: Path, project_data: ProjectCreate
    ) -> ProjectManifest:
        """Create project manifest with narrative structure"""
        # Generate narrative chapters based on structure
        chapters = []
        structure_template = self.NARRATIVE_STRUCTURES[project_data.narrative_structure]

        for i, (chapter_id, chapter_name) in enumerate(structure_template):
            chapters.append(ChapterInfo(id=chapter_id, name=chapter_name, order=i + 1, scenes=[]))

        # Create narrative config
        narrative = NarrativeConfig(structure=project_data.narrative_structure, chapters=chapters)

        # Create project manifest
        manifest = ProjectManifest(
            id=str(uuid4()),
            name=project_data.name,
            quality=project_data.quality,
            narrative=narrative,
            metadata={
                "director": project_data.director or os.environ.get("USER", "unknown"),
                "description": project_data.description or "",
            },
            git={
                "initialized": True,
                "lfs_enabled": True,
            },
        )

        return manifest

    def _save_project_manifest(self, project_path: Path, manifest: ProjectManifest) -> None:
        """Save project manifest to project.json"""
        manifest_path = project_path / "project.json"

        with open(manifest_path, "w") as f:
            json.dump(manifest.dict(), f, indent=2, default=str)

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
        result = ProjectStructureValidation(valid=True)

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
            repo = git.Repo(project_path)
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

    def list_projects(self) -> List[Dict[str, any]]:
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

    def get_project_manifest(self, project_path: Path) -> Optional[ProjectManifest]:
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
