# Story: File Management API

**Story ID**: STORY-004  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Backend  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a frontend developer, I need REST API endpoints for managing projects and files so that users can create projects, upload assets, and organize their creative content through the web interface while enforcing the programmatically defined project structure.

## Acceptance Criteria

### Functional Requirements
- [ ] Create new projects with validation against the numbered directory structure
- [ ] Enforce workspace/project hierarchy (workspace → projects → numbered directories)
- [ ] List all projects in workspace with Git status integration
- [ ] Get individual project details including directory structure validation
- [ ] Delete projects (with confirmation and Git cleanup)
- [ ] Upload files to project asset folders with type-based routing
- [ ] Download files from projects with path validation
- [ ] List files in project directories following the numbered structure
- [ ] Handle file size limits appropriately (with Git LFS consideration)
- [ ] Validate all operations against the directory contract
- [ ] Generate deterministic output paths for node Takes (scene/shot/take structure)
- [ ] Support relative path resolution for Function Runner volumes
- [ ] Store and retrieve node output metadata in project state

### Technical Requirements
- [ ] Implement async file I/O operations for performance
- [ ] Validate file types and sizes before processing
- [ ] Enforce numbered directory structure (01_Assets, 02_Scripts, etc.)
- [ ] Use proper HTTP status codes for structure violations
- [ ] Return consistent JSON responses with structure metadata
- [ ] Handle cross-platform paths correctly (workspace volume mounts)
- [ ] Implement request validation with Pydantic
- [ ] Integrate Git operations for file tracking and status
- [ ] Support Git LFS for large media files
- [ ] Validate operations against programmatic structure enforcement

### API Endpoints
```
GET    /api/v1/workspace/config      # Get workspace configuration with structure
GET    /api/v1/workspace/validate    # Validate workspace structure integrity
GET    /api/v1/projects              # List all projects with Git status
POST   /api/v1/projects              # Create new project with structure
GET    /api/v1/projects/{id}         # Get project details and structure
PUT    /api/v1/projects/{id}         # Update project metadata
DELETE /api/v1/projects/{id}         # Delete project with Git cleanup
GET    /api/v1/projects/{id}/structure  # Validate project directory structure

POST   /api/v1/projects/{id}/assets  # Upload with type-based routing
GET    /api/v1/projects/{id}/assets  # List assets by directory type
GET    /api/v1/projects/{id}/assets/{path}  # Download with path validation
DELETE /api/v1/projects/{id}/assets/{path}  # Delete with Git tracking

# Takes Management Endpoints
POST   /api/v1/projects/{id}/takes/register  # Register node output as Take
GET    /api/v1/projects/{id}/takes/{scene}/{shot}  # List Takes for scene/shot
GET    /api/v1/projects/{id}/takes/path     # Generate next Take path
POST   /api/v1/projects/{id}/nodes/{node_id}/state  # Store node state/data
GET    /api/v1/projects/{id}/nodes/{node_id}/state  # Retrieve node state

GET    /api/v1/projects/{id}/git/status     # Get Git status for project
POST   /api/v1/projects/{id}/git/track      # Track file in Git/LFS

# Character Asset Management Endpoints
POST   /api/v1/projects/{id}/characters     # Create new character asset
GET    /api/v1/projects/{id}/characters     # List all character assets
GET    /api/v1/projects/{id}/characters/{char_id}  # Get character details
PUT    /api/v1/projects/{id}/characters/{char_id}  # Update character metadata
POST   /api/v1/projects/{id}/characters/{char_id}/base-face  # Upload base face image
POST   /api/v1/projects/{id}/characters/{char_id}/lora       # Upload LoRA model
POST   /api/v1/projects/{id}/characters/{char_id}/variations # Upload variations
GET    /api/v1/projects/{id}/characters/{char_id}/usage     # Find character usage
```

## Implementation Notes

