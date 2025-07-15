"""
CLI Commands for Template Management

Provides commands for validating, registering, and managing function templates.
"""

import click
import yaml
import json
import sys
from pathlib import Path
from typing import Optional
from tabulate import tabulate

from app.templates import (
    TemplateValidator, 
    FunctionTemplate,
    TemplateValidationPipeline,
    ValidationContext,
    ValidationResultFormatter,
    OutputFormat
)
from app.templates.registry import TemplateRegistry


@click.group()
def template():
    """Function template management commands"""
    pass


@template.command()
@click.argument('template_file', type=click.Path(exists=True, path_type=Path))
@click.option('--verbose', '-v', is_flag=True, help='Show detailed validation output')
@click.option('--strict', is_flag=True, help='Enable strict validation mode')
@click.option('--format', type=click.Choice(['cli', 'json', 'markdown']), default='cli', help='Output format')
@click.option('--no-color', is_flag=True, help='Disable colored output')
def validate(template_file: Path, verbose: bool, strict: bool, format: str, no_color: bool):
    """Validate a template definition file with comprehensive checks"""
    if not no_color:
        click.echo(f"Validating template: {template_file}")
    
    try:
        # Load template file
        content = template_file.read_text()
        if template_file.suffix == '.json':
            definition = json.loads(content)
        else:
            definition = yaml.safe_load(content)
        
        # Use comprehensive validation pipeline
        pipeline = TemplateValidationPipeline()
        formatter = ValidationResultFormatter()
        
        # Create validation context
        context = ValidationContext(
            strict_mode=strict,
            check_uniqueness=True,
            check_dependencies=True
        )
        
        # Run validation
        import asyncio
        result = asyncio.run(pipeline.validate(definition, context))
        
        # Format output
        output_format = OutputFormat(format)
        if output_format == OutputFormat.CLI:
            output = formatter.format_cli(result, use_color=not no_color)
            click.echo(output)
        elif output_format == OutputFormat.JSON:
            output = formatter.format_json(result)
            click.echo(json.dumps(output, indent=2))
        elif output_format == OutputFormat.MARKDOWN:
            output = formatter.format_markdown(result)
            click.echo(output)
        
        # Exit with error code if validation failed
        if not result.is_valid():
            sys.exit(1)
            
        # Show additional info if verbose and valid
        if verbose and result.is_valid() and output_format == OutputFormat.CLI:
            # Show template info
            template = FunctionTemplate(definition)
            click.echo(f"\nTemplate Info:")
            click.echo(f"  ID: {template.id}")
            click.echo(f"  Name: {template.name}")
            click.echo(f"  Version: {template.version}")
            click.echo(f"  Category: {template.category}")
            click.echo(f"  Author: {template.author}")
            click.echo(f"  GPU Required: {template.resources.gpu}")
    
    except Exception as e:
        click.echo(click.style(f"❌ Error loading template: {e}", fg='red'))
        sys.exit(1)


@template.command()
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              default=Path('./templates'), help='Template directory')
@click.option('--category', '-c', help='Filter by category')
@click.option('--tag', '-t', multiple=True, help='Filter by tags')
@click.option('--format', '-f', type=click.Choice(['table', 'json', 'yaml']),
              default='table', help='Output format')
def list(directory: Path, category: Optional[str], tag: tuple, format: str):
    """List available templates"""
    try:
        # Create temporary registry
        registry = TemplateRegistry([directory])
        
        # Initialize synchronously (simplified for CLI)
        import asyncio
        asyncio.run(registry.initialize())
        
        # Get templates
        templates = registry.list_templates(category=category, tags=list(tag) if tag else None)
        
        if not templates:
            click.echo("No templates found matching criteria")
            return
        
        if format == 'table':
            # Table format
            headers = ['ID', 'Version', 'Name', 'Category', 'GPU', 'Tags']
            rows = []
            for tmpl in templates:
                rows.append([
                    tmpl.id,
                    tmpl.version,
                    tmpl.name[:30] + '...' if len(tmpl.name) > 30 else tmpl.name,
                    tmpl.category,
                    '✓' if tmpl.requires_gpu else '',
                    ', '.join(tmpl.tags[:3])
                ])
            
            click.echo(tabulate(rows, headers=headers, tablefmt='grid'))
            click.echo(f"\nTotal: {len(templates)} templates")
            
        elif format == 'json':
            # JSON format
            import json
            data = [t.dict() for t in templates]
            click.echo(json.dumps(data, indent=2, default=str))
            
        elif format == 'yaml':
            # YAML format
            data = [t.dict() for t in templates]
            click.echo(yaml.dump(data, default_flow_style=False))
        
        # Cleanup
        registry.shutdown()
        
    except Exception as e:
        click.echo(click.style(f"Error listing templates: {e}", fg='red'))
        sys.exit(1)


