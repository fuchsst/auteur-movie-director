# Story: Git LFS Integration

**Story ID**: STORY-017  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 3 (Medium)  
**Priority**: Medium  
**Status**: 🔲 Not Started

## Story Description
As a user working with large media files, I need Git Large File Storage (LFS) automatically configured for my projects so that I can efficiently version control images, videos, and AI models without bloating the repository, while maintaining smooth Git operations.

## Acceptance Criteria

### Functional Requirements
- [ ] Auto-initialize Git LFS when creating new projects
- [ ] Create comprehensive .gitattributes with media patterns
- [ ] Validate Git LFS installation on startup
- [ ] Track files automatically based on size threshold
- [ ] Show LFS status in file browser
- [ ] Handle LFS pointer files correctly
- [ ] Support LFS for all media types
- [ ] Provide LFS setup instructions if missing
- [ ] Track LFS bandwidth usage
- [ ] Support batch LFS operations

### Technical Requirements
- [ ] Git LFS validation service
- [ ] .gitattributes template management
- [ ] File size checking before commits
- [ ] LFS tracking API endpoints
- [ ] WebSocket notifications for LFS operations
- [ ] Error handling for LFS failures
- [ ] Support for custom LFS servers

### UI/UX Requirements
- [ ] Visual indicators for LFS-tracked files
- [ ] File size warnings before tracking
- [ ] LFS status in project properties
- [ ] Progress bars for LFS operations
- [ ] Clear error messages for LFS issues

## Implementation Notes

