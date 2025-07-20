# User Story: STORY-084 - Structured GenerativeShotList Schema

## Story Description
**As a** filmmaker and AI system integrator
**I want** a comprehensive JSON schema for shot definitions that includes all production elements
**So that** every shot can be generated with complete cinematic control, emotional context, and asset consistency

## Acceptance Criteria

### Functional Requirements
- [ ] Create fully-structured JSON schema for GenerativeShotList entries
- [ ] Include emotional beat references with intensity scoring
- [ ] Support comprehensive asset reference arrays (Character, Wardrobe, Props, etc.)
- [ ] Define camera setup specifications with cinematic parameters
- [ ] Integrate SFX flags with configurable parameters
- [ ] Include audio prompt structure with dialogue, music, and sound references
- [ ] Support shot-to-shot dependency tracking
- [ ] Enable programmatic generation parameter control

### Technical Requirements
- [ ] JSON Schema validation for all shot definitions
- [ ] AssetReference UUID resolution and validation
- [ ] Emotional beat integration with generation parameters
- [ ] Camera setup parameter mapping to generative models
- [ ] Audio asset linking and synchronization
- [ ] Shot sequence validation and continuity checking
- [ ] Export compatibility with video assembly pipeline
- [ ] Backward compatibility with existing shot formats

### Quality Requirements
- [ ] Schema validation unit tests
- [ ] Asset reference resolution tests
- [ ] Emotional beat parameter mapping tests
- [ ] Camera setup validation tests
- [ ] Cross-shot dependency tests
- [ ] Performance tests for large shot lists (1000+ shots)
- [ ] Integration tests with video assembly pipeline

## Implementation Notes

