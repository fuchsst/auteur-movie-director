# Story: Quality Preset System

**Story ID**: STORY-050  
**Epic**: EPIC-003-function-runner-architecture  
**Type**: Feature  
**Points**: 8 (Large)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description
As a content creator, I want intuitive quality presets (draft, standard, high, ultra) that automatically configure all generation parameters across different function types, so that I can quickly choose between speed and quality without understanding complex technical settings.

## Acceptance Criteria

### Functional Requirements
- [ ] Four standard quality levels: draft, standard, high, ultra
- [ ] Quality presets work consistently across all function types
- [ ] Custom quality profiles can be created and saved
- [ ] Quality affects generation time, resource usage, and output quality
- [ ] Visual preview of quality differences in UI
- [ ] Quality recommendations based on use case
- [ ] Batch operations can use mixed quality levels
- [ ] Quality presets are template-aware

### Technical Requirements
- [ ] Implement `QualityPresetManager` with preset definitions
- [ ] Create quality mapping for each template type
- [ ] Build quality-based parameter calculation
- [ ] Implement custom preset storage and retrieval
- [ ] Add quality impact estimation (time, cost, resources)
- [ ] Create quality comparison tools
- [ ] Implement preset inheritance and overrides
- [ ] Add preset validation and compatibility checks

### Quality Requirements
- [ ] Preset selection response time < 100ms
- [ ] Quality estimation accuracy within 15%
- [ ] Support for 100+ custom presets per user
- [ ] Preset compatibility check < 50ms
- [ ] Zero quality degradation from preset bugs
- [ ] Consistent results with same preset
- [ ] Memory usage < 10MB for preset system

## Implementation Notes

