"""
CLI commands for the application
"""

import click

from .template_commands import template_commands
from .resource_commands import resource_commands


@click.group()
def cli():
    """Auteur Movie Director CLI"""
    pass


# Add command groups
cli.add_command(template_commands)
cli.add_command(resource_commands)


if __name__ == "__main__":
    cli()