### GenerativeShotList JSON Schema
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "title": "GenerativeShotList",
  "properties": {
    "shots": {
      "type": "array",
      "items": {
        "$ref": "#/definitions/GenerativeShot"
      }
    }
  },
  "definitions": {
    "GenerativeShot": {
      "type": "object",
      "required": ["shot_id", "shot_description", "emotional_beat_ref", "visual_prompt"],
      "properties": {
        "shot_id": {
          "type": "string",
          "format": "uuid",
          "description": "Unique identifier for this shot"
        },
        "shot_description": {
          "type": "string",
          "description": "Human-readable description of the shot's core narrative action"
        },
        "emotional_beat_ref": {
          "type": "string",
          "enum": [
            "opening_image", "theme_stated", "set_up", "catalyst", "debate",
            "break_into_two", "b_story", "fun_and_games", "midpoint",
            "bad_guys_close_in", "all_is_lost", "dark_night_of_the_soul",
            "break_into_three", "finale", "final_image"
          ],
          "description": "Reference to the governing beat from the Emotional Beat Sheet"
        },
        "emotional_intensity": {
          "type": "number",
          "minimum": 0.0,
          "maximum": 1.0,
          "description": "Strength of the beat's emotion (0.0 = subtle, 1.0 = intense)"
        },
        "visual_prompt": {
          "$ref": "#/definitions/VisualPrompt"
        },
        "audio_prompt": {
          "$ref": "#/definitions/AudioPrompt"
        },
        "dependencies": {
          "type": "array",
          "items": {
            "type": "string"
          },
          "description": "Array of shot_ids this shot depends on"
        },
        "metadata": {
          "$ref": "#/definitions/ShotMetadata"
        }
      }
    },
    "VisualPrompt": {
      "type": "object",
      "required": ["base_text", "character_references", "style_reference"],
      "properties": {
        "base_text": {
          "type": "string",
          "description": "Core action description without asset-specific keywords"
        },
        "character_references": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/CharacterReference"
          }
        },
        "wardrobe_references": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/WardrobeReference"
          }
        },
        "prop_references": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uuid"
          }
        },
        "style_reference": {
          "type": "string",
          "format": "uuid"
        },
        "set_dressing_references": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uuid"
          }
        },
        "camera_setup": {
          "$ref": "#/definitions/CameraSetup"
        },
        "sfx_flags": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/SFXFlag"
          }
        },
        "gen_params": {
          "$ref": "#/definitions/GenerationParameters"
        }
      }
    },
    "CharacterReference": {
      "type": "object",
      "required": ["asset_id", "position"],
      "properties": {
        "asset_id": {
          "type": "string",
          "format": "uuid"
        },
        "expression": {
          "type": "string",
          "enum": ["neutral", "happy", "sad", "angry", "surprised", "contemplative", "fearful"]
        },
        "action": {
          "type": "string",
          "description": "Character's action or pose"
        },
        "position": {
          "type": "object",
          "properties": {
            "x": {"type": "number", "minimum": 0, "maximum": 1},
            "y": {"type": "number", "minimum": 0, "maximum": 1},
            "z": {"type": "number", "description": "Depth layer"}
          }
        },
        "scale": {
          "type": "number",
          "minimum": 0.1,
          "maximum": 10.0,
          "default": 1.0
        }
      }
    },
    "WardrobeReference": {
      "type": "object",
      "required": ["asset_id", "character_id", "state"],
      "properties": {
        "asset_id": {
          "type": "string",
          "format": "uuid"
        },
        "character_id": {
          "type": "string",
          "format": "uuid"
        },
        "state": {
          "type": "string",
          "description": "Wardrobe condition state"
        }
      }
    },
    "CameraSetup": {
      "type": "object",
      "properties": {
        "shot_size": {
          "type": "string",
          "enum": ["extreme_close_up", "close_up", "medium_close_up", "medium_shot", "medium_long_shot", "long_shot", "extreme_long_shot"]
        },
        "angle": {
          "type": "string",
          "enum": ["eye_level", "high_angle", "low_angle", "overhead", "dutch_angle"]
        },
        "movement": {
          "type": "string",
          "enum": ["static", "pan_left", "pan_right", "tilt_up", "tilt_down", "zoom_in", "zoom_out", "dolly_in", "dolly_out", "tracking"]
        },
        "focal_length": {
          "type": "number",
          "description": "Lens focal length in mm"
        },
        "depth_of_field": {
          "type": "string",
          "enum": ["shallow", "medium", "deep"]
        },
        "composition": {
          "type": "string",
          "enum": ["rule_of_thirds", "centered", "leading_lines", "symmetrical", "asymmetrical"]
        }
      }
    },
    "SFXFlag": {
      "type": "object",
      "required": ["type"],
      "properties": {
        "type": {
          "type": "string",
          "enum": ["rain", "snow", "fog", "explosion", "fire", "smoke", "particles", "lighting"]
        },
        "intensity": {
          "type": "string",
          "enum": ["light", "medium", "heavy", "extreme"]
        },
        "color": {
          "type": "string",
          "description": "Primary color for the effect"
        },
        "duration": {
          "type": "number",
          "description": "Duration in seconds"
        }
      }
    },
    "GenerationParameters": {
      "type": "object",
      "properties": {
        "cfg_scale": {
          "type": "number",
          "minimum": 1.0,
          "maximum": 30.0,
          "default": 7.5
        },
        "steps": {
          "type": "integer",
          "minimum": 10,
          "maximum": 150,
          "default": 30
        },
        "seed": {
          "type": "integer",
          "description": "Random seed for reproducible generation"
        },
        "resolution": {
          "type": "string",
          "enum": ["1920x1080", "2560x1440", "3840x2160"],
          "default": "1920x1080"
        },
        "sampler": {
          "type": "string",
          "enum": ["euler", "euler_a", "dpm++", "ddim"],
          "default": "euler_a"
        }
      }
    },
    "AudioPrompt": {
      "type": "object",
      "properties": {
        "dialogue_references": {
          "type": "array",
          "items": {
            "$ref": "#/definitions/DialogueReference"
          }
        },
        "music_reference": {
          "type": "string",
          "format": "uuid"
        },
        "sound_references": {
          "type": "array",
          "items": {
            "type": "string",
            "format": "uuid"
          }
        },
        "ambient_sound": {
          "type": "string",
          "description": "Description of ambient sound environment"
        }
      }
    },
    "DialogueReference": {
      "type": "object",
      "required": ["asset_id", "character_id", "text", "timing"],
      "properties": {
        "asset_id": {
          "type": "string",
          "format": "uuid"
        },
        "character_id": {
          "type": "string",
          "format": "uuid"
        },
        "text": {
          "type": "string",
          "description": "Dialogue text content"
        },
        "timing": {
          "type": "object",
          "properties": {
            "start": {"type": "number", "description": "Start time in seconds"},
            "duration": {"type": "number", "description": "Duration in seconds"}
          }
        },
        "emotion": {
          "type": "string",
          "enum": ["neutral", "happy", "sad", "angry", "surprised", "contemplative", "fearful"]
        }
      }
    },
    "ShotMetadata": {
      "type": "object",
      "properties": {
        "duration": {
          "type": "number",
          "description": "Shot duration in seconds"
        },
        "scene_id": {
          "type": "string",
          "format": "uuid"
        },
        "chapter_id": {
          "type": "string",
          "format": "uuid"
        },
        "act_id": {
          "type": "string",
          "format": "uuid"
        },
        "tags": {
          "type": "array",
          "items": {
            "type": "string"
          }
        },
        "notes": {
          "type": "string",
          "description": "Director's notes for this shot"
        }
      }
    }
  }
}
```

### Example Shot Definition
```json
{
  "shot_id": "shot-15a-b3c1-4f2e",
  "shot_description": "John stands by the rain-streaked window, contemplating his next move",
  "emotional_beat_ref": "all_is_lost",
  "emotional_intensity": 0.85,
  "visual_prompt": {
    "base_text": "a man stands by a large, grimy warehouse window, looking out at the city",
    "character_references": [
      {
        "asset_id": "char-john-detective-v2",
        "expression": "contemplative",
        "action": "slumped shoulders, hand on chin",
        "position": {"x": 0.3, "y": 0.6, "z": 1.0}
      }
    ],
    "wardrobe_references": [
      {
        "asset_id": "wardrobe-trench-coat-v1",
        "character_id": "char-john-detective-v2",
        "state": "wet"
      }
    ],
    "prop_references": ["prop-whiskey-glass-v1"],
    "style_reference": "style-noir-dramatic-v1",
    "camera_setup": {
      "shot_size": "medium_close_up",
      "angle": "low_angle",
      "movement": "slow_push_in",
      "focal_length": 85,
      "depth_of_field": "shallow"
    },
    "sfx_flags": [
      {
        "type": "rain",
        "intensity": "heavy",
        "color": "blue_gray",
        "duration": 5.0
      }
    ],
    "gen_params": {
      "cfg_scale": 3.5,
      "steps": 30,
      "seed": 12345,
      "resolution": "1920x1080"
    }
  },
  "audio_prompt": {
    "music_reference": "music-tense-underscore-v2",
    "sound_references": ["sound-rain-heavy-v1", "sound-distant-thunder-v3"],
    "ambient_sound": "Low rumble of thunder, rhythmic rain on glass"
  },
  "dependencies": ["shot-14b", "shot-15a"],
  "metadata": {
    "duration": 5.2,
    "scene_id": "scene-05-warehouse",
    "tags": ["emotional", "rain", "noir"],
    "notes": "Focus on the weight of his decision. Rain should feel oppressive."
  }
}
```

### Implementation Architecture

#### Shot Schema Validator
```python
import jsonschema
from typing import Dict, List, Any

