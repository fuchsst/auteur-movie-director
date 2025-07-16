"""
Tests for Quality Preset System (STORY-050)

Tests the complete quality preset functionality including:
- Built-in presets
- Custom preset creation and management
- Parameter calculation
- Quality comparison
- Recommendations
- Impact estimation
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.quality import (
    QualityPreset,
    QualityLevel,
    QualityPresetManager,
    CustomPresetBuilder,
    ParameterCalculator,
    QualityComparisonService,
    QualityRecommendationEngine,
    QualityImpactEstimator,
    PresetStorage,
    PresetNotFoundError,
    PresetIncompatibleError
)
from app.quality.recommendation import UseCase, RecommendationContext
from app.templates.base import FunctionTemplate


class TestQualityPresets:
    """Test quality preset definitions and management"""
    
    def test_builtin_presets(self):
        """Test that built-in presets are properly defined"""
        manager = QualityPresetManager()
        
        # Check all built-in presets exist
        assert 'draft' in manager.presets
        assert 'standard' in manager.presets
        assert 'high' in manager.presets
        assert 'ultra' in manager.presets
        
        # Check preset properties
        draft = manager.presets['draft']
        assert draft.level == QualityLevel.DRAFT
        assert draft.time_multiplier == 0.3
        assert draft.resource_multiplier == 0.5
        assert draft.cost_multiplier == 0.25
        assert not draft.is_custom
        
        # Check parameter definitions
        assert 'image_generation' in draft.parameters
        assert 'steps' in draft.parameters['image_generation']
        assert draft.parameters['image_generation']['steps'] == 15
    
    def test_preset_hierarchy(self):
        """Test quality preset hierarchy and multipliers"""
        manager = QualityPresetManager()
        
        # Verify multipliers increase with quality
        assert manager.presets['draft'].time_multiplier < manager.presets['standard'].time_multiplier
        assert manager.presets['standard'].time_multiplier < manager.presets['high'].time_multiplier
        assert manager.presets['high'].time_multiplier < manager.presets['ultra'].time_multiplier
        
        # Same for resource multipliers
        assert manager.presets['draft'].resource_multiplier < manager.presets['ultra'].resource_multiplier
    
    def test_preset_serialization(self):
        """Test preset serialization and deserialization"""
        preset = QualityPreset(
            id='test',
            name='Test Preset',
            description='Test description',
            level=QualityLevel.STANDARD,
            is_custom=True,
            time_multiplier=1.5
        )
        
        # Serialize
        data = preset.to_dict()
        assert data['id'] == 'test'
        assert data['level'] == 2  # QualityLevel.STANDARD
        
        # Deserialize
        restored = QualityPreset.from_dict(data)
        assert restored.id == preset.id
        assert restored.level == preset.level


class TestCustomPresetBuilder:
    """Test custom preset builder functionality"""
    
    def test_basic_preset_creation(self):
        """Test creating a basic custom preset"""
        preset = (CustomPresetBuilder()
                 .with_name("My Custom Preset")
                 .with_description("Custom preset for testing")
                 .with_level(QualityLevel.HIGH)
                 .build())
        
        assert preset.name == "My Custom Preset"
        assert preset.description == "Custom preset for testing"
        assert preset.level == QualityLevel.HIGH
        assert preset.is_custom
        assert preset.id.startswith("custom_")
    
    def test_preset_inheritance(self):
        """Test creating preset based on existing one"""
        preset = (CustomPresetBuilder()
                 .with_name("Enhanced Standard")
                 .based_on("standard")
                 .with_time_multiplier(1.2)
                 .build())
        
        assert preset.base_preset == "standard"
        assert preset.time_multiplier == 1.2
    
    def test_preset_with_parameters(self):
        """Test adding custom parameters to preset"""
        preset = (CustomPresetBuilder()
                 .with_name("Fast Images")
                 .with_parameters("image_generation", {
                     "steps": 20,
                     "sampler": "ddim"
                 })
                 .build())
        
        assert preset.parameters["image_generation"]["steps"] == 20
        assert preset.parameters["image_generation"]["sampler"] == "ddim"
    
    def test_preset_validation(self):
        """Test preset validation"""
        builder = CustomPresetBuilder()
        
        # Should fail without name
        with pytest.raises(ValueError, match="must have a name"):
            # Clear the name that was set by default
            builder.preset.name = ""
            builder.build()


class TestQualityPresetManager:
    """Test quality preset manager operations"""
    
    @pytest.mark.asyncio
    async def test_apply_preset(self):
        """Test applying preset to template inputs"""
        manager = QualityPresetManager()
        
        # Mock template
        template = Mock(spec=FunctionTemplate)
        template.id = "test_template"
        template.category = "image"
        
        # Mock compatibility checker
        manager.compatibility_checker.check = AsyncMock(
            return_value=Mock(is_compatible=True)
        )
        
        # Mock parameter calculator
        manager.parameter_calculator.calculate = AsyncMock(
            return_value={"width": 512, "height": 512, "steps": 30}
        )
        
        # Apply preset
        result = await manager.apply_preset(
            "standard",
            template,
            {"prompt": "test"}
        )
        
        assert "_quality_preset" in result
        assert result["_quality_preset"]["id"] == "standard"
        assert result["_quality_preset"]["level"] == 2
        assert "estimated_time" in result["_quality_preset"]
    
    @pytest.mark.asyncio
    async def test_preset_not_found(self):
        """Test handling of non-existent preset"""
        manager = QualityPresetManager()
        template = Mock(spec=FunctionTemplate)
        
        with pytest.raises(PresetNotFoundError):
            await manager.apply_preset("nonexistent", template, {})
    
    @pytest.mark.asyncio
    async def test_preset_incompatible(self):
        """Test handling of incompatible preset"""
        manager = QualityPresetManager()
        template = Mock(spec=FunctionTemplate)
        
        # Mock incompatible
        manager.compatibility_checker.check = AsyncMock(
            return_value=Mock(is_compatible=False, reason="Incompatible")
        )
        
        with pytest.raises(PresetIncompatibleError):
            await manager.apply_preset("standard", template, {})
    
    @pytest.mark.asyncio
    async def test_custom_preset_creation(self):
        """Test creating and managing custom presets"""
        storage = Mock(spec=PresetStorage)
        storage.save_preset = AsyncMock(return_value=True)
        
        manager = QualityPresetManager(storage=storage)
        
        preset = QualityPreset(
            id="custom_test",
            name="Test Custom",
            description="Test",
            level=QualityLevel.HIGH,
            is_custom=True
        )
        
        saved = await manager.create_custom_preset(preset, "user123")
        
        assert saved.created_by == "user123"
        assert saved.created_at is not None
        storage.save_preset.assert_called_once()


class TestParameterCalculator:
    """Test parameter calculation based on presets"""
    
    @pytest.mark.asyncio
    async def test_image_parameter_calculation(self):
        """Test image generation parameter calculation"""
        calculator = ParameterCalculator()
        
        preset = QualityPreset(
            id="test",
            name="Test",
            description="Test",
            level=QualityLevel.HIGH,
            parameters={
                "image_generation": {
                    "steps": 50,
                    "cfg_scale": 8.0,
                    "sampler": "dpm++_2m_karras"
                }
            }
        )
        
        template = Mock(spec=FunctionTemplate)
        template.category = "image"
        
        inputs = {"width": 1024, "height": 1024, "prompt": "test"}
        
        result = await calculator.calculate(preset, template, inputs)
        
        assert result["steps"] == 50
        assert result["cfg_scale"] == 8.0
        assert result["sampler"] == "dpm++_2m_karras"
        assert result["_quality_level"] == 3  # HIGH
        assert "_resource_hints" in result
    
    @pytest.mark.asyncio
    async def test_resolution_scaling(self):
        """Test resolution scaling in draft mode"""
        calculator = ParameterCalculator()
        
        preset = QualityPreset(
            id="draft",
            name="Draft",
            description="Draft",
            level=QualityLevel.DRAFT,
            parameters={
                "image_generation": {
                    "resolution_scale": 0.75
                }
            }
        )
        
        template = Mock(spec=FunctionTemplate)
        template.category = "image"
        
        inputs = {"width": 1024, "height": 1024}
        
        result = await calculator.calculate(preset, template, inputs)
        
        assert result["width"] == 768  # 1024 * 0.75
        assert result["height"] == 768
    
    @pytest.mark.asyncio
    async def test_quality_specific_features(self):
        """Test enabling features based on quality level"""
        calculator = ParameterCalculator()
        
        # Ultra quality preset
        preset = QualityPreset(
            id="ultra",
            name="Ultra",
            description="Ultra",
            level=QualityLevel.ULTRA,
            parameters={"image_generation": {}}
        )
        
        template = Mock(spec=FunctionTemplate)
        template.category = "image"
        
        result = await calculator.calculate(preset, template, {"prompt": "test"})
        
        # Ultra should enable high-quality features
        assert result.get("enable_attention_slicing") is False
        assert result.get("enable_hr_fix") is True


class TestQualityComparisonService:
    """Test quality comparison functionality"""
    
    @pytest.mark.asyncio
    async def test_comparison_generation(self):
        """Test generating quality comparisons"""
        service = QualityComparisonService()
        
        # Mock function runner
        mock_task = AsyncMock()
        mock_task.wait = AsyncMock(return_value={"output": "test_output"})
        
        service.function_runner = Mock()
        service.function_runner.submit_task = AsyncMock(return_value=mock_task)
        
        result = await service.generate_comparison(
            template_id="test_template",
            inputs={"prompt": "test"},
            presets=["draft", "standard"]
        )
        
        assert result.template_id == "test_template"
        assert "draft" in result.results
        assert "standard" in result.results
        assert "draft" in result.timings
        assert "standard" in result.timings
        assert result.analysis is not None
    
    @pytest.mark.asyncio
    async def test_comparison_analysis(self):
        """Test comparison analysis generation"""
        service = QualityComparisonService()
        
        # Create mock results
        results = {
            "draft": {"output": "draft_output"},
            "standard": {"output": "standard_output"},
            "high": {"output": "high_output"}
        }
        
        timings = {
            "draft": 10.0,
            "standard": 30.0,
            "high": 75.0
        }
        
        resource_usage = {
            "draft": {"vram_gb": 4.0},
            "standard": {"vram_gb": 6.0},
            "high": {"vram_gb": 8.0}
        }
        
        analysis = await service._analyze_results(
            results, timings, resource_usage, "image_generation"
        )
        
        # Check time ratios
        assert analysis.time_ratios["draft"] == 0.33  # 10/30
        assert analysis.time_ratios["standard"] == 1.0
        assert analysis.time_ratios["high"] == 2.5  # 75/30
        
        # Check recommendations
        assert len(analysis.recommendations) > 0
        
        # Check best value calculation
        assert analysis.best_value_preset in ["draft", "standard", "high"]


class TestQualityRecommendationEngine:
    """Test quality recommendation system"""
    
    @pytest.mark.asyncio
    async def test_use_case_recommendation(self):
        """Test recommendations based on use case"""
        engine = QualityRecommendationEngine()
        
        # Preview use case
        context = RecommendationContext(use_case=UseCase.PREVIEW)
        recommendation = await engine.recommend(context)
        
        assert recommendation.recommended_preset == "draft"
        assert recommendation.confidence > 0.8
        assert "preview" in recommendation.reasoning.lower()
        
        # Final delivery use case
        context = RecommendationContext(use_case=UseCase.FINAL_DELIVERY)
        recommendation = await engine.recommend(context)
        
        assert recommendation.recommended_preset == "ultra"
    
    @pytest.mark.asyncio
    async def test_constraint_based_recommendation(self):
        """Test recommendations with constraints"""
        engine = QualityRecommendationEngine()
        
        # Time constraint
        context = RecommendationContext(
            use_case=UseCase.FINAL_DELIVERY,
            time_constraint=30.0  # 30 seconds max
        )
        
        recommendation = await engine.recommend(context)
        
        # Should downgrade from ultra due to time constraint
        assert recommendation.recommended_preset != "ultra"
        assert recommendation.confidence < 1.0
        assert "time constraint" in recommendation.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_platform_specific_recommendation(self):
        """Test platform-specific recommendations"""
        engine = QualityRecommendationEngine()
        
        context = RecommendationContext(
            target_platform="instagram",
            resolution=(1080, 1080)
        )
        
        recommendation = await engine.recommend(context)
        
        assert recommendation.recommended_preset == "standard"
        assert "instagram" in recommendation.reasoning.lower()
    
    @pytest.mark.asyncio
    async def test_recommendation_alternatives(self):
        """Test alternative preset suggestions"""
        engine = QualityRecommendationEngine()
        
        context = RecommendationContext(use_case=UseCase.REVIEW)
        recommendation = await engine.recommend(context)
        
        assert len(recommendation.alternatives) > 0
        
        # Check alternatives are different from recommended
        for alt in recommendation.alternatives:
            assert alt["preset_id"] != recommendation.recommended_preset
            assert "reason" in alt
            assert "score" in alt


class TestQualityImpactEstimator:
    """Test quality impact estimation"""
    
    @pytest.mark.asyncio
    async def test_time_estimation(self):
        """Test execution time estimation"""
        estimator = QualityImpactEstimator()
        
        template = Mock(spec=FunctionTemplate)
        template.resources.estimated_time_seconds = 60.0
        template.category = "image"
        
        preset = QualityPreset(
            id="high",
            name="High",
            description="High",
            level=QualityLevel.HIGH,
            time_multiplier=2.5
        )
        
        inputs = {"width": 512, "height": 512}
        
        impact = await estimator.estimate_impact(template, preset, inputs)
        
        assert impact.estimated_time.expected_seconds == 150.0  # 60 * 2.5
        assert impact.estimated_time.min_seconds < impact.estimated_time.expected_seconds
        assert impact.estimated_time.max_seconds > impact.estimated_time.expected_seconds
    
    @pytest.mark.asyncio
    async def test_resource_estimation(self):
        """Test resource requirement estimation"""
        estimator = QualityImpactEstimator()
        
        template = Mock(spec=FunctionTemplate)
        template.resources.vram_gb = 6.0
        template.resources.memory_gb = 8.0
        template.resources.cpu_cores = 4
        template.resources.disk_gb = 10.0
        template.category = "image"
        
        preset = QualityPreset(
            id="ultra",
            name="Ultra",
            description="Ultra",
            level=QualityLevel.ULTRA,
            resource_multiplier=2.0
        )
        
        inputs = {"width": 2048, "height": 2048}  # High resolution
        
        impact = await estimator.estimate_impact(template, preset, inputs)
        
        # Check resource scaling
        assert impact.resource_requirements.vram_gb > 12.0  # Base 6 * 2 * resolution factor
        assert impact.resource_requirements.memory_gb > 16.0
        
        # Check warnings for high resource usage
        assert len(impact.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_quality_metrics_estimation(self):
        """Test quality metrics estimation"""
        estimator = QualityImpactEstimator()
        
        template = Mock(spec=FunctionTemplate)
        template.category = "image"
        
        # Test different quality levels
        for level, expected_detail in [
            (QualityLevel.DRAFT, 0.6),
            (QualityLevel.STANDARD, 0.8),
            (QualityLevel.HIGH, 0.9),
            (QualityLevel.ULTRA, 0.95)
        ]:
            preset = QualityPreset(
                id=f"test_{level}",
                name=f"Test {level}",
                description="Test",
                level=level,
                parameters={"image_generation": {"resolution_scale": 1.0}}
            )
            
            impact = await estimator.estimate_impact(
                template, preset, {"width": 1024, "height": 1024}
            )
            
            assert impact.quality_metrics.detail_level == expected_detail
            assert impact.quality_metrics.resolution == (1024, 1024)


class TestPresetStorage:
    """Test preset storage functionality"""
    
    @pytest.mark.asyncio
    async def test_save_and_load_preset(self, tmp_path):
        """Test saving and loading custom presets"""
        storage = PresetStorage(storage_path=tmp_path)
        
        preset = QualityPreset(
            id="custom_123",
            name="My Custom",
            description="Custom preset",
            level=QualityLevel.HIGH,
            is_custom=True,
            created_by="user123",
            created_at=datetime.now()
        )
        
        # Save preset
        success = await storage.save_preset(preset, "user123")
        assert success
        
        # Load preset
        loaded = await storage.get_preset("custom_123", "user123")
        assert loaded is not None
        assert loaded.id == preset.id
        assert loaded.name == preset.name
        assert loaded.level == preset.level
    
    @pytest.mark.asyncio
    async def test_user_preset_isolation(self, tmp_path):
        """Test that user presets are isolated"""
        storage = PresetStorage(storage_path=tmp_path)
        
        # Save preset for user1
        preset1 = QualityPreset(
            id="preset1",
            name="User1 Preset",
            description="Test",
            level=QualityLevel.STANDARD,
            is_custom=True
        )
        await storage.save_preset(preset1, "user1")
        
        # Save preset for user2
        preset2 = QualityPreset(
            id="preset2",
            name="User2 Preset",
            description="Test",
            level=QualityLevel.HIGH,
            is_custom=True
        )
        await storage.save_preset(preset2, "user2")
        
        # Check user1 presets
        user1_presets = await storage.get_user_presets("user1")
        assert len(user1_presets) == 1
        assert user1_presets[0].id == "preset1"
        
        # Check user2 presets
        user2_presets = await storage.get_user_presets("user2")
        assert len(user2_presets) == 1
        assert user2_presets[0].id == "preset2"
    
    @pytest.mark.asyncio
    async def test_preset_sharing(self, tmp_path):
        """Test sharing presets between users"""
        storage = PresetStorage(storage_path=tmp_path)
        
        preset = QualityPreset(
            id="shared_preset",
            name="Shared Preset",
            description="To be shared",
            level=QualityLevel.HIGH,
            is_custom=True,
            created_by="user1"
        )
        
        # Save and share
        await storage.save_preset(preset, "user1")
        success = await storage.share_preset("shared_preset", "user1")
        assert success
        
        # Check shared presets
        shared = await storage.get_shared_presets()
        assert len(shared) == 1
        assert shared[0].id == "shared_preset"
    
    @pytest.mark.asyncio
    async def test_preset_export_import(self, tmp_path):
        """Test exporting and importing presets"""
        storage = PresetStorage(storage_path=tmp_path)
        
        # Create and save preset
        preset = QualityPreset(
            id="export_test",
            name="Export Test",
            description="Test export",
            level=QualityLevel.HIGH,
            is_custom=True,
            parameters={"image_generation": {"steps": 50}}
        )
        await storage.save_preset(preset, "user1")
        
        # Export preset
        export_path = await storage.export_preset("export_test", "user1")
        assert export_path is not None
        
        # Read exported data
        import json
        with open(export_path, 'r') as f:
            export_data = json.load(f)
        
        # Import as different user
        imported = await storage.import_preset(export_data, "user2")
        assert imported.name == preset.name
        assert imported.id != preset.id  # Should have new ID
        assert imported.created_by == "user2"
        assert imported.parameters == preset.parameters


class TestIntegration:
    """Integration tests for the quality preset system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self, tmp_path):
        """Test complete workflow from preset creation to application"""
        # Setup
        storage = PresetStorage(storage_path=tmp_path)
        manager = QualityPresetManager(storage=storage)
        
        # Create custom preset
        builder = CustomPresetBuilder()
        custom_preset = (builder
                        .with_name("Fast Preview")
                        .with_description("Optimized for quick previews")
                        .based_on("draft")
                        .with_parameters("image_generation", {"steps": 10})
                        .build())
        
        # Save preset
        saved = await manager.create_custom_preset(custom_preset, "user123")
        
        # Create template
        template = Mock(spec=FunctionTemplate)
        template.id = "sd_generate"
        template.category = "image"
        template.resources.estimated_time_seconds = 30.0
        
        # Mock compatibility
        manager.compatibility_checker.check = AsyncMock(
            return_value=Mock(is_compatible=True)
        )
        
        # Apply preset
        inputs = {"prompt": "a beautiful sunset", "width": 512, "height": 512}
        result = await manager.apply_preset(saved.id, template, inputs)
        
        # Verify results
        assert result["_quality_preset"]["id"] == saved.id
        assert result.get("steps") == 10  # From custom parameters
        assert "prompt" in result  # Original input preserved
    
    @pytest.mark.asyncio
    async def test_recommendation_to_execution(self):
        """Test from recommendation to execution"""
        # Setup services
        engine = QualityRecommendationEngine()
        manager = QualityPresetManager()
        estimator = QualityImpactEstimator()
        
        # Get recommendation
        context = RecommendationContext(
            use_case=UseCase.SOCIAL_MEDIA,
            target_platform="instagram",
            resolution=(1080, 1080),
            time_constraint=60.0
        )
        
        recommendation = await engine.recommend(context)
        
        # Get recommended preset
        preset = await manager.get_preset(recommendation.recommended_preset)
        assert preset is not None
        
        # Estimate impact
        template = Mock(spec=FunctionTemplate)
        template.resources.estimated_time_seconds = 30.0
        template.resources.vram_gb = 6.0
        template.resources.memory_gb = 8.0
        template.category = "image"
        
        impact = await estimator.estimate_impact(
            template,
            preset,
            {"width": 1080, "height": 1080}
        )
        
        # Verify estimates align with constraints
        assert impact.estimated_time.expected_seconds <= context.time_constraint * 1.5
        assert impact.quality_metrics.detail_level >= 0.7  # Acceptable quality