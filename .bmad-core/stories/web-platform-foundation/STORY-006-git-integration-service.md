# Story: Git Integration Service with LFS Support

**Story ID**: STORY-006  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ✅ Completed  
**Completion Date**: 2025-07-06  

## Story Description
As a creative professional, I need automatic Git version control with LFS (Large File Storage) support for my projects so that I can efficiently track changes to both code and large media files, revert to previous versions, and maintain a complete history of my creative decisions without manual version management or repository bloat.

## Acceptance Criteria

### Functional Requirements
- [ ] New projects automatically initialize as Git repositories with LFS enabled
- [ ] Git LFS is configured during project initialization (mandatory)
- [ ] Comprehensive .gitattributes template for all media file types
- [ ] Project creation commits initial structure including LFS configuration
- [ ] API endpoint to commit current project state
- [ ] API endpoint to view Git status (including LFS status)
- [ ] API endpoint to list commit history
- [ ] API endpoint to validate project structure before Git operations
- [ ] Appropriate .gitignore excludes generated and temporary content

### Technical Requirements
- [ ] Use GitPython for standard Git operations
- [ ] Execute Git LFS commands via subprocess for LFS operations
- [ ] Handle Git operations asynchronously
- [ ] Validate Git LFS installation on service startup
- [ ] Provide meaningful commit messages with semantic prefixes
- [ ] Include author information in commits
- [ ] Handle Git and LFS errors gracefully
- [ ] Support Windows, Mac, and Linux
- [ ] Container volume considerations for Git operations

### Git LFS Configuration
- Automatic LFS track patterns for media files
- .gitattributes includes all common media formats
- LFS pointer files for tracked binaries
- Proper handling of LFS storage in containers

### Git Operations
- Initialize repository with LFS on project creation
- Validate project structure before commits
- Auto-commit project.json and metadata changes
- Manual commit endpoint for creative checkpoints
- Status endpoint showing changed files and LFS status
- History endpoint with recent commits and file sizes

## Implementation Notes

