"""
Base Template Classes

Defines the core structure and behavior of function templates.
"""

import logging
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum
from pydantic import BaseModel, Field, create_model, ValidationError

from .exceptions import TemplateValidationError

logger = logging.getLogger(__name__)


class ParameterType(str, Enum):
    """Supported parameter types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


class ParameterConstraints(BaseModel):
    """Constraints for parameter validation"""
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None
    enum: Optional[List[Any]] = None
    format: Optional[List[str]] = None  # For file types


class InputParameter(BaseModel):
    """Input parameter definition"""
    name: str
    type: ParameterType
    description: str
    required: bool = False
    default: Optional[Any] = None
    constraints: Optional[ParameterConstraints] = None


class OutputParameter(BaseModel):
    """Output parameter definition"""
    name: str
    type: ParameterType
    description: str
    format: Optional[List[str]] = None  # For file types
    properties: Optional[Dict[str, Any]] = None  # For object types


class FunctionInterface(BaseModel):
    """Function interface definition"""
    inputs: Dict[str, InputParameter]
    outputs: Dict[str, OutputParameter]


class ResourceRequirements(BaseModel):
    """Resource requirements for function execution"""
    gpu: bool = False
    vram_gb: float = 0.0
    cpu_cores: int = 1
    memory_gb: float = 2.0
    disk_gb: float = 10.0
    estimated_time_seconds: Optional[float] = None


class QualityPreset(BaseModel):
    """Quality preset configuration"""
    name: str
    parameters: Dict[str, Any]
    resource_multiplier: float = 1.0


class ModelRequirement(BaseModel):
    """Required model specification"""
    name: str
    type: str  # checkpoint, lora, vae, etc.
    size_gb: float
    source: Optional[str] = None  # URL or path
    hash: Optional[str] = None  # For verification


class FunctionExample(BaseModel):
    """Example usage of the function"""
    name: str
    description: Optional[str] = None
    inputs: Dict[str, Any]
    expected_output: Optional[Dict[str, Any]] = None


class FunctionTemplate:
    """Base class for function templates"""
    
    def __init__(self, definition: Dict[str, Any]):
        """Initialize template from definition"""
        template_data = definition.get('template', {})
        
        # Basic metadata
        self.id = template_data['id']
        self.name = template_data['name']
        self.version = template_data['version']
        self.description = template_data.get('description', '')
        self.category = template_data.get('category', 'general')
        self.author = template_data.get('author', 'Unknown')
        self.tags = template_data.get('tags', [])
        
        # Parse interface
        self.interface = self._parse_interface(template_data.get('interface', {}))
        
        # Parse requirements
        requirements = template_data.get('requirements', {})
        self.resources = ResourceRequirements(**requirements.get('resources', {}))
        self.models = [ModelRequirement(**m) for m in requirements.get('models', [])]
        
        # Parse quality presets
        self.quality_presets = {}
        for name, config in requirements.get('quality_presets', {}).items():
            self.quality_presets[name] = QualityPreset(
                name=name,
                parameters=config
            )
        
        # Parse examples
        self.examples = [
            FunctionExample(**ex) for ex in template_data.get('examples', [])
        ]
        
        # Create validation models
        self._input_model = self._create_input_model()
        self._output_model = self._create_output_model()
        
        logger.info(f"Loaded template: {self.id} v{self.version}")
    
    def _parse_interface(self, interface_data: Dict) -> FunctionInterface:
        """Parse interface definition"""
        inputs = {}
        outputs = {}
        
        # Parse inputs
        for name, spec in interface_data.get('inputs', {}).items():
            constraints = None
            if any(k in spec for k in ['min', 'max', 'min_length', 'max_length', 'pattern', 'enum']):
                constraints = ParameterConstraints(
                    min_value=spec.get('min'),
                    max_value=spec.get('max'),
                    min_length=spec.get('min_length'),
                    max_length=spec.get('max_length'),
                    pattern=spec.get('pattern'),
                    enum=spec.get('enum')
                )
            
            inputs[name] = InputParameter(
                name=name,
                type=ParameterType(spec['type']),
                description=spec.get('description', ''),
                required=spec.get('required', False),
                default=spec.get('default'),
                constraints=constraints
            )
        
        # Parse outputs
        for name, spec in interface_data.get('outputs', {}).items():
            outputs[name] = OutputParameter(
                name=name,
                type=ParameterType(spec['type']),
                description=spec.get('description', ''),
                format=spec.get('format'),
                properties=spec.get('properties')
            )
        
        return FunctionInterface(inputs=inputs, outputs=outputs)
    
    def _get_python_type(self, param_type: ParameterType) -> Type:
        """Convert parameter type to Python type"""
        type_mapping = {
            ParameterType.STRING: str,
            ParameterType.INTEGER: int,
            ParameterType.FLOAT: float,
            ParameterType.BOOLEAN: bool,
            ParameterType.ARRAY: list,
            ParameterType.OBJECT: dict,
            ParameterType.FILE: str,  # File path
        }
        return type_mapping.get(param_type, Any)
    
    def _create_field_validators(self, param: InputParameter) -> Dict[str, Any]:
        """Create Pydantic field validators from constraints"""
        validators = {}
        
        if param.constraints:
            if param.constraints.min_value is not None:
                validators['ge'] = param.constraints.min_value
            if param.constraints.max_value is not None:
                validators['le'] = param.constraints.max_value
            if param.constraints.min_length is not None:
                validators['min_length'] = param.constraints.min_length
            if param.constraints.max_length is not None:
                validators['max_length'] = param.constraints.max_length
            if param.constraints.pattern is not None:
                validators['regex'] = param.constraints.pattern
        
        return validators
    
    def _create_input_model(self) -> Type[BaseModel]:
        """Dynamically create Pydantic model for inputs"""
        fields = {}
        
        for name, param in self.interface.inputs.items():
            field_type = self._get_python_type(param.type)
            validators = self._create_field_validators(param)
            
            # Handle enum constraints
            if param.constraints and param.constraints.enum:
                # Create literal type for enum values
                from typing import Literal
                field_type = Literal[tuple(param.constraints.enum)]
            
            if param.required:
                fields[name] = (field_type, Field(..., description=param.description, **validators))
            else:
                from typing import Optional
                fields[name] = (
                    Optional[field_type], 
                    Field(default=param.default, description=param.description, **validators)
                )
        
        return create_model(f"{self.id}_Input", **fields)
    
    def _create_output_model(self) -> Type[BaseModel]:
        """Dynamically create Pydantic model for outputs"""
        fields = {}
        
        for name, param in self.interface.outputs.items():
            field_type = self._get_python_type(param.type)
            fields[name] = (field_type, Field(..., description=param.description))
        
        return create_model(f"{self.id}_Output", **fields)
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs against template schema"""
        try:
            validated = self._input_model(**inputs)
            return validated.dict(exclude_unset=True)
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                msg = error['msg']
                errors.append(f"{field}: {msg}")
            raise TemplateValidationError(f"Input validation failed: {'; '.join(errors)}")
    
    def validate_outputs(self, outputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate outputs against template schema"""
        try:
            validated = self._output_model(**outputs)
            return validated.dict()
        except ValidationError as e:
            errors = []
            for error in e.errors():
                field = '.'.join(str(loc) for loc in error['loc'])
                msg = error['msg']
                errors.append(f"{field}: {msg}")
            raise TemplateValidationError(f"Output validation failed: {'; '.join(errors)}")
    
    def get_resource_requirements(self, inputs: Dict[str, Any]) -> ResourceRequirements:
        """Calculate resource requirements based on inputs"""
        # Start with base requirements
        base_reqs = self.resources.dict()
        
        # Adjust based on quality level if present
        quality = inputs.get('quality', 'standard')
        if quality in self.quality_presets:
            preset = self.quality_presets[quality]
            # Apply resource multiplier
            if preset.resource_multiplier != 1.0:
                base_reqs['memory_gb'] *= preset.resource_multiplier
                base_reqs['vram_gb'] *= preset.resource_multiplier
        
        # Adjust based on resolution if applicable
        width = inputs.get('width', 512)
        height = inputs.get('height', 512)
        if width > 1024 or height > 1024:
            # High resolution needs more VRAM
            base_reqs['vram_gb'] *= 1.5
        
        return ResourceRequirements(**base_reqs)
    
    def get_quality_parameters(self, quality: str) -> Dict[str, Any]:
        """Get parameters for a quality preset"""
        if quality not in self.quality_presets:
            raise ValueError(f"Unknown quality preset: {quality}")
        
        return self.quality_presets[quality].parameters
    
    def to_openapi_schema(self) -> Dict[str, Any]:
        """Generate OpenAPI schema for this template"""
        return {
            "operationId": f"{self.id}_execute",
            "summary": self.name,
            "description": self.description,
            "tags": [self.category] + self.tags,
            "requestBody": {
                "required": True,
                "content": {
                    "application/json": {
                        "schema": self._input_model.schema()
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Successful execution",
                    "content": {
                        "application/json": {
                            "schema": self._output_model.schema()
                        }
                    }
                }
            }
        }
    
    def __repr__(self) -> str:
        return f"<FunctionTemplate {self.id}@{self.version}>"