### Quality Preset Architecture
```python
@dataclass
class QualityPreset:
    """Definition of a quality preset"""
    id: str
    name: str
    description: str
    level: int  # 1-4 (draft to ultra)
    is_custom: bool = False
    base_preset: Optional[str] = None  # For inheritance
    
    # Global multipliers
    time_multiplier: float = 1.0
    resource_multiplier: float = 1.0
    cost_multiplier: float = 1.0
    
    # Parameter overrides by function type
    parameters: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # Resource requirements scaling
    resource_scaling: Dict[str, float] = field(default_factory=dict)
    
    # Metadata
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    usage_count: int = 0
    average_satisfaction: Optional[float] = None

class QualityPresetManager:
    """Manage quality presets across all function types"""
    
    # Built-in presets
    BUILTIN_PRESETS = {
        'draft': QualityPreset(
            id='draft',
            name='Draft',
            description='Fast generation for previews and iterations',
            level=1,
            time_multiplier=0.3,
            resource_multiplier=0.5,
            cost_multiplier=0.25,
            parameters={
                'image_generation': {
                    'steps': 15,
                    'cfg_scale': 7.0,
                    'sampler': 'euler',
                    'resolution_scale': 0.75
                },
                'video_generation': {
                    'fps': 12,
                    'frames': 24,
                    'resolution_scale': 0.5,
                    'motion_quality': 'low'
                },
                'audio_generation': {
                    'sample_rate': 22050,
                    'bitrate': 128,
                    'processing_quality': 'fast'
                }
            },
            resource_scaling={
                'cpu': 0.5,
                'memory': 0.6,
                'gpu_memory': 0.7
            }
        ),
        'standard': QualityPreset(
            id='standard',
            name='Standard',
            description='Balanced quality and speed for most use cases',
            level=2,
            time_multiplier=1.0,
            resource_multiplier=1.0,
            cost_multiplier=1.0,
            parameters={
                'image_generation': {
                    'steps': 30,
                    'cfg_scale': 7.5,
                    'sampler': 'dpm++_2m',
                    'resolution_scale': 1.0
                },
                'video_generation': {
                    'fps': 24,
                    'frames': 48,
                    'resolution_scale': 1.0,
                    'motion_quality': 'medium'
                },
                'audio_generation': {
                    'sample_rate': 44100,
                    'bitrate': 192,
                    'processing_quality': 'balanced'
                }
            }
        ),
        'high': QualityPreset(
            id='high',
            name='High Quality',
            description='Enhanced quality for professional use',
            level=3,
            time_multiplier=2.5,
            resource_multiplier=1.5,
            cost_multiplier=2.0,
            parameters={
                'image_generation': {
                    'steps': 50,
                    'cfg_scale': 8.0,
                    'sampler': 'dpm++_2m_karras',
                    'resolution_scale': 1.0,
                    'enable_hr_fix': True,
                    'hr_scale': 2.0
                },
                'video_generation': {
                    'fps': 30,
                    'frames': 90,
                    'resolution_scale': 1.0,
                    'motion_quality': 'high',
                    'interpolation': True
                }
            }
        ),
        'ultra': QualityPreset(
            id='ultra',
            name='Ultra Quality',
            description='Maximum quality for final production',
            level=4,
            time_multiplier=5.0,
            resource_multiplier=2.0,
            cost_multiplier=4.0,
            parameters={
                'image_generation': {
                    'steps': 100,
                    'cfg_scale': 8.5,
                    'sampler': 'dpm++_3m_sde_karras',
                    'resolution_scale': 1.0,
                    'enable_hr_fix': True,
                    'hr_scale': 2.0,
                    'hr_steps': 20,
                    'enable_refinement': True
                }
            }
        )
    }
    
    def __init__(self, storage: PresetStorage):
        self.storage = storage
        self.presets = {**self.BUILTIN_PRESETS}
        self.parameter_calculator = ParameterCalculator()
        self.compatibility_checker = CompatibilityChecker()
    
    async def apply_preset(self, 
                          preset_id: str,
                          template: FunctionTemplate,
                          base_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Apply quality preset to function inputs"""
        
        preset = await self.get_preset(preset_id)
        if not preset:
            raise PresetNotFoundError(f"Preset '{preset_id}' not found")
        
        # Check compatibility
        compatibility = await self.compatibility_checker.check(preset, template)
        if not compatibility.is_compatible:
            raise PresetIncompatibleError(
                f"Preset '{preset_id}' incompatible with template '{template.id}': "
                f"{compatibility.reason}"
            )
        
        # Calculate final parameters
        final_params = await self.parameter_calculator.calculate(
            preset=preset,
            template=template,
            base_inputs=base_inputs
        )
        
        # Add quality metadata
        final_params['_quality_preset'] = {
            'id': preset.id,
            'name': preset.name,
            'level': preset.level,
            'estimated_time': self._estimate_time(preset, template),
            'estimated_cost': self._estimate_cost(preset, template)
        }
        
        return final_params
```

### Parameter Calculation System
```python
class ParameterCalculator:
    """Calculate final parameters based on quality preset"""
    
    def __init__(self):
        self.calculators = {
            'image_generation': ImageParameterCalculator(),
            'video_generation': VideoParameterCalculator(),
            'audio_generation': AudioParameterCalculator(),
            'text_generation': TextParameterCalculator()
        }
    
    async def calculate(self,
                       preset: QualityPreset,
                       template: FunctionTemplate,
                       base_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final parameters for execution"""
        
        # Start with base inputs
        final_params = base_inputs.copy()
        
        # Get template category
        category = template.category
        
        # Apply preset parameters
        if category in preset.parameters:
            preset_params = preset.parameters[category]
            final_params.update(preset_params)
        
        # Apply calculator-specific logic
        calculator = self.calculators.get(category)
        if calculator:
            final_params = await calculator.calculate(
                final_params, preset, template
            )
        
        # Apply global scaling
        final_params = self._apply_global_scaling(
            final_params, preset, template
        )
        
        return final_params
    
    def _apply_global_scaling(self,
                            params: Dict[str, Any],
                            preset: QualityPreset,
                            template: FunctionTemplate) -> Dict[str, Any]:
        """Apply global quality scaling to parameters"""
        
        # Scale resolution if applicable
        if 'width' in params and 'resolution_scale' in preset.parameters.get(template.category, {}):
            scale = preset.parameters[template.category]['resolution_scale']
            params['width'] = int(params['width'] * scale)
            params['height'] = int(params['height'] * scale)
        
        # Scale iterations/steps
        if 'steps' in params:
            # Already set by preset
            pass
        elif 'iterations' in params:
            params['iterations'] = int(params['iterations'] * preset.time_multiplier)
        
        return params

class ImageParameterCalculator:
    """Calculate image generation parameters"""
    
    async def calculate(self,
                       params: Dict[str, Any],
                       preset: QualityPreset,
                       template: FunctionTemplate) -> Dict[str, Any]:
        """Apply image-specific calculations"""
        
        # Adjust sampler based on quality
        if preset.level >= 3 and params.get('sampler') == 'euler':
            # Upgrade to better sampler for high quality
            params['sampler'] = 'dpm++_2m_karras'
        
        # Enable advanced features for high/ultra
        if preset.level >= 3:
            params['enable_attention_slicing'] = False  # Better quality
            params['enable_vae_slicing'] = False
        
        # Adjust CFG scale based on resolution
        if params.get('width', 512) > 1024:
            params['cfg_scale'] = params.get('cfg_scale', 7.5) + 0.5
        
        return params
```

