"""End-to-End Project Flow Integration Tests

Tests the complete project creation and management flow across all components.
"""

import pytest
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List
import aiofiles
from httpx import AsyncClient

from app.main import app
from app.services.workspace import WorkspaceService
from app.services.git import git_service
from app.redis_client import redis_client


@pytest.mark.asyncio
async def test_complete_project_flow(async_client: AsyncClient, tmp_workspace: Path):
    """Test complete project creation and management flow"""
    
    # 1. Create project through API
    project_data = {
        "name": "integration-test-project",
        "quality": "standard",
        "narrative_structure": "three-act"
    }
    
    response = await async_client.post("/api/v1/projects", json=project_data)
    assert response.status_code == 201
    project = response.json()
    assert project["name"] == project_data["name"]
    assert project["quality"] == project_data["quality"]
    assert "id" in project
    
    # 2. Verify project directory structure
    workspace_service = WorkspaceService()
    project_path = workspace_service.get_project_path(project["name"])
    assert project_path.exists()
    
    # Check all required directories
    expected_dirs = [
        "01_Assets/Characters",
        "01_Assets/Locations", 
        "01_Assets/Styles",
        "01_Assets/Music",
        "02_Source_Creative/Treatments",
        "02_Source_Creative/Scripts",
        "02_Source_Creative/ShotLists",
        "02_Source_Creative/Canvas",
        "03_Renders",
        "04_Project_Files",
        "05_Cache",
        "06_Exports"
    ]
    
    for dir_path in expected_dirs:
        assert (project_path / dir_path).exists()
    
    # 3. Verify project.json
    project_json_path = project_path / "project.json"
    assert project_json_path.exists()
    
    async with aiofiles.open(project_json_path, mode='r') as f:
        manifest = json.loads(await f.read())
    
    assert manifest["name"] == project_data["name"]
    assert manifest["quality"] == project_data["quality"]
    assert manifest["narrative"]["structure"] == project_data["narrative_structure"]
    assert manifest["version"] == "1.0.0"
    
    # 4. Verify Git initialization
    git_status = await git_service.get_status(project_path)
    assert git_status.initialized
    assert not git_status.is_dirty
    
    # Check Git LFS configuration
    gitattributes_path = project_path / ".gitattributes"
    assert gitattributes_path.exists()
    
    async with aiofiles.open(gitattributes_path, mode='r') as f:
        gitattributes = await f.read()
    
    assert "*.mp4 filter=lfs" in gitattributes
    assert "*.mov filter=lfs" in gitattributes
    assert "*.wav filter=lfs" in gitattributes
    assert "*.png filter=lfs" in gitattributes
    assert "*.exr filter=lfs" in gitattributes
    assert "*.safetensors filter=lfs" in gitattributes
    
    # Check .gitignore
    gitignore_path = project_path / ".gitignore"
    assert gitignore_path.exists()
    
    async with aiofiles.open(gitignore_path, mode='r') as f:
        gitignore = await f.read()
    
    assert "05_Cache/" in gitignore
    assert "06_Exports/" in gitignore
    assert "__pycache__" in gitignore
    
    # 5. Test file upload
    test_file_content = b"Test image data"
    files = {"files": ("test.png", test_file_content, "image/png")}
    
    response = await async_client.post(
        f"/api/v1/projects/{project['id']}/assets?category=characters",
        files=files
    )
    assert response.status_code == 200
    upload_result = response.json()
    assert len(upload_result["uploaded"]) == 1
    
    # Verify file in correct location
    uploaded_file = project_path / "01_Assets" / "Characters" / "test.png"
    assert uploaded_file.exists()
    
    # 6. Test WebSocket updates (simulated)
    # In a real test, we'd connect a WebSocket client
    # For now, verify Redis pub/sub is configured
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"project:{project['id']}")
    
    # Publish test event
    await redis_client.publish(
        f"project:{project['id']}",
        json.dumps({
            "type": "project.updated",
            "data": {"status": "active"}
        })
    )
    
    # 7. List projects
    response = await async_client.get("/api/v1/projects")
    assert response.status_code == 200
    projects = response.json()
    assert any(p["name"] == project_data["name"] for p in projects)
    
    # 8. Delete project
    response = await async_client.delete(f"/api/v1/projects/{project['id']}")
    assert response.status_code == 204
    
    # Verify cleanup
    assert not project_path.exists()


