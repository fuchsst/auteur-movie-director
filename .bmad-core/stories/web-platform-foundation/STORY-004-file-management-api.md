# Story: File Management API

**Story ID**: STORY-004  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need REST API endpoints for managing projects and files so that users can create projects, upload assets, and organize their creative content through the web interface.

## Acceptance Criteria

### Functional Requirements
- [ ] Create new projects with validation
- [ ] List all projects in workspace
- [ ] Get individual project details
- [ ] Delete projects (with confirmation)
- [ ] Upload files to project asset folders
- [ ] Download files from projects
- [ ] List files in project directories
- [ ] Handle file size limits appropriately

### Technical Requirements
- [ ] Implement async file I/O operations
- [ ] Validate file types and sizes
- [ ] Use proper HTTP status codes
- [ ] Return consistent JSON responses
- [ ] Handle cross-platform paths correctly
- [ ] Implement request validation with Pydantic

### API Endpoints
```
GET    /api/v1/workspace/config      # Get workspace configuration
GET    /api/v1/projects              # List all projects
POST   /api/v1/projects              # Create new project
GET    /api/v1/projects/{id}         # Get project details
PUT    /api/v1/projects/{id}         # Update project metadata
DELETE /api/v1/projects/{id}         # Delete project

POST   /api/v1/projects/{id}/assets  # Upload asset files
GET    /api/v1/projects/{id}/assets  # List project assets
GET    /api/v1/projects/{id}/assets/{path}  # Download specific file
DELETE /api/v1/projects/{id}/assets/{path}  # Delete specific file
```

## Implementation Notes

### Request/Response Models
```python
# app/schemas/project.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quality: Literal["draft", "standard", "premium"] = "standard"
    fps: int = Field(24, ge=1, le=120)
    resolution: tuple[int, int] = (1920, 1080)

class ProjectResponse(BaseModel):
    id: str
    name: str
    created: datetime
    modified: datetime
    quality: str
    size_bytes: int
    file_count: int
    git_status: Optional[str]

class FileUploadResponse(BaseModel):
    filename: str
    size: int
    path: str
    asset_type: str
    uploaded_at: datetime

class WorkspaceConfig(BaseModel):
    root_path: str
    total_size: int
    project_count: int
    available_space: int
```

### File Upload Handling
```python
# app/api/projects.py
from fastapi import UploadFile, File, HTTPException
from typing import List

ALLOWED_EXTENSIONS = {
    "scripts": [".fdx", ".txt", ".md"],
    "characters": [".json", ".yaml"],
    "styles": [".jpg", ".png", ".webp"],
    "environments": [".hdr", ".exr", ".jpg"],
    "audio": [".wav", ".mp3", ".ogg"]
}

MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB

@router.post("/{project_id}/assets")
async def upload_assets(
    project_id: str,
    asset_type: str,
    files: List[UploadFile] = File(...)
):
    # Validate asset type
    if asset_type not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Invalid asset type")
    
    # Check file extensions and sizes
    for file in files:
        validate_file(file, asset_type)
    
    # Save files to appropriate directory
    results = await save_files(project_id, asset_type, files)
    return {"files": results}
```

### Service Layer
```python
# app/services/project.py
class ProjectService:
    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root
    
    async def create_project(self, data: ProjectCreate) -> Project:
        """Create new project with directory structure"""
        
    async def list_projects(self) -> List[ProjectSummary]:
        """List all projects with metadata"""
        
    async def get_project(self, project_id: str) -> ProjectDetail:
        """Get detailed project information"""
        
    async def delete_project(self, project_id: str) -> None:
        """Delete project and all contents"""
        
    async def save_file(self, project_id: str, file: UploadFile, 
                       asset_type: str) -> FileInfo:
        """Save uploaded file to project"""
```

### Error Handling
```python
# app/core/exceptions.py
class ProjectNotFoundError(Exception):
    pass

class InvalidFileTypeError(Exception):
    pass

class StorageQuotaExceededError(Exception):
    pass

# app/api/errors.py
@app.exception_handler(ProjectNotFoundError)
async def project_not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": {
                "code": "PROJECT_NOT_FOUND",
                "message": str(exc)
            }
        }
    )
```

## Dependencies
- Workspace service from STORY-002
- FastAPI app from STORY-003
- File system access and permissions
- Python-multipart for file uploads

## Testing Criteria
- [ ] Project CRUD operations work correctly
- [ ] File uploads validate size and type
- [ ] Large files are handled efficiently
- [ ] Concurrent uploads don't interfere
- [ ] Path traversal attacks are prevented
- [ ] Deleted projects clean up completely

## Definition of Done
- [ ] All endpoints implemented and documented
- [ ] Request/response models validated
- [ ] File operations use async I/O
- [ ] Error cases return appropriate responses
- [ ] Unit tests cover happy and error paths
- [ ] API documentation updated in OpenAPI

## Story Links
- **Depends On**: STORY-002-project-structure-definition, STORY-003-fastapi-application-bootstrap
- **Blocks**: STORY-008-project-gallery-view
- **Related PRD**: PRD-004-project-asset-management