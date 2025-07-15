"""
Multi-stage Template Validation Pipeline

Provides comprehensive validation of function templates through multiple
validation stages with caching and detailed error reporting.
"""

import re
import asyncio
import hashlib
import json
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from cachetools import TTLCache
import jsonschema
from jsonschema import Draft7Validator
from packaging.version import Version, InvalidVersion

from .base import FunctionTemplate, ParameterType
from .exceptions import TemplateValidationError


class Severity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationIssue:
    """Single validation issue"""
    stage: str
    path: str
    message: str
    severity: Severity
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = {
            "stage": self.stage,
            "path": self.path,
            "message": self.message,
            "severity": self.severity.value
        }
        if self.suggestion:
            result["suggestion"] = self.suggestion
        return result


@dataclass
class StageResult:
    """Result from a single validation stage"""
    stage: str
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    duration_ms: float = 0
    
    def add_issue(self, path: str, message: str, severity: Severity, 
                  suggestion: Optional[str] = None):
        """Add validation issue"""
        issue = ValidationIssue(
            stage=self.stage,
            path=path,
            message=message,
            severity=severity,
            suggestion=suggestion
        )
        
        if severity == Severity.CRITICAL or severity == Severity.ERROR:
            self.errors.append(issue)
        elif severity == Severity.WARNING:
            self.warnings.append(issue)
        else:
            self.info.append(issue)
    
    def add_error(self, path: str, message: str, suggestion: Optional[str] = None):
        """Add error issue"""
        self.add_issue(path, message, Severity.ERROR, suggestion)
    
    def add_warning(self, path: str, message: str, suggestion: Optional[str] = None):
        """Add warning issue"""
        self.add_issue(path, message, Severity.WARNING, suggestion)
    
    def add_info(self, path: str, message: str, suggestion: Optional[str] = None):
        """Add info issue"""
        self.add_issue(path, message, Severity.INFO, suggestion)
    
    def has_critical_errors(self) -> bool:
        """Check if stage has critical errors"""
        return any(e.severity == Severity.CRITICAL for e in self.errors)


@dataclass
class ValidationResult:
    """Complete validation result"""
    template_id: Optional[str]
    version: Optional[str]
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    stages_completed: List[str] = field(default_factory=list)
    total_duration_ms: float = 0
    cached: bool = False
    
    def merge(self, stage_result: StageResult):
        """Merge stage result into overall result"""
        self.errors.extend(stage_result.errors)
        self.warnings.extend(stage_result.warnings)
        self.info.extend(stage_result.info)
        self.stages_completed.append(stage_result.stage)
        self.total_duration_ms += stage_result.duration_ms
    
    def is_valid(self) -> bool:
        """Check if validation passed"""
        return len(self.errors) == 0
    
    def get_summary(self) -> Dict[str, int]:
        """Get issue count summary"""
        return {
            "errors": len(self.errors),
            "warnings": len(self.warnings),
            "info": len(self.info),
            "critical": sum(1 for e in self.errors if e.severity == Severity.CRITICAL)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "valid": self.is_valid(),
            "template_id": self.template_id,
            "version": self.version,
            "errors": [e.to_dict() for e in self.errors],
            "warnings": [w.to_dict() for w in self.warnings],
            "info": [i.to_dict() for i in self.info],
            "stages_completed": self.stages_completed,
            "summary": self.get_summary(),
            "duration_ms": self.total_duration_ms,
            "cached": self.cached
        }


@dataclass
class ValidationContext:
    """Context for validation run"""
    strict_mode: bool = False
    check_uniqueness: bool = True
    check_dependencies: bool = True
    registry: Optional[Any] = None  # TemplateRegistry
    existing_templates: Optional[Dict[str, List[str]]] = None


class ValidationStage(ABC):
    """Base class for validation stages"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Run validation stage"""
        pass