### Custom Preset Management
```python
class CustomPresetBuilder:
    """Builder for creating custom quality presets"""
    
    def __init__(self):
        self.preset = QualityPreset(
            id=f"custom_{uuid.uuid4().hex[:8]}",
            name="Custom Preset",
            description="",
            level=2,
            is_custom=True
        )
    
    def with_name(self, name: str) -> 'CustomPresetBuilder':
        self.preset.name = name
        return self
    
    def based_on(self, base_preset_id: str) -> 'CustomPresetBuilder':
        """Inherit from existing preset"""
        self.preset.base_preset = base_preset_id
        return self
    
    def with_parameters(self, 
                       function_type: str,
                       parameters: Dict[str, Any]) -> 'CustomPresetBuilder':
        """Set parameters for specific function type"""
        if function_type not in self.preset.parameters:
            self.preset.parameters[function_type] = {}
        self.preset.parameters[function_type].update(parameters)
        return self
    
    def with_time_multiplier(self, multiplier: float) -> 'CustomPresetBuilder':
        self.preset.time_multiplier = multiplier
        return self
    
    def build(self) -> QualityPreset:
        """Build and validate the preset"""
        # Validate preset
        if not self.preset.name:
            raise ValueError("Preset must have a name")
        
        # Apply inheritance if specified
        if self.preset.base_preset:
            self._apply_inheritance()
        
        return self.preset
    
    def _apply_inheritance(self):
        """Apply inheritance from base preset"""
        base = QualityPresetManager.BUILTIN_PRESETS.get(self.preset.base_preset)
        if not base:
            return
        
        # Inherit values not explicitly set
        if self.preset.time_multiplier == 1.0:
            self.preset.time_multiplier = base.time_multiplier
        
        # Merge parameters
        for func_type, params in base.parameters.items():
            if func_type not in self.preset.parameters:
                self.preset.parameters[func_type] = params.copy()
            else:
                # Merge with base, custom values override
                merged = params.copy()
                merged.update(self.preset.parameters[func_type])
                self.preset.parameters[func_type] = merged
```

