# Story: Function Template Registry

**Story ID**: STORY-044  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 8 (Large)  
**Priority**: High  
**Status**: ✅ Completed  

## Story Description
As a platform developer, I want a centralized registry for function templates that defines the interface, requirements, and behavior of each AI function type, so that new functions can be easily added to the platform with consistent structure and automatic validation of inputs and outputs.

## Acceptance Criteria

### Functional Requirements
- [ ] Central registry stores all function template definitions
- [ ] Templates define input/output schemas with validation rules
- [ ] Templates specify resource requirements (CPU, memory, GPU)
- [ ] Templates include metadata (version, author, description, examples)
- [ ] Registry supports template versioning and deprecation
- [ ] Hot-reload of templates without service restart
- [ ] Template inheritance for common patterns
- [ ] CLI tool for template validation and registration

### Technical Requirements
- [ ] Implement `FunctionTemplate` base class with validation
- [ ] Create YAML/JSON schema for template definitions
- [ ] Build template loader with file watching capability
- [ ] Implement template validation with Pydantic models
- [ ] Add template registry with thread-safe access
- [ ] Create template discovery mechanism
- [ ] Implement template caching for performance
- [ ] Add OpenAPI schema generation from templates

### Quality Requirements
- [ ] Template loading time < 100ms per template
- [ ] Template validation catches 100% of schema errors
- [ ] Registry lookup time < 1ms
- [ ] Support for 1000+ templates
- [ ] Zero downtime template updates
- [ ] Template hot-reload within 5 seconds
- [ ] Memory usage < 100MB for full registry

## Implementation Notes

### Template Definition Schema
```yaml
# templates/image_generation.yaml
template:
  id: "image_generation_v1"
  name: "Image Generation"
  version: "1.0.0"
  description: "Generate images from text prompts using Stable Diffusion"
  category: "generation"
  author: "Auteur Team"
  
  interface:
    inputs:
      prompt:
        type: string
        description: "Text description of the image"
        required: true
        min_length: 1
        max_length: 1000
        
      negative_prompt:
        type: string
        description: "What to avoid in the image"
        required: false
        default: ""
        
      width:
        type: integer
        description: "Image width in pixels"
        required: false
        default: 512
        enum: [512, 768, 1024]
        
      height:
        type: integer
        description: "Image height in pixels"
        required: false
        default: 512
        enum: [512, 768, 1024]
        
      quality:
        type: string
        description: "Generation quality level"
        required: false
        default: "standard"
        enum: ["draft", "standard", "high", "ultra"]
        
      seed:
        type: integer
        description: "Random seed for reproducibility"
        required: false
        min: 0
        max: 2147483647
        
    outputs:
      image:
        type: file
        format: ["png", "jpg"]
        description: "Generated image file"
        
      metadata:
        type: object
        description: "Generation metadata"
        properties:
          actual_seed:
            type: integer
          generation_time:
            type: float
          model_version:
            type: string
            
  requirements:
    resources:
      gpu: true
      vram_gb: 8
      cpu_cores: 2
      memory_gb: 8
      
    models:
      - name: "stable-diffusion-v1-5"
        type: "checkpoint"
        size_gb: 4.2
        
    quality_presets:
      draft:
        steps: 20
        cfg_scale: 7
        sampler: "euler_a"
      standard:
        steps: 30
        cfg_scale: 7.5
        sampler: "dpm++_2m"
      high:
        steps: 50
        cfg_scale: 8
        sampler: "dpm++_2m_karras"
      ultra:
        steps: 100
        cfg_scale: 8.5
        sampler: "dpm++_3m_sde"
        
  examples:
    - name: "Portrait Generation"
      inputs:
        prompt: "Professional portrait photo of a woman, studio lighting"
        negative_prompt: "cartoon, anime, illustration"
        width: 512
        height: 768
        quality: "high"
```

