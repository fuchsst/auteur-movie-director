# Story: Git Integration Service

**Story ID**: STORY-006  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 3 (Small)  
**Priority**: Medium  

## Story Description
As a creative professional, I need automatic Git version control for my projects so that I can track changes, revert to previous versions, and maintain a history of my creative decisions without manual version management.

## Acceptance Criteria

### Functional Requirements
- [ ] New projects automatically initialize as Git repositories
- [ ] Project creation commits initial structure
- [ ] API endpoint to commit current project state
- [ ] API endpoint to view Git status
- [ ] API endpoint to list commit history
- [ ] Appropriate .gitignore excludes generated content

### Technical Requirements
- [ ] Use GitPython for Git operations
- [ ] Handle Git operations asynchronously
- [ ] Provide meaningful commit messages
- [ ] Include author information in commits
- [ ] Handle Git errors gracefully
- [ ] Support Windows, Mac, and Linux

### Git Operations
- Initialize repository on project creation
- Auto-commit project.json changes
- Manual commit endpoint for checkpoints
- Status endpoint showing changed files
- History endpoint with recent commits

## Implementation Notes

### Git Service Implementation
```python
# app/services/git.py
from git import Repo, GitCommandError
from pathlib import Path
from typing import List, Optional
from datetime import datetime

class GitService:
    def __init__(self):
        self.author_name = "Generative Media Studio"
        self.author_email = "studio@localhost"
    
    async def init_repository(self, project_path: Path) -> Repo:
        """Initialize Git repository for new project"""
        try:
            repo = Repo.init(project_path)
            
            # Create .gitignore
            gitignore_content = """
# Generated content (recreatable)
/generated/

# Temporary files
*.tmp
*.cache
.DS_Store
Thumbs.db

# Large binary exports
/exports/renders/*.mp4
/exports/renders/*.mov

# But keep directory structure
!.gitkeep
            """.strip()
            
            gitignore_path = project_path / ".gitignore"
            gitignore_path.write_text(gitignore_content)
            
            # Initial commit
            repo.index.add([".gitignore", "project.json"])
            repo.index.commit(
                "Initial project structure",
                author=Actor(self.author_name, self.author_email)
            )
            
            return repo
            
        except GitCommandError as e:
            raise Exception(f"Failed to initialize Git: {str(e)}")
    
    async def commit_changes(self, project_path: Path, 
                           message: str, 
                           files: Optional[List[str]] = None) -> str:
        """Commit specific files or all changes"""
        repo = Repo(project_path)
        
        if repo.is_dirty() or repo.untracked_files:
            # Add files
            if files:
                repo.index.add(files)
            else:
                # Add all tracked files that changed
                repo.git.add(update=True)
            
            # Commit
            commit = repo.index.commit(
                message,
                author=Actor(self.author_name, self.author_email)
            )
            
            return commit.hexsha
        
        return None
    
    async def get_status(self, project_path: Path) -> dict:
        """Get current Git status"""
        repo = Repo(project_path)
        
        return {
            "is_dirty": repo.is_dirty(),
            "untracked_files": repo.untracked_files,
            "modified_files": [item.a_path for item in repo.index.diff(None)],
            "staged_files": [item.a_path for item in repo.index.diff("HEAD")],
            "current_commit": repo.head.commit.hexsha[:8],
            "branch": repo.active_branch.name
        }
    
    async def get_history(self, project_path: Path, limit: int = 10) -> List[dict]:
        """Get commit history"""
        repo = Repo(project_path)
        commits = []
        
        for commit in repo.iter_commits(max_count=limit):
            commits.append({
                "sha": commit.hexsha[:8],
                "message": commit.message.strip(),
                "author": commit.author.name,
                "timestamp": commit.committed_datetime.isoformat(),
                "files_changed": len(commit.stats.files)
            })
        
        return commits
```

### API Endpoints
```python
# app/api/git.py
from fastapi import APIRouter, HTTPException
from app.services.git import GitService

router = APIRouter(prefix="/projects/{project_id}/git")
git_service = GitService()

@router.post("/commit")
async def commit_project(
    project_id: str,
    message: str,
    files: Optional[List[str]] = None
):
    """Create a Git commit for the project"""
    project_path = get_project_path(project_id)
    
    try:
        commit_sha = await git_service.commit_changes(
            project_path, message, files
        )
        
        if commit_sha:
            return {
                "status": "success",
                "commit": commit_sha,
                "message": message
            }
        else:
            return {
                "status": "no_changes",
                "message": "No changes to commit"
            }
            
    except Exception as e:
        raise HTTPException(500, f"Git operation failed: {str(e)}")

@router.get("/status")
async def get_git_status(project_id: str):
    """Get current Git status for the project"""
    project_path = get_project_path(project_id)
    
    try:
        status = await git_service.get_status(project_path)
        return status
    except Exception as e:
        raise HTTPException(500, f"Failed to get Git status: {str(e)}")

@router.get("/history")
async def get_commit_history(project_id: str, limit: int = 10):
    """Get commit history for the project"""
    project_path = get_project_path(project_id)
    
    try:
        history = await git_service.get_history(project_path, limit)
        return {"commits": history}
    except Exception as e:
        raise HTTPException(500, f"Failed to get history: {str(e)}")
```

### Auto-commit Integration
```python
# app/services/project.py
async def update_project_manifest(self, project_id: str, data: dict):
    """Update project.json and auto-commit"""
    project_path = self.get_project_path(project_id)
    manifest_path = project_path / "project.json"
    
    # Update manifest
    manifest_path.write_text(json.dumps(data, indent=2))
    
    # Auto-commit the change
    await self.git_service.commit_changes(
        project_path,
        f"Update project settings: {data.get('name', 'unnamed')}",
        ["project.json"]
    )
```

## Dependencies
- GitPython library
- File system access
- Project structure from STORY-002

## Testing Criteria
- [ ] Git initializes for new projects
- [ ] .gitignore correctly excludes files
- [ ] Commits include proper metadata
- [ ] Status endpoint reflects actual state
- [ ] History shows commits correctly
- [ ] Git operations don't block API

## Definition of Done
- [ ] Git service implemented with all methods
- [ ] API endpoints return expected data
- [ ] .gitignore template is comprehensive
- [ ] Auto-commit works for project.json changes
- [ ] Error handling covers Git failures
- [ ] Cross-platform compatibility verified

## Story Links
- **Depends On**: STORY-002-project-structure-definition
- **Enhances**: STORY-004-file-management-api
- **Related PRD**: PRD-004-project-asset-management