### Git Service Implementation
```python
# app/services/git.py
import subprocess
from git import Repo, GitCommandError, Actor
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GitService:
    def __init__(self):
        self.author_name = "Auteur Movie Director"
        self.author_email = "auteur@localhost"
        self._validate_lfs_installation()
    
    def _validate_lfs_installation(self):
        """Validate Git LFS is installed and available"""
        try:
            result = subprocess.run(
                ["git", "lfs", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Git LFS detected: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Git LFS is not installed. Please install Git LFS to use this service."
            )
    
    async def init_repository(self, project_path: Path) -> Repo:
        """Initialize Git repository with LFS for new project"""
        try:
            repo = Repo.init(project_path)
            
            # Initialize Git LFS
            subprocess.run(
                ["git", "lfs", "install"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            # Create comprehensive .gitattributes for media files
            gitattributes_content = """
# Video files
*.mp4 filter=lfs diff=lfs merge=lfs -text
*.mov filter=lfs diff=lfs merge=lfs -text
*.avi filter=lfs diff=lfs merge=lfs -text
*.mkv filter=lfs diff=lfs merge=lfs -text
*.webm filter=lfs diff=lfs merge=lfs -text
*.flv filter=lfs diff=lfs merge=lfs -text
*.wmv filter=lfs diff=lfs merge=lfs -text
*.mpg filter=lfs diff=lfs merge=lfs -text
*.mpeg filter=lfs diff=lfs merge=lfs -text

# Audio files
*.wav filter=lfs diff=lfs merge=lfs -text
*.mp3 filter=lfs diff=lfs merge=lfs -text
*.flac filter=lfs diff=lfs merge=lfs -text
*.aac filter=lfs diff=lfs merge=lfs -text
*.ogg filter=lfs diff=lfs merge=lfs -text
*.wma filter=lfs diff=lfs merge=lfs -text
*.m4a filter=lfs diff=lfs merge=lfs -text
*.aiff filter=lfs diff=lfs merge=lfs -text

# Image files (large assets)
*.psd filter=lfs diff=lfs merge=lfs -text
*.psb filter=lfs diff=lfs merge=lfs -text
*.ai filter=lfs diff=lfs merge=lfs -text
*.tiff filter=lfs diff=lfs merge=lfs -text
*.tif filter=lfs diff=lfs merge=lfs -text
*.exr filter=lfs diff=lfs merge=lfs -text
*.hdr filter=lfs diff=lfs merge=lfs -text

# 3D files
*.blend filter=lfs diff=lfs merge=lfs -text
*.fbx filter=lfs diff=lfs merge=lfs -text
*.obj filter=lfs diff=lfs merge=lfs -text
*.dae filter=lfs diff=lfs merge=lfs -text
*.3ds filter=lfs diff=lfs merge=lfs -text
*.max filter=lfs diff=lfs merge=lfs -text

# ML model files
*.ckpt filter=lfs diff=lfs merge=lfs -text
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text

# Archive files
*.zip filter=lfs diff=lfs merge=lfs -text
*.rar filter=lfs diff=lfs merge=lfs -text
*.7z filter=lfs diff=lfs merge=lfs -text
*.tar filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text

# Keep smaller images as regular files for quick preview
*.jpg -filter=lfs -diff=lfs -merge=lfs
*.jpeg -filter=lfs -diff=lfs -merge=lfs
*.png -filter=lfs -diff=lfs -merge=lfs
*.gif -filter=lfs -diff=lfs -merge=lfs
*.webp -filter=lfs -diff=lfs -merge=lfs
            """.strip()
            
            gitattributes_path = project_path / ".gitattributes"
            gitattributes_path.write_text(gitattributes_content)
            
            # Create .gitignore
            gitignore_content = """
# Generated content (recreatable)
/generated/
/outputs/temp/

# Temporary files
*.tmp
*.cache
*.log
.DS_Store
Thumbs.db
__pycache__/
*.pyc

# IDE files
.vscode/
.idea/
*.swp
*.swo

# Environment files
.env
.env.local

# Large exports (tracked by LFS if committed)
/exports/renders/wip/

# But keep directory structure
!.gitkeep

# ComfyUI specific
comfyui_session.json
*.ckpt.tmp
            """.strip()
            
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(gitignore_content)
            
            # Track LFS config
            subprocess.run(
                ["git", "lfs", "track"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            # Initial commit
            repo.index.add([".gitignore", ".gitattributes", "project.json"])
            repo.index.commit(
                "feat: Initialize project with Git LFS support",
                author=Actor(self.author_name, self.author_email)
            )
            
            return repo
            
        except (GitCommandError, subprocess.CalledProcessError) as e:
            raise Exception(f"Failed to initialize Git repository: {str(e)}")
    
    async def validate_project_structure(self, project_path: Path) -> Dict[str, bool]:
        """Validate project structure before Git operations"""
        required_files = ["project.json", ".gitignore", ".gitattributes"]
        required_dirs = ["assets", "sequences", "outputs", "exports"]
        
        validation = {
            "valid": True,
            "missing_files": [],
            "missing_dirs": []
        }
        
        for file in required_files:
            if not (project_path / file).exists():
                validation["missing_files"].append(file)
                validation["valid"] = False
        
        for dir_name in required_dirs:
            if not (project_path / dir_name).is_dir():
                validation["missing_dirs"].append(dir_name)
                validation["valid"] = False
        
        return validation
    
    async def commit_changes(self, project_path: Path, 
                           message: str, 
                           files: Optional[List[str]] = None,
                           validate_structure: bool = True) -> str:
        """Commit specific files or all changes with structure validation"""
        repo = Repo(project_path)
        
        # Validate structure if requested
        if validate_structure:
            validation = await self.validate_project_structure(project_path)
            if not validation["valid"]:
                raise ValueError(
                    f"Invalid project structure: "
                    f"Missing files: {validation['missing_files']}, "
                    f"Missing dirs: {validation['missing_dirs']}"
                )
        
        if repo.is_dirty() or repo.untracked_files:
            # Add files
            if files:
                repo.index.add(files)
            else:
                # Add all tracked files that changed
                repo.git.add(update=True)
            
            # Add any new LFS files
            lfs_status = subprocess.run(
                ["git", "lfs", "status", "--porcelain"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            if lfs_status.stdout:
                # Stage LFS files
                subprocess.run(
                    ["git", "add", ".gitattributes"],
                    cwd=project_path,
                    check=True
                )
            
            # Use semantic commit message prefix
            if not any(message.startswith(prefix) for prefix in 
                      ["feat:", "fix:", "docs:", "style:", "refactor:", 
                       "test:", "chore:", "perf:"]):
                # Auto-add prefix based on content
                if "project.json" in files if files else True:
                    message = f"chore: {message}"
            
            # Commit
            commit = repo.index.commit(
                message,
                author=Actor(self.author_name, self.author_email)
            )
            
            return commit.hexsha
        
        return None
    
    async def get_status(self, project_path: Path) -> dict:
        """Get current Git status including LFS information"""
        repo = Repo(project_path)
        
        # Get LFS status
        lfs_result = subprocess.run(
            ["git", "lfs", "status", "--porcelain"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        lfs_files = []
        if lfs_result.returncode == 0 and lfs_result.stdout:
            lfs_files = [
                line.split()[-1] 
                for line in lfs_result.stdout.strip().split('\n')
                if line
            ]
        
        return {
            "is_dirty": repo.is_dirty(),
            "untracked_files": repo.untracked_files,
            "modified_files": [item.a_path for item in repo.index.diff(None)],
            "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
            "lfs_files": lfs_files,
            "current_commit": repo.head.commit.hexsha[:8],
            "branch": repo.active_branch.name,
            "has_lfs": (project_path / ".gitattributes").exists()
        }
    
    async def get_history(self, project_path: Path, limit: int = 10) -> List[dict]:
        """Get commit history with file size information"""
        repo = Repo(project_path)
        commits = []
        
        for commit in repo.iter_commits(max_count=limit):
            # Get file sizes for this commit
            file_sizes = {}
            for item in commit.tree.traverse():
                if item.type == 'blob':
                    file_sizes[item.path] = item.size
            
            commits.append({
                "sha": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": commit.author.name,
                "timestamp": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files),
                "total_size": sum(file_sizes.values()),
                "has_lfs_files": any(
                    path.endswith(('.mp4', '.mov', '.wav', '.psd', '.blend'))
                    for path in file_sizes.keys()
                )
            })
        
        return commits
```