### Git LFS Service Enhancement
```python
# backend/app/services/git_lfs.py
import subprocess
import os
from pathlib import Path
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class GitLFSService:
    """Service for managing Git LFS operations"""
    
    # File patterns for LFS tracking
    LFS_PATTERNS = [
        # Images
        "*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.tiff", "*.tif",
        "*.webp", "*.ico", "*.svg", "*.psd", "*.ai", "*.eps",
        # Videos
        "*.mp4", "*.avi", "*.mov", "*.wmv", "*.flv", "*.webm", "*.mkv",
        "*.m4v", "*.mpg", "*.mpeg", "*.3gp", "*.3g2",
        # Audio
        "*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.wma", "*.m4a",
        "*.opus", "*.aiff", "*.alac",
        # 3D Models
        "*.obj", "*.fbx", "*.dae", "*.3ds", "*.blend", "*.stl", "*.ply",
        # AI Models
        "*.ckpt", "*.safetensors", "*.pt", "*.pth", "*.pkl", "*.h5",
        "*.onnx", "*.pb", "*.tflite", "*.bin", "*.model",
        # Archives
        "*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2", "*.xz",
        # Other large files
        "*.pdf", "*.exe", "*.dmg", "*.iso", "*.deb", "*.rpm"
    ]
    
    # Size threshold for automatic LFS tracking (50MB)
    SIZE_THRESHOLD = 50 * 1024 * 1024
    
    def __init__(self):
        self.lfs_available = self.check_lfs_installed()
    
    def check_lfs_installed(self) -> bool:
        """Check if Git LFS is installed and available"""
        try:
            result = subprocess.run(
                ["git", "lfs", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Git LFS version: {result.stdout.strip()}")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("Git LFS is not installed or not in PATH")
            return False
    
    def initialize_lfs(self, project_path: Path) -> bool:
        """Initialize Git LFS in a project"""
        if not self.lfs_available:
            raise RuntimeError("Git LFS is not installed")
        
        try:
            # Initialize LFS
            subprocess.run(
                ["git", "lfs", "install"],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            # Create .gitattributes
            self.create_gitattributes(project_path)
            
            logger.info(f"Git LFS initialized for project: {project_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to initialize Git LFS: {e.stderr}")
            raise
    
    def create_gitattributes(self, project_path: Path) -> None:
        """Create .gitattributes file with LFS patterns"""
        gitattributes_path = project_path / ".gitattributes"
        
        content = ["# Git LFS patterns for Auteur Movie Director\n"]
        content.append("# Auto-generated - do not edit manually\n\n")
        
        # Group patterns by category
        categories = {
            "Images": ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.tiff", 
                      "*.tif", "*.webp", "*.psd", "*.ai", "*.eps"],
            "Videos": ["*.mp4", "*.avi", "*.mov", "*.wmv", "*.flv", "*.webm", 
                      "*.mkv", "*.m4v", "*.mpg", "*.mpeg"],
            "Audio": ["*.mp3", "*.wav", "*.flac", "*.aac", "*.ogg", "*.wma", 
                     "*.m4a", "*.opus"],
            "3D Models": ["*.obj", "*.fbx", "*.dae", "*.3ds", "*.blend", "*.stl"],
            "AI Models": ["*.ckpt", "*.safetensors", "*.pt", "*.pth", "*.pkl", 
                         "*.h5", "*.onnx", "*.pb", "*.tflite", "*.bin"],
            "Archives": ["*.zip", "*.rar", "*.7z", "*.tar", "*.gz", "*.bz2"],
            "Large Files": ["*.pdf", "*.exe", "*.dmg", "*.iso"]
        }
        
        for category, patterns in categories.items():
            content.append(f"# {category}\n")
            for pattern in patterns:
                content.append(f"{pattern} filter=lfs diff=lfs merge=lfs -text\n")
            content.append("\n")
        
        # Write file
        with open(gitattributes_path, 'w') as f:
            f.writelines(content)
        
        # Stage the .gitattributes file
        subprocess.run(
            ["git", "add", ".gitattributes"],
            cwd=project_path,
            check=True
        )
    
    def track_file(self, project_path: Path, file_path: str) -> bool:
        """Track a specific file with Git LFS"""
        if not self.lfs_available:
            raise RuntimeError("Git LFS is not installed")
        
        try:
            subprocess.run(
                ["git", "lfs", "track", file_path],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            # Stage the updated .gitattributes
            subprocess.run(
                ["git", "add", ".gitattributes"],
                cwd=project_path,
                check=True
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to track file with LFS: {e.stderr}")
            return False
    
    def untrack_file(self, project_path: Path, pattern: str) -> bool:
        """Untrack a pattern from Git LFS"""
        if not self.lfs_available:
            raise RuntimeError("Git LFS is not installed")
        
        try:
            subprocess.run(
                ["git", "lfs", "untrack", pattern],
                cwd=project_path,
                check=True,
                capture_output=True
            )
            
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to untrack pattern from LFS: {e.stderr}")
            return False
    
    def get_lfs_files(self, project_path: Path) -> List[Dict[str, any]]:
        """Get list of files tracked by Git LFS"""
        if not self.lfs_available:
            return []
        
        try:
            result = subprocess.run(
                ["git", "lfs", "ls-files", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                check=True
            )
            
            files = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    # Parse: oid size path
                    parts = line.split(None, 2)
                    if len(parts) >= 3:
                        files.append({
                            'oid': parts[0],
                            'size': int(parts[1]),
                            'path': parts[2]
                        })
            
            return files
            
        except subprocess.CalledProcessError:
            return []
    
    def check_file_size(self, file_path: Path) -> bool:
        """Check if file should be tracked by LFS based on size"""
        try:
            size = file_path.stat().st_size
            return size > self.SIZE_THRESHOLD
        except OSError:
            return False
    
    def get_lfs_status(self, project_path: Path) -> Dict[str, any]:
        """Get comprehensive LFS status for a project"""
        if not self.lfs_available:
            return {
                'enabled': False,
                'installed': False,
                'error': 'Git LFS is not installed'
            }
        
        try:
            # Check if LFS is initialized
            result = subprocess.run(
                ["git", "config", "--get", "filter.lfs.clean"],
                cwd=project_path,
                capture_output=True,
                text=True
            )
            
            lfs_initialized = result.returncode == 0
            
            # Get tracked patterns
            patterns = []
            gitattributes = project_path / ".gitattributes"
            if gitattributes.exists():
                with open(gitattributes, 'r') as f:
                    for line in f:
                        if 'filter=lfs' in line:
                            pattern = line.split()[0]
                            patterns.append(pattern)
            
            # Get LFS files
            lfs_files = self.get_lfs_files(project_path)
            
            return {
                'enabled': True,
                'installed': True,
                'initialized': lfs_initialized,
                'tracked_patterns': patterns,
                'tracked_files': lfs_files,
                'file_count': len(lfs_files),
                'total_size': sum(f['size'] for f in lfs_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to get LFS status: {e}")
            return {
                'enabled': True,
                'installed': True,
                'initialized': False,
                'error': str(e)
            }
    
    def validate_lfs_setup(self) -> Dict[str, any]:
        """Validate system-wide LFS setup"""
        validation = {
            'git_installed': False,
            'lfs_installed': False,
            'lfs_version': None,
            'git_version': None,
            'issues': []
        }
        
        # Check Git
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            validation['git_installed'] = True
            validation['git_version'] = result.stdout.strip()
        except (subprocess.CalledProcessError, FileNotFoundError):
            validation['issues'].append("Git is not installed")
        
        # Check Git LFS
        if validation['git_installed']:
            try:
                result = subprocess.run(
                    ["git", "lfs", "version"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                validation['lfs_installed'] = True
                validation['lfs_version'] = result.stdout.strip()
            except (subprocess.CalledProcessError, FileNotFoundError):
                validation['issues'].append("Git LFS is not installed")
        
        return validation

# Global instance
git_lfs_service = GitLFSService()
```