### Request/Response Models
```python
# app/schemas/project.py
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class AssetType(str, Enum):
    # Aligned with generative pipeline asset types
    CHARACTERS = "Characters"      # Character definitions & LoRAs
    STYLES = "Styles"             # Visual style references
    LOCATIONS = "Locations"       # Environment assets
    MUSIC = "Music"               # Musical tracks and themes
    
class CreativeDocType(str, Enum):
    # Creative documents that guide the pipeline
    TREATMENTS = "Treatments"     # Story treatments
    SCRIPTS = "Scripts"           # Screenplays & emotional beat sheets
    SHOT_LISTS = "Shot_Lists"     # Generative shot lists
    CANVAS = "Canvas"             # Node graph saves

class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    quality: Literal["low", "standard", "high"] = "standard"
    narrative_structure: Literal["three-act", "hero-journey", "beat-sheet", "story-circle"] = "three-act"
    fps: int = Field(24, ge=1, le=120)
    resolution: tuple[int, int] = (1920, 1080)
    init_git: bool = True
    use_lfs: bool = True
    
    @validator('name')
    def validate_project_name(cls, v):
        # Ensure no path traversal or invalid characters
        if any(c in v for c in ['/', '\\', '..', '\0']):
            raise ValueError('Invalid project name')
        return v

class ProjectStructure(BaseModel):
    directories: Dict[DirectoryType, bool]  # Which dirs exist
    is_valid: bool
    missing_dirs: List[DirectoryType]
    extra_dirs: List[str]

class ProjectResponse(BaseModel):
    id: str
    name: str
    created: datetime
    modified: datetime
    quality: str
    size_bytes: int
    file_count: int
    git_status: Optional[str]
    structure: ProjectStructure
    workspace_path: str

class FileUploadResponse(BaseModel):
    filename: str
    size: int
    path: str
    asset_type: DirectoryType
    uploaded_at: datetime
    git_tracked: bool
    use_lfs: bool

# Takes System Models (aligned with filmmaking hierarchy)
class TakeMetadata(BaseModel):
    take_number: int
    chapter: str  # Chapter in narrative structure
    scene: str    # Scene identifier
    shot: str     # Shot identifier
    node_id: str
    node_type: str
    parameters: Dict[str, Any]  # Node parameters for reproducibility
    # Composite prompt data for reproducibility
    text_prompt: str
    character_refs: List[str] = []  # Character asset IDs used
    style_refs: List[str] = []      # Style asset IDs used
    location_ref: Optional[str] = None  # Location asset ID
    created_at: datetime
    relative_path: str  # Path relative to project root
    absolute_path: str  # Full path for Function Runner
    
class TakePathRequest(BaseModel):
    scene: str = Field(..., pattern=r'^S\d{3}$')  # S001 format
    shot: str = Field(..., pattern=r'^P\d{3}$')   # P001 format
    node_type: str  # text-to-image, video-to-video, etc.
    extension: str = ".png"  # File extension
    
class TakePathResponse(BaseModel):
    take_number: int
    relative_path: str  # e.g., "03_Renders/S001/P001/S001_P001_T001.png"
    absolute_path: str  # Full path for container access
    volume_path: str    # Path for Function Runner shared volume
    
class NodeStateData(BaseModel):
    node_id: str
    node_type: str
    position: Dict[str, float]  # x, y coordinates
    data: Dict[str, Any]  # Node-specific data
    outputs: List[TakeMetadata]  # Generated Takes
    connections: List[str]  # Connected node IDs

class WorkspaceConfig(BaseModel):
    root_path: str
    total_size: int
    project_count: int
    available_space: int
    volume_mounted: bool
    git_available: bool
    lfs_available: bool
    structure_version: str = "1.0"

# Character Asset Models
class CharacterCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=10)
    triggerWord: Optional[str] = None  # Auto-generated if not provided
    
class CharacterUpdate(BaseModel):
    description: Optional[str] = None
    triggerWord: Optional[str] = None
    
class CharacterVariationType(str, Enum):
    EXPRESSION_NEUTRAL = "expression_neutral"
    EXPRESSION_HAPPY = "expression_happy"
    EXPRESSION_ANGRY = "expression_angry"
    EXPRESSION_SURPRISED = "expression_surprised"
    EXPRESSION_SAD = "expression_sad"
    ANGLE_LEFT = "angle_left"
    ANGLE_RIGHT = "angle_right"
    ANGLE_PROFILE_LEFT = "angle_profile_left"
    ANGLE_PROFILE_RIGHT = "angle_profile_right"
    POSE_BUST = "pose_bust"
    POSE_UPPER_BODY = "pose_upper_body"
    POSE_FULL_STANDING = "pose_full_standing"
    POSE_WALKING = "pose_walking"
    POSE_SITTING = "pose_sitting"
    
class CharacterResponse(BaseModel):
    assetId: str
    assetType: Literal["Character"] = "Character"
    name: str
    description: str
    triggerWord: str
    baseFaceImagePath: Optional[str] = None
    loraModelPath: Optional[str] = None
    loraTrainingStatus: Literal["untrained", "training", "completed", "failed"]
    variations: Dict[str, str] = {}
    usage: List[str] = []
    created: datetime
    modified: datetime
```