### API Endpoints
```python
# app/api/git.py
import subprocess
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import List, Optional
from app.services.git import GitService
from app.services.project import get_project_path

router = APIRouter(prefix="/projects/{project_id}/git")
git_service = GitService()

class CommitRequest(BaseModel):
    message: str
    files: Optional[List[str]] = None
    validate_structure: bool = True

@router.post("/validate")
async def validate_project_structure(project_id: str):
    """Validate project structure for Git operations"""
    project_path = get_project_path(project_id)
    
    try:
        validation = await git_service.validate_project_structure(project_path)
        return validation
    except Exception as e:
        raise HTTPException(500, f"Validation failed: {str(e)}")

@router.post("/commit")
async def commit_project(
    project_id: str,
    request: CommitRequest
):
    """Create a Git commit for the project with LFS support"""
    project_path = get_project_path(project_id)
    
    try:
        commit_sha = await git_service.commit_changes(
            project_path, 
            request.message, 
            request.files,
            request.validate_structure
        )
        
        if commit_sha:
            # Get updated status to show LFS files
            status = await git_service.get_status(project_path)
            
            return {
                "status": "success",
                "commit": commit_sha,
                "message": request.message,
                "lfs_files": status.get("lfs_files", [])
            }
        else:
            return {
                "status": "no_changes",
                "message": "No changes to commit"
            }
            
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Git operation failed: {str(e)}")

@router.get("/status")
async def get_git_status(project_id: str):
    """Get current Git status including LFS information"""
    project_path = get_project_path(project_id)
    
    try:
        status = await git_service.get_status(project_path)
        return status
    except Exception as e:
        raise HTTPException(500, f"Failed to get Git status: {str(e)}")

@router.get("/history")
async def get_commit_history(project_id: str, limit: int = 10):
    """Get commit history with file size information"""
    project_path = get_project_path(project_id)
    
    try:
        history = await git_service.get_history(project_path, limit)
        return {
            "commits": history,
            "has_lfs": (project_path / ".gitattributes").exists()
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get history: {str(e)}")

@router.get("/lfs/status")
async def get_lfs_status(project_id: str):
    """Get detailed LFS status for the project"""
    project_path = get_project_path(project_id)
    
    try:
        # Check LFS tracking status
        result = subprocess.run(
            ["git", "lfs", "ls-files"],
            cwd=project_path,
            capture_output=True,
            text=True
        )
        
        tracked_files = []
        if result.returncode == 0:
            tracked_files = [
                line.split()[-1] 
                for line in result.stdout.strip().split('\n')
                if line
            ]
        
        return {
            "lfs_enabled": (project_path / ".gitattributes").exists(),
            "tracked_files": tracked_files,
            "tracked_count": len(tracked_files)
        }
    except Exception as e:
        raise HTTPException(500, f"Failed to get LFS status: {str(e)}")
```

