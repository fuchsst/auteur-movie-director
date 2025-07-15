# Story: Template Validation System

**Story ID**: STORY-045  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: ✅ Completed  

## Story Description
As a function developer, I want a comprehensive validation system that checks function templates for correctness, completeness, and compatibility before registration, so that invalid templates are caught early and function execution errors are minimized.

## Acceptance Criteria

### Functional Requirements
- [ ] Validate template schema against JSON Schema specification
- [ ] Check input/output parameter types and constraints
- [ ] Verify resource requirement specifications are valid
- [ ] Validate example inputs match template schema
- [ ] Check for circular dependencies in template inheritance
- [ ] Validate quality preset configurations
- [ ] Ensure unique template ID and version combinations
- [ ] Generate detailed validation error reports

### Technical Requirements
- [ ] Implement multi-stage validation pipeline
- [ ] Create custom validators for complex constraints
- [ ] Build validation cache to avoid re-validation
- [ ] Implement async validation for large templates
- [ ] Add validation hooks for custom extensions
- [ ] Create validation report formatter
- [ ] Implement validation API endpoints
- [ ] Add batch validation support

### Quality Requirements
- [ ] Validation completes within 100ms per template
- [ ] 100% detection rate for schema violations
- [ ] Clear error messages with fix suggestions
- [ ] Support for custom validation rules
- [ ] Zero false positives in validation
- [ ] Validation results cacheable for 1 hour
- [ ] Memory efficient for large batch validations

## Implementation Notes

### Validation Pipeline
```python
class TemplateValidationPipeline:
    """Multi-stage validation pipeline for templates"""
    
    def __init__(self):
        self.stages = [
            SchemaValidator(),
            TypeValidator(),
            ConstraintValidator(),
            ResourceValidator(),
            ExampleValidator(),
            DependencyValidator(),
            UniquenessValidator()
        ]
        self.cache = TTLCache(maxsize=1000, ttl=3600)
    
    async def validate(self, template_data: Dict[str, Any], 
                      context: ValidationContext = None) -> ValidationResult:
        """Run full validation pipeline"""
        
        # Check cache
        cache_key = self._get_cache_key(template_data)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Initialize result
        result = ValidationResult(
            template_id=template_data.get('template', {}).get('id'),
            version=template_data.get('template', {}).get('version'),
            errors=[],
            warnings=[],
            info=[]
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
                result.errors.append(ValidationError(
                    stage=stage.name,
                    message=f"Validation stage failed: {str(e)}",
                    severity='critical'
                ))
                break
        
        # Cache result
        self.cache[cache_key] = result
        
        return result
```

### Schema Validator
```python
class SchemaValidator(ValidationStage):
    """Validate template against JSON schema"""
    
    def __init__(self):
        self.schema = self._load_template_schema()
        self.validator = Draft7Validator(self.schema)
    
    async def validate(self, template_data: Dict, 
                      context: ValidationContext) -> StageResult:
        """Validate basic schema structure"""
        result = StageResult(stage='schema')
        
        # Check against JSON schema
        for error in self.validator.iter_errors(template_data):
            result.add_error(
                path='.'.join(str(p) for p in error.path),
                message=error.message,
                severity='error' if error.validator != 'required' else 'critical'
            )
        
        # Additional structural checks
        if 'template' in template_data:
            template = template_data['template']
            
            # Check version format
            if not self._is_valid_semver(template.get('version', '')):
                result.add_error(
                    path='template.version',
                    message='Version must follow semantic versioning (x.y.z)',
                    severity='error'
                )
            
            # Check ID format
            if not re.match(r'^[a-z0-9_]+$', template.get('id', '')):
                result.add_error(
                    path='template.id',
                    message='ID must contain only lowercase letters, numbers, and underscores',
                    severity='error'
                )
        
        return result
```