@template.command()
@click.argument('template_id')
@click.option('--version', '-v', help='Specific version (latest if not specified)')
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path),
              default=Path('./templates'), help='Template directory')
@click.option('--examples', '-e', is_flag=True, help='Show usage examples')
def info(template_id: str, version: Optional[str], directory: Path, examples: bool):
    """Show detailed information about a template"""
    try:
        # Create temporary registry
        registry = TemplateRegistry([directory])
        
        # Initialize
        import asyncio
        asyncio.run(registry.initialize())
        
        # Get template
        template = registry.get_template(template_id, version)
        
        # Display info
        click.echo(f"Template: {template.name}")
        click.echo(f"{'=' * len(f'Template: {template.name}')}")
        click.echo(f"ID: {template.id}")
        click.echo(f"Version: {template.version}")
        click.echo(f"Category: {template.category}")
        click.echo(f"Author: {template.author}")
        click.echo(f"Description: {template.description}")
        
        if template.tags:
            click.echo(f"Tags: {', '.join(template.tags)}")
        
        # Resource requirements
        click.echo(f"\nResource Requirements:")
        click.echo(f"  GPU: {'Required' if template.resources.gpu else 'Not required'}")
        if template.resources.gpu:
            click.echo(f"  VRAM: {template.resources.vram_gb} GB")
        click.echo(f"  CPU Cores: {template.resources.cpu_cores}")
        click.echo(f"  Memory: {template.resources.memory_gb} GB")
        click.echo(f"  Disk: {template.resources.disk_gb} GB")
        
        # Models
        if template.models:
            click.echo(f"\nRequired Models:")
            for model in template.models:
                click.echo(f"  • {model.name} ({model.type}, {model.size_gb} GB)")
        
        # Quality presets
        if template.quality_presets:
            click.echo(f"\nQuality Presets:")
            for name in template.quality_presets:
                click.echo(f"  • {name}")
        
        # Interface
        click.echo(f"\nInputs:")
        for name, param in template.interface.inputs.items():
            req = click.style("required", fg='red') if param.required else "optional"
            desc = param.description[:50] + '...' if len(param.description) > 50 else param.description
            click.echo(f"  {name} ({param.type.value}, {req})")
            click.echo(f"    {desc}")
            
            if param.constraints:
                constraints = []
                if param.constraints.enum:
                    constraints.append(f"values: {param.constraints.enum}")
                if param.constraints.min_value is not None:
                    constraints.append(f"min: {param.constraints.min_value}")
                if param.constraints.max_value is not None:
                    constraints.append(f"max: {param.constraints.max_value}")
                if constraints:
                    click.echo(f"    Constraints: {', '.join(constraints)}")
        
        click.echo(f"\nOutputs:")
        for name, param in template.interface.outputs.items():
            click.echo(f"  {name} ({param.type.value}): {param.description}")
        
        # Examples
        if examples and template.examples:
            click.echo(f"\nExamples:")
            for i, example in enumerate(template.examples, 1):
                click.echo(f"\n  Example {i}: {example.name}")
                if example.description:
                    click.echo(f"  {example.description}")
                click.echo(f"  Inputs:")
                for key, value in example.inputs.items():
                    click.echo(f"    {key}: {value}")
        
        # Cleanup
        registry.shutdown()
        
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)


@template.command()
@click.argument('template_file', type=click.Path(exists=True, path_type=Path))
@click.option('--inputs', '-i', help='JSON string of input values')
@click.option('--input-file', '-f', type=click.Path(exists=True, path_type=Path),
              help='JSON file with input values')