### Auto-commit Integration
```python
# app/services/project.py
async def update_project_manifest(self, project_id: str, data: dict):
    """Update project.json and auto-commit with semantic message"""
    project_path = self.get_project_path(project_id)
    manifest_path = project_path / "project.json"
    
    # Determine what changed for semantic commit message
    old_data = json.loads(manifest_path.read_text())
    changes = []
    
    if old_data.get("name") != data.get("name"):
        changes.append("project name")
    if old_data.get("settings") != data.get("settings"):
        changes.append("settings")
    if old_data.get("metadata") != data.get("metadata"):
        changes.append("metadata")
    
    # Update manifest
    manifest_path.write_text(json.dumps(data, indent=2))
    
    # Auto-commit with semantic message
    change_summary = ", ".join(changes) if changes else "project configuration"
    await self.git_service.commit_changes(
        project_path,
        f"chore: Update {change_summary}",
        ["project.json"]
    )

async def create_project(self, project_data: dict) -> str:
    """Create new project with Git LFS initialization"""
    project_id = generate_project_id()
    project_path = self.workspace_root / project_id
    
    # Create project structure
    await self._scaffold_project_structure(project_path, project_data)
    
    # Initialize Git with LFS
    await self.git_service.init_repository(project_path)
    
    return project_id
```

### Container Volume Considerations
```yaml
# docker-compose.yml additions for Git operations
services:
  backend:
    volumes:
      - ./workspace:/app/workspace
      - git-lfs-cache:/var/cache/git-lfs  # LFS object cache
    environment:
      - GIT_LFS_SKIP_SMUDGE=0  # Enable LFS file downloads
      - GIT_AUTHOR_NAME=Auteur Movie Director
      - GIT_AUTHOR_EMAIL=auteur@localhost
      - GIT_COMMITTER_NAME=Auteur Movie Director
      - GIT_COMMITTER_EMAIL=auteur@localhost

volumes:
  git-lfs-cache:
    driver: local
```

### Environment Setup Script
```python
# app/services/git.py addition
class GitService:
    def __init__(self):
        self.author_name = os.getenv("GIT_AUTHOR_NAME", "Auteur Movie Director")
        self.author_email = os.getenv("GIT_AUTHOR_EMAIL", "auteur@localhost")
        self._validate_lfs_installation()
        self._configure_git_environment()
    
    def _configure_git_environment(self):
        """Configure Git environment for container usage"""
        # Set Git config for container
        subprocess.run(
            ["git", "config", "--global", "user.name", self.author_name],
            check=True
        )
        subprocess.run(
            ["git", "config", "--global", "user.email", self.author_email],
            check=True
        )
        # Configure LFS
        subprocess.run(
            ["git", "config", "--global", "lfs.storage", "/var/cache/git-lfs"],
            check=True
        )
```

## Dependencies
- GitPython library (>= 3.1.0)
- Git LFS command-line tool (mandatory)
- subprocess module for LFS operations
- File system access with write permissions
- Project structure from STORY-002
- Environment variables for Git configuration

## Testing Criteria
- [ ] Git LFS validation fails gracefully if not installed
- [ ] Git initializes with LFS for new projects
- [ ] .gitattributes tracks all media file types correctly
- [ ] .gitignore correctly excludes generated/temporary files
- [ ] Structure validation catches missing files/directories
- [ ] Commits include proper semantic prefixes
- [ ] Status endpoint shows LFS file information
- [ ] History endpoint includes file size data
- [ ] Container volumes preserve Git/LFS data
- [ ] Git operations don't block API (async execution)
- [ ] Cross-platform compatibility (Windows, Mac, Linux)

## Definition of Done
- [ ] Git service implemented with LFS support
- [ ] Structure validation before Git operations
- [ ] All API endpoints return expected data with LFS info
- [ ] Comprehensive .gitattributes for media files
- [ ] .gitignore template excludes appropriate files
- [ ] Auto-commit uses semantic commit messages
- [ ] Container configuration supports Git/LFS operations
- [ ] Error handling covers Git and LFS failures
- [ ] Integration with project scaffolding process
- [ ] Unit tests cover all Git service methods
- [ ] Integration tests verify LFS functionality

## Story Links
- **Depends On**: STORY-002-project-structure-definition
- **Enhances**: STORY-004-file-management-api
- **Related PRD**: PRD-004-project-asset-management

## Implementation Status

✅ **Completed Features:**
- Git repository initialization with LFS support for new projects
- Comprehensive .gitattributes template for all media file types (video, audio, images, 3D files, ML models)
- GitPython integration for standard Git operations
- Subprocess execution for Git LFS commands
- Asynchronous Git operations handling
- Git LFS installation validation on service startup
- Semantic commit message prefixes
- Project structure validation before commits
- API endpoints for commit, status, history, and LFS operations
- Container volume considerations with Git environment configuration
- Auto-commit functionality for project.json changes
- Support for Windows, Mac, and Linux platforms

### Implementation Notes:
- Successfully integrated GitPython library for repository management
- Git LFS commands executed via subprocess for reliable LFS operations
- Comprehensive file type tracking patterns established in .gitattributes
- Environment variables properly configured for container usage
- Validation ensures project structure integrity before commits
- WebSocket integration ready for real-time Git status updates