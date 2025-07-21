# User Story: STORY-083 - Expanded Asset System for Breakdown Elements

## Story Description
**As a** filmmaker using the generative platform
**I want** comprehensive asset management for all traditional breakdown elements
**So that** I can maintain consistency across props, wardrobe, vehicles, and other production elements throughout the video assembly pipeline

## Acceptance Criteria

### Functional Requirements
- [ ] Implement PropAsset system for physical objects with reference images and 3D model support
- [ ] Create WardrobeAsset system linked to CharacterAssets with state management (clean, torn, damp)
- [ ] Build VehicleAsset system with model year, condition, and reference tracking
- [ ] Establish SetDressingAsset system for environmental consistency
- [ ] Implement SoundAsset library for reusable audio cues
- [ ] Create MusicAsset system for mood-based scoring
- [ ] Ensure all assets integrate with AssetReference pointer system
- [ ] Support asset versioning and change propagation

### Technical Requirements
- [ ] Expand project.json schema to include new asset types
- [ ] Create directory structure for new asset categories
- [ ] Implement asset validation and integrity checks
- [ ] Build asset dependency tracking system
- [ ] Create asset search and filtering capabilities
- [ ] Implement asset state management (wardrobe conditions, prop variations)
- [ ] Support 3D model references for props and vehicles
- [ ] Enable asset linking between related elements (wardrobe->character, props->scenes)

### Quality Requirements
- [ ] Unit tests for all new asset types
- [ ] Integration tests with existing Character/Style/Location assets
- [ ] Performance tests for asset loading and resolution
- [ ] Asset consistency validation across project
- [ ] User acceptance testing for asset creation workflows
- [ ] Cross-project asset reusability testing
- [ ] Asset change propagation testing

## Implementation Notes

### Asset Architecture Overview
```
01_Assets/
├── Generative_Assets/
│   ├── Characters/          # Existing CharacterAsset
│   ├── Styles/              # Existing StyleAsset
│   ├── Locations/           # Existing LocationAsset
│   ├── Props/               # NEW: PropAsset
│   │   ├── Heros_Sword/
│   │   │   ├── asset.json
│   │   │   ├── reference_images/
│   │   │   ├── 3d_models/
│   │   │   └── variations/
│   │   └── Vintage_Book/
│   ├── Wardrobe/            # NEW: WardrobeAsset
│   │   ├── Trench_Coat/
│   │   │   ├── asset.json
│   │   │   ├── texture_maps/
│   │   │   ├── states/
│   │   │   │   ├── clean.jpg
│   │   │   │   ├── torn.jpg
│   │   │   │   └── damp.jpg
│   │   │   └── worn_by/
│   │   └── Evening_Gown/
│   ├── Vehicles/            # NEW: VehicleAsset
│   │   ├── Police_Cruiser/
│   │   │   ├── asset.json
│   │   │   ├── reference_images/
│   │   │   └── 3d_models/
│   │   └── Vintage_Motorcycle/
│   ├── Set_Dressing/        # NEW: SetDressingAsset
│   │   ├── Vintage_Lamp/
│   │   └── Antique_Mirror/
│   ├── Sounds/              # NEW: SoundAsset
│   │   ├── Footsteps_Gravel/
│   │   └── Door_Creak/
│   └── Music/               # NEW: MusicAsset
│       ├── Tense_Underscore/
│       └── Romantic_Melody/
```

### Data Models

#### PropAsset Schema
```json
{
  "assetId": "prop-heros-sword-v1",
  "name": "Hero's Sword",
  "description": "Ancient bronze sword with intricate runes",
  "category": "weapon",
  "referenceImages": [
    "reference_images/front_view.jpg",
    "reference_images/side_view.jpg",
    "reference_images/detail_run.jpg"
  ],
  "3dModelPath": "3d_models/sword.obj",
  "triggerWord": "ancient_bronze_sword",
  "variations": {
    "pristine": "variations/pristine.jpg",
    "worn": "variations/worn.jpg",
    "magical_glow": "variations/magical.jpg"
  },
  "tags": ["medieval", "magical", "hero_prop"],
  "createdAt": "2024-01-15T10:30:00Z",
  "updatedAt": "2024-01-15T14:45:00Z"
}
```

#### WardrobeAsset Schema
```json
{
  "assetId": "wardrobe-trench-coat-v1",
  "name": "Detective Trench Coat",
  "description": "Classic beige trench coat, weathered from years of use",
  "wornBy": "char-detective-john-v2",
  "textureMaps": {
    "diffuse": "texture_maps/diffuse.jpg",
    "normal": "texture_maps/normal.jpg",
    "roughness": "texture_maps/roughness.jpg"
  },
  "states": {
    "clean": "states/clean.jpg",
    "weathered": "states/weathered.jpg",
    "wet": "states/wet.jpg",
    "torn": "states/torn.jpg"
  },
  "tags": ["detective", "classic", "weathered"],
  "createdAt": "2024-01-15T11:00:00Z",
  "updatedAt": "2024-01-15T15:20:00Z"
}
```