### Template Registry Implementation
```python
class FunctionTemplate:
    """Base class for function templates"""
    
    def __init__(self, definition: Dict[str, Any]):
        self.id = definition['template']['id']
        self.name = definition['template']['name']
        self.version = definition['template']['version']
        self.interface = self.parse_interface(definition['template']['interface'])
        self.requirements = definition['template']['requirements']
        self.examples = definition['template'].get('examples', [])
        
        # Create Pydantic models for validation
        self.input_model = self.create_input_model()
        self.output_model = self.create_output_model()
    
    def parse_interface(self, interface: Dict) -> FunctionInterface:
        """Parse and validate interface definition"""
        inputs = {}
        outputs = {}
        
        for name, spec in interface.get('inputs', {}).items():
            inputs[name] = InputParameter(
                name=name,
                type=spec['type'],
                required=spec.get('required', False),
                default=spec.get('default'),
                description=spec.get('description'),
                constraints=self.parse_constraints(spec)
            )
        
        for name, spec in interface.get('outputs', {}).items():
            outputs[name] = OutputParameter(
                name=name,
                type=spec['type'],
                format=spec.get('format'),
                description=spec.get('description')
            )
        
        return FunctionInterface(inputs=inputs, outputs=outputs)
    
    def create_input_model(self) -> Type[BaseModel]:
        """Dynamically create Pydantic model for inputs"""
        fields = {}
        
        for name, param in self.interface.inputs.items():
            field_type = self.get_python_type(param.type)
            
            if param.required:
                fields[name] = (field_type, Field(..., description=param.description))
            else:
                fields[name] = (Optional[field_type], Field(param.default, description=param.description))
        
        return create_model(f"{self.id}_Input", **fields)
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs against template schema"""
        try:
            validated = self.input_model(**inputs)
            return validated.dict()
        except ValidationError as e:
            raise TemplateValidationError(f"Input validation failed: {e}")
    
    def get_resource_requirements(self, inputs: Dict[str, Any]) -> ResourceRequirements:
        """Calculate resource requirements based on inputs"""
        base_reqs = self.requirements['resources'].copy()
        
        # Adjust based on quality level
        if 'quality' in inputs:
            quality_preset = self.requirements['quality_presets'].get(inputs['quality'])
            if quality_preset and quality_preset.get('extra_vram_gb'):
                base_reqs['vram_gb'] += quality_preset['extra_vram_gb']
        
        return ResourceRequirements(**base_reqs)
```

### Template Registry Manager
```python
class TemplateRegistry:
    """Central registry for all function templates"""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.templates: Dict[str, FunctionTemplate] = {}
        self.template_versions: Dict[str, List[str]] = {}
        self._lock = threading.RLock()
        self._file_watcher = None
    
    async def initialize(self):
        """Load all templates and start file watcher"""
        await self.load_templates()
        self._start_file_watcher()
    
    async def load_templates(self):
        """Load all templates from directory"""
        template_files = list(self.template_dir.glob("**/*.yaml")) + \
                        list(self.template_dir.glob("**/*.yml"))
        
        for file_path in template_files:
            try:
                await self.load_template_file(file_path)
            except Exception as e:
                logger.error(f"Failed to load template {file_path}: {e}")
    
    async def load_template_file(self, file_path: Path):
        """Load and validate a single template file"""
        with open(file_path, 'r') as f:
            definition = yaml.safe_load(f)
        
        # Validate against schema
        self.validate_template_schema(definition)
        
        # Create template instance
        template = FunctionTemplate(definition)
        
        # Register template
        with self._lock:
            template_key = f"{template.id}@{template.version}"
            self.templates[template_key] = template
            
            # Track versions
            if template.id not in self.template_versions:
                self.template_versions[template.id] = []
            if template.version not in self.template_versions[template.id]:
                self.template_versions[template.id].append(template.version)
                self.template_versions[template.id].sort(key=Version)
        
        logger.info(f"Loaded template: {template_key}")
    
    def get_template(self, template_id: str, version: str = None) -> FunctionTemplate:
        """Get template by ID and optional version"""
        with self._lock:
            if version:
                template_key = f"{template_id}@{version}"
                if template_key not in self.templates:
                    raise TemplateNotFoundError(f"Template {template_key} not found")
                return self.templates[template_key]
            else:
                # Get latest version
                if template_id not in self.template_versions:
                    raise TemplateNotFoundError(f"Template {template_id} not found")
                
                latest_version = self.template_versions[template_id][-1]
                return self.get_template(template_id, latest_version)
    
    def list_templates(self, category: str = None) -> List[TemplateInfo]:
        """List all available templates"""
        with self._lock:
            templates = []
            
            for template in self.templates.values():
                if category and template.category != category:
                    continue
                
                templates.append(TemplateInfo(
                    id=template.id,
                    name=template.name,
                    version=template.version,
                    category=template.category,
                    description=template.description,
                    requires_gpu=template.requirements['resources'].get('gpu', False)
                ))
            
            return templates
    
    def _start_file_watcher(self):
        """Watch template directory for changes"""
        async def watch_files():
            async for changes in awatch(self.template_dir):
                for change_type, file_path in changes:
                    if file_path.suffix in ['.yaml', '.yml']:
                        logger.info(f"Template file {change_type}: {file_path}")
                        
                        if change_type in [Change.added, Change.modified]:
                            await self.load_template_file(Path(file_path))
                        elif change_type == Change.deleted:
                            await self.unload_template_file(Path(file_path))
        
        self._file_watcher = asyncio.create_task(watch_files())
```

