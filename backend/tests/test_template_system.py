"""
Tests for Function Template System
"""

import pytest
import asyncio
import yaml
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

from app.templates import (
    FunctionTemplate, TemplateRegistry, TemplateValidator,
    TemplateValidationError, TemplateNotFoundError,
    InputParameter, OutputParameter, ParameterType
)
from app.templates.base import ResourceRequirements, QualityPreset


class TestFunctionTemplate:
    """Test FunctionTemplate class"""
    
    @pytest.fixture
    def sample_template_definition(self):
        """Sample template definition"""
        return {
            'template': {
                'id': 'test_function',
                'name': 'Test Function',
                'version': '1.0.0',
                'description': 'A test function template',
                'category': 'processing',
                'author': 'Test Author',
                'tags': ['test', 'sample'],
                'interface': {
                    'inputs': {
                        'text': {
                            'type': 'string',
                            'description': 'Input text',
                            'required': True,
                            'min_length': 1,
                            'max_length': 100
                        },
                        'count': {
                            'type': 'integer',
                            'description': 'Repeat count',
                            'required': False,
                            'default': 1,
                            'min': 1,
                            'max': 10
                        },
                        'mode': {
                            'type': 'string',
                            'description': 'Processing mode',
                            'required': False,
                            'default': 'normal',
                            'enum': ['normal', 'fast', 'accurate']
                        }
                    },
                    'outputs': {
                        'result': {
                            'type': 'string',
                            'description': 'Processed result'
                        },
                        'stats': {
                            'type': 'object',
                            'description': 'Processing statistics'
                        }
                    }
                },
                'requirements': {
                    'resources': {
                        'gpu': False,
                        'cpu_cores': 2,
                        'memory_gb': 4.0
                    },
                    'quality_presets': {
                        'normal': {'iterations': 10},
                        'fast': {'iterations': 5},
                        'accurate': {'iterations': 20}
                    }
                },
                'examples': [
                    {
                        'name': 'Basic Example',
                        'inputs': {
                            'text': 'Hello World',
                            'count': 2
                        }
                    }
                ]
            }
        }
    
    def test_template_initialization(self, sample_template_definition):
        """Test template initialization from definition"""
        template = FunctionTemplate(sample_template_definition)
        
        assert template.id == 'test_function'
        assert template.name == 'Test Function'
        assert template.version == '1.0.0'
        assert template.category == 'processing'
        assert template.author == 'Test Author'
        assert 'test' in template.tags
        
        # Check interface
        assert len(template.interface.inputs) == 3
        assert len(template.interface.outputs) == 2
        assert 'text' in template.interface.inputs
        assert template.interface.inputs['text'].required is True
        
        # Check resources
        assert template.resources.gpu is False
        assert template.resources.cpu_cores == 2
        assert template.resources.memory_gb == 4.0
        
        # Check quality presets
        assert len(template.quality_presets) == 3
        assert 'normal' in template.quality_presets
    
    def test_input_validation_valid(self, sample_template_definition):
        """Test input validation with valid inputs"""
        template = FunctionTemplate(sample_template_definition)
        
        # Valid inputs
        inputs = {
            'text': 'Hello World',
            'count': 5,
            'mode': 'fast'
        }
        
        validated = template.validate_inputs(inputs)
        assert validated['text'] == 'Hello World'
        assert validated['count'] == 5
        assert validated['mode'] == 'fast'
    
    def test_input_validation_defaults(self, sample_template_definition):
        """Test input validation with defaults"""
        template = FunctionTemplate(sample_template_definition)
        
        # Only required input
        inputs = {'text': 'Hello'}
        
        validated = template.validate_inputs(inputs)
        assert validated['text'] == 'Hello'
        assert validated['count'] == 1  # Default value
        assert validated['mode'] == 'normal'  # Default value
    
    def test_input_validation_invalid(self, sample_template_definition):
        """Test input validation with invalid inputs"""
        template = FunctionTemplate(sample_template_definition)
        
        # Missing required field
        with pytest.raises(TemplateValidationError) as exc_info:
            template.validate_inputs({})
        assert 'text' in str(exc_info.value)
        
        # Invalid type
        with pytest.raises(TemplateValidationError):
            template.validate_inputs({'text': 123})  # Should be string
        
        # Out of range
        with pytest.raises(TemplateValidationError):
            template.validate_inputs({'text': 'Hello', 'count': 20})  # Max is 10
        
        # Invalid enum value
        with pytest.raises(TemplateValidationError):
            template.validate_inputs({'text': 'Hello', 'mode': 'invalid'})
        
        # String too long
        with pytest.raises(TemplateValidationError):
            template.validate_inputs({'text': 'x' * 101})  # Max length is 100
    
    def test_resource_requirements(self, sample_template_definition):
        """Test resource requirement calculation"""
        template = FunctionTemplate(sample_template_definition)
        
        # Base requirements
        reqs = template.get_resource_requirements({})
        assert reqs.gpu is False
        assert reqs.cpu_cores == 2
        assert reqs.memory_gb == 4.0
    
    def test_quality_parameters(self, sample_template_definition):
        """Test quality preset parameters"""
        template = FunctionTemplate(sample_template_definition)
        
        params = template.get_quality_parameters('fast')
        assert params['iterations'] == 5
        
        with pytest.raises(ValueError):
            template.get_quality_parameters('invalid')
    
    def test_openapi_schema_generation(self, sample_template_definition):
        """Test OpenAPI schema generation"""
        template = FunctionTemplate(sample_template_definition)
        
        schema = template.to_openapi_schema()
        assert schema['operationId'] == 'test_function_execute'
        assert schema['summary'] == 'Test Function'
        assert 'processing' in schema['tags']
        assert 'requestBody' in schema
        assert 'responses' in schema


