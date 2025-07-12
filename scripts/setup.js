#!/usr/bin/env node

/**
 * Main setup orchestrator for Auteur Movie Director
 * Runs all setup steps in sequence
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function execCommand(command, options = {}) {
  try {
    log(`  → ${command}`, 'cyan');
    execSync(command, { stdio: 'inherit', ...options });
    return true;
  } catch (error) {
    log(`  ✗ Command failed: ${command}`, 'red');
    return false;
  }
}

async function setupBackend() {
  log('\n📦 Setting up backend dependencies...', 'blue');
  
  const backendDir = path.join(__dirname, '..', 'backend');
  
  // Check if pip is available
  try {
    execSync('pip --version', { stdio: 'ignore' });
  } catch (error) {
    log('  ⚠ pip not found, trying pip3...', 'yellow');
    try {
      execSync('pip3 --version', { stdio: 'ignore' });
      // Create pip alias for this session
      process.env.PIP = 'pip3';
    } catch (error2) {
      log('  ✗ Neither pip nor pip3 found. Please install Python first.', 'red');
      return false;
    }
  }
  
  const pip = process.env.PIP || 'pip';
  
  // Install backend dependencies
  if (fs.existsSync(path.join(backendDir, 'requirements.txt'))) {
    if (!execCommand(`${pip} install -r requirements.txt`, { cwd: backendDir })) {
      return false;
    }
  }
  
  // Install dev dependencies if they exist
  if (fs.existsSync(path.join(backendDir, 'requirements-dev.txt'))) {
    if (!execCommand(`${pip} install -r requirements-dev.txt`, { cwd: backendDir })) {
      log('  ⚠ Dev dependencies failed to install (non-critical)', 'yellow');
    }
  }
  
  log('  ✓ Backend dependencies installed', 'green');
  return true;
}

async function setupFrontend() {
  log('\n📦 Setting up frontend dependencies...', 'blue');
  
  const frontendDir = path.join(__dirname, '..', 'frontend');
  
  // Check if frontend package.json exists
  if (!fs.existsSync(path.join(frontendDir, 'package.json'))) {
    log('  ⚠ Frontend not initialized. Creating SvelteKit project...', 'yellow');
    
    // Initialize SvelteKit project
    const initCommand = 'npm create vite@latest . -- --template svelte';
    if (!execCommand(initCommand, { cwd: frontendDir })) {
      return false;
    }
  }
  
  // Install dependencies
  const packageManager = fs.existsSync(path.join(frontendDir, 'pnpm-lock.yaml')) ? 'pnpm' : 'npm';
  
  if (!execCommand(`${packageManager} install`, { cwd: frontendDir })) {
    return false;
  }
  
  log('  ✓ Frontend dependencies installed', 'green');
  return true;
}

async function installRootDependencies() {
  log('\n📦 Installing root dependencies...', 'blue');
  
  const rootDir = path.join(__dirname, '..');
  
  // Check if concurrently is already installed
  try {
    require.resolve('concurrently');
    log('  ✓ Root dependencies already installed', 'green');
    return true;
  } catch (e) {
    // Need to install
    if (!execCommand('npm install', { cwd: rootDir })) {
      return false;
    }
    log('  ✓ Root dependencies installed', 'green');
    return true;
  }
}

async function main() {
  console.clear();
  log('🎬 Generative Media Studio Setup', 'cyan');
  log('=' .repeat(50), 'cyan');
  
  // Step 1: Check prerequisites
  log('\n1️⃣  Checking prerequisites...', 'blue');
  try {
    execSync('node scripts/check-prerequisites.js', { stdio: 'inherit' });
  } catch (error) {
    log('\n✗ Prerequisites check failed. Please install missing requirements.', 'red');
    process.exit(1);
  }
  
  // Step 2: Install root dependencies (needed for concurrently)
  if (!await installRootDependencies()) {
    log('\n✗ Failed to install root dependencies', 'red');
    process.exit(1);
  }
  
  // Step 3: Setup environment
  log('\n2️⃣  Setting up environment...', 'blue');
  try {
    execSync('node scripts/setup-env.js', { stdio: 'inherit' });
  } catch (error) {
    log('\n✗ Environment setup failed', 'red');
    process.exit(1);
  }
  
  // Step 4: Setup backend
  log('\n3️⃣  Setting up backend...', 'blue');
  if (!await setupBackend()) {
    log('\n✗ Backend setup failed', 'red');
    process.exit(1);
  }
  
  // Step 5: Setup frontend
  log('\n4️⃣  Setting up frontend...', 'blue');
  if (!await setupFrontend()) {
    log('\n✗ Frontend setup failed', 'red');
    process.exit(1);
  }
  
  // Success!
  log('\n' + '=' .repeat(50), 'green');
  log('✅ Setup complete!', 'green');
  log('=' .repeat(50), 'green');
  
  log('\n🚀 Next steps:', 'blue');
  log('  1. Review and update .env file with your configuration', 'blue');
  log('  2. Run "npm run dev" to start development servers', 'blue');
  log('  3. Open http://localhost:3000 in your browser', 'blue');
  
  log('\n📚 Available commands:', 'yellow');
  log('  npm run dev         - Start development servers', 'yellow');
  log('  npm run test        - Run tests', 'yellow');
  log('  npm run lint        - Check code quality', 'yellow');
  log('  npm run format      - Format code', 'yellow');
  log('  npm run docker:up   - Start Docker services', 'yellow');
  
  log('\n💡 Tips:', 'cyan');
  log('  - Use "npm run setup:check" to verify prerequisites', 'cyan');
  log('  - Check logs/ directory for service logs', 'cyan');
  log('  - Run "npm run docker:up" to start AI services', 'cyan');
}

// Run main function
if (require.main === module) {
  main().catch(error => {
    log(`\n✗ Setup failed with error: ${error.message}`, 'red');
    process.exit(1);
  });
}