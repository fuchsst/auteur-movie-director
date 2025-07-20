"""
Asset Propagation System
STORY-089 Implementation

Handles asset inheritance, propagation, resolution, and management across
story hierarchy (Project -> Act -> Chapter -> Scene -> Shot -> Take).
"""

import json
import logging
from typing import Dict, List, Optional, Any, Set, Union
from pathlib import Path
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field
from app.models.asset_types import AssetType, PropagationMode, BaseAsset
from app.models.breakdown_models import BreakdownElement, ElementCategory

logger = logging.getLogger(__name__)


class AssetPropagationRule(BaseModel):
    """Rule for how assets propagate between hierarchy levels."""
    
    rule_id: str = Field(default_factory=lambda: str(uuid4()))
    asset_type: AssetType
    source_level: str  # project, act, chapter, scene, shot, take
    target_level: str
    propagation_mode: PropagationMode = Field(default=PropagationMode.INHERIT, description="Asset propagation behavior")
    conditions: Dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, description="Higher priority rules override lower ones")
    enabled: bool = True


class AssetReference(BaseModel):
    """Reference to an asset with propagation context."""
    
    asset_id: str
    asset_type: AssetType
    reference_id: str = Field(default_factory=lambda: str(uuid4()))
    level: str  # project, act, chapter, scene, shot, take
    level_id: str  # ID of the specific level instance
    source_level: str  # Where this asset was originally defined
    source_id: str
    override_data: Dict[str, Any] = Field(default_factory=dict)
    is_overridden: bool = False
    usage_context: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class AssetPropagationContext(BaseModel):
    """Context for asset propagation at a specific hierarchy level."""
    
    project_id: str
    level: str
    level_id: str
    parent_context: Optional['AssetPropagationContext'] = None
    child_contexts: List['AssetPropagationContext'] = Field(default_factory=list)
    local_assets: List[AssetReference] = Field(default_factory=list)
    inherited_assets: List[AssetReference] = Field(default_factory=list)
    resolved_assets: Dict[str, AssetReference] = Field(default_factory=dict)
    override_rules: List[AssetPropagationRule] = Field(default_factory=list)
    
    def get_all_assets(self) -> Dict[str, AssetReference]:
        """Get all resolved assets for this context."""
        return self.resolved_assets.copy()
    
    def get_assets_by_type(self, asset_type: AssetType) -> List[AssetReference]:
        """Get all assets of a specific type."""
        return [asset for asset in self.resolved_assets.values() 
                if asset.asset_type == asset_type]