### API Endpoints
```python
# backend/app/api/v1/git_lfs.py
from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
from typing import List, Dict

from app.services.git_lfs import git_lfs_service
from app.services.workspace import get_workspace_service
from app.schemas.git import LFSStatus, LFSTrackRequest

router = APIRouter(prefix="/git/lfs", tags=["git-lfs"])

@router.get("/validate")
async def validate_lfs_setup():
    """Validate Git LFS installation"""
    validation = git_lfs_service.validate_lfs_setup()
    
    if not validation['lfs_installed']:
        raise HTTPException(
            status_code=424,
            detail="Git LFS is not installed. Please install Git LFS to use this feature."
        )
    
    return validation

@router.post("/projects/{project_id}/initialize")
async def initialize_project_lfs(project_id: str):
    """Initialize Git LFS for a project"""
    workspace_service = get_workspace_service()
    project_path = workspace_service.get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        git_lfs_service.initialize_lfs(project_path)
        return {"message": "Git LFS initialized successfully"}
    except RuntimeError as e:
        raise HTTPException(status_code=424, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize LFS: {str(e)}")

@router.get("/projects/{project_id}/status")
async def get_project_lfs_status(project_id: str) -> LFSStatus:
    """Get LFS status for a project"""
    workspace_service = get_workspace_service()
    project_path = workspace_service.get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    return git_lfs_service.get_lfs_status(project_path)

@router.post("/projects/{project_id}/track")
async def track_file_pattern(project_id: str, request: LFSTrackRequest):
    """Track a file pattern with Git LFS"""
    workspace_service = get_workspace_service()
    project_path = workspace_service.get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        success = git_lfs_service.track_file(project_path, request.pattern)
        if success:
            return {"message": f"Pattern '{request.pattern}' is now tracked by Git LFS"}
        else:
            raise HTTPException(status_code=400, detail="Failed to track pattern")
    except RuntimeError as e:
        raise HTTPException(status_code=424, detail=str(e))

@router.post("/projects/{project_id}/untrack")
async def untrack_file_pattern(project_id: str, request: LFSTrackRequest):
    """Untrack a file pattern from Git LFS"""
    workspace_service = get_workspace_service()
    project_path = workspace_service.get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        success = git_lfs_service.untrack_file(project_path, request.pattern)
        if success:
            return {"message": f"Pattern '{request.pattern}' is no longer tracked by Git LFS"}
        else:
            raise HTTPException(status_code=400, detail="Failed to untrack pattern")
    except RuntimeError as e:
        raise HTTPException(status_code=424, detail=str(e))

@router.get("/projects/{project_id}/files")
async def get_lfs_tracked_files(project_id: str) -> List[Dict]:
    """Get list of files tracked by Git LFS in a project"""
    workspace_service = get_workspace_service()
    project_path = workspace_service.get_project_path(project_id)
    
    if not project_path.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    
    return git_lfs_service.get_lfs_files(project_path)
```

### Frontend Integration
```typescript
// src/lib/api/git.ts - Add LFS methods
export const gitLFSApi = {
  async validateSetup(): Promise<LFSValidation> {
    return api.get<LFSValidation>('/git/lfs/validate');
  },
  
  async initializeProject(projectId: string): Promise<void> {
    await api.post(`/git/lfs/projects/${projectId}/initialize`);
  },
  
  async getStatus(projectId: string): Promise<LFSStatus> {
    return api.get<LFSStatus>(`/git/lfs/projects/${projectId}/status`);
  },
  
  async trackPattern(projectId: string, pattern: string): Promise<void> {
    await api.post(`/git/lfs/projects/${projectId}/track`, { pattern });
  },
  
  async untrackPattern(projectId: string, pattern: string): Promise<void> {
    await api.post(`/git/lfs/projects/${projectId}/untrack`, { pattern });
  },
  
  async getTrackedFiles(projectId: string): Promise<LFSFile[]> {
    return api.get<LFSFile[]>(`/git/lfs/projects/${projectId}/files`);
  }
};
```

