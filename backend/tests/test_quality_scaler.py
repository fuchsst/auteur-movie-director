"""
Tests for quality-based resource scaling
"""

import pytest

from app.resources import ResourceSpec, QualityResourceScaler


@pytest.fixture
def scaler():
    """Create quality scaler instance"""
    return QualityResourceScaler()


@pytest.fixture
def base_spec():
    """Base resource specification"""
    return ResourceSpec(
        cpu_cores=2.0,
        memory_gb=4.0,
        gpu_count=1,
        gpu_memory_gb=8.0,
        disk_gb=50.0
    )


class TestQualityResourceScaler:
    """Test quality-based resource scaling"""
    
    def test_draft_quality_scaling(self, scaler, base_spec):
        """Test draft quality reduces resources"""
        scaled = scaler.scale_requirements(base_spec, "draft")
        
        assert scaled.cpu_cores < base_spec.cpu_cores
        assert scaled.memory_gb < base_spec.memory_gb
        assert scaled.gpu_memory_gb < base_spec.gpu_memory_gb
        assert scaled.gpu_count == base_spec.gpu_count  # GPU count doesn't scale
    
    def test_standard_quality_unchanged(self, scaler, base_spec):
        """Test standard quality keeps resources unchanged"""
        scaled = scaler.scale_requirements(base_spec, "standard")
        
        assert scaled.cpu_cores == base_spec.cpu_cores
        assert scaled.memory_gb == base_spec.memory_gb
        assert scaled.gpu_memory_gb == base_spec.gpu_memory_gb
        assert scaled.gpu_count == base_spec.gpu_count
    
    def test_high_quality_scaling(self, scaler, base_spec):
        """Test high quality increases resources"""
        scaled = scaler.scale_requirements(base_spec, "high")
        
        assert scaled.cpu_cores > base_spec.cpu_cores
        assert scaled.memory_gb > base_spec.memory_gb
        assert scaled.gpu_memory_gb > base_spec.gpu_memory_gb
        assert scaled.gpu_count == base_spec.gpu_count
    
    def test_ultra_quality_scaling(self, scaler, base_spec):
        """Test ultra quality significantly increases resources"""
        scaled = scaler.scale_requirements(base_spec, "ultra")
        
        assert scaled.cpu_cores > base_spec.cpu_cores * 1.5
        assert scaled.memory_gb > base_spec.memory_gb * 1.2
        assert scaled.gpu_memory_gb > base_spec.gpu_memory_gb * 1.2
    
    def test_unknown_quality_fallback(self, scaler, base_spec):
        """Test unknown quality falls back to standard"""
        scaled = scaler.scale_requirements(base_spec, "unknown")
        
        # Should be same as standard
        assert scaled.cpu_cores == base_spec.cpu_cores
        assert scaled.memory_gb == base_spec.memory_gb
    
    def test_task_specific_scaling(self, scaler, base_spec):
        """Test task-specific scaling overrides"""
        # Image generation has specific scaling
        scaled = scaler.scale_requirements(base_spec, "ultra", "image_generation")
        
        # Should have different scaling than generic ultra
        assert scaled.gpu_memory_gb > base_spec.gpu_memory_gb * 1.5
    
    def test_custom_scaling(self, scaler, base_spec):
        """Test custom scaling factors"""
        custom_scaling = {"cpu": 3.0, "memory": 2.0}
        
        scaled = scaler.scale_requirements(
            base_spec, 
            "standard", 
            custom_scaling=custom_scaling
        )
        
        assert scaled.cpu_cores == base_spec.cpu_cores * 3.0
        assert scaled.memory_gb == base_spec.memory_gb * 2.0
    
    def test_duration_estimation(self, scaler):
        """Test duration estimation scaling"""
        base_duration = 100.0  # seconds
        
        draft_duration = scaler.estimate_duration(base_duration, "draft")
        standard_duration = scaler.estimate_duration(base_duration, "standard")
        ultra_duration = scaler.estimate_duration(base_duration, "ultra")
        
        assert draft_duration < standard_duration < ultra_duration
        assert standard_duration == base_duration  # Standard is 1.0x
    
    def test_task_specific_duration(self, scaler):
        """Test task-specific duration estimation"""
        base_duration = 100.0
        
        # Image generation has specific time scaling
        duration = scaler.estimate_duration(
            base_duration, 
            "ultra", 
            "image_generation"
        )
        
        # Should be different from generic ultra
        assert duration > base_duration * 4.0  # Image gen ultra is 6x
    
    def test_priority_levels(self, scaler):
        """Test priority assignment by quality"""
        draft_priority = scaler.get_priority("draft")
        standard_priority = scaler.get_priority("standard")
        high_priority = scaler.get_priority("high")
        ultra_priority = scaler.get_priority("ultra")
        
        assert draft_priority < standard_priority < high_priority < ultra_priority
    
    def test_quality_info(self, scaler):
        """Test getting quality level information"""
        info = scaler.get_quality_info("high")
        
        assert info["valid"] is True
        assert info["quality"] == "high"
        assert "multipliers" in info
        assert "priority" in info
        assert "description" in info
    
    def test_invalid_quality_info(self, scaler):
        """Test getting info for invalid quality"""
        info = scaler.get_quality_info("invalid")
        
        assert info["valid"] is False
        assert "error" in info
    
    def test_quality_recommendation(self, scaler, base_spec):
        """Test quality recommendation based on available resources"""
        # Large available resources - should recommend preferred
        large_available = ResourceSpec(
            cpu_cores=8.0,
            memory_gb=16.0,
            gpu_count=1,
            gpu_memory_gb=16.0,
            disk_gb=100.0  # Ensure enough disk space
        )
        
        recommended = scaler.recommend_quality(
            large_available,
            base_spec,
            "ultra"
        )
        
        assert recommended == "ultra"
    
    def test_quality_recommendation_constrained(self, scaler, base_spec):
        """Test quality recommendation with limited resources"""
        # Small available resources - should recommend lower quality
        small_available = ResourceSpec(
            cpu_cores=1.0,
            memory_gb=2.0,
            gpu_count=1,
            gpu_memory_gb=4.0,
            disk_gb=100.0  # Ensure enough disk space
        )
        
        recommended = scaler.recommend_quality(
            small_available,
            base_spec,
            "ultra"
        )
        
        # Should recommend lower quality
        assert recommended in ["draft", "standard"]
    
    def test_all_quality_requirements(self, scaler, base_spec):
        """Test getting requirements for all quality levels"""
        all_reqs = scaler.get_all_quality_requirements(base_spec, "image_generation")
        
        assert "draft" in all_reqs
        assert "standard" in all_reqs
        assert "high" in all_reqs
        assert "ultra" in all_reqs
        
        # Verify scaling order
        draft_cpu = all_reqs["draft"].cpu_cores
        standard_cpu = all_reqs["standard"].cpu_cores
        high_cpu = all_reqs["high"].cpu_cores
        ultra_cpu = all_reqs["ultra"].cpu_cores
        
        assert draft_cpu <= standard_cpu <= high_cpu <= ultra_cpu
    
    def test_minimum_resource_bounds(self, scaler):
        """Test that scaling doesn't go below minimum bounds"""
        tiny_spec = ResourceSpec(cpu_cores=0.1, memory_gb=0.1)
        
        # Even draft quality should maintain minimums
        scaled = scaler.scale_requirements(tiny_spec, "draft")
        
        assert scaled.cpu_cores >= 0.1
        assert scaled.memory_gb >= 0.1
    
    def test_resource_rounding(self, scaler, base_spec):
        """Test that scaled resources are rounded appropriately"""
        scaled = scaler.scale_requirements(base_spec, "high")
        
        # Check that values are rounded to reasonable precision
        assert scaled.cpu_cores == round(scaled.cpu_cores, 1)
        assert scaled.memory_gb == round(scaled.memory_gb, 1)
        assert scaled.gpu_memory_gb == round(scaled.gpu_memory_gb, 1)


