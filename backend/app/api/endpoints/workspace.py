"""
Workspace API endpoints for project management.
Enforces the Project-as-Repository model with strict structure validation.
"""

import logging
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.schemas.project import (
    ProjectCreate,
    ProjectManifest,
    ProjectStructureValidation,
)
from app.services.workspace import WorkspaceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workspace", tags=["workspace"])


class CharacterCreateRequest(BaseModel):
    """Request to add a character to project"""

    name: str
    description: str = ""


class WorkspaceConfig(BaseModel):
    """Workspace configuration response"""

    root_path: str
    projects_count: int
    available_space_gb: float
    enforced_structure: list[str]
    narrative_structures: list[str]


class ProjectListItem(BaseModel):
    """Project list item response"""

    id: str
    name: str
    path: str
    created: str
    modified: str
    quality: str
    narrative_structure: str
    git_status: str
    validation: ProjectStructureValidation


class ProjectResponse(BaseModel):
    """Project creation/update response"""

    id: str
    name: str
    path: str
    manifest: ProjectManifest


# Initialize workspace service
workspace_root = os.environ.get("WORKSPACE_ROOT", "./workspace")
workspace_service = WorkspaceService(workspace_root)


@router.get("/config", response_model=WorkspaceConfig)
async def get_workspace_config():
    """Get workspace configuration with enforced structure"""
    try:
        # Calculate available space
        stat = os.statvfs(workspace_root)
        available_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)

        # Count projects
        projects = workspace_service.list_projects()

        return WorkspaceConfig(
            root_path=str(workspace_service.workspace_root),
            projects_count=len(projects),
            available_space_gb=round(available_gb, 2),
            enforced_structure=WorkspaceService.REQUIRED_STRUCTURE,
            narrative_structures=list(WorkspaceService.NARRATIVE_STRUCTURES.keys()),
        )
    except Exception as e:
        logger.error(f"Error getting workspace config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate")
async def validate_workspace():
    """Validate workspace structure integrity"""
    try:
        # Check workspace exists
        if not workspace_service.workspace_root.exists():
            return {
                "valid": False,
                "errors": ["Workspace directory does not exist"],
            }

        # Check permissions
        if not os.access(workspace_service.workspace_root, os.W_OK):
            return {
                "valid": False,
                "errors": ["Workspace directory is not writable"],
            }

        return {
            "valid": True,
            "workspace_path": str(workspace_service.workspace_root),
        }
    except Exception as e:
        logger.error(f"Error validating workspace: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects", response_model=list[ProjectListItem])
async def list_projects(
    quality: str = Query(None, description="Filter by quality level"),
    structure: str = Query(None, description="Filter by narrative structure"),
):
    """List all projects with Git status and validation"""
    try:
        projects = workspace_service.list_projects()

        # Convert to response format
        result = []
        for project in projects:
            manifest = project["manifest"]

            # Apply filters
            if quality and manifest.get("quality") != quality:
                continue
            if structure and manifest.get("narrative", {}).get("structure") != structure:
                continue

            # Get Git status (simplified for now)
            git_status = "clean"
            if project["validation"].git_initialized:
                # TODO: Implement actual Git status check
                git_status = "clean"
            else:
                git_status = "uninitialized"

            result.append(
                ProjectListItem(
                    id=manifest["id"],
                    name=manifest["name"],
                    path=project["path"],
                    created=manifest["created"],
                    modified=manifest["modified"],
                    quality=manifest["quality"],
                    narrative_structure=manifest["narrative"]["structure"],
                    git_status=git_status,
                    validation=project["validation"],
                )
            )

        return result
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects", response_model=ProjectResponse)
async def create_project(project_data: ProjectCreate):
    """Create new project with enforced structure"""
    try:
        project_path, manifest = workspace_service.create_project(project_data)

        return ProjectResponse(
            id=manifest.id,
            name=manifest.name,
            path=str(project_path),
            manifest=manifest,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/structure")
async def validate_project_structure(project_id: str):
    """Validate project directory structure"""
    try:
        # Find project by ID
        projects = workspace_service.list_projects()
        project = None

        for p in projects:
            if p["manifest"]["id"] == project_id:
                project = p
                break

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Validate structure
        project_path = Path(project["path"])
        validation = workspace_service.validate_project_structure(project_path)

        return validation
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating project structure: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/projects/{project_id}/characters")
async def add_character(project_id: str, character_data: CharacterCreateRequest):
    """Add character to project manifest - data only, no processing"""
    try:
        # Find project by ID
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        # Add character to project
        character = workspace_service.add_character_to_project(
            project_path, character_data.name, character_data.description
        )

        if not character:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to add character. Character '{character_data.name}' may already exist.",
            )

        return {
            "success": True,
            "character": character.dict(),
            "message": f"Character '{character_data.name}' added to project",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding character: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{project_id}/characters")
async def list_characters(project_id: str):
    """List all characters in a project"""
    try:
        # Get project manifest
        project_path = workspace_service.get_project_path(project_id)
        if not project_path:
            raise HTTPException(status_code=404, detail="Project not found")

        manifest = workspace_service.get_project_manifest(project_path)
        if not manifest:
            raise HTTPException(status_code=404, detail="Project manifest not found")

        # Get characters from manifest
        characters = manifest.assets.get("characters", [])

        return {"characters": [char.dict() for char in characters], "total": len(characters)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing characters: {e}")
        raise HTTPException(status_code=500, detail=str(e))