#### VehicleAsset Schema
```json
{
  "assetId": "vehicle-police-cruiser-v1",
  "name": "Police Cruiser",
  "description": "Modern police interceptor with realistic details",
  "modelYear": "2022",
  "make": "Ford",
  "model": "Explorer Police Interceptor",
  "referenceImages": [
    "reference_images/exterior_front.jpg",
    "reference_images/exterior_side.jpg",
    "reference_images/interior.jpg"
  ],
  "3dModelPath": "3d_models/police_cruiser.obj",
  "condition": "pristine",
  "tags": ["police", "emergency", "modern"],
  "createdAt": "2024-01-15T12:00:00Z",
  "updatedAt": "2024-01-15T16:30:00Z"
}
```

### Implementation Architecture

#### Asset Manager Service
```python
class AssetManager:
    def __init__(self, project_root: str):
        self.project_root = project_root
        self.assets = {}
        self.dependencies = {}
    
    def create_prop_asset(self, name: str, description: str, **kwargs) -> PropAsset:
        """Create new PropAsset with validation"""
        asset = PropAsset(name, description, **kwargs)
        self.validate_asset(asset)
        self.save_asset(asset)
        return asset
    
    def link_wardrobe_to_character(self, wardrobe_id: str, character_id: str):
        """Link wardrobe asset to character for consistency"""
        wardrobe = self.get_asset(wardrobe_id)
        wardrobe.wornBy = character_id
        self.propagate_change(wardrobe_id)
    
    def propagate_asset_change(self, asset_id: str):
        """Update all dependent shots when asset changes"""
        dependents = self.dependencies.get(asset_id, [])
        for dependent_id in dependents:
            self.update_dependent_shot(dependent_id)
```

#### Asset Validation
```python
class AssetValidator:
    def validate_prop_asset(self, asset: PropAsset) -> bool:
        """Validate PropAsset integrity"""
        checks = [
            self.validate_asset_id(asset.assetId),
            self.validate_reference_images(asset.referenceImages),
            self.validate_3d_model(asset.model3dPath),
            self.validate_tags(asset.tags)
        ]
        return all(checks)
    
    def validate_wardrobe_states(self, asset: WardrobeAsset) -> bool:
        """Ensure all required states have images"""
        required_states = ["clean", "weathered", "wet", "torn"]
        return all(state in asset.states for state in required_states)
```

### API Endpoints

#### Asset Creation
```python
POST /api/v1/assets/props
{
  "name": "Hero's Sword",
  "description": "Ancient bronze sword with intricate runes",
  "category": "weapon",
  "referenceImages": ["base64_image_data"],
  "3dModel": "base64_model_data"
}

POST /api/v1/assets/wardrobe
{
  "name": "Detective Trench Coat",
  "description": "Classic beige trench coat",
  "wornBy": "char-detective-john-v2",
  "states": {
    "clean": "base64_image_data",
    "weathered": "base64_image_data"
  }
}
```

### Testing Strategy

#### Unit Tests
```python
def test_prop_asset_creation():
    manager = AssetManager("./test_project")
    prop = manager.create_prop_asset(
        name="Test Sword",
        description="A test sword for validation"
    )
    assert prop.assetId.startswith("prop-")
    assert prop.name == "Test Sword"
    assert os.path.exists(f"./test_project/01_Assets/Generative_Assets/Props/Test_Sword")

def test_wardrobe_character_linking():
    manager = AssetManager("./test_project")
    wardrobe = manager.create_wardrobe_asset(name="Test Coat")
    character = manager.create_character_asset(name="Test Character")
    
    manager.link_wardrobe_to_character(wardrobe.assetId, character.assetId)
    assert wardrobe.wornBy == character.assetId
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 1-2 (Phase 1)**

## Dependencies
- **Project Structure**: Existing Character/Style/Location asset system
- **File System**: Asset storage and organization
- **Validation Framework**: Asset integrity checking
- **Change Propagation**: Asset update mechanisms

## Success Criteria
- All new asset types created and validated
- Directory structure implemented and tested
- Asset linking between related elements working
- Change propagation system operational
- Cross-project asset reusability confirmed
- Performance benchmarks met (1000+ assets @ 60 FPS)
- User acceptance testing passed for asset creation workflows

## Future Enhancements
- **AI Asset Generation**: Automated asset creation from descriptions
- **3D Model Integration**: Full 3D pipeline support
- **Asset Marketplaces**: Community asset sharing
- **Version Control**: Advanced asset versioning
- **Collaborative Editing**: Multi-user asset management