"""
Quality Configuration Manager

Provides fixed quality-to-workflow mappings for the three-tier quality system.
Maps user-selected quality tiers (Low/Standard/High) directly to predefined workflows.
"""

import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)

class QualityConfigManager:
    """
    Manages fixed quality tier mappings to workflows.
    
    Provides direct mapping from quality tier selection to specific workflow paths
    without resource analysis or dynamic routing.
    """
    
    def __init__(self, config_path: str):
        """
        Initialize quality configuration manager.
        
        Args:
            config_path: Path to YAML configuration file
        """
        self.config_path = Path(config_path)
        self.config_data = {}
        self._load_configuration()
    
    def _load_configuration(self) -> None:
        """Load quality configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    self.config_data = yaml.safe_load(f) or {}
                    logger.info(f"Loaded quality configuration from {self.config_path}")
            else:
                logger.warning(f"Configuration file not found: {self.config_path}")
                self.config_data = {"version": "1.0", "mappings": {}}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config_data = {"version": "1.0", "mappings": {}}
    
    def get_workflow_path(self, task_type: str, quality_tier: str) -> Optional[str]:
        """
        Get fixed workflow path for task type and quality tier.
        
        Args:
            task_type: Type of generation task (e.g., 'character_portrait')
            quality_tier: Quality tier ('low', 'standard', 'high')
            
        Returns:
            Workflow path or None if not found
        """
        mappings = self.config_data.get('mappings', {})
        
        if task_type not in mappings:
            logger.warning(f"Task type not found: {task_type}")
            return None
        
        task_mappings = mappings[task_type]
        
        if quality_tier not in task_mappings:
            logger.warning(f"Quality tier not found: {quality_tier} for {task_type}")
            return None
        
        return task_mappings[quality_tier].get('workflow_path')
    
    def get_quality_config(self, task_type: str, quality_tier: str) -> Optional[Dict[str, Any]]:
        """
        Get complete quality configuration for task and tier.
        
        Args:
            task_type: Type of generation task
            quality_tier: Quality tier
            
        Returns:
            Complete configuration dict or None
        """
        mappings = self.config_data.get('mappings', {})
        
        if task_type not in mappings:
            return None
        
        task_mappings = mappings[task_type]
        
        if quality_tier not in task_mappings:
            return None
        
        return task_mappings[quality_tier]
    
    def get_available_tiers(self, task_type: str) -> List[str]:
        """
        Get available quality tiers for a task type.
        
        Args:
            task_type: Type of generation task
            
        Returns:
            List of available quality tiers
        """
        mappings = self.config_data.get('mappings', {})
        
        if task_type not in mappings:
            return []
        
        return list(mappings[task_type].keys())
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Validate all quality mappings exist and are properly configured.
        
        Returns:
            Validation report with status and issues
        """
        report = {
            'valid': True,
            'issues': [],
            'total_mappings': 0,
            'valid_mappings': 0
        }
        
        mappings = self.config_data.get('mappings', {})
        
        for task_type, tiers in mappings.items():
            for tier_name, config in tiers.items():
                report['total_mappings'] += 1
                
                # Check required fields
                required_fields = ['workflow_path', 'description', 'parameters']
                missing_fields = [f for f in required_fields if f not in config]
                
                if missing_fields:
                    report['issues'].append(
                        f"Task {task_type}, tier {tier_name}: Missing fields {missing_fields}"
                    )
                    report['valid'] = False
                    continue
                
                # Check workflow path exists
                workflow_path = config.get('workflow_path')
                if not workflow_path:
                    report['issues'].append(
                        f"Task {task_type}, tier {tier_name}: Missing workflow_path"
                    )
                    report['valid'] = False
                    continue
                
                report['valid_mappings'] += 1
        
        return report
    
    def get_all_configurations(self) -> Dict[str, Any]:
        """
        Get all quality configurations.
        
        Returns:
            Complete configuration data
        """
        return self.config_data
    
    def reload_configuration(self) -> None:
        """Reload configuration from file."""
        self._load_configuration()


class QualityTierMapper:
    """
    High-level mapper for quality tiers to workflows.
    
    Provides simple, fixed mapping without resource analysis or dynamic routing.
    """
    
    def __init__(self, config_manager: QualityConfigManager):
        """
        Initialize quality tier mapper.
        
        Args:
            config_manager: Quality configuration manager instance
        """
        self.config_manager = config_manager
    
    def map_to_workflow(self, task_type: str, quality_tier: str) -> Dict[str, Any]:
        """
        Map task type and quality tier to workflow configuration.
        
        Args:
            task_type: Type of generation task
            quality_tier: Selected quality tier
            
        Returns:
            Workflow configuration including path and parameters
            
        Raises:
            ValueError: If task type or quality tier is invalid
        """
        config = self.config_manager.get_quality_config(task_type, quality_tier)
        
        if not config:
            raise ValueError(
                f"No configuration found for task '{task_type}' with quality '{quality_tier}'"
            )
        
        return {
            'workflow_path': config['workflow_path'],
            'parameters': config['parameters'],
            'description': config['description'],
            'quality_tier': quality_tier,
            'task_type': task_type
        }
    
    def get_available_mappings(self) -> Dict[str, List[str]]:
        """
        Get all available task type to quality tier mappings.
        
        Returns:
            Dictionary mapping task types to available quality tiers
        """
        mappings = self.config_manager.get_all_configurations().get('mappings', {})
        
        return {
            task_type: list(tiers.keys())
            for task_type, tiers in mappings.items()
        }