### Type and Constraint Validator
```python
class TypeValidator(ValidationStage):
    """Validate parameter types and constraints"""
    
    VALID_TYPES = {'string', 'integer', 'float', 'boolean', 'array', 'object', 'file'}
    
    TYPE_CONSTRAINTS = {
        'string': ['min_length', 'max_length', 'pattern', 'enum'],
        'integer': ['min', 'max', 'enum'],
        'float': ['min', 'max', 'precision'],
        'array': ['min_items', 'max_items', 'unique_items'],
        'file': ['format', 'max_size', 'mime_types']
    }
    
    async def validate(self, template_data: Dict, 
                      context: ValidationContext) -> StageResult:
        """Validate input/output types and constraints"""
        result = StageResult(stage='types')
        
        interface = template_data.get('template', {}).get('interface', {})
        
        # Validate inputs
        for name, spec in interface.get('inputs', {}).items():
            self._validate_parameter(name, spec, 'input', result)
        
        # Validate outputs
        for name, spec in interface.get('outputs', {}).items():
            self._validate_parameter(name, spec, 'output', result)
        
        return result
    
    def _validate_parameter(self, name: str, spec: Dict, 
                           param_type: str, result: StageResult):
        """Validate individual parameter"""
        path_prefix = f"template.interface.{param_type}s.{name}"
        
        # Check type
        param_type = spec.get('type')
        if param_type not in self.VALID_TYPES:
            result.add_error(
                path=f"{path_prefix}.type",
                message=f"Invalid type '{param_type}'. Must be one of: {', '.join(self.VALID_TYPES)}",
                severity='error'
            )
            return
        
        # Check constraints
        valid_constraints = self.TYPE_CONSTRAINTS.get(param_type, [])
        for constraint, value in spec.items():
            if constraint in ['type', 'description', 'required', 'default']:
                continue
                
            if constraint not in valid_constraints:
                result.add_warning(
                    path=f"{path_prefix}.{constraint}",
                    message=f"Constraint '{constraint}' is not applicable to type '{param_type}'"
                )
        
        # Validate enum values
        if 'enum' in spec:
            if not isinstance(spec['enum'], list) or len(spec['enum']) == 0:
                result.add_error(
                    path=f"{path_prefix}.enum",
                    message="Enum must be a non-empty list",
                    severity='error'
                )
        
        # Validate default value
        if 'default' in spec:
            if not self._is_valid_default(spec['default'], param_type, spec):
                result.add_error(
                    path=f"{path_prefix}.default",
                    message=f"Default value does not match type '{param_type}' or constraints",
                    severity='error'
                )
```

### Resource Validator
```python
class ResourceValidator(ValidationStage):
    """Validate resource requirements"""
    
    async def validate(self, template_data: Dict, 
                      context: ValidationContext) -> StageResult:
        """Validate resource specifications"""
        result = StageResult(stage='resources')
        
        requirements = template_data.get('template', {}).get('requirements', {})
        resources = requirements.get('resources', {})
        
        # Check GPU requirements
        if resources.get('gpu'):
            vram = resources.get('vram_gb', 0)
            if vram <= 0:
                result.add_error(
                    path='template.requirements.resources.vram_gb',
                    message='GPU templates must specify VRAM requirements',
                    severity='error'
                )
            elif vram > 48:  # Current max consumer GPU VRAM
                result.add_warning(
                    path='template.requirements.resources.vram_gb',
                    message=f'VRAM requirement of {vram}GB exceeds typical hardware'
                )
        
        # Check CPU requirements
        cpu_cores = resources.get('cpu_cores', 1)
        if cpu_cores < 1:
            result.add_error(
                path='template.requirements.resources.cpu_cores',
                message='CPU cores must be at least 1',
                severity='error'
            )
        elif cpu_cores > 64:
            result.add_warning(
                path='template.requirements.resources.cpu_cores',
                message=f'CPU requirement of {cpu_cores} cores is unusually high'
            )
        
        # Check memory requirements
        memory_gb = resources.get('memory_gb', 0)
        if memory_gb <= 0:
            result.add_error(
                path='template.requirements.resources.memory_gb',
                message='Memory requirement must be specified',
                severity='error'
            )
        
        # Validate quality presets
        quality_presets = requirements.get('quality_presets', {})
        for preset_name, preset_config in quality_presets.items():
            self._validate_quality_preset(preset_name, preset_config, result)
        
        return result
    
    def _validate_quality_preset(self, name: str, config: Dict, result: StageResult):
        """Validate quality preset configuration"""
        path_prefix = f"template.requirements.quality_presets.{name}"
        
        # Check required fields based on template type
        # This would be customized per template type
        pass
```