### File Upload Handling
```python
# app/api/projects.py
from fastapi import UploadFile, File, HTTPException
from typing import List
import aiofiles
from pathlib import Path

# Asset type file mapping (aligned with generative pipeline)
ASSET_EXTENSIONS = {
    AssetType.CHARACTERS: [".json", ".yaml", ".safetensors", ".ckpt", ".png", ".jpg"],  # Includes LoRAs
    AssetType.STYLES: [".jpg", ".png", ".webp", ".json", ".safetensors"],
    AssetType.LOCATIONS: [".hdr", ".exr", ".jpg", ".png", ".json"],
    AssetType.MUSIC: [".wav", ".mp3", ".ogg", ".flac", ".m4a"],
}

# Creative document extensions
CREATIVE_DOC_EXTENSIONS = {
    CreativeDocType.TREATMENTS: [".md", ".txt", ".docx"],
    CreativeDocType.SCRIPTS: [".fountain", ".fdx", ".txt", ".md"],  # Includes beat sheets
    CreativeDocType.SHOT_LISTS: [".json", ".csv", ".xlsx"],  # Generative shot lists
    CreativeDocType.CANVAS: [".json"],  # Node graph saves
}

# Git LFS patterns for large files
LFS_PATTERNS = ["*.png", "*.jpg", "*.wav", "*.mp4", "*.safetensors"]
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
LFS_THRESHOLD = 10 * 1024 * 1024   # 10MB - use LFS for files larger than this

@router.post("/{project_id}/assets")
async def upload_assets(
    project_id: str,
    directory_type: DirectoryType,
    files: List[UploadFile] = File(...),
    project_service: ProjectService = Depends(get_project_service)
):
    # Validate project structure first
    structure = await project_service.validate_structure(project_id)
    if not structure.is_valid:
        raise HTTPException(400, f"Invalid project structure: {structure.missing_dirs}")
    
    # Validate directory type exists
    if directory_type not in structure.directories:
        raise HTTPException(400, f"Directory {directory_type} not found in project")
    
    # Validate files against directory type
    allowed_exts = DIRECTORY_EXTENSIONS.get(directory_type, [])
    for file in files:
        ext = Path(file.filename).suffix.lower()
        if ext not in allowed_exts:
            raise HTTPException(400, 
                f"File {file.filename} not allowed in {directory_type}. "
                f"Allowed: {allowed_exts}")
        
        # Check file size
        if file.size > MAX_FILE_SIZE:
            raise HTTPException(413, f"File {file.filename} too large")
    
    # Save files with async I/O
    results = []
    for file in files:
        result = await project_service.save_file(
            project_id, 
            file, 
            directory_type,
            use_lfs=(file.size > LFS_THRESHOLD)
        )
        results.append(result)
    
    return {"files": results}

# Character Asset Endpoints
@router.post("/{project_id}/characters")
async def create_character(
    project_id: str,
    character_data: CharacterCreate,
    project_service: ProjectService = Depends(get_project_service)
) -> CharacterResponse:
    """Create new character asset with directory structure"""
    character = await project_service.create_character(project_id, character_data)
    return character

@router.get("/{project_id}/characters")
async def list_characters(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> List[CharacterResponse]:
    """List all character assets in project"""
    characters = await project_service.list_characters(project_id)
    return characters

@router.get("/{project_id}/characters/{char_id}")
async def get_character(
    project_id: str,
    char_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> CharacterResponse:
    """Get character asset details"""
    character = await project_service.get_character(project_id, char_id)
    return character

@router.post("/{project_id}/characters/{char_id}/base-face")
async def upload_base_face(
    project_id: str,
    char_id: str,
    file: UploadFile = File(...),
    project_service: ProjectService = Depends(get_project_service)
) -> CharacterResponse:
    """Upload character's canonical base face image"""
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(400, "Base face must be PNG or JPEG")
    
    character = await project_service.upload_character_base_face(
        project_id, char_id, file
    )
    return character

@router.post("/{project_id}/characters/{char_id}/variations")
async def upload_variations(
    project_id: str,
    char_id: str,
    variation_type: CharacterVariationType,
    file: UploadFile = File(...),
    project_service: ProjectService = Depends(get_project_service)
) -> CharacterResponse:
    """Upload character variation image"""
    character = await project_service.upload_character_variation(
        project_id, char_id, variation_type, file
    )
    return character

@router.get("/{project_id}/characters/{char_id}/usage")
async def find_character_usage(
    project_id: str,
    char_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> Dict[str, List[str]]:
    """Find all shots where character is used"""
    usage = await project_service.find_character_usage(project_id, char_id)
    return {"usage": usage}

# Takes Management Endpoints
@router.post("/{project_id}/takes/register")
async def register_take(
    project_id: str,
    take_data: TakeMetadata,
    project_service: ProjectService = Depends(get_project_service)
):
    """Register a node output as a Take with metadata"""
    result = await project_service.register_take(project_id, take_data)
    return result

@router.get("/{project_id}/takes/{scene}/{shot}")
async def list_takes(
    project_id: str,
    scene: str,
    shot: str,
    project_service: ProjectService = Depends(get_project_service)
):
    """List all Takes for a given scene/shot"""
    takes = await project_service.list_takes(project_id, scene, shot)
    return {"takes": takes}

@router.post("/{project_id}/takes/path")
async def generate_take_path(
    project_id: str,
    request: TakePathRequest,
    project_service: ProjectService = Depends(get_project_service)
) -> TakePathResponse:
    """Generate the next available Take path for a scene/shot"""
    return await project_service.generate_take_path(project_id, request)

@router.post("/{project_id}/nodes/{node_id}/state")
async def save_node_state(
    project_id: str,
    node_id: str,
    state_data: NodeStateData,
    project_service: ProjectService = Depends(get_project_service)
):
    """Save node state and connections for project persistence"""
    await project_service.save_node_state(project_id, node_id, state_data)
    return {"status": "saved", "node_id": node_id}

@router.get("/{project_id}/nodes/{node_id}/state")
async def get_node_state(
    project_id: str,
    node_id: str,
    project_service: ProjectService = Depends(get_project_service)
) -> NodeStateData:
    """Retrieve saved node state"""
    return await project_service.get_node_state(project_id, node_id)
```

