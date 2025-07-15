"""
Tests for the template validation pipeline
"""

import pytest
import asyncio
from pathlib import Path

from app.templates import (
    TemplateValidationPipeline,
    ValidationContext,
    ValidationResultFormatter,
    OutputFormat,
    Severity,
    SchemaValidator,
    TypeValidator,
    ResourceValidator,
    ExampleValidator,
    DependencyValidator,
    UniquenessValidator
)


@pytest.fixture
def valid_template():
    """A valid template definition"""
    return {
        "template": {
            "id": "test_template",
            "name": "Test Template",
            "version": "1.0.0",
            "description": "A test template",
            "category": "generation",
            "author": "Test Author",
            "tags": ["test", "sample"],
            "interface": {
                "inputs": {
                    "prompt": {
                        "type": "string",
                        "description": "Input prompt",
                        "required": True,
                        "min_length": 1,
                        "max_length": 1000
                    },
                    "quality": {
                        "type": "string",
                        "description": "Quality level",
                        "required": False,
                        "default": "standard",
                        "enum": ["draft", "standard", "high"]
                    },
                    "seed": {
                        "type": "integer",
                        "description": "Random seed",
                        "required": False,
                        "min": 0,
                        "max": 2147483647
                    }
                },
                "outputs": {
                    "image": {
                        "type": "file",
                        "description": "Generated image",
                        "format": ["png", "jpg"]
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Generation metadata"
                    }
                }
            },
            "requirements": {
                "resources": {
                    "gpu": True,
                    "vram_gb": 8,
                    "cpu_cores": 2,
                    "memory_gb": 16
                },
                "models": [
                    {
                        "name": "stable-diffusion-v1-5",
                        "type": "checkpoint",
                        "size_gb": 4.2
                    }
                ],
                "quality_presets": {
                    "draft": {
                        "steps": 20
                    },
                    "standard": {
                        "steps": 30
                    },
                    "high": {
                        "steps": 50
                    }
                }
            },
            "examples": [
                {
                    "name": "Basic Example",
                    "inputs": {
                        "prompt": "A beautiful landscape",
                        "quality": "standard"
                    }
                }
            ]
        }
    }


@pytest.fixture
def pipeline():
    """Create validation pipeline"""
    return TemplateValidationPipeline()


@pytest.fixture
def context():
    """Create validation context"""
    return ValidationContext(
        strict_mode=False,
        check_uniqueness=True,
        check_dependencies=True
    )