class SchemaValidator(ValidationStage):
    """Validate template against JSON schema"""
    
    TEMPLATE_SCHEMA = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["template"],
        "properties": {
            "template": {
                "type": "object",
                "required": ["id", "name", "version", "interface", "requirements"],
                "properties": {
                    "id": {
                        "type": "string",
                        "pattern": "^[a-z0-9_]+$",
                        "minLength": 3,
                        "maxLength": 50
                    },
                    "name": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 100
                    },
                    "version": {
                        "type": "string",
                        "pattern": "^\\d+\\.\\d+\\.\\d+(-[a-zA-Z0-9]+)?$"
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 500
                    },
                    "category": {
                        "type": "string",
                        "enum": ["generation", "processing", "analysis", "utility"]
                    },
                    "author": {"type": "string"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    },
                    "interface": {"type": "object"},
                    "requirements": {"type": "object"},
                    "examples": {"type": "array"}
                }
            }
        }
    }
    
    def __init__(self):
        super().__init__("schema")
        self.validator = Draft7Validator(self.TEMPLATE_SCHEMA)
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Validate basic schema structure"""
        import time
        start_time = time.time()
        result = StageResult(stage=self.name)
        
        # Validate against JSON schema
        for error in self.validator.iter_errors(template_data):
            path = '.'.join(str(p) for p in error.path)
            severity = Severity.CRITICAL if error.validator == 'required' else Severity.ERROR
            
            # Add helpful suggestions
            suggestion = None
            if error.validator == 'pattern' and 'id' in path:
                suggestion = "Template ID must contain only lowercase letters, numbers, and underscores"
            elif error.validator == 'pattern' and 'version' in path:
                suggestion = "Version must follow semantic versioning (e.g., 1.0.0 or 1.0.0-beta)"
            
            result.add_issue(
                path=path,
                message=error.message,
                severity=severity,
                suggestion=suggestion
            )
        
        # Additional structural checks
        if 'template' in template_data:
            template = template_data['template']
            
            # Validate semantic version
            version = template.get('version', '')
            try:
                Version(version)
            except InvalidVersion:
                result.add_error(
                    'template.version',
                    f"Invalid semantic version: {version}",
                    "Use format like 1.0.0 or 2.1.3-beta"
                )
            
            # Check ID format
            template_id = template.get('id', '')
            if template_id and not re.match(r'^[a-z0-9_]+$', template_id):
                result.add_error(
                    'template.id',
                    'ID contains invalid characters',
                    'Use only lowercase letters, numbers, and underscores'
                )
            
            # Warn about missing optional fields
            if 'description' not in template:
                result.add_info(
                    'template.description',
                    'Consider adding a description for better documentation'
                )
            
            if 'tags' not in template:
                result.add_info(
                    'template.tags',
                    'Consider adding tags for better discoverability'
                )
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result


class TypeValidator(ValidationStage):
    """Validate parameter types and constraints"""
    
    VALID_TYPES = {'string', 'integer', 'float', 'boolean', 'array', 'object', 'file'}
    
    TYPE_CONSTRAINTS = {
        'string': ['min_length', 'max_length', 'pattern', 'enum', 'format'],
        'integer': ['min', 'max', 'enum', 'multiple_of'],
        'float': ['min', 'max', 'precision', 'enum'],
        'boolean': [],
        'array': ['min_items', 'max_items', 'unique_items', 'items'],
        'object': ['properties', 'required', 'additional_properties'],
        'file': ['format', 'max_size', 'mime_types', 'extensions']
    }
    
    def __init__(self):
        super().__init__("types")
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Validate input/output types and constraints"""
        import time
        start_time = time.time()
        result = StageResult(stage=self.name)
        
        interface = template_data.get('template', {}).get('interface', {})
        
        # Validate inputs
        for name, spec in interface.get('inputs', {}).items():
            self._validate_parameter(name, spec, 'input', result)
        
        # Validate outputs
        for name, spec in interface.get('outputs', {}).items():
            self._validate_parameter(name, spec, 'output', result)
        
        # Check for at least one output
        if not interface.get('outputs'):
            result.add_error(
                'template.interface.outputs',
                'Template must define at least one output'
            )
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result
    
    def _validate_parameter(self, name: str, spec: Dict, 
                           param_type: str, result: StageResult):
        """Validate individual parameter"""
        path_prefix = f"template.interface.{param_type}s.{name}"
        
        # Check parameter name format
        if not re.match(r'^[a-z][a-z0-9_]*$', name):
            result.add_error(
                path_prefix,
                f"Parameter name '{name}' must start with lowercase letter and contain only letters, numbers, and underscores"
            )
        
        # Check type
        type_value = spec.get('type')
        if not type_value:
            result.add_error(
                f"{path_prefix}.type",
                "Parameter must specify a type",
                f"Valid types: {', '.join(self.VALID_TYPES)}"
            )
            return
        
        if type_value not in self.VALID_TYPES:
            result.add_error(
                f"{path_prefix}.type",
                f"Invalid type '{type_value}'",
                f"Valid types: {', '.join(self.VALID_TYPES)}"
            )
            return
        
        # Check constraints are valid for type
        valid_constraints = self.TYPE_CONSTRAINTS.get(type_value, [])
        for constraint, value in spec.items():
            if constraint in ['type', 'description', 'required', 'default']:
                continue
            
            if constraint not in valid_constraints:
                result.add_warning(
                    f"{path_prefix}.{constraint}",
                    f"Constraint '{constraint}' is not applicable to type '{type_value}'",
                    f"Valid constraints for {type_value}: {', '.join(valid_constraints)}"
                )
        
        # Type-specific validations
        self._validate_type_constraints(name, spec, type_value, path_prefix, result)
        
        # Validate default value
        if 'default' in spec:
            self._validate_default_value(spec['default'], type_value, spec, path_prefix, result)
    
    def _validate_type_constraints(self, name: str, spec: Dict, type_value: str,
                                  path_prefix: str, result: StageResult):
        """Validate type-specific constraints"""
        
        # String constraints
        if type_value == 'string':
            if 'min_length' in spec and 'max_length' in spec:
                if spec['min_length'] > spec['max_length']:
                    result.add_error(
                        f"{path_prefix}.min_length",
                        "min_length cannot be greater than max_length"
                    )
            
            if 'pattern' in spec:
                try:
                    re.compile(spec['pattern'])
                except re.error as e:
                    result.add_error(
                        f"{path_prefix}.pattern",
                        f"Invalid regex pattern: {e}"
                    )
        
        # Numeric constraints
        elif type_value in ['integer', 'float']:
            if 'min' in spec and 'max' in spec:
                if spec['min'] > spec['max']:
                    result.add_error(
                        f"{path_prefix}.min",
                        "min value cannot be greater than max value"
                    )
            
            if type_value == 'integer' and 'multiple_of' in spec:
                if spec['multiple_of'] <= 0:
                    result.add_error(
                        f"{path_prefix}.multiple_of",
                        "multiple_of must be positive"
                    )
        
        # Array constraints
        elif type_value == 'array':
            if 'min_items' in spec and 'max_items' in spec:
                if spec['min_items'] > spec['max_items']:
                    result.add_error(
                        f"{path_prefix}.min_items",
                        "min_items cannot be greater than max_items"
                    )
        
        # File constraints
        elif type_value == 'file':
            if 'max_size' in spec and spec['max_size'] <= 0:
                result.add_error(
                    f"{path_prefix}.max_size",
                    "max_size must be positive"
                )
            
            if 'format' in spec and not isinstance(spec['format'], list):
                result.add_error(
                    f"{path_prefix}.format",
                    "format must be a list of file extensions"
                )
        
        # Enum validation
        if 'enum' in spec:
            if not isinstance(spec['enum'], list) or len(spec['enum']) == 0:
                result.add_error(
                    f"{path_prefix}.enum",
                    "enum must be a non-empty list"
                )
            elif len(set(spec['enum'])) != len(spec['enum']):
                result.add_error(
                    f"{path_prefix}.enum",
                    "enum values must be unique"
                )
    
    def _validate_default_value(self, default: Any, type_value: str, spec: Dict,
                               path_prefix: str, result: StageResult):
        """Validate default value matches type and constraints"""
        
        # Type checking
        type_check = {
            'string': lambda x: isinstance(x, str),
            'integer': lambda x: isinstance(x, int) and not isinstance(x, bool),
            'float': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
            'boolean': lambda x: isinstance(x, bool),
            'array': lambda x: isinstance(x, list),
            'object': lambda x: isinstance(x, dict),
            'file': lambda x: x is None  # Files can't have defaults
        }
        
        if type_value in type_check and not type_check[type_value](default):
            result.add_error(
                f"{path_prefix}.default",
                f"Default value type does not match parameter type '{type_value}'"
            )
            return
        
        # Constraint checking
        if 'enum' in spec and default not in spec['enum']:
            result.add_error(
                f"{path_prefix}.default",
                "Default value must be one of the enum values"
            )
        
        if type_value == 'string':
            if 'min_length' in spec and len(default) < spec['min_length']:
                result.add_error(
                    f"{path_prefix}.default",
                    f"Default value length ({len(default)}) is less than min_length ({spec['min_length']})"
                )
            if 'max_length' in spec and len(default) > spec['max_length']:
                result.add_error(
                    f"{path_prefix}.default",
                    f"Default value length ({len(default)}) exceeds max_length ({spec['max_length']})"
                )
            if 'pattern' in spec:
                try:
                    if not re.match(spec['pattern'], default):
                        result.add_error(
                            f"{path_prefix}.default",
                            "Default value does not match pattern constraint"
                        )
                except re.error:
                    pass  # Already validated pattern above
        
        elif type_value in ['integer', 'float']:
            if 'min' in spec and default < spec['min']:
                result.add_error(
                    f"{path_prefix}.default",
                    f"Default value ({default}) is less than min ({spec['min']})"
                )
            if 'max' in spec and default > spec['max']:
                result.add_error(
                    f"{path_prefix}.default",
                    f"Default value ({default}) exceeds max ({spec['max']})"
                )