class TestTemplateValidator:
    """Test template validation"""
    
    def test_valid_template(self):
        """Test validation of valid template"""
        validator = TemplateValidator()
        
        definition = {
            'template': {
                'id': 'valid_template',
                'name': 'Valid Template',
                'version': '1.0.0',
                'interface': {
                    'inputs': {},
                    'outputs': {
                        'result': {'type': 'string'}
                    }
                },
                'requirements': {
                    'resources': {}
                }
            }
        }
        
        errors = validator.validate(definition)
        assert len(errors) == 0
    
    def test_missing_required_fields(self):
        """Test validation with missing required fields"""
        validator = TemplateValidator()
        
        # Missing template key
        errors = validator.validate({})
        assert len(errors) > 0
        
        # Missing required fields
        definition = {'template': {}}
        errors = validator.validate(definition)
        assert len(errors) > 0
        assert any('id' in error for error in errors)
    
    def test_invalid_id_format(self):
        """Test validation of invalid ID format"""
        validator = TemplateValidator()
        
        definition = {
            'template': {
                'id': 'Invalid-ID',  # Should be lowercase with underscores
                'name': 'Test',
                'version': '1.0.0',
                'interface': {'inputs': {}, 'outputs': {'result': {'type': 'string'}}},
                'requirements': {'resources': {}}
            }
        }
        
        errors = validator.validate(definition)
        assert any('id' in error for error in errors)
    
    def test_invalid_version_format(self):
        """Test validation of invalid version format"""
        validator = TemplateValidator()
        
        definition = {
            'template': {
                'id': 'test',
                'name': 'Test',
                'version': '1.0',  # Should be semantic version
                'interface': {'inputs': {}, 'outputs': {'result': {'type': 'string'}}},
                'requirements': {'resources': {}}
            }
        }
        
        errors = validator.validate(definition)
        assert any('version' in error for error in errors)
    
    def test_constraint_validation(self):
        """Test parameter constraint validation"""
        validator = TemplateValidator()
        
        definition = {
            'template': {
                'id': 'test',
                'name': 'Test',
                'version': '1.0.0',
                'interface': {
                    'inputs': {
                        'text': {
                            'type': 'string',
                            'min': 10  # Invalid: min/max for string type
                        }
                    },
                    'outputs': {'result': {'type': 'string'}}
                },
                'requirements': {'resources': {}}
            }
        }
        
        errors = validator.validate(definition)
        assert any('min/max constraints only valid for numeric types' in error for error in errors)
    
    def test_example_validation(self):
        """Test example validation against interface"""
        validator = TemplateValidator()
        
        definition = {
            'template': {
                'id': 'test',
                'name': 'Test',
                'version': '1.0.0',
                'interface': {
                    'inputs': {
                        'required_field': {
                            'type': 'string',
                            'required': True
                        }
                    },
                    'outputs': {'result': {'type': 'string'}}
                },
                'requirements': {'resources': {}},
                'examples': [
                    {
                        'name': 'Bad Example',
                        'inputs': {}  # Missing required field
                    }
                ]
            }
        }
        
        errors = validator.validate(definition)
        assert any('missing required input' in error for error in errors)


