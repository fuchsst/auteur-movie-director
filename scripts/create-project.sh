#!/bin/bash

# Create a new project with the required directory structure
# Following the BMAD project organization standards

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default workspace
WORKSPACE_ROOT="${WORKSPACE_ROOT:-./workspace}"

# Function to print colored output
print_color() {
    echo -e "${2}${1}${NC}"
}

# Function to create project structure
create_project_structure() {
    local project_path="$1"
    
    # Create numbered directories as per BMAD standard
    local directories=(
        "01_Assets/Characters"
        "01_Assets/Styles"
        "01_Assets/Locations"
        "01_Assets/Music"
        "02_Scripts/Treatments"
        "02_Scripts/Scripts"
        "02_Scripts/Shot_Lists"
        "02_Scripts/Canvas"
        "03_Renders/Drafts"
        "03_Renders/Finals"
        "03_Renders/Previews"
        "04_Generated/Images"
        "04_Generated/Videos"
        "04_Generated/Audio"
        "04_Generated/Models"
        "05_Versions"
        "06_Exports"
        ".auteur"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$project_path/$dir"
        touch "$project_path/$dir/.gitkeep"
    done
}

# Function to create project.json
create_project_json() {
    local project_path="$1"
    local project_name="$2"
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    cat > "$project_path/project.json" << EOF
{
  "name": "$project_name",
  "id": "$(uuidgen 2>/dev/null || echo "$(date +%s)-$(shuf -i 1000-9999 -n 1)")",
  "created": "$timestamp",
  "modified": "$timestamp",
  "version": "1.0.0",
  "quality": "standard",
  "takes_system_enabled": true,
  "metadata": {
    "director": "${USER:-unknown}",
    "genre": "",
    "style": "",
    "description": "",
    "tags": []
  },
  "settings": {
    "default_quality": "standard",
    "output_format": "mp4",
    "frame_rate": 24,
    "resolution": {
      "width": 1920,
      "height": 1080
    }
  },
  "git": {
    "initialized": true,
    "lfs_enabled": true,
    "remote": ""
  }
}
EOF
}

# Function to initialize Git repository
init_git_repo() {
    local project_path="$1"
    
    cd "$project_path"
    
    # Initialize Git
    git init
    
    # Configure Git LFS
    git lfs install
    git lfs track "*.png" "*.jpg" "*.jpeg" "*.mp4" "*.mov" "*.wav" "*.mp3"
    git lfs track "*.psd" "*.blend" "*.exr" "*.tiff"
    git lfs track "04_Generated/**/*" "03_Renders/**/*"
    
    # Create .gitignore
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
ENV/

# Node
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Project specific
.auteur/cache/
.auteur/temp/
*.log
.env.local

# Large files handled by Git LFS
!.gitattributes
EOF

    # Initial commit
    git add .
    git commit -m "Initial project structure"
    
    cd - > /dev/null
}

# Main script
main() {
    print_color "🎬 Auteur Movie Director - New Project Creator" "$BLUE"
    echo "============================================="
    echo
    
    # Check if workspace exists
    if [ ! -d "$WORKSPACE_ROOT" ]; then
        print_color "Creating workspace directory: $WORKSPACE_ROOT" "$YELLOW"
        mkdir -p "$WORKSPACE_ROOT"
    fi
    
    # Get project name
    read -p "Enter project name: " project_name
    
    # Validate project name
    if [ -z "$project_name" ]; then
        print_color "Error: Project name cannot be empty" "$RED"
        exit 1
    fi
    
    # Sanitize project name for directory
    project_dir=$(echo "$project_name" | sed 's/[^a-zA-Z0-9-_]/_/g')
    project_path="$WORKSPACE_ROOT/$project_dir"
    
    # Check if project already exists
    if [ -d "$project_path" ]; then
        print_color "Error: Project '$project_name' already exists at $project_path" "$RED"
        exit 1
    fi
    
    # Create project
    print_color "\nCreating project structure..." "$BLUE"
    mkdir -p "$project_path"
    create_project_structure "$project_path"
    
    print_color "Creating project.json..." "$BLUE"
    create_project_json "$project_path" "$project_name"
    
    print_color "Initializing Git repository..." "$BLUE"
    init_git_repo "$project_path"
    
    # Success message
    print_color "\n✅ Project created successfully!" "$GREEN"
    print_color "\nProject location: $project_path" "$BLUE"
    print_color "\nNext steps:" "$YELLOW"
    echo "  1. cd $project_path"
    echo "  2. Start adding your creative assets"
    echo "  3. Use the web interface to manage your project"
    echo
}

# Run main function
main "$@"