# STORY-022: Character Asset Data Model (Foundation Only)

## Story
As a developer, I need to define the basic character asset data structure in project.json that will serve as a foundation for future character consistency features. This story only creates the minimal data model scaffolding - actual LoRA training, character generation, and management will be implemented in PRD-003 (Character Consistency Engine).

## Important Note
This is a **foundation story only**. We are creating the data structure to support future features, but NOT implementing:
- LoRA training functionality
- Character generation
- Voice model integration
- Automated variation generation
- Character Sheet UI (covered in PRD-004)

## Acceptance Criteria
- [ ] Basic character data structure added to project.json schema
- [ ] Minimal fields for future LoRA support (path placeholders)
- [ ] Simple character metadata structure
- [ ] Basic file path references for assets
- [ ] Integration with existing project structure

## Technical Details

### Minimal Character Data Model for project.json

```json
{
  "assets": {
    "characters": [
      {
        "assetId": "char-uuid",
        "assetType": "Character",
        "name": "Character Name",
        "description": "Basic description",
        "triggerWord": null,  // Placeholder for future LoRA
        "baseFaceImagePath": null,  // Placeholder
        "loraModelPath": null,  // Placeholder for future
        "loraTrainingStatus": "untrained",
        "variations": {},  // Empty, will be populated later
        "usage": []  // Will track shot IDs in future
      }
    ]
  }
}
```

### Python Schema Update

```python
# backend/app/schemas/project.py
from typing import Optional, Dict, List
from pydantic import BaseModel

class CharacterAsset(BaseModel):
    """Basic character asset model - foundation only"""
    assetId: str
    assetType: str = "Character"
    name: str
    description: Optional[str] = None
    
    # Placeholders for future features
    triggerWord: Optional[str] = None
    baseFaceImagePath: Optional[str] = None
    loraModelPath: Optional[str] = None
    loraTrainingStatus: str = "untrained"
    variations: Dict[str, str] = {}
    usage: List[str] = []

class ProjectAssets(BaseModel):
    """Asset container in project.json"""
    characters: List[CharacterAsset] = []
    locations: List[dict] = []  # Future
    styles: List[dict] = []     # Future
    music: List[dict] = []      # Future
```

### Basic API Endpoint

```python
# backend/app/api/endpoints/projects.py
@router.post("/{project_id}/characters")
async def add_character_placeholder(
    project_id: str,
    character: CharacterAsset
):
    """Add character to project.json - data only, no processing"""
    # Simply add to project.json structure
    # No LoRA training or generation in this story
    pass
```

## What This Story Does NOT Include

1. **Character Generation UI** - Covered in PRD-004
2. **LoRA Training Pipeline** - Covered in PRD-003
3. **Voice Model Integration** - Future PRD
4. **Character Variation Generation** - Requires Function Runner (PRD-003)
5. **Character Sheet Component** - Covered in PRD-004
6. **Usage Tracking Logic** - Covered in PRD-004

## Dependencies
- STORY-002: Project Structure (for project.json)
- STORY-004: File Management API

## Notes
This story creates the minimal data structure needed to support future character features. The actual implementation of character consistency, LoRA training, and asset management will be done in their respective PRDs.