class TestTemplateRegistry:
    """Test template registry functionality"""
    
    @pytest.fixture
    async def temp_template_dir(self):
        """Create temporary template directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    async def sample_registry(self, temp_template_dir):
        """Create registry with sample templates"""
        # Create sample template files
        template1 = {
            'template': {
                'id': 'template1',
                'name': 'Template 1',
                'version': '1.0.0',
                'category': 'generation',
                'interface': {
                    'inputs': {},
                    'outputs': {'result': {'type': 'string'}}
                },
                'requirements': {'resources': {'gpu': True}}
            }
        }
        
        template2 = {
            'template': {
                'id': 'template2',
                'name': 'Template 2',
                'version': '1.0.0',
                'category': 'processing',
                'tags': ['test', 'sample'],
                'interface': {
                    'inputs': {},
                    'outputs': {'result': {'type': 'string'}}
                },
                'requirements': {'resources': {'gpu': False}}
            }
        }
        
        # Write templates
        (temp_template_dir / 'template1.yaml').write_text(yaml.dump(template1))
        (temp_template_dir / 'template2.yaml').write_text(yaml.dump(template2))
        
        # Create registry
        registry = TemplateRegistry([temp_template_dir])
        await registry.initialize()
        
        yield registry
        
        # Cleanup
        registry.shutdown()
    
    @pytest.mark.asyncio
    async def test_registry_initialization(self, sample_registry):
        """Test registry initialization"""
        templates = sample_registry.list_templates()
        assert len(templates) == 2
        
        # Check templates loaded
        assert sample_registry.template_exists('template1')
        assert sample_registry.template_exists('template2')
    
    @pytest.mark.asyncio
    async def test_get_template(self, sample_registry):
        """Test getting templates"""
        # Get specific version
        template = sample_registry.get_template('template1', '1.0.0')
        assert template.id == 'template1'
        assert template.version == '1.0.0'
        
        # Get latest version
        template = sample_registry.get_template('template1')
        assert template.id == 'template1'
        
        # Non-existent template
        with pytest.raises(TemplateNotFoundError):
            sample_registry.get_template('nonexistent')
    
    @pytest.mark.asyncio
    async def test_list_templates_with_filters(self, sample_registry):
        """Test listing templates with filters"""
        # Filter by category
        templates = sample_registry.list_templates(category='generation')
        assert len(templates) == 1
        assert templates[0].category == 'generation'
        
        # Filter by tags
        templates = sample_registry.list_templates(tags=['test'])
        assert len(templates) == 1
        assert 'test' in templates[0].tags
        
        # Multiple tag filter
        templates = sample_registry.list_templates(tags=['test', 'sample'])
        assert len(templates) == 1
    
    @pytest.mark.asyncio
    async def test_get_categories_and_tags(self, sample_registry):
        """Test getting unique categories and tags"""
        categories = sample_registry.get_categories()
        assert set(categories) == {'generation', 'processing'}
        
        tags = sample_registry.get_all_tags()
        assert set(tags) == {'test', 'sample'}
    
    @pytest.mark.asyncio
    async def test_hot_reload(self, temp_template_dir):
        """Test hot-reload functionality"""
        registry = TemplateRegistry([temp_template_dir])
        await registry.initialize()
        
        # Initially no templates
        assert len(registry.list_templates()) == 0
        
        # Add new template file
        new_template = {
            'template': {
                'id': 'hot_reload_test',
                'name': 'Hot Reload Test',
                'version': '1.0.0',
                'interface': {
                    'inputs': {},
                    'outputs': {'result': {'type': 'string'}}
                },
                'requirements': {'resources': {}}
            }
        }
        
        template_file = temp_template_dir / 'hot_reload.yaml'
        template_file.write_text(yaml.dump(new_template))
        
        # Wait for hot-reload
        await asyncio.sleep(2)
        
        # Check template loaded
        assert registry.template_exists('hot_reload_test')
        
        registry.shutdown()
    
    @pytest.mark.asyncio
    async def test_invalid_template_handling(self, temp_template_dir):
        """Test handling of invalid templates"""
        # Create invalid template
        invalid_template = {'invalid': 'template'}
        (temp_template_dir / 'invalid.yaml').write_text(yaml.dump(invalid_template))
        
        # Registry should still initialize
        registry = TemplateRegistry([temp_template_dir])
        await registry.initialize()
        
        # Invalid template should not be loaded
        templates = registry.list_templates()
        assert len(templates) == 0
        
        registry.shutdown()


class TestTemplateAPI:
    """Test template API endpoints"""
    
    @pytest.fixture
    def mock_registry(self):
        """Mock template registry"""
        registry = MagicMock(spec=TemplateRegistry)
        
        # Mock template info
        template_info = MagicMock()
        template_info.id = 'test_template'
        template_info.name = 'Test Template'
        template_info.version = '1.0.0'
        template_info.category = 'processing'
        template_info.requires_gpu = False
        
        registry.list_templates.return_value = [template_info]
        registry.get_categories.return_value = ['processing']
        registry.get_all_tags.return_value = ['test']
        
        return registry
    
    def test_api_list_templates(self, mock_registry):
        """Test template listing API"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        # Patch registry
        with patch('app.api.endpoints.templates.template_registry', mock_registry):
            client = TestClient(app)
            response = client.get("/api/v1/templates/")
            
            assert response.status_code == 200
            data = response.json()
            assert data['total'] == 1
            assert len(data['templates']) == 1
            assert data['categories'] == ['processing']


if __name__ == "__main__":
    pytest.main([__file__])