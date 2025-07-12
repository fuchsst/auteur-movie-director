#!/usr/bin/env node

/**
 * Setup environment files if they don't exist
 */

const fs = require('fs');
const path = require('path');

const ENV_EXAMPLE = `.env.example`;
const ENV_FILE = `.env`;

const envTemplate = `# Auteur Movie Director Configuration

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true

# Frontend Configuration  
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000

# Workspace Configuration
WORKSPACE_ROOT=./workspace
DEFAULT_QUALITY=standard

# API Keys (for future use)
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=
# HUGGINGFACE_TOKEN=

# Development Settings
DEBUG=true
LOG_LEVEL=INFO

# Git Configuration
GIT_AUTO_COMMIT=false
GIT_LFS_ENABLED=true
`;

function createEnvFile() {
  const rootDir = path.join(__dirname, '..');
  const envPath = path.join(rootDir, ENV_FILE);
  const examplePath = path.join(rootDir, ENV_EXAMPLE);
  
  // Create .env.example
  if (!fs.existsSync(examplePath)) {
    fs.writeFileSync(examplePath, envTemplate);
    console.log('✓ Created .env.example');
  }
  
  // Create .env if it doesn't exist
  if (!fs.existsSync(envPath)) {
    fs.writeFileSync(envPath, envTemplate);
    console.log('✓ Created .env from template');
    console.log('  Please update .env with your configuration');
  } else {
    console.log('✓ .env file already exists');
  }
  
  // Also create backend/.env
  const backendEnvPath = path.join(rootDir, 'backend', '.env');
  if (!fs.existsSync(backendEnvPath)) {
    fs.writeFileSync(backendEnvPath, envTemplate);
    console.log('✓ Created backend/.env');
  }
  
  // And frontend/.env.local
  const frontendEnvPath = path.join(rootDir, 'frontend', '.env.local');
  const frontendEnvTemplate = `# Frontend Environment Variables
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
`;
  
  if (!fs.existsSync(frontendEnvPath)) {
    fs.writeFileSync(frontendEnvPath, frontendEnvTemplate);
    console.log('✓ Created frontend/.env.local');
  }
}

function createDirectories() {
  const rootDir = path.join(__dirname, '..');
  const dirs = [
    'workspace',
    'workspace/Projects',
    'workspace/Library',
    'backend/app',
    'frontend/src'
  ];
  
  dirs.forEach(dir => {
    const dirPath = path.join(rootDir, dir);
    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
      console.log(`✓ Created directory: ${dir}`);
    }
  });
}

function main() {
  console.log('\nSetting up environment...');
  console.log('=' .repeat(40));
  
  createEnvFile();
  createDirectories();
  
  console.log('=' .repeat(40));
  console.log('✓ Environment setup complete!');
}

if (require.main === module) {
  main();
}