"""
Template Validation System

Validates template definitions against schema and business rules.
"""

import jsonschema
from typing import Dict, List, Any
from packaging.version import Version, InvalidVersion

from .exceptions import TemplateValidationError


class TemplateValidator:
    """Validate template definitions"""
    
    # JSON Schema for template validation
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
                        "maxLength": 50,
                        "description": "Unique template identifier"
                    },
                    "name": {
                        "type": "string",
                        "minLength": 3,
                        "maxLength": 100,
                        "description": "Human-readable template name"
                    },
                    "version": {
                        "type": "string",
                        "pattern": "^\\d+\\.\\d+\\.\\d+$",
                        "description": "Semantic version"
                    },
                    "description": {
                        "type": "string",
                        "maxLength": 500
                    },
                    "category": {
                        "type": "string",
                        "enum": ["generation", "processing", "analysis", "utility"],
                        "default": "general"
                    },
                    "author": {
                        "type": "string"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "uniqueItems": True
                    },
                    "interface": {
                        "type": "object",
                        "properties": {
                            "inputs": {
                                "type": "object",
                                "patternProperties": {
                                    "^[a-z][a-z0-9_]*$": {
                                        "type": "object",
                                        "required": ["type"],
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": ["string", "integer", "float", "boolean", "array", "object", "file"]
                                            },
                                            "description": {"type": "string"},
                                            "required": {"type": "boolean", "default": False},
                                            "default": {},
                                            "min": {"type": "number"},
                                            "max": {"type": "number"},
                                            "min_length": {"type": "integer", "minimum": 0},
                                            "max_length": {"type": "integer", "minimum": 0},
                                            "pattern": {"type": "string"},
                                            "enum": {"type": "array", "minItems": 1, "uniqueItems": True},
                                            "format": {"type": "array", "items": {"type": "string"}}
                                        }
                                    }
                                }
                            },
                            "outputs": {
                                "type": "object",
                                "patternProperties": {
                                    "^[a-z][a-z0-9_]*$": {
                                        "type": "object",
                                        "required": ["type"],
                                        "properties": {
                                            "type": {
                                                "type": "string",
                                                "enum": ["string", "integer", "float", "boolean", "array", "object", "file"]
                                            },
                                            "description": {"type": "string"},
                                            "format": {"type": "array", "items": {"type": "string"}},
                                            "properties": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "requirements": {
                        "type": "object",
                        "required": ["resources"],
                        "properties": {
                            "resources": {
                                "type": "object",
                                "properties": {
                                    "gpu": {"type": "boolean", "default": False},
                                    "vram_gb": {"type": "number", "minimum": 0, "default": 0},
                                    "cpu_cores": {"type": "integer", "minimum": 1, "default": 1},
                                    "memory_gb": {"type": "number", "minimum": 0.5, "default": 2},
                                    "disk_gb": {"type": "number", "minimum": 0, "default": 10},
                                    "estimated_time_seconds": {"type": "number", "minimum": 0}
                                }
                            },
                            "models": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "required": ["name", "type", "size_gb"],
                                    "properties": {
                                        "name": {"type": "string"},
                                        "type": {"type": "string"},
                                        "size_gb": {"type": "number", "minimum": 0},
                                        "source": {"type": "string"},
                                        "hash": {"type": "string"}
                                    }
                                }
                            },
                            "quality_presets": {
                                "type": "object",
                                "patternProperties": {
                                    "^[a-z_]+$": {
                                        "type": "object"
                                    }
                                }
                            }
                        }
                    },
                    "examples": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "inputs"],
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"},
                                "inputs": {"type": "object"},
                                "expected_output": {"type": "object"}
                            }
                        }
                    }
                }
            }
        }
    }
    
    def __init__(self):
        """Initialize validator"""
        self.schema_validator = jsonschema.Draft7Validator(self.TEMPLATE_SCHEMA)
    
    def validate(self, definition: Dict[str, Any]) -> List[str]:
        """
        Validate template definition.
        
        Returns list of error messages, empty if valid.
        """
        errors = []
        
        # Schema validation
        for error in self.schema_validator.iter_errors(definition):
            path = '.'.join(str(p) for p in error.path)
            errors.append(f"Schema error at {path}: {error.message}")
        
        # If schema is valid, perform additional validation
        if not errors and 'template' in definition:
            template = definition['template']
            
            # Validate version format
            errors.extend(self._validate_version(template.get('version', '')))
            
            # Validate interface
            if 'interface' in template:
                errors.extend(self._validate_interface(template['interface']))
            
            # Validate examples
            if 'examples' in template and 'interface' in template:
                errors.extend(self._validate_examples(
                    template['examples'], 
                    template['interface']
                ))
            
            # Validate quality presets
            if 'requirements' in template and 'quality_presets' in template['requirements']:
                errors.extend(self._validate_quality_presets(
                    template['requirements']['quality_presets'],
                    template.get('interface', {}).get('inputs', {})
                ))
        
        return errors
    
    def _validate_version(self, version: str) -> List[str]:
        """Validate semantic version"""
        errors = []
        try:
            Version(version)
        except InvalidVersion:
            errors.append(f"Invalid semantic version: {version}")
        return errors
    
    def _validate_interface(self, interface: Dict[str, Any]) -> List[str]:
        """Validate interface definition"""
        errors = []
        
        inputs = interface.get('inputs', {})
        outputs = interface.get('outputs', {})
        
        # Check for at least one output
        if not outputs:
            errors.append("Interface must define at least one output")
        
        # Validate parameter constraints
        for param_name, param_def in inputs.items():
            param_errors = self._validate_parameter_constraints(
                f"inputs.{param_name}", param_def
            )
            errors.extend(param_errors)
        
        return errors
    
    def _validate_parameter_constraints(self, path: str, param: Dict[str, Any]) -> List[str]:
        """Validate parameter constraint consistency"""
        errors = []
        
        param_type = param.get('type')
        
        # Numeric constraints only for numeric types
        if 'min' in param or 'max' in param:
            if param_type not in ['integer', 'float']:
                errors.append(
                    f"{path}: min/max constraints only valid for numeric types"
                )
            elif 'min' in param and 'max' in param:
                if param['min'] > param['max']:
                    errors.append(f"{path}: min value cannot be greater than max")
        
        # Length constraints only for string/array types
        if 'min_length' in param or 'max_length' in param:
            if param_type not in ['string', 'array']:
                errors.append(
                    f"{path}: length constraints only valid for string/array types"
                )
            elif 'min_length' in param and 'max_length' in param:
                if param['min_length'] > param['max_length']:
                    errors.append(
                        f"{path}: min_length cannot be greater than max_length"
                    )
        
        # Pattern only for strings
        if 'pattern' in param and param_type != 'string':
            errors.append(f"{path}: pattern constraint only valid for string type")
        
        # Enum validation
        if 'enum' in param:
            enum_values = param['enum']
            if not enum_values:
                errors.append(f"{path}: enum must contain at least one value")
            
            # Check default is in enum
            if 'default' in param and param['default'] not in enum_values:
                errors.append(f"{path}: default value must be in enum")
        
        # File format only for file type
        if 'format' in param and param_type != 'file':
            errors.append(f"{path}: format constraint only valid for file type")
        
        return errors
    
    def _validate_examples(self, examples: List[Dict], interface: Dict) -> List[str]:
        """Validate examples against interface"""
        errors = []
        
        input_params = interface.get('inputs', {})
        
        for i, example in enumerate(examples):
            example_inputs = example.get('inputs', {})
            
            # Check required inputs are provided
            for param_name, param_def in input_params.items():
                if param_def.get('required', False) and param_name not in example_inputs:
                    errors.append(
                        f"Example {i} missing required input: {param_name}"
                    )
            
            # Check example inputs exist in interface
            for input_name in example_inputs:
                if input_name not in input_params:
                    errors.append(
                        f"Example {i} has unknown input: {input_name}"
                    )
        
        return errors
    
    def _validate_quality_presets(self, presets: Dict, inputs: Dict) -> List[str]:
        """Validate quality presets reference valid parameters"""
        errors = []
        
        # If interface defines quality input with enum, validate preset names
        if 'quality' in inputs and 'enum' in inputs['quality']:
            valid_qualities = inputs['quality']['enum']
            
            for preset_name in presets:
                if preset_name not in valid_qualities:
                    errors.append(
                        f"Quality preset '{preset_name}' not in quality enum values"
                    )
        
        return errors
    
    def validate_strict(self, definition: Dict[str, Any]) -> None:
        """
        Validate template definition, raising exception on errors.
        
        Raises:
            TemplateValidationError: If validation fails
        """
        errors = self.validate(definition)
        if errors:
            raise TemplateValidationError(
                f"Template validation failed with {len(errors)} errors:\n" + 
                '\n'.join(f"  - {error}" for error in errors)
            )