class AssetPropagationService:
    """
    Service for managing asset propagation across story hierarchy.
    
    Hierarchy levels:
    - project: Root level with global defaults
    - act: Story act level
    - chapter: Narrative chapter level
    - scene: Individual scene level
    - shot: Camera shot level
    - take: Version/take level (most specific)
    """
    
    HIERARCHY_LEVELS = ['project', 'act', 'chapter', 'scene', 'shot', 'take']
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.propagation_dir = self.project_root / "02_Story" / "asset_propagation"
        self.propagation_dir.mkdir(parents=True, exist_ok=True)
        self.contexts: Dict[str, AssetPropagationContext] = {}
        self.rules: List[AssetPropagationRule] = []
        self._load_default_rules()
    
    def _load_default_rules(self) -> None:
        """Load default propagation rules."""
        default_rules = [
            # Characters propagate from project to all levels
            AssetPropagationRule(
                asset_type=AssetType.CHARACTER,
                source_level="project",
                target_level="take",
                propagation_mode="inherit",
                priority=1
            ),
            # Styles propagate from project to all levels
            AssetPropagationRule(
                asset_type=AssetType.STYLE,
                source_level="project",
                target_level="take",
                propagation_mode="inherit",
                priority=1
            ),
            # Locations propagate from scene to shot/take
            AssetPropagationRule(
                asset_type=AssetType.LOCATION,
                source_level="scene",
                target_level="take",
                propagation_mode="inherit",
                priority=2
            ),
            # Props can be overridden at shot level
            AssetPropagationRule(
                asset_type=AssetType.PROP,
                source_level="scene",
                target_level="shot",
                propagation_mode="override",
                priority=3
            ),
            # Wardrobe can be overridden at character level
            AssetPropagationRule(
                asset_type=AssetType.WARDROBE,
                source_level="project",
                target_level="shot",
                propagation_mode="override",
                priority=4
            )
        ]
        self.rules.extend(default_rules)
    
    def add_propagation_rule(self, rule: AssetPropagationRule) -> None:
        """Add a custom propagation rule."""
        self.rules.append(rule)
        self._save_rules()
    
    def _save_rules(self) -> None:
        """Save propagation rules to file."""
        rules_file = self.propagation_dir / "propagation_rules.json"
        rules_data = [rule.model_dump() for rule in self.rules]
        with open(rules_file, 'w') as f:
            json.dump(rules_data, f, indent=2, default=str)
    
    def _load_rules(self) -> None:
        """Load propagation rules from file."""
        rules_file = self.propagation_dir / "propagation_rules.json"
        if rules_file.exists():
            with open(rules_file) as f:
                rules_data = json.load(f)
                self.rules = [AssetPropagationRule(**rule) for rule in rules_data]
    
    def create_context(self, project_id: str, level: str, level_id: str, 
                      parent_context: Optional[AssetPropagationContext] = None) -> AssetPropagationContext:
        """Create a new asset propagation context."""
        context = AssetPropagationContext(
            project_id=project_id,
            level=level,
            level_id=level_id,
            parent_context=parent_context
        )
        
        if parent_context:
            parent_context.child_contexts.append(context)
        
        context_key = f"{project_id}:{level}:{level_id}"
        self.contexts[context_key] = context
        
        return context
    
    def add_asset_to_context(self, project_id: str, level: str, level_id: str, 
                           asset_id: str, asset_type: AssetType, 
                           override_data: Dict[str, Any] = None) -> AssetReference:
        """Add an asset to a specific context."""
        context_key = f"{project_id}:{level}:{level_id}"
        
        if context_key not in self.contexts:
            # Create context if it doesn't exist
            parent_level, parent_id = self._get_parent_context(level, level_id)
            parent_context = None
            if parent_level:
                parent_key = f"{project_id}:{parent_level}:{parent_id}"
                parent_context = self.contexts.get(parent_key)
            
            self.create_context(project_id, level, level_id, parent_context)
        
        context = self.contexts[context_key]
        
        asset_ref = AssetReference(
            asset_id=asset_id,
            asset_type=asset_type,
            level=level,
            level_id=level_id,
            source_level=level,  # This is where it's defined
            source_id=level_id,
            override_data=override_data or {},
            is_overridden=bool(override_data)
        )
        
        context.local_assets.append(asset_ref)
        return asset_ref
    
    def _get_parent_context(self, level: str, level_id: str) -> tuple:
        """Get parent context for a given level and ID."""
        level_index = self.HIERARCHY_LEVELS.index(level)
        if level_index > 0:
            parent_level = self.HIERARCHY_LEVELS[level_index - 1]
            # Simple ID mapping - in real implementation would need proper mapping
            parent_id = level_id.split('-')[0] if '-' in level_id else level_id
            return parent_level, parent_id
        return None, None
    
    def resolve_assets(self, project_id: str, level: str, level_id: str) -> Dict[str, AssetReference]:
        """
        Resolve all assets for a specific hierarchy level using propagation rules.
        
        Args:
            project_id: Project identifier
            level: Hierarchy level (project, act, chapter, scene, shot, take)
            level_id: Specific instance ID
            
        Returns:
            Dictionary of resolved assets keyed by asset_type:asset_id
        """
        context_key = f"{project_id}:{level}:{level_id}"
        
        if context_key not in self.contexts:
            self.create_context(project_id, level, level_id)
        
        context = self.contexts[context_key]
        
        # Get all relevant rules for this level
        level_index = self.HIERARCHY_LEVELS.index(level)
        relevant_rules = []
        
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            source_index = self.HIERARCHY_LEVELS.index(rule.source_level)
            target_index = self.HIERARCHY_LEVELS.index(rule.target_level)
            
            if source_index <= level_index and target_index >= level_index:
                relevant_rules.append(rule)
        
        # Sort by priority (highest first)
        relevant_rules.sort(key=lambda r: r.priority, reverse=True)
        
        # Resolve assets from parent contexts
        resolved_assets = {}
        
        # Process inheritance from parent contexts
        if context.parent_context:
            parent_assets = self.resolve_assets(
                project_id,
                context.parent_context.level,
                context.parent_context.level_id
            )
            
            for asset_key, parent_asset in parent_assets.items():
                resolved_assets[asset_key] = AssetReference(
                    asset_id=parent_asset.asset_id,
                    asset_type=parent_asset.asset_type,
                    level=level,
                    level_id=level_id,
                    source_level=parent_asset.source_level,
                    source_id=parent_asset.source_id,
                    inherited=True
                )
        
        # Apply local assets (overrides)
        for local_asset in context.local_assets:
            asset_key = f"{local_asset.asset_type.value}:{local_asset.asset_id}"
            
            # Check if this asset should override inherited ones
            should_override = True
            for rule in relevant_rules:
                if (rule.asset_type == local_asset.asset_type and
                    rule.target_level == level):
                    if rule.propagation_mode == "override":
                        should_override = True
                        break
                    elif rule.propagation_mode == "block":
                        should_override = False
                        break
            
            if should_override:
                local_copy = local_asset.model_copy()
                local_copy.level = level
                local_copy.level_id = level_id
                resolved_assets[asset_key] = local_copy
        
        context.resolved_assets = resolved_assets
        return resolved_assets
    
    def get_asset_for_level(self, project_id: str, level: str, level_id: str, 
                          asset_type: AssetType, asset_id: str) -> Optional[AssetReference]:
        """Get a specific asset for a given level, resolving inheritance."""
        resolved_assets = self.resolve_assets(project_id, level, level_id)
        asset_key = f"{asset_type.value}:{asset_id}"
        return resolved_assets.get(asset_key)
    
    def get_all_assets_for_level(self, project_id: str, level: str, level_id: str) -> Dict[str, List[AssetReference]]:
        """Get all assets grouped by type for a specific level."""
        resolved_assets = self.resolve_assets(project_id, level, level_id)
        
        grouped_assets = {}
        for asset_type in AssetType:
            typed_assets = [asset for asset in resolved_assets.values() 
                           if asset.asset_type == asset_type]
            if typed_assets:
                grouped_assets[asset_type.value] = typed_assets
        
        return grouped_assets
    
    def track_asset_usage(self, project_id: str, asset_id: str, 
                         level: str, level_id: str, usage_context: Dict[str, Any] = None) -> None:
        """Track where an asset is being used."""
        usage_file = self.propagation_dir / "asset_usage.json"
        
        usage_data = {}
        if usage_file.exists():
            with open(usage_file) as f:
                usage_data = json.load(f)
        
        if project_id not in usage_data:
            usage_data[project_id] = {}
        
        if asset_id not in usage_data[project_id]:
            usage_data[project_id][asset_id] = []
        
        usage_entry = {
            "level": level,
            "level_id": level_id,
            "usage_context": usage_context or {},
            "timestamp": datetime.now().isoformat()
        }
        
        usage_data[project_id][asset_id].append(usage_entry)
        
        with open(usage_file, 'w') as f:
            json.dump(usage_data, f, indent=2, default=str)
    
    def get_asset_usage(self, project_id: str, asset_id: str) -> List[Dict[str, Any]]:
        """Get all usage instances for a specific asset."""
        usage_file = self.propagation_dir / "asset_usage.json"
        
        if not usage_file.exists():
            return []
        
        with open(usage_file) as f:
            usage_data = json.load(f)
        
        return usage_data.get(project_id, {}).get(asset_id, [])
    
    def validate_asset_consistency(self, project_id: str) -> Dict[str, Any]:
        """Validate asset consistency across the project."""
        validation_results = {
            "project_id": project_id,
            "consistent": True,
            "issues": [],
            "warnings": [],
            "statistics": {}
        }
        
        # Check for missing assets
        for context_key, context in self.contexts.items():
            if not context_key.startswith(f"{project_id}:"):
                continue
                
            resolved_assets = self.resolve_assets(project_id, context.level, context.level_id)
            
            for asset_key, asset_ref in resolved_assets.items():
                # TODO: Check if asset actually exists in asset registry
                # For now, just check basic consistency
                if asset_ref.source_level not in self.HIERARCHY_LEVELS:
                    validation_results["issues"].append({
                        "type": "invalid_source_level",
                        "asset_id": asset_ref.asset_id,
                        "source_level": asset_ref.source_level,
                        "context": f"{context.level}:{context.level_id}"
                    })
                    validation_results["consistent"] = False
        
        # Generate usage statistics
        usage_stats = {}
        for asset_type in AssetType:
            usage_stats[asset_type.value] = len([
                asset for contexts in self.contexts.values()
                for asset in contexts.resolved_assets.values()
                if asset.asset_type == asset_type
            ])
        
        validation_results["statistics"] = usage_stats
        
        return validation_results
    
    def export_propagation_state(self, project_id: str) -> Dict[str, Any]:
        """Export the complete propagation state for a project."""
        export_data = {
            "project_id": project_id,
            "timestamp": datetime.now().isoformat(),
            "contexts": {},
            "rules": [rule.model_dump() for rule in self.rules],
            "validation": self.validate_asset_consistency(project_id)
        }
        
        for context_key, context in self.contexts.items():
            if context_key.startswith(f"{project_id}:"):
                export_data["contexts"][context_key] = {
                    "level": context.level,
                    "level_id": context.level_id,
                    "local_assets": [asset.model_dump() for asset in context.local_assets],
                    "resolved_assets": {k: v.model_dump() for k, v in context.resolved_assets.items()}
                }
        
        return export_data
    
    def save_state(self, project_id: str) -> None:
        """Save the propagation state to file."""
        state_file = self.propagation_dir / f"{project_id}_propagation_state.json"
        export_data = self.export_propagation_state(project_id)
        
        with open(state_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
    
    def load_state(self, project_id: str) -> None:
        """Load propagation state from file."""
        state_file = self.propagation_dir / f"{project_id}_propagation_state.json"
        
        if not state_file.exists():
            return
        
        with open(state_file) as f:
            state_data = json.load(f)
        
        # Load contexts
        for context_key, context_data in state_data.get("contexts", {}).items():
            parts = context_key.split(":")
            if len(parts) >= 3:
                project, level, level_id = parts[0], parts[1], ":".join(parts[2:])
                
                if project == project_id:
                    context = self.create_context(project, level, level_id)
                    
                    # Load local assets
                    for asset_data in context_data.get("local_assets", []):
                        asset_ref = AssetReference(**asset_data)
                        context.local_assets.append(asset_ref)
        
        # Load rules
        self._load_rules()


class AssetResolver:
    """Utility for resolving assets for generative processes."""
    
    def __init__(self, propagation_service: AssetPropagationService):
        self.propagation_service = propagation_service
    
    def resolve_for_generation(self, project_id: str, level: str, level_id: str) -> Dict[str, Any]:
        """
        Resolve all assets needed for generation at a specific level.
        
        Returns a structured dict suitable for generative prompts.
        """
        resolved_assets = self.propagation_service.resolve_assets(project_id, level, level_id)
        
        generation_context = {
            "characters": [],
            "styles": [],
            "locations": [],
            "props": [],
            "wardrobe": [],
            "vehicles": [],
            "set_dressing": [],
            "sfx": [],
            "sounds": [],
            "music": []
        }
        
        # Group assets by type for generation
        for asset_ref in resolved_assets.values():
            asset_data = {
                "id": asset_ref.asset_id,
                "type": asset_ref.asset_type.value,
                "override_data": asset_ref.override_data,
                "context": asset_ref.usage_context
            }
            
            type_key = asset_ref.asset_type.value
            if type_key in generation_context:
                generation_context[type_key].append(asset_data)
        
        # Add metadata
        generation_context["metadata"] = {
            "project_id": project_id,
            "level": level,
            "level_id": level_id,
            "resolved_at": datetime.now().isoformat()
        }
        
        return generation_context
    
    def get_asset_dependencies(self, project_id: str, asset_id: str) -> List[str]:
        """Get all levels that depend on a specific asset."""
        usage = self.propagation_service.get_asset_usage(project_id, asset_id)
        return [f"{usage_entry['level']}:{usage_entry['level_id']}" 
                for usage_entry in usage]
    
    def check_asset_consistency(self, project_id: str, asset_id: str) -> Dict[str, Any]:
        """Check if an asset is used consistently across the project."""
        usage = self.propagation_service.get_asset_usage(project_id, asset_id)
        
        consistency_report = {
            "asset_id": asset_id,
            "usage_count": len(usage),
            "levels": list(set([entry['level'] for entry in usage])),
            "consistent": True,
            "issues": []
        }
        
        # Check for potential consistency issues
        if len(usage) > 1:
            # Look for override conflicts
            overrides = [entry for entry in usage if entry.get('usage_context', {}).get('override_data')]
            if overrides:
                consistency_report["warnings"] = [f"Asset has overrides in {len(overrides)} locations"]
        
        return consistency_report