### Service Layer
```python
# app/services/project.py
import aiofiles
import asyncio
from pathlib import Path
from typing import List, Optional
from git import Repo

class ProjectService:
    def __init__(self, workspace_root: Path, git_service: GitService):
        self.workspace_root = workspace_root
        self.git_service = git_service
        self.required_dirs = list(DirectoryType)
    
    async def create_project(self, data: ProjectCreate) -> ProjectResponse:
        """Create new project with enforced directory structure"""
        project_path = self.workspace_root / data.name
        
        # Validate project doesn't exist
        if project_path.exists():
            raise ValueError(f"Project {data.name} already exists")
        
        # Create base directory
        project_path.mkdir(parents=True)
        
        # Create project structure (aligned with pipeline)
        # 01_Assets subdirectories
        assets_dir = project_path / "01_Assets"
        for asset_type in AssetType:
            (assets_dir / asset_type.value).mkdir(parents=True)
        
        # 02_Source_Creative subdirectories
        creative_dir = project_path / "02_Source_Creative"
        for doc_type in CreativeDocType:
            (creative_dir / doc_type.value).mkdir(parents=True)
        
        # 03_Renders - hierarchical structure for Takes
        renders_dir = project_path / "03_Renders"
        renders_dir.mkdir()
        
        # Other directories
        (project_path / "04_Project_Files").mkdir()
        (project_path / "05_Cache").mkdir()
        (project_path / "06_Exports").mkdir()
        
        # Initialize project.json with narrative structure
        project_config = {
            "name": data.name,
            "quality": data.quality,
            "narrative": {
                "structure": data.narrative_structure,
                "chapters": [],
                "emotionalBeats": []
            },
            "assets": {
                "characters": [],
                "styles": [],
                "locations": [],
                "music": []
            },
            "fps": data.fps,
            "resolution": data.resolution,
            "created": datetime.now().isoformat(),
            "structure_version": "1.0"
        }
        
        async with aiofiles.open(project_path / "project.json", "w") as f:
            await f.write(json.dumps(project_config, indent=2))
        
        # Initialize Git if requested
        if data.init_git:
            await self.git_service.init_repository(project_path, use_lfs=data.use_lfs)
        
        # Validate structure was created correctly
        structure = await self.validate_structure(data.name)
        
        return ProjectResponse(
            id=data.name,
            name=data.name,
            created=datetime.now(),
            modified=datetime.now(),
            quality=data.quality,
            size_bytes=0,
            file_count=0,
            git_status="clean" if data.init_git else None,
            structure=structure,
            workspace_path=str(project_path)
        )
    
    async def validate_structure(self, project_id: str) -> ProjectStructure:
        """Validate project follows the numbered directory structure"""
        project_path = self.workspace_root / project_id
        
        directories = {}
        missing_dirs = []
        extra_dirs = []
        
        # Check required directories
        for dir_type in self.required_dirs:
            dir_path = project_path / dir_type.value
            directories[dir_type] = dir_path.exists()
            if not dir_path.exists():
                missing_dirs.append(dir_type)
        
        # Check for extra directories (not in structure)
        for item in project_path.iterdir():
            if item.is_dir() and item.name not in [d.value for d in self.required_dirs]:
                if not item.name.startswith('.'):  # Ignore hidden dirs like .git
                    extra_dirs.append(item.name)
        
        is_valid = len(missing_dirs) == 0 and len(extra_dirs) == 0
        
        return ProjectStructure(
            directories=directories,
            is_valid=is_valid,
            missing_dirs=missing_dirs,
            extra_dirs=extra_dirs
        )
    
    async def save_file(self, project_id: str, file: UploadFile, 
                       directory_type: DirectoryType, use_lfs: bool = False) -> FileUploadResponse:
        """Save file to correct directory with async I/O and Git tracking"""
        project_path = self.workspace_root / project_id
        target_dir = project_path / directory_type.value
        target_path = target_dir / file.filename
        
        # Ensure directory exists (structure enforcement)
        if not target_dir.exists():
            raise ValueError(f"Directory {directory_type.value} does not exist")
        
        # Save file with async I/O
        async with aiofiles.open(target_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Track in Git
        git_tracked = False
        if await self.git_service.is_git_repo(project_path):
            if use_lfs:
                await self.git_service.track_lfs(project_path, target_path)
            git_tracked = await self.git_service.add_file(project_path, target_path)
        
        return FileUploadResponse(
            filename=file.filename,
            size=len(content),
            path=str(target_path.relative_to(project_path)),
            asset_type=directory_type,
            uploaded_at=datetime.now(),
            git_tracked=git_tracked,
            use_lfs=use_lfs
        )
    
    async def list_projects(self) -> List[ProjectResponse]:
        """List all projects with Git status and structure validation"""
        projects = []
        
        for project_dir in self.workspace_root.iterdir():
            if project_dir.is_dir() and (project_dir / "project.json").exists():
                project_info = await self.get_project(project_dir.name)
                projects.append(project_info)
        
        return projects
    
    # Takes System Methods
    async def generate_take_path(self, project_id: str, request: TakePathRequest) -> TakePathResponse:
        """Generate deterministic path for next Take"""
        project_path = self.workspace_root / project_id
        renders_dir = project_path / DirectoryType.RENDERS.value
        scene_dir = renders_dir / request.scene
        shot_dir = scene_dir / request.shot
        
        # Ensure directories exist
        shot_dir.mkdir(parents=True, exist_ok=True)
        
        # Find next take number
        existing_takes = list(shot_dir.glob(f"{request.scene}_{request.shot}_T*.{request.extension}"))
        take_numbers = []
        for take in existing_takes:
            try:
                # Extract take number from filename
                take_part = take.stem.split('_T')[-1]
                take_numbers.append(int(take_part))
            except ValueError:
                continue
        
        next_take = max(take_numbers) + 1 if take_numbers else 1
        
        # Generate filename
        filename = f"{request.scene}_{request.shot}_T{next_take:03d}{request.extension}"
        relative_path = f"{DirectoryType.RENDERS.value}/{request.scene}/{request.shot}/{filename}"
        absolute_path = project_path / relative_path
        
        # Generate volume path for Function Runner
        volume_path = f"/workspace/{project_id}/{relative_path}"
        
        return TakePathResponse(
            take_number=next_take,
            relative_path=relative_path,
            absolute_path=str(absolute_path),
            volume_path=volume_path
        )
    
    async def register_take(self, project_id: str, take_data: TakeMetadata) -> TakeMetadata:
        """Register a completed Take with metadata"""
        project_path = self.workspace_root / project_id
        takes_dir = project_path / DirectoryType.CONFIG.value / "takes"
        takes_dir.mkdir(parents=True, exist_ok=True)
        
        # Save take metadata
        take_file = takes_dir / f"{take_data.scene}_{take_data.shot}_T{take_data.take_number:03d}.json"
        async with aiofiles.open(take_file, 'w') as f:
            await f.write(take_data.json(indent=2))
        
        # Track in Git
        if await self.git_service.is_git_repo(project_path):
            await self.git_service.add_file(project_path, take_file)
        
        return take_data
    
    async def list_takes(self, project_id: str, scene: str, shot: str) -> List[TakeMetadata]:
        """List all Takes for a scene/shot"""
        project_path = self.workspace_root / project_id
        takes_dir = project_path / DirectoryType.CONFIG.value / "takes"
        
        takes = []
        if takes_dir.exists():
            for take_file in takes_dir.glob(f"{scene}_{shot}_T*.json"):
                async with aiofiles.open(take_file, 'r') as f:
                    content = await f.read()
                    take_data = TakeMetadata.parse_raw(content)
                    takes.append(take_data)
        
        return sorted(takes, key=lambda t: t.take_number)
    
    async def save_node_state(self, project_id: str, node_id: str, state_data: NodeStateData):
        """Save node state for project persistence"""
        project_path = self.workspace_root / project_id
        nodes_dir = project_path / DirectoryType.CONFIG.value / "nodes"
        nodes_dir.mkdir(parents=True, exist_ok=True)
        
        node_file = nodes_dir / f"{node_id}.json"
        async with aiofiles.open(node_file, 'w') as f:
            await f.write(state_data.json(indent=2))
        
        # Track in Git
        if await self.git_service.is_git_repo(project_path):
            await self.git_service.add_file(project_path, node_file)
    
    async def get_node_state(self, project_id: str, node_id: str) -> NodeStateData:
        """Retrieve saved node state"""
        project_path = self.workspace_root / project_id
        node_file = project_path / DirectoryType.CONFIG.value / "nodes" / f"{node_id}.json"
        
        if not node_file.exists():
            raise ValueError(f"Node state not found for {node_id}")
        
        async with aiofiles.open(node_file, 'r') as f:
            content = await f.read()
            return NodeStateData.parse_raw(content)
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

class InvalidProjectStructureError(Exception):
    pass

class DirectoryNotFoundError(Exception):
    pass

class GitOperationError(Exception):
    pass

# app/api/errors.py
from fastapi.responses import JSONResponse

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

@app.exception_handler(InvalidProjectStructureError)
async def invalid_structure_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_PROJECT_STRUCTURE",
                "message": str(exc),
                "details": {
                    "required_structure": [d.value for d in DirectoryType],
                    "structure_version": "1.0"
                }
            }
        }
    )

@app.exception_handler(DirectoryNotFoundError)
async def directory_not_found_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "DIRECTORY_NOT_FOUND",
                "message": str(exc),
                "hint": "File must be uploaded to a valid numbered directory"
            }
        }
    )
```