class ResourceValidator(ValidationStage):
    """Validate resource requirements"""
    
    def __init__(self):
        super().__init__("resources")
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Validate resource specifications"""
        import time
        start_time = time.time()
        result = StageResult(stage=self.name)
        
        requirements = template_data.get('template', {}).get('requirements', {})
        resources = requirements.get('resources', {})
        
        # Check basic resource requirements
        if not resources:
            result.add_error(
                'template.requirements.resources',
                'Resource requirements must be specified'
            )
            return result
        
        # Validate GPU requirements
        if resources.get('gpu', False):
            vram = resources.get('vram_gb', 0)
            if vram <= 0:
                result.add_error(
                    'template.requirements.resources.vram_gb',
                    'GPU templates must specify positive VRAM requirements'
                )
            elif vram > 80:  # Current max datacenter GPU VRAM
                result.add_warning(
                    'template.requirements.resources.vram_gb',
                    f'VRAM requirement of {vram}GB exceeds typical hardware',
                    'Consider if this requirement is necessary'
                )
            elif vram > 24:  # Typical high-end consumer GPU
                result.add_info(
                    'template.requirements.resources.vram_gb',
                    f'VRAM requirement of {vram}GB requires professional/datacenter GPUs'
                )
        
        # Validate CPU requirements
        cpu_cores = resources.get('cpu_cores', 0)
        if cpu_cores < 1:
            result.add_error(
                'template.requirements.resources.cpu_cores',
                'CPU cores must be at least 1'
            )
        elif cpu_cores > 128:
            result.add_warning(
                'template.requirements.resources.cpu_cores',
                f'CPU requirement of {cpu_cores} cores is unusually high'
            )
        
        # Validate memory requirements
        memory_gb = resources.get('memory_gb', 0)
        if memory_gb <= 0:
            result.add_error(
                'template.requirements.resources.memory_gb',
                'Memory requirement must be positive'
            )
        elif memory_gb > 1024:
            result.add_warning(
                'template.requirements.resources.memory_gb',
                f'Memory requirement of {memory_gb}GB is unusually high'
            )
        
        # Validate disk requirements
        if 'disk_gb' in resources:
            disk_gb = resources['disk_gb']
            if disk_gb < 0:
                result.add_error(
                    'template.requirements.resources.disk_gb',
                    'Disk requirement cannot be negative'
                )
            elif disk_gb > 1000:
                result.add_warning(
                    'template.requirements.resources.disk_gb',
                    f'Disk requirement of {disk_gb}GB is very large'
                )
        
        # Validate model requirements
        if 'models' in requirements:
            self._validate_models(requirements['models'], result)
        
        # Validate quality presets
        if 'quality_presets' in requirements:
            self._validate_quality_presets(
                requirements['quality_presets'],
                template_data.get('template', {}).get('interface', {}).get('inputs', {}),
                result
            )
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result
    
    def _validate_models(self, models: List[Dict], result: StageResult):
        """Validate model requirements"""
        seen_models = set()
        
        for i, model in enumerate(models):
            path_prefix = f"template.requirements.models[{i}]"
            
            # Check for duplicates
            model_id = f"{model.get('name')}:{model.get('type')}"
            if model_id in seen_models:
                result.add_error(
                    path_prefix,
                    f"Duplicate model definition: {model_id}"
                )
            seen_models.add(model_id)
            
            # Validate size
            size_gb = model.get('size_gb', 0)
            if size_gb <= 0:
                result.add_error(
                    f"{path_prefix}.size_gb",
                    'Model size must be positive'
                )
            elif size_gb > 100:
                result.add_warning(
                    f"{path_prefix}.size_gb",
                    f'Model size of {size_gb}GB is very large',
                    'Ensure users have sufficient disk space'
                )
            
            # Validate hash if provided
            if 'hash' in model:
                hash_value = model['hash']
                if not re.match(r'^[a-fA-F0-9]{64}$', hash_value):
                    result.add_error(
                        f"{path_prefix}.hash",
                        'Model hash must be a valid SHA256 hash'
                    )
    
    def _validate_quality_presets(self, presets: Dict, inputs: Dict, result: StageResult):
        """Validate quality preset configurations"""
        
        # If template has quality input with enum, validate preset names match
        if 'quality' in inputs and 'enum' in inputs['quality']:
            valid_qualities = inputs['quality']['enum']
            
            for preset_name in presets:
                if preset_name not in valid_qualities:
                    result.add_error(
                        f"template.requirements.quality_presets.{preset_name}",
                        f"Quality preset '{preset_name}' not in quality input enum values",
                        f"Valid values: {', '.join(valid_qualities)}"
                    )
        
        # Validate resource multipliers if specified
        for preset_name, preset_config in presets.items():
            if isinstance(preset_config, dict):
                if 'resource_multiplier' in preset_config:
                    multiplier = preset_config['resource_multiplier']
                    if not isinstance(multiplier, (int, float)) or multiplier <= 0:
                        result.add_error(
                            f"template.requirements.quality_presets.{preset_name}.resource_multiplier",
                            'Resource multiplier must be a positive number'
                        )
                    elif multiplier > 10:
                        result.add_warning(
                            f"template.requirements.quality_presets.{preset_name}.resource_multiplier",
                            f'Resource multiplier of {multiplier}x is very high'
                        )


class ExampleValidator(ValidationStage):
    """Validate template examples"""
    
    def __init__(self):
        super().__init__("examples")
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Validate example inputs against template schema"""
        import time
        start_time = time.time()
        result = StageResult(stage=self.name)
        
        template = template_data.get('template', {})
        examples = template.get('examples', [])
        
        if not examples:
            result.add_info(
                'template.examples',
                'No examples provided',
                'Consider adding examples for better documentation'
            )
            return result
        
        # Create template instance for validation
        try:
            temp_template = FunctionTemplate(template_data)
        except Exception as e:
            result.add_error(
                'template',
                f'Cannot create template for example validation: {str(e)}',
                severity=Severity.CRITICAL
            )
            return result
        
        # Validate each example
        seen_names = set()
        for idx, example in enumerate(examples):
            example_path = f"template.examples[{idx}]"
            
            # Check example structure
            if 'name' not in example:
                result.add_error(
                    f"{example_path}.name",
                    'Example must have a name'
                )
            else:
                # Check for duplicate names
                name = example['name']
                if name in seen_names:
                    result.add_error(
                        f"{example_path}.name",
                        f"Duplicate example name: '{name}'"
                    )
                seen_names.add(name)
            
            if 'inputs' not in example:
                result.add_error(
                    f"{example_path}.inputs",
                    'Example must have inputs'
                )
                continue
            
            # Validate example inputs
            try:
                validated_inputs = temp_template.validate_inputs(example['inputs'])
                
                # Check if all required inputs are provided
                input_spec = template.get('interface', {}).get('inputs', {})
                for param_name, param_def in input_spec.items():
                    if param_def.get('required', False) and param_name not in example['inputs']:
                        result.add_error(
                            f"{example_path}.inputs.{param_name}",
                            f"Example missing required input: '{param_name}'"
                        )
                
            except Exception as e:
                result.add_error(
                    f"{example_path}.inputs",
                    f'Example inputs validation failed: {str(e)}'
                )
            
            # Warn about unknown inputs
            if 'inputs' in example:
                input_spec = template.get('interface', {}).get('inputs', {})
                for input_name in example['inputs']:
                    if input_name not in input_spec:
                        result.add_warning(
                            f"{example_path}.inputs.{input_name}",
                            f"Example has unknown input: '{input_name}'"
                        )
            
            # Info about expected output
            if 'expected_output' in example:
                result.add_info(
                    f"{example_path}.expected_output",
                    'Expected output provided for testing'
                )
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result


