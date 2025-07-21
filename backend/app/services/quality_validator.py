"""
Quality Configuration Validator

Validates quality tier configurations and ensures workflow availability.
Provides validation for fixed quality-to-workflow mappings.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Tuple
import logging

logger = logging.getLogger(__name__)

class QualityValidator:
    """
    Validates quality tier configurations and workflow mappings.
    
    Ensures that all quality tiers have valid configurations and that
    referenced workflows exist and are properly structured.
    """
    
    def __init__(self, workflows_root: str, config_path: str):
        """
        Initialize quality validator.
        
        Args:
            workflows_root: Root directory for ComfyUI workflows
            config_path: Path to quality mappings configuration
        """
        self.workflows_root = Path(workflows_root)
        self.config_path = Path(config_path)
        self.validation_report = {}
    
    def validate_all(self) -> Dict[str, Any]:
        """
        Perform complete validation of quality configuration.
        
        Returns:
            Comprehensive validation report
        """
        report = {
            'valid': True,
            'config_valid': False,
            'workflows_valid': False,
            'issues': [],
            'warnings': [],
            'summary': {
                'total_task_types': 0,
                'total_mappings': 0,
                'valid_mappings': 0,
                'missing_workflows': 0,
                'invalid_parameters': 0
            }
        }
        
        # Validate configuration file
        config_report = self._validate_configuration()
        report.update(config_report)
        
        if report['config_valid']:
            # Validate workflow files
            workflow_report = self._validate_workflows()
            report.update(workflow_report)
        
        # Determine overall validity
        report['valid'] = report['config_valid'] and report['workflows_valid']
        
        self.validation_report = report
        return report
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate YAML configuration structure and content."""
        
        report = {
            'config_valid': False,
            'config_issues': [],
            'config_warnings': []
        }
        
        if not self.config_path.exists():
            report['config_issues'].append(f"Configuration file not found: {self.config_path}")
            return report
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception as e:
            report['config_issues'].append(f"Failed to load configuration: {e}")
            return report
        
        # Validate basic structure
        if not isinstance(config, dict):
            report['config_issues'].append("Configuration must be a YAML dictionary")
            return report
        
        if 'version' not in config:
            report['config_warnings'].append("Missing 'version' field")
        
        if 'mappings' not in config:
            report['config_issues'].append("Missing 'mappings' section")
            return report
        
        mappings = config.get('mappings', {})
        if not isinstance(mappings, dict):
            report['config_issues'].append("'mappings' must be a dictionary")
            return report
        
        # Validate each task type mapping
        total_mappings = 0
        valid_mappings = 0
        
        for task_type, tiers in mappings.items():
            if not isinstance(tiers, dict):
                report['config_issues'].append(
                    f"Task type '{task_type}' must contain tier mappings"
                )
                continue
            
            for tier_name, tier_config in tiers.items():
                total_mappings += 1
                
                # Validate tier name
                if tier_name not in ['low', 'standard', 'high']:
                    report['config_warnings'].append(
                        f"Unusual tier name '{tier_name}' for task '{task_type}'"
                    )
                
                # Validate required fields
                required_fields = ['workflow_path', 'description', 'parameters']
                missing_fields = [
                    f for f in required_fields 
                    if f not in tier_config
                ]
                
                if missing_fields:
                    report['config_issues'].append(
                        f"Task '{task_type}', tier '{tier_name}': Missing fields {missing_fields}"
                    )
                    continue
                
                # Validate workflow path format
                workflow_path = tier_config.get('workflow_path')
                if not workflow_path or not isinstance(workflow_path, str):
                    report['config_issues'].append(
                        f"Task '{task_type}', tier '{tier_name}': Invalid workflow_path"
                    )
                    continue
                
                # Validate parameters
                parameters = tier_config.get('parameters', {})
                if not isinstance(parameters, dict):
                    report['config_issues'].append(
                        f"Task '{task_type}', tier '{tier_name}': Parameters must be a dictionary"
                    )
                    continue
                
                valid_mappings += 1
        
        report['config_valid'] = len(report['config_issues']) == 0
        report['summary'] = {
            'total_task_types': len(mappings),
            'total_mappings': total_mappings,
            'valid_mappings': valid_mappings
        }
        
        return report
    
    def _validate_workflows(self) -> Dict[str, Any]:
        """Validate that referenced workflow files exist and are valid."""
        
        report = {
            'workflows_valid': False,
            'workflow_issues': [],
            'workflow_warnings': []
        }
        
        if not self.config_path.exists():
            report['workflow_issues'].append("Cannot validate workflows without valid configuration")
            return report
        
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except Exception:
            report['workflow_issues'].append("Cannot validate workflows with invalid configuration")
            return report
        
        mappings = config.get('mappings', {})
        missing_workflows = 0
        invalid_manifests = 0
        
        for task_type, tiers in mappings.items():
            for tier_name, tier_config in tiers.items():
                workflow_path = tier_config.get('workflow_path')
                if not workflow_path:
                    continue
                
                # Construct full path
                full_path = self.workflows_root / workflow_path
                
                # Check if directory exists
                if not full_path.exists():
                    missing_workflows += 1
                    report['workflow_issues'].append(
                        f"Missing workflow directory: {full_path}"
                    )
                    continue
                
                # Check for required files
                required_files = ['workflow_api.json', 'manifest.yaml']
                for req_file in required_files:
                    file_path = full_path / req_file
                    if not file_path.exists():
                        report['workflow_issues'].append(
                            f"Missing {req_file} in {full_path}"
                        )
                        invalid_manifests += 1
                
                # Validate manifest if it exists
                manifest_path = full_path / 'manifest.yaml'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as mf:
                            manifest = yaml.safe_load(mf)
                        
                        # Basic manifest validation
                        if not isinstance(manifest, dict):
                            report['workflow_issues'].append(
                                f"Invalid manifest format in {full_path}"
                            )
                        elif 'metadata' not in manifest:
                            report['workflow_warnings'].append(
                                f"Manifest missing metadata in {full_path}"
                            )
                    
                    except Exception as e:
                        report['workflow_issues'].append(
                            f"Failed to read manifest in {full_path}: {e}"
                        )
        
        report['workflows_valid'] = (
            len(report['workflow_issues']) == 0 and 
            missing_workflows == 0 and 
            invalid_manifests == 0
        )
        
        report['summary'].update({
            'missing_workflows': missing_workflows,
            'invalid_parameters': invalid_manifests
        })
        
        return report
    
    def validate_workflow_directory(self, workflow_path: str) -> Dict[str, Any]:
        """
        Validate a specific workflow directory.
        
        Args:
            workflow_path: Relative path to workflow directory
            
        Returns:
            Validation report for the specific workflow
        """
        full_path = self.workflows_root / workflow_path
        
        report = {
            'valid': True,
            'exists': full_path.exists(),
            'has_workflow_api': False,
            'has_manifest': False,
            'issues': []
        }
        
        if not report['exists']:
            report['valid'] = False
            report['issues'].append(f"Workflow directory does not exist: {full_path}")
            return report
        
        # Check for workflow API file
        workflow_api_path = full_path / 'workflow_api.json'
        report['has_workflow_api'] = workflow_api_path.exists()
        if not report['has_workflow_api']:
            report['valid'] = False
            report['issues'].append("Missing workflow_api.json")
        
        # Check for manifest file
        manifest_path = full_path / 'manifest.yaml'
        report['has_manifest'] = manifest_path.exists()
        if not report['has_manifest']:
            report['valid'] = False
            report['issues'].append("Missing manifest.yaml")
        
        # Validate manifest content
        if report['has_manifest']:
            try:
                with open(manifest_path, 'r') as mf:
                    manifest = yaml.safe_load(mf)
                
                if not isinstance(manifest, dict):
                    report['valid'] = False
                    report['issues'].append("Invalid manifest format")
                elif 'metadata' not in manifest:
                    report['issues'].append("Manifest missing metadata section")
            
            except Exception as e:
                report['valid'] = False
                report['issues'].append(f"Failed to read manifest: {e}")
        
        return report
    
    def generate_validation_report(self, output_path: str = None) -> str:
        """
        Generate a human-readable validation report.
        
        Args:
            output_path: Optional path to save report
            
        Returns:
            Formatted validation report as string
        """
        if not self.validation_report:
            self.validate_all()
        
        report = self.validation_report
        
        lines = [
            "Quality Configuration Validation Report",
            "=" * 40,
            "",
            f"Overall Status: {'✓ VALID' if report['valid'] else '✗ INVALID'}",
            "",
            "Summary:",
            f"  Total Task Types: {report['summary']['total_task_types']}",
            f"  Total Mappings: {report['summary']['total_mappings']}",
            f"  Valid Mappings: {report['summary']['valid_mappings']}",
            f"  Missing Workflows: {report['summary']['missing_workflows']}",
            f"  Invalid Parameters: {report['summary']['invalid_parameters']}",
            ""
        ]
        
        if report['issues']:
            lines.extend([
                "Issues:",
                *[f"  - {issue}" for issue in report['issues']],
                ""
            ])
        
        if report['warnings']:
            lines.extend([
                "Warnings:",
                *[f"  - {warning}" for warning in report['warnings']],
                ""
            ])
        
        report_text = "\n".join(lines)
        
        if output_path:
            with open(output_path, 'w') as f:
                f.write(report_text)
        
        return report_text