@pytest.mark.asyncio
async def test_invalid_project_names(async_client: AsyncClient):
    """Test validation of invalid project names"""
    
    invalid_names = [
        "",  # Empty
        "test/project",  # Contains slash
        "test\\project",  # Contains backslash  
        "test:project",  # Contains colon
        "test*project",  # Contains asterisk
        "test?project",  # Contains question mark
        "test<project>",  # Contains angle brackets
        "test|project",  # Contains pipe
        ".hidden",  # Starts with dot
        "CON",  # Windows reserved name
        "PRN",  # Windows reserved name
        "AUX",  # Windows reserved name
        "a" * 256,  # Too long
    ]
    
    for name in invalid_names:
        response = await async_client.post(
            "/api/v1/projects",
            json={"name": name, "quality": "standard"}
        )
        assert response.status_code == 422 or response.status_code == 400
        assert "name" in response.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_concurrent_project_creation(async_client: AsyncClient, tmp_workspace: Path):
    """Test multiple concurrent project creations"""
    
    # Create multiple projects concurrently
    project_names = [f"concurrent-test-{i}" for i in range(5)]
    
    async def create_project(name: str):
        response = await async_client.post(
            "/api/v1/projects",
            json={"name": name, "quality": "standard"}
        )
        return response
    
    # Execute concurrently
    responses = await asyncio.gather(*[
        create_project(name) for name in project_names
    ])
    
    # Verify all succeeded
    for i, response in enumerate(responses):
        assert response.status_code == 201
        project = response.json()
        assert project["name"] == project_names[i]
    
    # Verify all directories exist
    workspace_service = WorkspaceService()
    for name in project_names:
        project_path = workspace_service.get_project_path(name)
        assert project_path.exists()
    
    # Cleanup
    for response in responses:
        project = response.json()
        await async_client.delete(f"/api/v1/projects/{project['id']}")


@pytest.mark.asyncio
async def test_websocket_task_execution_flow(async_client: AsyncClient, tmp_workspace: Path):
    """Test WebSocket task execution with quality mapping"""
    
    # Create project with specific quality
    response = await async_client.post("/api/v1/projects", json={
        "name": "task-execution-test",
        "quality": "high"
    })
    assert response.status_code == 201
    project = response.json()
    
    # Submit a task
    task_data = {
        "type": "text_to_image",
        "prompt": "A beautiful sunset over mountains",
        "node_id": "test-node-123",
        "parameters": {
            "width": 1024,
            "height": 1024,
            "seed": 42
        }
    }
    
    response = await async_client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json=task_data
    )
    assert response.status_code == 202
    task = response.json()
    
    # Verify task created with quality mapping
    assert task["status"] == "pending"
    assert task["type"] == "text_to_image"
    assert task["project_id"] == project["id"]
    assert task["node_id"] == "test-node-123"
    
    # Quality 'high' should map to specific parameters
    assert task["parameters"]["steps"] == 50
    assert task["parameters"]["cfg_scale"] == 7.5
    assert task["parameters"]["sampler"] == "dpm++_2m"
    
    # Verify task in Redis queue
    task_key = f"task:{task['id']}"
    task_data = await redis_client.get(task_key)
    assert task_data is not None
    
    # Simulate task progress
    progress_channel = f"project:{project['id']}"
    
    # Publish progress updates
    for progress in [0, 25, 50, 75, 100]:
        await redis_client.publish(
            progress_channel,
            json.dumps({
                "type": "task.progress",
                "data": {
                    "task_id": task["id"],
                    "node_id": "test-node-123",
                    "progress": progress,
                    "status": "running" if progress < 100 else "completed"
                }
            })
        )
        await asyncio.sleep(0.1)
    
    # Simulate task completion
    output_path = f"03_Renders/output_{task['id']}.png"
    await redis_client.publish(
        progress_channel,
        json.dumps({
            "type": "task.completed",
            "data": {
                "task_id": task["id"],
                "node_id": "test-node-123",
                "output_path": output_path,
                "duration": 15.5
            }
        })
    )
    
    # Cleanup
    await async_client.delete(f"/api/v1/projects/{project['id']}")


