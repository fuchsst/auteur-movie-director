"""
Tests for character asset data model functionality.
"""

import json

import pytest

from app.schemas.project import CharacterAsset, LoRATrainingStatus
from app.services.workspace import WorkspaceService


@pytest.fixture
def workspace_service(tmp_path):
    """Create workspace service with temporary directory"""
    return WorkspaceService(str(tmp_path))


@pytest.fixture
def test_project(workspace_service):
    """Create a test project"""
    from app.schemas.project import NarrativeStructure, ProjectCreate, QualityLevel

    project_data = ProjectCreate(
        name="Test Movie",
        narrative_structure=NarrativeStructure.THREE_ACT,
        quality=QualityLevel.STANDARD,
        director="Test Director",
        description="Test project for character assets",
    )

    project_path, manifest = workspace_service.create_project(project_data)
    return project_path, manifest


def test_character_asset_schema():
    """Test CharacterAsset schema validation"""
    # Test with minimal fields
    character = CharacterAsset(
        assetId="test-uuid",
        assetType="Character",
        name="Test Character",
        description="A test character",
        id="test-uuid",
        type="Character",
        path="/assets/characters/test_character",
    )

    assert character.assetId == "test-uuid"
    assert character.name == "Test Character"
    assert character.loraTrainingStatus == LoRATrainingStatus.UNTRAINED
    assert character.variations == {}
    assert character.usage == []

    # Test serialization
    data = character.dict()
    assert data["assetId"] == "test-uuid"
    assert data["loraTrainingStatus"] == "untrained"


def test_add_character_to_project(workspace_service, test_project):
    """Test adding character to project manifest"""
    project_path, manifest = test_project

    # Add character
    character = workspace_service.add_character_to_project(
        project_path, "Hero Character", "The main protagonist of our story"
    )

    assert character is not None
    assert character.name == "Hero Character"
    assert character.description == "The main protagonist of our story"
    assert character.loraTrainingStatus == "untrained"

    # Verify character directory structure
    char_dir = project_path / "01_Assets" / "Characters" / "Hero_Character"
    assert char_dir.exists()
    assert (char_dir / "lora").exists()
    assert (char_dir / "variations").exists()

    # Verify project.json was updated
    manifest_path = project_path / "project.json"
    with open(manifest_path) as f:
        data = json.load(f)

    assert len(data["assets"]["characters"]) == 1
    assert data["assets"]["characters"][0]["name"] == "Hero Character"


def test_add_duplicate_character(workspace_service, test_project):
    """Test that duplicate characters are rejected"""
    project_path, manifest = test_project

    # Add first character
    character1 = workspace_service.add_character_to_project(
        project_path, "Hero Character", "The main protagonist"
    )
    assert character1 is not None

    # Try to add duplicate
    character2 = workspace_service.add_character_to_project(
        project_path, "Hero Character", "Different description"
    )
    assert character2 is None


def test_character_structure_creation(workspace_service, test_project):
    """Test character directory structure creation"""
    project_path, manifest = test_project

    # Create character structure directly
    char_path = workspace_service.create_character_structure(project_path, "Test Character")

    assert char_path.exists()
    assert char_path.name == "Test_Character"
    assert (char_path / "lora").exists()
    assert (char_path / "variations").exists()
    assert (char_path / "lora" / ".gitkeep").exists()
    assert (char_path / "variations" / ".gitkeep").exists()


def test_character_name_sanitization(workspace_service, test_project):
    """Test that character names are properly sanitized"""
    project_path, manifest = test_project

    # Add character with special characters
    character = workspace_service.add_character_to_project(
        project_path, "Hero@Character#123!", "Character with special name"
    )

    assert character is not None
    assert character.name == "Hero@Character#123!"  # Original name preserved

    # Check directory name is sanitized
    char_dir = project_path / "01_Assets" / "Characters" / "Hero_Character_123"
    assert char_dir.exists()


def test_list_characters_from_manifest(workspace_service, test_project):
    """Test retrieving characters from project manifest"""
    project_path, manifest = test_project

    # Add multiple characters
    characters = [
        ("Hero", "The protagonist"),
        ("Villain", "The antagonist"),
        ("Sidekick", "The helper"),
    ]

    for name, desc in characters:
        workspace_service.add_character_to_project(project_path, name, desc)

    # Load manifest and check characters
    updated_manifest = workspace_service.get_project_manifest(project_path)
    assert len(updated_manifest.assets["characters"]) == 3

    # Verify character names
    # Handle both dict and object forms
    character_names = []
    for char in updated_manifest.assets["characters"]:
        if isinstance(char, dict):
            character_names.append(char["name"])
        else:
            character_names.append(char.name)

    assert "Hero" in character_names
    assert "Villain" in character_names
    assert "Sidekick" in character_names