### Visual Indicators in File Browser
```svelte
<!-- Update AssetBrowser to show LFS status -->
<script lang="ts">
  import { gitLFSApi } from '$lib/api/git';
  
  let lfsFiles: Set<string> = new Set();
  
  onMount(async () => {
    const tracked = await gitLFSApi.getTrackedFiles(projectId);
    lfsFiles = new Set(tracked.map(f => f.path));
  });
  
  function isLFSTracked(filePath: string): boolean {
    return lfsFiles.has(filePath);
  }
  
  function formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unit = 0;
    while (size > 1024 && unit < units.length - 1) {
      size /= 1024;
      unit++;
    }
    return `${size.toFixed(1)} ${units[unit]}`;
  }
</script>

<!-- In file list -->
{#each files as file}
  <div class="file-item">
    <span class="file-name">{file.name}</span>
    <span class="file-size">{formatFileSize(file.size)}</span>
    {#if isLFSTracked(file.path)}
      <span class="lfs-badge" title="Tracked by Git LFS">LFS</span>
    {:else if file.size > 50 * 1024 * 1024}
      <span class="lfs-warning" title="Large file - consider using LFS">!</span>
    {/if}
  </div>
{/each}

<style>
  .lfs-badge {
    background: var(--color-primary);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: bold;
  }
  
  .lfs-warning {
    color: var(--color-warning);
    font-weight: bold;
  }
</style>
```

### Setup Instructions Component
```svelte
<!-- src/lib/components/help/LFSSetup.svelte -->
<script lang="ts">
  export let onClose: () => void;
</script>

<div class="lfs-setup">
  <h2>Git LFS Setup Required</h2>
  
  <p>Git Large File Storage (LFS) is required for managing media files efficiently.</p>
  
  <div class="setup-steps">
    <h3>Installation Steps:</h3>
    
    <div class="platform-tabs">
      <button class="tab">Windows</button>
      <button class="tab">macOS</button>
      <button class="tab">Linux</button>
    </div>
    
    <div class="instructions">
      <!-- Windows -->
      <div class="platform-content">
        <ol>
          <li>Download Git LFS from <a href="https://git-lfs.github.com/">git-lfs.github.com</a></li>
          <li>Run the installer</li>
          <li>Open a terminal and run: <code>git lfs install</code></li>
          <li>Restart the application</li>
        </ol>
      </div>
      
      <!-- macOS -->
      <div class="platform-content">
        <ol>
          <li>Install via Homebrew: <code>brew install git-lfs</code></li>
          <li>Run: <code>git lfs install</code></li>
          <li>Restart the application</li>
        </ol>
      </div>
      
      <!-- Linux -->
      <div class="platform-content">
        <ol>
          <li>Install via package manager:
            <ul>
              <li>Ubuntu/Debian: <code>sudo apt install git-lfs</code></li>
              <li>Fedora: <code>sudo dnf install git-lfs</code></li>
            </ul>
          </li>
          <li>Run: <code>git lfs install</code></li>
          <li>Restart the application</li>
        </ol>
      </div>
    </div>
  </div>
  
  <div class="actions">
    <button on:click={onClose}>Close</button>
    <button on:click={() => window.location.reload()}>Retry</button>
  </div>
</div>
```

## Dependencies
- Git integration (STORY-006)
- File management API (STORY-004)
- Project structure (STORY-002)

## Testing Criteria
- [ ] Git LFS initializes on project creation
- [ ] .gitattributes includes all media patterns
- [ ] Large files are automatically tracked
- [ ] LFS status displays correctly
- [ ] Validation catches missing LFS
- [ ] Setup instructions are clear
- [ ] File browser shows LFS indicators
- [ ] Untrack functionality works

## Definition of Done
- [ ] Git LFS service implemented
- [ ] API endpoints functional
- [ ] Frontend integration complete
- [ ] Visual indicators working
- [ ] Setup documentation provided
- [ ] Error handling robust
- [ ] Performance optimized
- [ ] Tests written and passing

## Story Links
- **Depends On**: STORY-006 (Git Integration Service)
- **Blocks**: None
- **Related PRD**: PRD-001-web-platform-foundation