@pytest.mark.asyncio
async def test_character_asset_lifecycle(async_client: AsyncClient, tmp_workspace: Path):
    """Test complete character asset lifecycle"""
    
    # 1. Create project
    response = await async_client.post("/api/v1/projects", json={
        "name": "character-lifecycle-test",
        "quality": "standard"
    })
    assert response.status_code == 201
    project = response.json()
    
    # 2. Create character
    character_data = {
        "name": "Elena Vasquez",
        "description": "A skilled detective with sharp features and intense gaze",
        "base_prompt": "professional detective, sharp features, intense gaze"
    }
    
    response = await async_client.post(
        f"/api/v1/projects/{project['id']}/characters",
        json=character_data
    )
    assert response.status_code == 201
    character = response.json()
    
    assert character["name"] == character_data["name"]
    assert character["description"] == character_data["description"]
    assert "id" in character
    
    # 3. Verify character directory structure
    workspace_service = WorkspaceService()
    project_path = workspace_service.get_project_path(project["name"])
    char_dir = project_path / "01_Assets" / "Characters" / character["id"]
    
    assert char_dir.exists()
    assert (char_dir / "metadata.json").exists()
    
    # 4. Upload base face image
    test_image = b"fake image data for testing"
    files = {"file": ("base_face.png", test_image, "image/png")}
    
    response = await async_client.post(
        f"/api/v1/projects/{project['id']}/characters/{character['id']}/base-face",
        files=files
    )
    assert response.status_code == 200
    
    # Verify base face stored
    base_face_path = char_dir / "base_face.png"
    assert base_face_path.exists()
    
    # 5. List project characters
    response = await async_client.get(
        f"/api/v1/projects/{project['id']}/characters"
    )
    assert response.status_code == 200
    characters = response.json()
    assert len(characters) == 1
    assert characters[0]["name"] == character_data["name"]
    
    # 6. Update character in project manifest
    workspace_service = WorkspaceService()
    project_path = workspace_service.get_project_path(project["name"])
    manifest_path = project_path / "project.json"
    
    async with aiofiles.open(manifest_path, mode='r') as f:
        manifest = json.loads(await f.read())
    
    # Verify character in manifest
    assert "characters" in manifest
    assert len(manifest["characters"]) == 1
    assert manifest["characters"][0]["id"] == character["id"]
    assert manifest["characters"][0]["name"] == character["name"]
    
    # 7. Cleanup
    await async_client.delete(f"/api/v1/projects/{project['id']}")


@pytest.mark.asyncio  
async def test_quality_mapping_parameters(async_client: AsyncClient):
    """Test that quality presets map to correct execution parameters"""
    
    quality_mappings = {
        "low": {
            "steps": 20,
            "cfg_scale": 7.0,
            "sampler": "euler",
            "target_vram": 12
        },
        "standard": {
            "steps": 30,
            "cfg_scale": 7.5, 
            "sampler": "euler_a",
            "target_vram": 16
        },
        "high": {
            "steps": 50,
            "cfg_scale": 7.5,
            "sampler": "dpm++_2m",
            "target_vram": 24
        }
    }
    
    for quality, expected_params in quality_mappings.items():
        # Create project with specific quality
        response = await async_client.post("/api/v1/projects", json={
            "name": f"quality-test-{quality}",
            "quality": quality
        })
        assert response.status_code == 201
        project = response.json()
        
        # Submit task
        response = await async_client.post(
            f"/api/v1/projects/{project['id']}/tasks",
            json={
                "type": "text_to_image",
                "prompt": "Test prompt",
                "node_id": f"node-{quality}"
            }
        )
        assert response.status_code == 202
        task = response.json()
        
        # Verify parameters mapped correctly
        for param, value in expected_params.items():
            if param in task["parameters"]:
                assert task["parameters"][param] == value
        
        # Cleanup
        await async_client.delete(f"/api/v1/projects/{project['id']}")