class DependencyValidator(ValidationStage):
    """Validate template dependencies and inheritance"""
    
    def __init__(self):
        super().__init__("dependencies")
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Check for circular dependencies in template inheritance"""
        import time
        start_time = time.time()
        result = StageResult(stage=self.name)
        
        if not context.check_dependencies:
            result.add_info(
                'dependencies',
                'Dependency validation skipped'
            )
            return result
        
        template = template_data.get('template', {})
        
        # Check extends/inherits field if present
        if 'extends' in template:
            parent_id = template['extends']
            
            if context.registry:
                try:
                    # Check if parent exists
                    parent = context.registry.get_template(parent_id)
                    
                    # Check for circular dependencies
                    visited = {template['id']}
                    current = parent
                    
                    while hasattr(current, 'extends') and current.extends:
                        if current.id in visited:
                            result.add_error(
                                'template.extends',
                                f"Circular dependency detected: {' -> '.join(visited)} -> {current.id}",
                                severity=Severity.CRITICAL
                            )
                            break
                        visited.add(current.id)
                        current = context.registry.get_template(current.extends)
                        
                except Exception as e:
                    result.add_error(
                        'template.extends',
                        f"Cannot resolve parent template '{parent_id}': {str(e)}"
                    )
            else:
                result.add_warning(
                    'template.extends',
                    'Cannot validate parent template without registry access'
                )
        
        # Check model dependencies
        if 'requirements' in template and 'models' in template['requirements']:
            for i, model in enumerate(template['requirements']['models']):
                if 'depends_on' in model:
                    for dep in model['depends_on']:
                        # Just check format for now
                        if not isinstance(dep, str):
                            result.add_error(
                                f"template.requirements.models[{i}].depends_on",
                                'Model dependencies must be strings'
                            )
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result


class UniquenessValidator(ValidationStage):
    """Validate template ID and version uniqueness"""
    
    def __init__(self):
        super().__init__("uniqueness")
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext) -> StageResult:
        """Ensure unique template ID and version combinations"""
        import time
        start_time = time.time()
        result = StageResult(stage=self.name)
        
        if not context.check_uniqueness:
            result.add_info(
                'uniqueness',
                'Uniqueness validation skipped'
            )
            return result
        
        template = template_data.get('template', {})
        template_id = template.get('id')
        version = template.get('version')
        
        if not template_id or not version:
            return result  # Schema validation will catch this
        
        # Check against registry
        if context.registry:
            try:
                existing = context.registry.get_template(template_id, version)
                if existing:
                    result.add_error(
                        'template',
                        f"Template '{template_id}' version '{version}' already exists",
                        'Use a different version number or template ID',
                        severity=Severity.CRITICAL
                    )
            except:
                # Template doesn't exist, which is good
                pass
        
        # Check against provided existing templates
        if context.existing_templates:
            if template_id in context.existing_templates:
                if version in context.existing_templates[template_id]:
                    result.add_error(
                        'template',
                        f"Template '{template_id}' version '{version}' already exists",
                        severity=Severity.CRITICAL
                    )
        
        result.duration_ms = (time.time() - start_time) * 1000
        return result


class TemplateValidationPipeline:
    """Multi-stage validation pipeline for templates"""
    
    def __init__(self, cache_size: int = 1000, cache_ttl: int = 3600):
        """
        Initialize validation pipeline.
        
        Args:
            cache_size: Maximum number of cached results
            cache_ttl: Cache time-to-live in seconds
        """
        self.stages = [
            SchemaValidator(),
            TypeValidator(),
            ResourceValidator(),
            ExampleValidator(),
            DependencyValidator(),
            UniquenessValidator()
        ]
        self.cache = TTLCache(maxsize=cache_size, ttl=cache_ttl)
    
    def _get_cache_key(self, template_data: Dict[str, Any]) -> str:
        """Generate cache key for template data"""
        # Create a stable hash of the template data
        json_str = json.dumps(template_data, sort_keys=True)
        return hashlib.sha256(json_str.encode()).hexdigest()
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: Optional[ValidationContext] = None) -> ValidationResult:
        """
        Run full validation pipeline.
        
        Args:
            template_data: Template definition to validate
            context: Optional validation context
            
        Returns:
            ValidationResult with all issues found
        """
        if context is None:
            context = ValidationContext()
        
        # Check cache
        cache_key = self._get_cache_key(template_data)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            cached_result.cached = True
            return cached_result
        
        # Initialize result
        template = template_data.get('template', {})
        result = ValidationResult(
            template_id=template.get('id'),
            version=template.get('version')
        )
        
        # Run validation stages
        for stage in self.stages:
            try:
                stage_result = await stage.validate(template_data, context)
                result.merge(stage_result)
                
                # Stop on critical errors
                if stage_result.has_critical_errors():
                    break
                
            except Exception as e:
                result.errors.append(ValidationIssue(
                    stage=stage.name,
                    path='',
                    message=f"Validation stage failed: {str(e)}",
                    severity=Severity.CRITICAL
                ))
                break
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
    
    async def validate_batch(self, template_files: List[Path], 
                           context: Optional[ValidationContext] = None) -> Dict[str, ValidationResult]:
        """
        Validate multiple template files.
        
        Args:
            template_files: List of template file paths
            context: Optional validation context
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        import yaml
        
        results = {}
        
        for file_path in template_files:
            try:
                with open(file_path, 'r') as f:
                    template_data = yaml.safe_load(f)
                
                result = await self.validate(template_data, context)
                results[str(file_path)] = result
                
            except Exception as e:
                # Create error result for file loading failure
                results[str(file_path)] = ValidationResult(
                    template_id=None,
                    version=None,
                    errors=[ValidationIssue(
                        stage='loading',
                        path='',
                        message=f"Failed to load template file: {str(e)}",
                        severity=Severity.CRITICAL
                    )]
                )
        
        return results