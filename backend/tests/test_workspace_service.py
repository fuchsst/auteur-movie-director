"""
Tests for workspace service - enforcing structure as API contract
"""

import json
import shutil
import tempfile

import pytest

from app.schemas.project import (
    NarrativeStructure,
    ProjectCreate,
    QualityLevel,
)
from app.services.workspace import WorkspaceService


class TestWorkspaceService:
    """Test workspace service functionality"""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def workspace_service(self, temp_workspace):
        """Create workspace service instance"""
        return WorkspaceService(temp_workspace)

    def test_create_project_with_enforced_structure(self, workspace_service):
        """Test project creation with all required directories"""
        # Create project
        project_data = ProjectCreate(
            name="Test Project",
            narrative_structure=NarrativeStructure.THREE_ACT,
            quality=QualityLevel.STANDARD,
            director="Test Director",
            description="Test Description",
        )

        project_path, manifest = workspace_service.create_project(project_data)

        # Verify project was created
        assert project_path.exists()
        assert project_path.name == "Test_Project"

        # Verify ALL required directories exist
        for required_dir in WorkspaceService.REQUIRED_STRUCTURE:
            dir_path = project_path / required_dir
            assert dir_path.exists(), f"Required directory missing: {required_dir}"
            # Check for .gitkeep
            gitkeep = dir_path / ".gitkeep"
            assert gitkeep.exists(), f"Missing .gitkeep in {required_dir}"

        # Verify project.json exists and is valid
        project_json = project_path / "project.json"
        assert project_json.exists()

        with open(project_json) as f:
            data = json.load(f)
            assert data["name"] == "Test Project"
            assert data["quality"] == "standard"
            assert data["narrative"]["structure"] == "three-act"
            assert len(data["narrative"]["chapters"]) == 3

    def test_git_initialization_with_lfs(self, workspace_service):
        """Test Git repository initialization with LFS"""
        project_data = ProjectCreate(
            name="Git Test Project", narrative_structure=NarrativeStructure.HERO_JOURNEY
        )

        project_path, _ = workspace_service.create_project(project_data)

        # Verify Git repository
        git_dir = project_path / ".git"
        assert git_dir.exists()

        # Verify .gitattributes with LFS rules
        gitattributes = project_path / ".gitattributes"
        assert gitattributes.exists()

        with open(gitattributes) as f:
            content = f.read()
            # Check for critical LFS patterns
            assert "*.png filter=lfs" in content
            assert "*.mp4 filter=lfs" in content
            assert "03_Renders/**/* filter=lfs" in content
            assert "01_Assets/Characters/*/lora/* filter=lfs" in content

        # Verify .gitignore
        gitignore = project_path / ".gitignore"
        assert gitignore.exists()

        with open(gitignore) as f:
            content = f.read()
            assert "__pycache__/" in content
            assert "05_Cache/" in content
            assert "06_Exports/" in content

    def test_narrative_structure_templates(self, workspace_service):
        """Test different narrative structure templates"""
        structures = [
            (NarrativeStructure.THREE_ACT, 3),
            (NarrativeStructure.HERO_JOURNEY, 4),
            (NarrativeStructure.BEAT_SHEET, 14),
            (NarrativeStructure.STORY_CIRCLE, 8),
        ]

        for structure, expected_chapters in structures:
            project_data = ProjectCreate(
                name=f"Test_{structure.value}", narrative_structure=structure
            )

            project_path, manifest = workspace_service.create_project(project_data)

            # Verify narrative structure
            assert manifest.narrative.structure == structure
            assert len(manifest.narrative.chapters) == expected_chapters

            # Clean up
            shutil.rmtree(project_path)

    def test_project_structure_validation(self, workspace_service):
        """Test structure validation detects deviations"""
        # Create valid project
        project_data = ProjectCreate(name="Validation Test")
        project_path, _ = workspace_service.create_project(project_data)

        # Validate - should be valid
        validation = workspace_service.validate_project_structure(project_path)
        assert validation.valid is True
        assert len(validation.missing_directories) == 0
        assert validation.git_initialized is True
        assert validation.git_lfs_enabled is True
        assert validation.project_json_valid is True

        # Remove a required directory
        shutil.rmtree(project_path / "01_Assets" / "Characters")

        # Validate again - should fail
        validation = workspace_service.validate_project_structure(project_path)
        assert validation.valid is False
        assert "01_Assets/Characters" in validation.missing_directories

        # Corrupt project.json
        with open(project_path / "project.json", "w") as f:
            f.write("invalid json")

        # Validate again - should fail
        validation = workspace_service.validate_project_structure(project_path)
        assert validation.valid is False
        assert validation.project_json_valid is False
        assert any("Invalid project.json" in err for err in validation.errors)

    def test_character_structure_creation(self, workspace_service):
        """Test character-specific directory structure"""
        project_data = ProjectCreate(name="Character Test")
        project_path, _ = workspace_service.create_project(project_data)

        # Create character structure
        char_path = workspace_service.create_character_structure(project_path, "John Doe")

        # Verify path
        expected_path = project_path / "01_Assets" / "Characters" / "John_Doe"
        assert char_path == expected_path
        assert char_path.exists()

        # Verify subdirectories
        assert (char_path / "lora").exists()
        assert (char_path / "variations").exists()
        assert (char_path / "lora" / ".gitkeep").exists()
        assert (char_path / "variations" / ".gitkeep").exists()

    def test_hierarchical_render_path(self, workspace_service):
        """Test Takes system hierarchical path generation"""
        project_data = ProjectCreate(name="Render Test")
        project_path, _ = workspace_service.create_project(project_data)

        # Create render path
        render_path = workspace_service.create_hierarchical_path(
            project_path, "act-1", "scene-01", "shot-001"
        )

        # Verify path
        expected = project_path / "03_Renders" / "act-1" / "scene-01" / "shot-001"
        assert render_path == expected
        assert render_path.exists()

    def test_project_name_sanitization(self, workspace_service):
        """Test project name sanitization"""
        project_data = ProjectCreate(name="Test @Project #1 (2024)!")

        project_path, _ = workspace_service.create_project(project_data)

        # Verify sanitized name
        assert project_path.name == "Test__Project__1__2024_"

    def test_duplicate_project_prevention(self, workspace_service):
        """Test that duplicate projects are prevented"""
        project_data = ProjectCreate(name="Duplicate Test")

        # Create first project
        workspace_service.create_project(project_data)

        # Try to create duplicate - should fail
        with pytest.raises(ValueError, match="already exists"):
            workspace_service.create_project(project_data)

    def test_list_projects(self, workspace_service):
        """Test listing projects in workspace"""
        # Create multiple projects
        for i in range(3):
            project_data = ProjectCreate(
                name=f"List Test {i}", quality=QualityLevel.LOW if i == 0 else QualityLevel.STANDARD
            )
            workspace_service.create_project(project_data)

        # List projects
        projects = workspace_service.list_projects()

        assert len(projects) == 3
        for project in projects:
            assert "path" in project
            assert "manifest" in project
            assert "validation" in project
            assert project["validation"].valid is True