@pytest.mark.asyncio
async def test_structure_enforcement(async_client: AsyncClient, tmp_workspace: Path):
    """Test that project structure is enforced correctly"""
    
    # Create project
    response = await async_client.post("/api/v1/projects", json={
        "name": "structure-test",
        "quality": "standard"
    })
    assert response.status_code == 201
    project = response.json()
    
    # Get project path
    workspace_service = WorkspaceService()
    project_path = workspace_service.get_project_path(project["name"])
    
    # Verify all required directories exist
    required_structure = [
        "01_Assets",
        "01_Assets/Characters",
        "01_Assets/Locations",
        "01_Assets/Styles", 
        "01_Assets/Music",
        "02_Source_Creative",
        "02_Source_Creative/Treatments",
        "02_Source_Creative/Scripts",
        "02_Source_Creative/ShotLists",
        "02_Source_Creative/Canvas",
        "03_Renders",
        "03_Renders/Chapter_01",
        "03_Renders/Chapter_01/Scene_01", 
        "03_Renders/Chapter_01/Scene_01/Shot_01",
        "04_Project_Files",
        "05_Cache",
        "06_Exports"
    ]
    
    for dir_name in required_structure:
        dir_path = project_path / dir_name
        assert dir_path.exists(), f"Missing directory: {dir_name}"
        assert dir_path.is_dir(), f"Not a directory: {dir_name}"
    
    # Verify .gitignore includes cache and exports
    gitignore_path = project_path / ".gitignore"
    async with aiofiles.open(gitignore_path, mode='r') as f:
        gitignore_content = await f.read()
    
    assert "05_Cache/" in gitignore_content
    assert "06_Exports/" in gitignore_content
    assert "*.tmp" in gitignore_content
    assert "__pycache__/" in gitignore_content
    
    # Cleanup
    await async_client.delete(f"/api/v1/projects/{project['id']}")


@pytest.mark.asyncio
async def test_takes_system_integration(async_client: AsyncClient, tmp_workspace: Path):
    """Test takes system creates versioned outputs correctly"""
    
    # Create project with takes enabled
    response = await async_client.post("/api/v1/projects", json={
        "name": "takes-integration-test",
        "quality": "standard",
        "takes_system_enabled": True
    })
    assert response.status_code == 201
    project = response.json()
    
    # Create a take
    take_data = {
        "shot_id": "S01_S01",
        "description": "First take of opening shot"
    }
    
    response = await async_client.post(
        f"/api/v1/projects/{project['id']}/shots/S01_S01/takes",
        json=take_data
    )
    assert response.status_code == 201
    take = response.json()
    
    assert take["take_number"] == 1
    assert take["shot_id"] == "S01_S01"
    assert "take_path" in take
    assert "take_001" in take["take_path"]
    
    # Verify take directory created
    workspace_service = WorkspaceService()
    project_path = workspace_service.get_project_path(project["name"])
    take_dir = project_path / "03_Renders" / "Chapter_01" / "Scene_01" / "Shot_01" / "takes" / "take_001"
    
    assert take_dir.exists()
    
    # Create second take
    response = await async_client.post(
        f"/api/v1/projects/{project['id']}/shots/S01_S01/takes",
        json={"shot_id": "S01_S01", "description": "Second take"}
    )
    assert response.status_code == 201
    take2 = response.json()
    
    assert take2["take_number"] == 2
    assert "take_002" in take2["take_path"]
    
    # Cleanup
    await async_client.delete(f"/api/v1/projects/{project['id']}")