### Template Validation
```python
class TemplateValidator:
    """Validate template definitions"""
    
    SCHEMA = {
        "type": "object",
        "required": ["template"],
        "properties": {
            "template": {
                "type": "object",
                "required": ["id", "name", "version", "interface", "requirements"],
                "properties": {
                    "id": {"type": "string", "pattern": "^[a-z0-9_]+$"},
                    "name": {"type": "string"},
                    "version": {"type": "string", "pattern": "^\\d+\\.\\d+\\.\\d+$"},
                    "interface": {
                        "type": "object",
                        "properties": {
                            "inputs": {"type": "object"},
                            "outputs": {"type": "object"}
                        }
                    },
                    "requirements": {
                        "type": "object",
                        "required": ["resources"],
                        "properties": {
                            "resources": {
                                "type": "object",
                                "properties": {
                                    "gpu": {"type": "boolean"},
                                    "vram_gb": {"type": "number"},
                                    "cpu_cores": {"type": "integer"},
                                    "memory_gb": {"type": "number"}
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    def validate(self, definition: Dict) -> List[str]:
        """Validate template against schema"""
        validator = jsonschema.Draft7Validator(self.SCHEMA)
        errors = []
        
        for error in validator.iter_errors(definition):
            errors.append(f"{'.'.join(error.path)}: {error.message}")
        
        # Additional validation
        if not errors:
            errors.extend(self.validate_interface(definition['template']['interface']))
            errors.extend(self.validate_examples(definition['template'].get('examples', [])))
        
        return errors
```

### Template CLI Tool
```python
# cli/template_tool.py
@click.group()
def template():
    """Function template management commands"""
    pass

@template.command()
@click.argument('template_file', type=click.Path(exists=True))
def validate(template_file):
    """Validate a template definition"""
    with open(template_file, 'r') as f:
        definition = yaml.safe_load(f)
    
    validator = TemplateValidator()
    errors = validator.validate(definition)
    
    if errors:
        click.echo("Template validation failed:")
        for error in errors:
            click.echo(f"  - {error}")
        sys.exit(1)
    else:
        click.echo("Template is valid!")

@template.command()
@click.argument('template_file', type=click.Path(exists=True))
@click.option('--registry-url', default='http://localhost:8000')
def register(template_file, registry_url):
    """Register a template with the registry"""
    # Implementation for registering templates
    pass
```

## Dependencies
- **STORY-045**: Template Validation System - validates template definitions
- **STORY-046**: Resource Requirement Mapping - uses resource definitions
- Pydantic for schema validation
- YAML/JSON for template definitions
- jsonschema for template schema validation
- watchdog for file monitoring

## Testing Criteria
- [ ] Unit tests for template parsing and validation
- [ ] Integration tests for template registry operations
- [ ] Load tests with 1000+ templates
- [ ] Hot-reload tests for template updates
- [ ] Schema validation tests for all template types
- [ ] CLI tool tests for all commands
- [ ] Performance tests for template lookup
- [ ] Thread safety tests for concurrent access

## Definition of Done
- [ ] FunctionTemplate base class implemented
- [ ] Template schema defined and documented
- [ ] Registry supports all CRUD operations
- [ ] File watcher enables hot-reload
- [ ] Validation catches all schema errors
- [ ] CLI tool for template management
- [ ] OpenAPI schemas generated from templates
- [ ] Performance meets lookup time requirements
- [ ] Documentation includes template authoring guide
- [ ] Code review passed with test coverage > 90%

## Story Links
- **Blocks**: STORY-047 (API Client Layer)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/templates/registry_design.md