### Quality Comparison Tools
```python
class QualityComparisonService:
    """Compare outputs across different quality presets"""
    
    async def generate_comparison(self,
                                 template_id: str,
                                 inputs: Dict[str, Any],
                                 presets: List[str] = None) -> ComparisonResult:
        """Generate outputs with different quality presets for comparison"""
        
        if not presets:
            presets = ['draft', 'standard', 'high', 'ultra']
        
        # Submit tasks for each preset
        tasks = []
        for preset_id in presets:
            task = await function_runner.submit_task(
                template_id=template_id,
                inputs={**inputs, 'quality': preset_id},
                metadata={'comparison_id': str(uuid.uuid4())}
            )
            tasks.append((preset_id, task))
        
        # Wait for all tasks to complete
        results = {}
        timings = {}
        
        for preset_id, task in tasks:
            start_time = time.time()
            try:
                result = await task.wait(timeout=600)  # 10 min timeout
                results[preset_id] = result
                timings[preset_id] = time.time() - start_time
            except Exception as e:
                results[preset_id] = {'error': str(e)}
                timings[preset_id] = None
        
        # Analyze differences
        analysis = await self._analyze_results(results, timings)
        
        return ComparisonResult(
            comparison_id=tasks[0][1].metadata['comparison_id'],
            template_id=template_id,
            inputs=inputs,
            results=results,
            timings=timings,
            analysis=analysis
        )
    
    async def _analyze_results(self, 
                             results: Dict[str, Any],
                             timings: Dict[str, float]) -> ComparisonAnalysis:
        """Analyze quality differences between results"""
        
        analysis = ComparisonAnalysis()
        
        # Time analysis
        valid_timings = {k: v for k, v in timings.items() if v is not None}
        if valid_timings:
            base_time = valid_timings.get('standard', 1.0)
            analysis.time_ratios = {
                k: v / base_time for k, v in valid_timings.items()
            }
        
        # Quality metrics (if applicable)
        # This would analyze actual output quality
        # For images: resolution, sharpness, artifacts
        # For video: frame consistency, motion smoothness
        # For audio: clarity, noise levels
        
        return analysis
```

### Quality Recommendation Engine
```python
class QualityRecommendationEngine:
    """Recommend quality presets based on use case"""
    
    def __init__(self):
        self.use_case_mappings = {
            'preview': 'draft',
            'iteration': 'draft',
            'review': 'standard',
            'client_presentation': 'high',
            'final_delivery': 'ultra',
            'social_media': 'standard',
            'print': 'ultra'
        }
        
        self.ml_model = self._load_recommendation_model()
    
    async def recommend(self,
                       context: RecommendationContext) -> QualityRecommendation:
        """Recommend quality preset based on context"""
        
        # Simple rule-based recommendation
        if context.use_case in self.use_case_mappings:
            preset_id = self.use_case_mappings[context.use_case]
            confidence = 0.9
        else:
            # ML-based recommendation
            features = self._extract_features(context)
            preset_id, confidence = await self._ml_recommend(features)
        
        # Get preset details
        preset = await preset_manager.get_preset(preset_id)
        
        # Calculate trade-offs
        trade_offs = self._calculate_trade_offs(preset, context)
        
        return QualityRecommendation(
            recommended_preset=preset_id,
            confidence=confidence,
            reasoning=self._generate_reasoning(preset, context),
            trade_offs=trade_offs,
            alternatives=self._get_alternatives(preset_id, context)
        )
    
    def _calculate_trade_offs(self,
                            preset: QualityPreset,
                            context: RecommendationContext) -> TradeOffs:
        """Calculate quality vs time/cost trade-offs"""
        
        base_preset = QualityPresetManager.BUILTIN_PRESETS['standard']
        
        return TradeOffs(
            time_factor=preset.time_multiplier / base_preset.time_multiplier,
            cost_factor=preset.cost_multiplier / base_preset.cost_multiplier,
            quality_gain=self._estimate_quality_gain(preset.level),
            resource_usage=preset.resource_multiplier
        )
```