class GenerativeShotValidator:
    def __init__(self, schema_path: str):
        with open(schema_path) as f:
            self.schema = json.load(f)
    
    def validate_shot(self, shot_data: Dict[str, Any]) -> bool:
        """Validate single shot against schema"""
        try:
            jsonschema.validate(shot_data, self.schema)
            return True
        except jsonschema.ValidationError as e:
            raise ValueError(f"Invalid shot data: {e.message}")
    
    def validate_shot_list(self, shots: List[Dict[str, Any]]) -> bool:
        """Validate entire shot list"""
        for shot in shots:
            self.validate_shot(shot)
        return True
    
    def resolve_asset_references(self, shot: Dict[str, Any], asset_registry: Dict[str, Any]) -> bool:
        """Ensure all asset references exist in registry"""
        # Validate character references
        for char_ref in shot.get("visual_prompt", {}).get("character_references", []):
            if char_ref["asset_id"] not in asset_registry:
                raise ValueError(f"Character asset not found: {char_ref['asset_id']}")
        
        # Validate other asset references
        asset_refs = [
            *shot.get("visual_prompt", {}).get("prop_references", []),
            *shot.get("visual_prompt", {}).get("wardrobe_references", []),
            *shot.get("visual_prompt", {}).get("set_dressing_references", []),
            shot.get("visual_prompt", {}).get("style_reference"),
            *shot.get("audio_prompt", {}).get("sound_references", []),
            shot.get("audio_prompt", {}).get("music_reference")
        ]
        
        for ref in asset_refs:
            if ref and ref not in asset_registry:
                raise ValueError(f"Asset reference not found: {ref}")
        
        return True