### Git Integration
```python
# app/services/git.py
import asyncio
from pathlib import Path
from git import Repo
from typing import Optional

class GitService:
    def __init__(self):
        self.lfs_patterns = LFS_PATTERNS
    
    async def init_repository(self, project_path: Path, use_lfs: bool = True):
        """Initialize Git repository with optional LFS"""
        repo = Repo.init(project_path)
        
        # Create .gitignore
        gitignore_content = """
# Cache and temporary files
09_Cache/
*.tmp
*.log

# System files
.DS_Store
Thumbs.db

# Python
__pycache__/
*.pyc
"""
        (project_path / ".gitignore").write_text(gitignore_content)
        
        # Initialize LFS if requested
        if use_lfs:
            await self._init_lfs(project_path)
        
        # Initial commit
        repo.index.add([".gitignore"])
        if use_lfs:
            repo.index.add([".gitattributes"])
        repo.index.commit("Initialize project structure")
    
    async def _init_lfs(self, project_path: Path):
        """Initialize Git LFS with patterns"""
        # Run git lfs install
        await asyncio.create_subprocess_exec(
            "git", "lfs", "install",
            cwd=project_path
        )
        
        # Create .gitattributes with LFS patterns
        gitattributes = "\n".join([f"{pattern} filter=lfs diff=lfs merge=lfs -text" 
                                  for pattern in self.lfs_patterns])
        (project_path / ".gitattributes").write_text(gitattributes)
    
    async def track_lfs(self, project_path: Path, file_path: Path):
        """Track file with Git LFS"""
        relative_path = file_path.relative_to(project_path)
        await asyncio.create_subprocess_exec(
            "git", "lfs", "track", str(relative_path),
            cwd=project_path
        )
    
    async def add_file(self, project_path: Path, file_path: Path) -> bool:
        """Add file to Git tracking"""
        try:
            repo = Repo(project_path)
            relative_path = file_path.relative_to(project_path)
            repo.index.add([str(relative_path)])
            return True
        except Exception:
            return False
    
    async def get_status(self, project_path: Path) -> str:
        """Get Git repository status"""
        try:
            repo = Repo(project_path)
            if repo.is_dirty():
                return "modified"
            elif repo.untracked_files:
                return "untracked"
            else:
                return "clean"
        except Exception:
            return "no-git"
    
    async def is_git_repo(self, project_path: Path) -> bool:
        """Check if path is a Git repository"""
        return (project_path / ".git").exists()
    
    # Character Asset Methods
    async def create_character(self, project_id: str, character_data: CharacterCreate) -> CharacterResponse:
        """Create new character asset with proper directory structure"""
        project_path = self.workspace_root / project_id
        
        # Generate unique ID and trigger word
        char_id = f"char-{uuid.uuid4().hex[:8]}"
        trigger_word = character_data.triggerWord or f"{character_data.name.lower().replace(' ', '')}v1"
        
        # Create character directory structure
        char_dir = project_path / "01_Assets" / "Characters" / character_data.name
        (char_dir / "lora").mkdir(parents=True, exist_ok=True)
        (char_dir / "variations").mkdir(exist_ok=True)
        
        # Create character data
        character = {
            "assetId": char_id,
            "assetType": "Character",
            "name": character_data.name,
            "description": character_data.description,
            "triggerWord": trigger_word,
            "baseFaceImagePath": None,
            "loraModelPath": None,
            "loraTrainingStatus": "untrained",
            "variations": {},
            "usage": [],
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat()
        }
        
        # Update project.json
        await self._update_project_characters(project_id, character)
        
        return CharacterResponse(**character)
    
    async def upload_character_base_face(self, project_id: str, char_id: str, file: UploadFile) -> CharacterResponse:
        """Upload and set character's base face image"""
        character = await self.get_character(project_id, char_id)
        
        # Save base face image
        char_dir = self.workspace_root / project_id / "01_Assets" / "Characters" / character.name
        base_face_path = char_dir / "base_face.png"
        
        async with aiofiles.open(base_face_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Update character data
        character.baseFaceImagePath = f"/01_Assets/Characters/{character.name}/base_face.png"
        character.loraTrainingStatus = "untrained"  # Reset training status
        character.modified = datetime.now()
        
        # Track in Git LFS
        if await self.git_service.is_git_repo(self.workspace_root / project_id):
            await self.git_service.track_lfs(self.workspace_root / project_id, base_face_path)
        
        await self._update_character_in_project(project_id, character)
        return character
    
    async def upload_character_variation(self, project_id: str, char_id: str, 
                                       variation_type: CharacterVariationType, 
                                       file: UploadFile) -> CharacterResponse:
        """Upload character variation image"""
        character = await self.get_character(project_id, char_id)
        
        # Save variation image
        char_dir = self.workspace_root / project_id / "01_Assets" / "Characters" / character.name
        variation_dir = char_dir / "variations"
        variation_path = variation_dir / f"{variation_type.value}.png"
        
        async with aiofiles.open(variation_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        # Update character variations
        character.variations[variation_type.value] = f"/01_Assets/Characters/{character.name}/variations/{variation_type.value}.png"
        character.modified = datetime.now()
        
        # Track in Git LFS
        if await self.git_service.is_git_repo(self.workspace_root / project_id):
            await self.git_service.track_lfs(self.workspace_root / project_id, variation_path)
        
        await self._update_character_in_project(project_id, character)
        return character
    
    async def find_character_usage(self, project_id: str, char_id: str) -> List[str]:
        """Find all shots where character is used"""
        # Read project.json and scan canvas nodes
        project_data = await self._read_project_json(project_id)
        usage = []
        
        # Scan canvas nodes for character references
        if "canvas" in project_data and "nodes" in project_data["canvas"]:
            for node in project_data["canvas"]["nodes"]:
                if node.get("type") == "CharacterAsset" and node.get("data", {}).get("assetId") == char_id:
                    # Find connected shot nodes
                    node_id = node.get("id")
                    for edge in project_data["canvas"].get("edges", []):
                        if edge.get("source") == node_id:
                            target_node = next((n for n in project_data["canvas"]["nodes"] 
                                              if n.get("id") == edge.get("target")), None)
                            if target_node and target_node.get("type") == "ShotNode":
                                shot_id = target_node.get("data", {}).get("shotId")
                                if shot_id and shot_id not in usage:
                                    usage.append(shot_id)
        
        return usage
```