### Example Validator
```python
class ExampleValidator(ValidationStage):
    """Validate template examples"""
    
    async def validate(self, template_data: Dict, 
                      context: ValidationContext) -> StageResult:
        """Validate example inputs against template schema"""
        result = StageResult(stage='examples')
        
        template = template_data.get('template', {})
        examples = template.get('examples', [])
        
        if not examples:
            result.add_info(
                path='template.examples',
                message='No examples provided. Consider adding examples for better documentation.'
            )
            return result
        
        # Create template instance for validation
        try:
            temp_template = FunctionTemplate(template_data)
        except Exception as e:
            result.add_error(
                path='template',
                message=f'Cannot create template for example validation: {str(e)}',
                severity='critical'
            )
            return result
        
        # Validate each example
        for idx, example in enumerate(examples):
            example_path = f"template.examples[{idx}]"
            
            # Check example structure
            if 'name' not in example:
                result.add_error(
                    path=f"{example_path}.name",
                    message='Example must have a name',
                    severity='error'
                )
            
            if 'inputs' not in example:
                result.add_error(
                    path=f"{example_path}.inputs",
                    message='Example must have inputs',
                    severity='error'
                )
                continue
            
            # Validate example inputs
            try:
                temp_template.validate_inputs(example['inputs'])
            except TemplateValidationError as e:
                result.add_error(
                    path=f"{example_path}.inputs",
                    message=f'Example inputs invalid: {str(e)}',
                    severity='error'
                )
        
        return result
```

### Validation Result Formatter
```python
class ValidationResultFormatter:
    """Format validation results for different outputs"""
    
    def format_cli(self, result: ValidationResult) -> str:
        """Format for CLI output"""
        output = []
        
        if result.is_valid():
            output.append(f"✅ Template '{result.template_id}' v{result.version} is valid!")
        else:
            output.append(f"❌ Template '{result.template_id}' v{result.version} validation failed")
        
        if result.errors:
            output.append("\nErrors:")
            for error in result.errors:
                icon = "🔴" if error.severity == 'critical' else "🟡"
                output.append(f"  {icon} [{error.stage}] {error.path}: {error.message}")
        
        if result.warnings:
            output.append("\nWarnings:")
            for warning in result.warnings:
                output.append(f"  ⚠️  [{warning.stage}] {warning.path}: {warning.message}")
        
        if result.info:
            output.append("\nInfo:")
            for info in result.info:
                output.append(f"  ℹ️  [{info.stage}] {info.path}: {info.message}")
        
        return '\n'.join(output)
    
    def format_json(self, result: ValidationResult) -> Dict:
        """Format for JSON API response"""
        return {
            'valid': result.is_valid(),
            'template_id': result.template_id,
            'version': result.version,
            'errors': [self._format_issue(e) for e in result.errors],
            'warnings': [self._format_issue(w) for w in result.warnings],
            'info': [self._format_issue(i) for i in result.info],
            'summary': {
                'error_count': len(result.errors),
                'warning_count': len(result.warnings),
                'info_count': len(result.info)
            }
        }
```

### Validation API
```python
@router.post("/templates/validate")
async def validate_template(
    template_file: UploadFile,
    strict: bool = False
) -> ValidationResponse:
    """Validate a template file"""
    
    # Parse template
    content = await template_file.read()
    try:
        template_data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        return ValidationResponse(
            valid=False,
            errors=[{
                'stage': 'parsing',
                'message': f'Invalid YAML: {str(e)}',
                'severity': 'critical'
            }]
        )
    
    # Create validation context
    context = ValidationContext(
        strict_mode=strict,
        check_uniqueness=True,
        registry=template_registry
    )
    
    # Run validation
    result = await validation_pipeline.validate(template_data, context)
    
    # Format response
    formatter = ValidationResultFormatter()
    return ValidationResponse(**formatter.format_json(result))
```

## Dependencies
- **STORY-044**: Function Template Registry - validates against registry
- **STORY-046**: Resource Requirement Mapping - validates resource specs
- JSON Schema for schema validation
- Pydantic for data validation
- SemVer for version validation

## Testing Criteria
- [ ] Unit tests for each validation stage
- [ ] Integration tests for full pipeline
- [ ] Test with valid and invalid templates
- [ ] Performance tests for large templates
- [ ] Cache effectiveness tests
- [ ] Error message clarity tests
- [ ] API endpoint tests
- [ ] Batch validation tests

## Definition of Done
- [ ] All validation stages implemented
- [ ] Clear error messages with suggestions
- [ ] Validation cache working correctly
- [ ] API endpoints documented
- [ ] CLI integration complete
- [ ] Performance meets requirements
- [ ] Comprehensive test coverage
- [ ] Documentation includes validation rules
- [ ] Code review passed with test coverage > 90%

## Story Links
- **Depends On**: STORY-044 (Function Template Registry)
- **Blocks**: STORY-047 (API Client Layer)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/validation/template_validation.md