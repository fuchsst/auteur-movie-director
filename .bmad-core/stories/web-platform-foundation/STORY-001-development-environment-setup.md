# Story: Development Environment Setup

**Story ID**: STORY-001  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Infrastructure  
**Points**: 2 (Small)  
**Priority**: High  

## Story Description
As a developer, I need a streamlined development environment setup process so that I can quickly start contributing to the Generative Media Studio project with all necessary dependencies and configurations in place.

## Acceptance Criteria

### Functional Requirements
- [ ] Running `npm run setup` completes successfully on Windows, Mac, and Linux
- [ ] Setup script checks for required prerequisites (Node.js 18+, Python 3.11+)
- [ ] Environment variables are properly configured from template files
- [ ] Both frontend and backend dependencies are installed correctly
- [ ] Development servers can be started with a single command

### Technical Requirements
- [ ] Create `.env.template` files for frontend and backend
- [ ] Implement setup scripts in `scripts/` directory
- [ ] Configure npm scripts in root `package.json` for orchestration
- [ ] Add prerequisite checking with clear error messages
- [ ] Support both npm and pnpm package managers

### Documentation Requirements
- [ ] Update README.md with quick start instructions
- [ ] Document all available npm scripts
- [ ] Include troubleshooting section for common issues
- [ ] Add platform-specific notes where needed

## Implementation Notes

### Setup Script Structure
```bash
scripts/
├── setup.js          # Main setup orchestrator
├── check-prereqs.js  # Verify system requirements
├── setup-env.js      # Create .env files from templates
└── setup-deps.js     # Install all dependencies
```

### Root package.json Scripts
```json
{
  "scripts": {
    "setup": "node scripts/setup.js",
    "setup:check": "node scripts/check-prereqs.js",
    "setup:env": "node scripts/setup-env.js",
    "dev": "concurrently \"npm:dev:*\"",
    "dev:backend": "cd backend && uvicorn app.main:app --reload",
    "dev:frontend": "cd frontend && npm run dev"
  }
}
```

### Environment Template Example
```env
# .env.template
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FRONTEND_PORT=3000
WORKSPACE_ROOT=./workspace
LOG_LEVEL=INFO
```

## Dependencies
- Node.js and Python runtime detection
- File system access for creating directories
- Cross-platform path handling

## Testing Criteria
- [ ] Clean install works on fresh system
- [ ] Re-running setup is idempotent
- [ ] Missing prerequisites show helpful errors
- [ ] All npm scripts execute correctly

## Definition of Done
- [ ] Setup scripts created and tested on all platforms
- [ ] Environment templates include all required variables
- [ ] README updated with setup instructions
- [ ] PR approved by at least one team member
- [ ] No hardcoded paths or platform-specific code

## Story Links
- **Blocks**: All other development stories
- **Related PRD**: PRD-001-web-platform-foundation