### Workspace Path Configuration
```python
# app/core/config.py
from pydantic import BaseSettings, validator
from pathlib import Path

class Settings(BaseSettings):
    workspace_root: Path = Path("./workspace")
    backend_host: str = "0.0.0.0"
    backend_port: int = 8000
    max_upload_size: int = 100 * 1024 * 1024  # 100MB
    
    # Container volume mounts
    docker_workspace_path: Optional[Path] = None
    is_docker: bool = False
    function_runner_volume: str = "/workspace"  # Shared volume for Function Runner
    
    @validator('workspace_root')
    def validate_workspace(cls, v):
        # Handle Docker volume mounts
        if os.getenv("DOCKER_CONTAINER"):
            return Path("/workspace")
        return v
    
    class Config:
        env_file = ".env"
```

## Dependencies
- Workspace service from STORY-002
- FastAPI app from STORY-003
- Git integration service from STORY-006
- File system access and permissions
- Python-multipart for file uploads
- aiofiles for async I/O
- GitPython for Git operations

## Testing Criteria
- [ ] Project CRUD operations work correctly
- [ ] Directory structure is enforced on project creation
- [ ] File uploads validate against directory type restrictions
- [ ] Structure validation catches missing/extra directories
- [ ] Large files trigger Git LFS integration
- [ ] Async file I/O handles concurrent uploads
- [ ] Path traversal attacks are prevented
- [ ] Git operations track files correctly
- [ ] Workspace volume mounts work in Docker
- [ ] Deleted projects clean up Git repositories
- [ ] Take path generation creates correct scene/shot/take structure
- [ ] Take numbers increment properly for multiple generations
- [ ] Node state persistence saves and retrieves correctly
- [ ] Volume paths work with Function Runner containers
- [ ] Takes metadata stores all required reproducibility info
- [ ] Character assets created with proper directory structure
- [ ] Character base face uploads work with Git LFS
- [ ] Character variations organized by type
- [ ] Character usage tracking finds all shot references
- [ ] Character metadata updates persist to project.json

## Definition of Done
- [ ] All endpoints implemented and documented
- [ ] Request/response models validated with structure enforcement
- [ ] File operations use async I/O for performance
- [ ] Directory structure validation integrated into all operations
- [ ] Git/LFS integration working for file tracking
- [ ] Error cases return appropriate responses with structure hints
- [ ] Unit tests cover structure validation scenarios
- [ ] Integration tests verify Git operations
- [ ] API documentation updated in OpenAPI with structure details
- [ ] Docker volume mount paths handled correctly
- [ ] Takes management endpoints fully functional
- [ ] Node state persistence integrated with project data
- [ ] Scene/shot/take directory structure auto-created
- [ ] Volume paths compatible with Function Runner architecture
- [ ] Takes metadata includes all parameters for reproducibility
- [ ] Character asset API endpoints fully functional
- [ ] Character file structure matches specification
- [ ] Character LoRA path management implemented
- [ ] Character variation type validation working

## Story Links
- **Depends On**: STORY-002-project-structure-definition, STORY-003-fastapi-application-bootstrap
- **Blocks**: STORY-008-project-gallery-view
- **Related PRD**: PRD-004-project-asset-management