class TestCustomQualityLevels:
    """Test custom quality level configuration"""
    
    def test_custom_multipliers(self):
        """Test scaler with custom multipliers"""
        custom_multipliers = {
            "custom_quality": {
                "cpu": 2.5,
                "memory": 1.8,
                "gpu_memory": 1.5,
                "time": 3.0,
                "priority": 3
            }
        }
        
        scaler = QualityResourceScaler(custom_multipliers)
        
        base_spec = ResourceSpec(cpu_cores=2.0, memory_gb=4.0, gpu_memory_gb=8.0)
        scaled = scaler.scale_requirements(base_spec, "custom_quality")
        
        assert scaled.cpu_cores == 2.0 * 2.5
        assert scaled.memory_gb == 4.0 * 1.8
        assert scaled.gpu_memory_gb == 8.0 * 1.5
    
    def test_override_existing_quality(self):
        """Test overriding existing quality level"""
        custom_multipliers = {
            "standard": {
                "cpu": 0.8,  # Override standard to be slightly lower
                "memory": 0.9,
                "time": 0.8
            }
        }
        
        scaler = QualityResourceScaler(custom_multipliers)
        
        base_spec = ResourceSpec(cpu_cores=2.0, memory_gb=4.0)
        scaled = scaler.scale_requirements(base_spec, "standard")
        
        assert scaled.cpu_cores == 2.0 * 0.8
        assert scaled.memory_gb == 4.0 * 0.9