def test(template_file: Path, inputs: Optional[str], input_file: Optional[Path]):
    """Test a template with sample inputs"""
    try:
        # Load template
        content = template_file.read_text()
        if template_file.suffix == '.json':
            definition = json.loads(content)
        else:
            definition = yaml.safe_load(content)
        
        # Validate first
        validator = TemplateValidator()
        errors = validator.validate(definition)
        if errors:
            click.echo(click.style("Template validation failed:", fg='red'))
            for error in errors:
                click.echo(f"  • {error}")
            sys.exit(1)
        
        # Create template
        template = FunctionTemplate(definition)
        
        # Get inputs
        test_inputs = {}
        if input_file:
            test_inputs = json.loads(input_file.read_text())
        elif inputs:
            test_inputs = json.loads(inputs)
        else:
            # Use first example if available
            if template.examples:
                test_inputs = template.examples[0].inputs
                click.echo(f"Using example inputs: {template.examples[0].name}")
            else:
                click.echo("No inputs provided and no examples available")
                sys.exit(1)
        
        # Validate inputs
        click.echo("\nValidating inputs...")
        try:
            validated = template.validate_inputs(test_inputs)
            click.echo(click.style("✓ Inputs are valid!", fg='green'))
            
            # Show validated inputs
            click.echo("\nValidated inputs:")
            for key, value in validated.items():
                click.echo(f"  {key}: {value}")
            
            # Calculate resource requirements
            resources = template.get_resource_requirements(validated)
            click.echo(f"\nResource requirements for these inputs:")
            click.echo(f"  GPU: {'Required' if resources.gpu else 'Not required'}")
            if resources.gpu:
                click.echo(f"  VRAM: {resources.vram_gb} GB")
            click.echo(f"  Memory: {resources.memory_gb} GB")
            
            # Show quality parameters if applicable
            if 'quality' in validated and validated['quality'] in template.quality_presets:
                params = template.get_quality_parameters(validated['quality'])
                click.echo(f"\nQuality parameters for '{validated['quality']}':")
                for key, value in params.items():
                    click.echo(f"  {key}: {value}")
            
        except Exception as e:
            click.echo(click.style(f"❌ Input validation failed: {e}", fg='red'))
            sys.exit(1)
        
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg='red'))
        sys.exit(1)


@template.command()
@click.argument('output_file', type=click.Path(path_type=Path))
@click.option('--id', required=True, help='Template ID (lowercase, underscores)')
@click.option('--name', required=True, help='Human-readable name')
@click.option('--category', type=click.Choice(['generation', 'processing', 'analysis', 'utility']),
              default='generation', help='Template category')
def create(output_file: Path, id: str, name: str, category: str):
    """Create a new template scaffold"""
    
    # Basic template structure
    template_data = {
        'template': {
            'id': id,
            'name': name,
            'version': '1.0.0',
            'description': f'{name} function template',
            'category': category,
            'author': 'Your Name',
            'tags': [],
            'interface': {
                'inputs': {
                    'prompt': {
                        'type': 'string',
                        'description': 'Input prompt or description',
                        'required': True,
                        'min_length': 1,
                        'max_length': 1000
                    },
                    'quality': {
                        'type': 'string',
                        'description': 'Quality level',
                        'required': False,
                        'default': 'standard',
                        'enum': ['draft', 'standard', 'high', 'ultra']
                    }
                },
                'outputs': {
                    'result': {
                        'type': 'file',
                        'description': 'Generated output file',
                        'format': ['png', 'jpg']
                    },
                    'metadata': {
                        'type': 'object',
                        'description': 'Generation metadata'
                    }
                }
            },
            'requirements': {
                'resources': {
                    'gpu': category == 'generation',
                    'vram_gb': 8.0 if category == 'generation' else 0.0,
                    'cpu_cores': 2,
                    'memory_gb': 4.0
                },
                'models': [],
                'quality_presets': {
                    'draft': {
                        'steps': 20
                    },
                    'standard': {
                        'steps': 30
                    },
                    'high': {
                        'steps': 50
                    },
                    'ultra': {
                        'steps': 100
                    }
                }
            },
            'examples': [
                {
                    'name': 'Basic Example',
                    'inputs': {
                        'prompt': 'A sample prompt',
                        'quality': 'standard'
                    }
                }
            ]
        }
    }
    
    # Write template
    if output_file.suffix == '.json':
        output_file.write_text(json.dumps(template_data, indent=2))
    else:
        output_file.write_text(yaml.dump(template_data, default_flow_style=False))
    
    click.echo(click.style(f"✓ Created template scaffold: {output_file}", fg='green'))
    click.echo(f"\nNext steps:")
    click.echo(f"1. Edit {output_file} to customize the template")
    click.echo(f"2. Run 'template validate {output_file}' to check validity")
    click.echo(f"3. Place in templates directory for auto-loading")