class TestSchemaValidator:
    """Test schema validation stage"""
    
    @pytest.mark.asyncio
    async def test_valid_schema(self, valid_template, context):
        """Test validation passes for valid schema"""
        validator = SchemaValidator()
        result = await validator.validate(valid_template, context)
        
        assert len(result.errors) == 0
        assert result.stage == "schema"
    
    @pytest.mark.asyncio
    async def test_missing_required_fields(self, context):
        """Test validation fails for missing required fields"""
        template = {"template": {"id": "test"}}  # Missing required fields
        
        validator = SchemaValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any(e.severity == Severity.CRITICAL for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_invalid_id_format(self, valid_template, context):
        """Test validation fails for invalid ID format"""
        template = valid_template.copy()
        template["template"]["id"] = "Invalid-ID!"
        
        validator = SchemaValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("ID contains invalid characters" in e.message for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_invalid_version_format(self, valid_template, context):
        """Test validation fails for invalid version format"""
        template = valid_template.copy()
        template["template"]["version"] = "1.0"  # Invalid semver
        
        validator = SchemaValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("Invalid semantic version" in e.message for e in result.errors)


class TestTypeValidator:
    """Test type validation stage"""
    
    @pytest.mark.asyncio
    async def test_valid_types(self, valid_template, context):
        """Test validation passes for valid types"""
        validator = TypeValidator()
        result = await validator.validate(valid_template, context)
        
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_invalid_parameter_type(self, valid_template, context):
        """Test validation fails for invalid parameter type"""
        template = valid_template.copy()
        template["template"]["interface"]["inputs"]["test"] = {
            "type": "invalid_type",
            "description": "Test"
        }
        
        validator = TypeValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("Invalid type" in e.message for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_invalid_constraints(self, valid_template, context):
        """Test validation warns for invalid constraints"""
        template = valid_template.copy()
        template["template"]["interface"]["inputs"]["prompt"]["min"] = 10  # Invalid for string
        
        validator = TypeValidator()
        result = await validator.validate(template, context)
        
        assert len(result.warnings) > 0
        assert any("not applicable to type 'string'" in w.message for w in result.warnings)
    
    @pytest.mark.asyncio
    async def test_invalid_default_value(self, valid_template, context):
        """Test validation fails for invalid default value"""
        template = valid_template.copy()
        template["template"]["interface"]["inputs"]["quality"]["default"] = "invalid"
        
        validator = TypeValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("Default value must be one of the enum values" in e.message for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_conflicting_constraints(self, valid_template, context):
        """Test validation fails for conflicting constraints"""
        template = valid_template.copy()
        template["template"]["interface"]["inputs"]["seed"]["min"] = 100
        template["template"]["interface"]["inputs"]["seed"]["max"] = 50
        
        validator = TypeValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("min value cannot be greater than max" in e.message for e in result.errors)


class TestResourceValidator:
    """Test resource validation stage"""
    
    @pytest.mark.asyncio
    async def test_valid_resources(self, valid_template, context):
        """Test validation passes for valid resources"""
        validator = ResourceValidator()
        result = await validator.validate(valid_template, context)
        
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_missing_gpu_vram(self, valid_template, context):
        """Test validation fails when GPU template missing VRAM"""
        template = valid_template.copy()
        template["template"]["requirements"]["resources"]["vram_gb"] = 0
        
        validator = ResourceValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("must specify positive VRAM" in e.message for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_excessive_resources(self, valid_template, context):
        """Test validation warns for excessive resources"""
        template = valid_template.copy()
        template["template"]["requirements"]["resources"]["vram_gb"] = 100
        template["template"]["requirements"]["resources"]["cpu_cores"] = 200
        
        validator = ResourceValidator()
        result = await validator.validate(template, context)
        
        assert len(result.warnings) > 0
        assert any("exceeds typical hardware" in w.message for w in result.warnings)
    
    @pytest.mark.asyncio
    async def test_invalid_quality_presets(self, valid_template, context):
        """Test validation fails for invalid quality presets"""
        template = valid_template.copy()
        template["template"]["requirements"]["quality_presets"]["invalid"] = {}
        
        validator = ResourceValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("not in quality input enum" in e.message for e in result.errors)


class TestExampleValidator:
    """Test example validation stage"""
    
    @pytest.mark.asyncio
    async def test_valid_examples(self, valid_template, context):
        """Test validation passes for valid examples"""
        validator = ExampleValidator()
        result = await validator.validate(valid_template, context)
        
        assert len(result.errors) == 0
    
    @pytest.mark.asyncio
    async def test_missing_required_inputs(self, valid_template, context):
        """Test validation fails when example missing required inputs"""
        template = valid_template.copy()
        template["template"]["examples"][0]["inputs"] = {"quality": "standard"}  # Missing prompt
        
        validator = ExampleValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("missing required input" in e.message for e in result.errors)
    
    @pytest.mark.asyncio
    async def test_unknown_inputs(self, valid_template, context):
        """Test validation warns for unknown inputs"""
        template = valid_template.copy()
        template["template"]["examples"][0]["inputs"]["unknown"] = "value"
        
        validator = ExampleValidator()
        result = await validator.validate(template, context)
        
        assert len(result.warnings) > 0
        assert any("unknown input" in w.message for w in result.warnings)
    
    @pytest.mark.asyncio
    async def test_duplicate_example_names(self, valid_template, context):
        """Test validation fails for duplicate example names"""
        template = valid_template.copy()
        template["template"]["examples"].append({
            "name": "Basic Example",  # Duplicate name
            "inputs": {"prompt": "Another prompt"}
        })
        
        validator = ExampleValidator()
        result = await validator.validate(template, context)
        
        assert len(result.errors) > 0
        assert any("Duplicate example name" in e.message for e in result.errors)


class TestValidationPipeline:
    """Test complete validation pipeline"""
    
    @pytest.mark.asyncio
    async def test_valid_template(self, valid_template, pipeline, context):
        """Test pipeline passes valid template"""
        result = await pipeline.validate(valid_template, context)
        
        assert result.is_valid()
        assert len(result.errors) == 0
        assert "schema" in result.stages_completed
        assert "types" in result.stages_completed
        assert "resources" in result.stages_completed
        assert "examples" in result.stages_completed
    
    @pytest.mark.asyncio
    async def test_critical_error_stops_pipeline(self, pipeline, context):
        """Test pipeline stops on critical errors"""
        template = {"invalid": "structure"}
        
        result = await pipeline.validate(template, context)
        
        assert not result.is_valid()
        assert len(result.errors) > 0
        assert len(result.stages_completed) < 6  # Should stop early
    
    @pytest.mark.asyncio
    async def test_caching(self, valid_template, pipeline, context):
        """Test validation results are cached"""
        # First validation
        result1 = await pipeline.validate(valid_template, context)
        assert not result1.cached
        
        # Second validation should be cached
        result2 = await pipeline.validate(valid_template, context)
        assert result2.cached
        assert result2.is_valid() == result1.is_valid()
    
    @pytest.mark.asyncio
    async def test_batch_validation(self, valid_template, pipeline, context, tmp_path):
        """Test batch validation of multiple templates"""
        # Create test files
        file1 = tmp_path / "template1.yaml"
        file2 = tmp_path / "template2.yaml"
        file3 = tmp_path / "invalid.yaml"
        
        import yaml
        
        # Valid template
        with open(file1, 'w') as f:
            yaml.dump(valid_template, f)
        
        # Another valid template
        template2 = valid_template.copy()
        template2["template"]["id"] = "test_template_2"
        with open(file2, 'w') as f:
            yaml.dump(template2, f)
        
        # Invalid template
        with open(file3, 'w') as f:
            yaml.dump({"invalid": "template"}, f)
        
        # Run batch validation
        results = await pipeline.validate_batch([file1, file2, file3], context)
        
        assert len(results) == 3
        assert results[str(file1)].is_valid()
        assert results[str(file2)].is_valid()
        assert not results[str(file3)].is_valid()


class TestValidationFormatter:
    """Test validation result formatting"""
    
    @pytest.mark.asyncio
    async def test_cli_format(self, valid_template, pipeline, context):
        """Test CLI formatting"""
        result = await pipeline.validate(valid_template, context)
        formatter = ValidationResultFormatter()
        
        output = formatter.format_cli(result, use_color=False)
        
        assert "✅ VALID" in output
        assert "Template: test_template v1.0.0" in output
        assert "Stages completed:" in output
    
    @pytest.mark.asyncio
    async def test_json_format(self, valid_template, pipeline, context):
        """Test JSON formatting"""
        result = await pipeline.validate(valid_template, context)
        formatter = ValidationResultFormatter()
        
        output = formatter.format_json(result)
        
        assert output["valid"] == True
        assert output["template_id"] == "test_template"
        assert output["version"] == "1.0.0"
        assert len(output["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_markdown_format(self, valid_template, pipeline, context):
        """Test Markdown formatting"""
        result = await pipeline.validate(valid_template, context)
        formatter = ValidationResultFormatter()
        
        output = formatter.format_markdown(result)
        
        assert "# Template Validation Result" in output
        assert "**Status:** ✅ VALID" in output
        assert "## Validation Details" in output
    
    @pytest.mark.asyncio
    async def test_html_format(self, valid_template, pipeline, context):
        """Test HTML formatting"""
        result = await pipeline.validate(valid_template, context)
        formatter = ValidationResultFormatter()
        
        output = formatter.format_html(result)
        
        assert '<div class="validation-result">' in output
        assert 'validation-status valid' in output
        assert 'Template: <strong>test_template</strong>' in output
    
    @pytest.mark.asyncio
    async def test_error_formatting(self, pipeline, context):
        """Test error formatting"""
        template = {
            "template": {
                "id": "Invalid-ID!",
                "name": "Test",
                "version": "1.0",
                "interface": {},
                "requirements": {}
            }
        }
        
        result = await pipeline.validate(template, context)
        formatter = ValidationResultFormatter()
        
        cli_output = formatter.format_cli(result, use_color=False)
        assert "❌ INVALID" in cli_output
        assert "Errors:" in cli_output
        
        json_output = formatter.format_json(result)
        assert json_output["valid"] == False
        assert len(json_output["errors"]) > 0


class TestValidationContext:
    """Test validation context options"""
    
    @pytest.mark.asyncio
    async def test_strict_mode(self, valid_template, pipeline):
        """Test strict mode validation"""
        strict_context = ValidationContext(
            strict_mode=True,
            check_uniqueness=True,
            check_dependencies=True
        )
        
        # Add a warning-level issue
        template = valid_template.copy()
        template["template"]["requirements"]["resources"]["cpu_cores"] = 64
        
        result = await pipeline.validate(template, strict_context)
        
        # In strict mode, warnings might be treated more seriously
        assert len(result.warnings) > 0
    
    @pytest.mark.asyncio
    async def test_skip_uniqueness_check(self, valid_template, pipeline):
        """Test skipping uniqueness check"""
        context = ValidationContext(
            strict_mode=False,
            check_uniqueness=False,
            check_dependencies=True
        )
        
        result = await pipeline.validate(valid_template, context)
        
        # Uniqueness stage should add info about being skipped
        uniqueness_stage_result = [
            i for i in result.info 
            if i.stage == "uniqueness" and "skipped" in i.message
        ]
        assert len(uniqueness_stage_result) > 0