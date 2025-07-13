#!/usr/bin/env python3
"""
Create a new Auteur Movie Director project with enforced structure.
This script is called by 'make new-project NAME=project_name'
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path setup
from backend.app.schemas.project import NarrativeStructure, ProjectCreate, QualityLevel
from backend.app.services.workspace import WorkspaceService

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Create a new Auteur Movie Director project"
    )
    parser.add_argument(
        "name",
        help="Project name"
    )
    parser.add_argument(
        "--structure",
        type=str,
        choices=["three-act", "hero-journey", "beat-sheet", "story-circle"],
        default="three-act",
        help="Narrative structure template (default: three-act)"
    )
    parser.add_argument(
        "--quality",
        type=str,
        choices=["low", "standard", "high"],
        default="standard",
        help="Default quality level (default: standard)"
    )
    parser.add_argument(
        "--director",
        type=str,
        help="Director name (default: current user)"
    )
    parser.add_argument(
        "--description",
        type=str,
        help="Project description"
    )
    parser.add_argument(
        "--workspace",
        type=str,
        default=os.environ.get("WORKSPACE_ROOT", "./workspace"),
        help="Workspace root directory"
    )
    
    args = parser.parse_args()
    
    # Create project data
    project_data = ProjectCreate(
        name=args.name,
        narrative_structure=NarrativeStructure(args.structure),
        quality=QualityLevel(args.quality),
        director=args.director,
        description=args.description
    )
    
    # Initialize workspace service
    workspace_service = WorkspaceService(args.workspace)
    
    try:
        # Create project
        logger.info(f"🎬 Creating project: {args.name}")
        logger.info(f"📁 Workspace: {args.workspace}")
        
        project_path, manifest = workspace_service.create_project(project_data)
        
        logger.info("✅ Project created successfully!")
        logger.info(f"📂 Location: {project_path}")
        logger.info(f"🎭 Narrative: {args.structure}")
        logger.info(f"⚡ Quality: {args.quality}")
        logger.info("\n🚀 Next steps:")
        logger.info(f"   1. cd {project_path}")
        logger.info("   2. Start adding creative assets")
        logger.info("   3. Use the web interface to manage your project")
        
    except Exception as e:
        logger.error(f"❌ Error creating project: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()