@template.command(name='validate-batch')
@click.argument('template_files', nargs=-1, type=click.Path(exists=True, path_type=Path))
@click.option('--directory', '-d', type=click.Path(exists=True, path_type=Path), 
              help='Validate all templates in directory')
@click.option('--pattern', '-p', default='*.yaml', help='File pattern for directory search')
@click.option('--strict', is_flag=True, help='Enable strict validation mode')
@click.option('--format', type=click.Choice(['cli', 'json']), default='cli', help='Output format')
def validate_batch(template_files: tuple, directory: Optional[Path], pattern: str, 
                  strict: bool, format: str):
    """Validate multiple template files"""
    # Collect files to validate
    files_to_validate = []
    
    if directory:
        files_to_validate.extend(directory.glob(pattern))
        if pattern != '*.yml':
            files_to_validate.extend(directory.glob('*.yml'))
    
    files_to_validate.extend(template_files)
    
    if not files_to_validate:
        click.echo("No template files found to validate", err=True)
        sys.exit(1)
    
    # Use validation pipeline
    pipeline = TemplateValidationPipeline()
    formatter = ValidationResultFormatter()
    
    # Create validation context
    context = ValidationContext(
        strict_mode=strict,
        check_uniqueness=True,
        check_dependencies=True
    )
    
    # Validate all files
    import asyncio
    results = asyncio.run(pipeline.validate_batch(files_to_validate, context))
    
    # Format output
    output_format = OutputFormat(format)
    summary = formatter.format_batch_summary(results, output_format)
    
    if output_format == OutputFormat.JSON:
        click.echo(json.dumps(summary, indent=2))
    else:
        click.echo(summary)
    
    # Exit with error code if any validation failed
    invalid_count = sum(1 for r in results.values() if not r.is_valid())
    if invalid_count > 0:
        sys.exit(1)


@template.command(name='validation-rules')
def show_validation_rules():
    """Show all template validation rules"""
    formatter = ValidationResultFormatter()
    
    click.echo(click.style("Template Validation Rules", bold=True))
    click.echo("=" * 50)
    
    click.echo(click.style("\nValidation Stages:", fg='cyan'))
    
    stages = [
        ("Schema", [
            "Template must have required fields: id, name, version, interface, requirements",
            "ID must contain only lowercase letters, numbers, and underscores",
            "Version must follow semantic versioning (e.g., 1.0.0)",
            "Category must be one of: generation, processing, analysis, utility"
        ]),
        ("Types", [
            "All parameters must have a valid type",
            "Valid types: string, integer, float, boolean, array, object, file",
            "Constraints must be appropriate for the parameter type",
            "Default values must match type and satisfy constraints"
        ]),
        ("Resources", [
            "GPU templates must specify VRAM requirements",
            "CPU cores must be at least 1",
            "Memory requirements must be positive",
            "Quality presets must match input enum values"
        ]),
        ("Examples", [
            "Examples must have unique names",
            "Example inputs must include all required parameters",
            "Example inputs must pass parameter validation"
        ]),
        ("Dependencies", [
            "No circular dependencies allowed",
            "Parent templates must exist"
        ]),
        ("Uniqueness", [
            "Template ID and version combination must be unique"
        ])
    ]
    
    for stage_name, rules in stages:
        click.echo(click.style(f"\n{stage_name}:", fg='yellow'))
        for rule in rules:
            click.echo(f"  • {rule}")
    
    click.echo(click.style("\nRun 'template validate <file>' to check your template", fg='blue'))


# Add to main CLI
def register_template_commands(cli):
    """Register template commands with main CLI"""
    cli.add_command(template)