```

#### Emotional Beat Integration
```python
class EmotionalBeatProcessor:
    def __init__(self):
        self.beat_parameters = {
            "all_is_lost": {
                "keywords": ["dark", "shadows", "rain", "gloom", "despair"],
                "cfg_scale_modifier": -0.5,
                "brightness_modifier": -0.3,
                "saturation_modifier": -0.2
            },
            "fun_and_games": {
                "keywords": ["bright", "colorful", "dynamic", "energetic"],
                "cfg_scale_modifier": 0.0,
                "brightness_modifier": 0.2,
                "saturation_modifier": 0.3
            }
        }
    
    def apply_emotional_context(self, shot: Dict[str, Any]) -> Dict[str, Any]:
        """Apply emotional beat parameters to generation settings"""
        beat_ref = shot["emotional_beat_ref"]
        intensity = shot.get("emotional_intensity", 0.5)
        
        if beat_ref in self.beat_parameters:
            params = self.beat_parameters[beat_ref]
            
            # Apply intensity-based modifications
            gen_params = shot["visual_prompt"]["gen_params"]
            gen_params["cfg_scale"] += params["cfg_scale_modifier"] * intensity
            
            # Add emotional keywords
            base_text = shot["visual_prompt"]["base_text"]
            keywords = " ".join(params["keywords"])
            shot["visual_prompt"]["base_text"] = f"{base_text}, {keywords}"
        
        return shot
```

### API Endpoints

#### Shot Management
```python
POST /api/v1/shots
{
  "shot_description": "John stands by the rain-streaked window",
  "emotional_beat_ref": "all_is_lost",
  "emotional_intensity": 0.85,
  "visual_prompt": {
    "base_text": "a man stands by a window",
    "character_references": [{"asset_id": "char-john-v2", "expression": "contemplative"}]
  }
}

GET /api/v1/shots/{shot_id}
PUT /api/v1/shots/{shot_id}
DELETE /api/v1/shots/{shot_id}
```

#### Validation Endpoints
```python
POST /api/v1/shots/validate
{
  "shots": [...]
}

POST /api/v1/shots/resolve-assets
{
  "shot_id": "shot-15a-b3c1",
  "project_id": "proj-123"
}
```

### Testing Strategy

#### Schema Validation Tests
```python
def test_valid_shot_structure():
    validator = GenerativeShotValidator("shot_schema.json")
    shot = {
        "shot_id": "test-123",
        "shot_description": "Test shot",
        "emotional_beat_ref": "all_is_lost",
        "emotional_intensity": 0.8,
        "visual_prompt": {
            "base_text": "test description",
            "character_references": [{"asset_id": "char-123", "position": {"x": 0.5, "y": 0.5}}],
            "style_reference": "style-123"
        }
    }
    assert validator.validate_shot(shot) is True

def test_emotional_beat_integration():
    processor = EmotionalBeatProcessor()
    shot = {
        "emotional_beat_ref": "all_is_lost",
        "emotional_intensity": 0.9,
        "visual_prompt": {
            "base_text": "man looking out window",
            "gen_params": {"cfg_scale": 7.5}
        }
    }
    
    processed = processor.apply_emotional_context(shot)
    assert "dark" in processed["visual_prompt"]["base_text"]
    assert processed["visual_prompt"]["gen_params"]["cfg_scale"] < 7.5
```

## Story Size: **Large (13 story points)**

## Sprint Assignment: **Sprint 1-2 (Phase 1)**

## Dependencies
- **STORY-083**: Expanded Asset System for asset references
- **Emotional Beat System**: Integration with story structure
- **Asset Registry**: Validation and resolution system
- **JSON Schema**: Validation framework

## Success Criteria
- JSON Schema validates 100% of shot definitions
- Asset reference resolution works for all asset types
- Emotional beat integration affects generation parameters
- Camera setup parameters map correctly to models
- Audio integration supports full soundtrack creation
- Schema handles 1000+ shot lists efficiently
- Backward compatibility maintained with existing formats
- Integration tests pass with video assembly pipeline

## Future Enhancements
- **AI Shot Optimization**: Automatic parameter tuning
- **Visual Scripting**: Drag-and-drop shot creation
- **Collaborative Editing**: Multi-user shot list editing
- **Template System**: Reusable shot templates
- **Export Plugins**: Integration with NLE systems