### Quality Impact Estimation
```python
class QualityImpactEstimator:
    """Estimate impact of quality settings on outputs"""
    
    def __init__(self):
        self.historical_data = HistoricalDataStore()
        
    async def estimate_impact(self,
                            template: FunctionTemplate,
                            preset: QualityPreset,
                            inputs: Dict[str, Any]) -> QualityImpact:
        """Estimate the impact of quality settings"""
        
        # Get historical data for similar tasks
        similar_tasks = await self.historical_data.find_similar(
            template_id=template.id,
            preset_id=preset.id,
            input_hash=self._hash_inputs(inputs)
        )
        
        # Calculate estimates
        time_estimate = self._estimate_time(template, preset, similar_tasks)
        resource_estimate = self._estimate_resources(template, preset)
        quality_metrics = self._estimate_quality_metrics(preset)
        
        return QualityImpact(
            estimated_time=time_estimate,
            time_confidence=self._calculate_confidence(similar_tasks),
            resource_requirements=resource_estimate,
            quality_metrics=quality_metrics,
            cost_estimate=self._estimate_cost(time_estimate, resource_estimate),
            sample_outputs=await self._get_sample_outputs(template, preset)
        )
    
    def _estimate_time(self,
                      template: FunctionTemplate,
                      preset: QualityPreset,
                      historical: List[TaskExecution]) -> TimeEstimate:
        """Estimate execution time"""
        
        base_time = template.metadata.get('base_execution_time', 60)
        
        if historical:
            # Use historical data
            times = [t.duration for t in historical]
            median_time = statistics.median(times)
            std_dev = statistics.stdev(times) if len(times) > 1 else 0
            
            return TimeEstimate(
                min_seconds=median_time - std_dev,
                max_seconds=median_time + std_dev,
                expected_seconds=median_time
            )
        else:
            # Use multipliers
            expected = base_time * preset.time_multiplier
            return TimeEstimate(
                min_seconds=expected * 0.8,
                max_seconds=expected * 1.5,
                expected_seconds=expected
            )
```

### Preset Storage and Retrieval
```python
class PresetStorage:
    """Store and retrieve custom presets"""
    
    def __init__(self, db: Database):
        self.db = db
        self.cache = TTLCache(maxsize=1000, ttl=300)
    
    async def save_preset(self, preset: QualityPreset, user_id: str):
        """Save custom preset"""
        
        # Validate preset
        if not preset.is_custom:
            raise ValueError("Cannot save built-in preset")
        
        # Store in database
        await self.db.presets.insert_one({
            'id': preset.id,
            'user_id': user_id,
            'name': preset.name,
            'description': preset.description,
            'level': preset.level,
            'base_preset': preset.base_preset,
            'parameters': preset.parameters,
            'multipliers': {
                'time': preset.time_multiplier,
                'resource': preset.resource_multiplier,
                'cost': preset.cost_multiplier
            },
            'created_at': preset.created_at or datetime.now(),
            'updated_at': datetime.now()
        })
        
        # Invalidate cache
        self.cache.pop(f"{user_id}:{preset.id}", None)
    
    async def get_user_presets(self, user_id: str) -> List[QualityPreset]:
        """Get all presets for a user"""
        
        cache_key = f"user_presets:{user_id}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Query database
        cursor = self.db.presets.find({'user_id': user_id})
        presets = []
        
        async for doc in cursor:
            preset = self._doc_to_preset(doc)
            presets.append(preset)
        
        self.cache[cache_key] = presets
        return presets
```

## Dependencies
- **STORY-044**: Function Template Registry - for template compatibility
- **STORY-046**: Resource Requirement Mapping - for resource calculations
- **STORY-013**: Function Runner Foundation - base implementation (completed)
- MongoDB for preset storage
- Redis for caching

## Testing Criteria
- [ ] Unit tests for preset calculations
- [ ] Integration tests with all function types
- [ ] Quality comparison accuracy tests
- [ ] Performance tests for preset application
- [ ] Custom preset creation and storage tests
- [ ] Recommendation engine accuracy tests
- [ ] Resource estimation tests
- [ ] UI preview generation tests

## Definition of Done
- [ ] Four standard quality presets implemented
- [ ] Parameter calculation for all function types
- [ ] Custom preset creation and management
- [ ] Quality comparison tools working
- [ ] Recommendation engine trained and tested
- [ ] Impact estimation accurate within 15%
- [ ] API endpoints documented
- [ ] UI components for preset selection
- [ ] Documentation includes preset guide
- [ ] Code review passed with test coverage > 85%

## Story Links
- **Depends On**: STORY-013 (completed), STORY-044, STORY-046
- **Blocks**: STORY-051 (Integration & Testing)
- **Related Epic**: EPIC-003-function-runner-architecture
- **Architecture Ref**: /concept/quality/preset_system.md