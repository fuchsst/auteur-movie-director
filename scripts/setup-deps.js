#!/usr/bin/env node

/**
 * Install all project dependencies
 * Handles both npm/pnpm for frontend and pip for backend
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const colors = {
  reset: '\x1b[0m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function detectPackageManager() {
  // Check for pnpm
  try {
    execSync('pnpm --version', { stdio: 'ignore' });
    return 'pnpm';
  } catch (e) {
    // Fall back to npm
    return 'npm';
  }
}

function installNodeDependencies(dir, name) {
  log(`\nInstalling ${name} dependencies...`, 'blue');
  
  if (!fs.existsSync(path.join(dir, 'package.json'))) {
    log(`  ⚠ No package.json found in ${name}`, 'yellow');
    return true;
  }
  
  const pm = detectPackageManager();
  log(`  Using ${pm}...`, 'cyan');
  
  try {
    execSync(`${pm} install`, { 
      cwd: dir, 
      stdio: 'inherit'
    });
    log(`  ✓ ${name} dependencies installed`, 'green');
    return true;
  } catch (error) {
    log(`  ✗ Failed to install ${name} dependencies`, 'red');
    return false;
  }
}

function installPythonDependencies(dir) {
  log('\nInstalling backend Python dependencies...', 'blue');
  
  const requirementsPath = path.join(dir, 'requirements.txt');
  if (!fs.existsSync(requirementsPath)) {
    log('  ⚠ No requirements.txt found', 'yellow');
    return true;
  }
  
  // Detect pip command
  let pipCmd = 'pip';
  try {
    execSync('pip --version', { stdio: 'ignore' });
  } catch (e) {
    try {
      execSync('pip3 --version', { stdio: 'ignore' });
      pipCmd = 'pip3';
    } catch (e2) {
      log('  ✗ pip not found. Please install Python first.', 'red');
      return false;
    }
  }
  
  try {
    // Install main requirements
    execSync(`${pipCmd} install -r requirements.txt`, { 
      cwd: dir, 
      stdio: 'inherit'
    });
    
    // Install dev requirements if they exist
    const devReqPath = path.join(dir, 'requirements-dev.txt');
    if (fs.existsSync(devReqPath)) {
      log('  Installing dev dependencies...', 'blue');
      execSync(`${pipCmd} install -r requirements-dev.txt`, { 
        cwd: dir, 
        stdio: 'inherit'
      });
    }
    
    log('  ✓ Python dependencies installed', 'green');
    return true;
  } catch (error) {
    log('  ✗ Failed to install Python dependencies', 'red');
    return false;
  }
}

function main() {
  const rootDir = path.join(__dirname, '..');
  
  log('Installing all project dependencies...', 'blue');
  log('=' .repeat(40), 'blue');
  
  // Install root dependencies
  if (!installNodeDependencies(rootDir, 'root')) {
    process.exit(1);
  }
  
  // Install backend dependencies
  const backendDir = path.join(rootDir, 'backend');
  if (!installPythonDependencies(backendDir)) {
    process.exit(1);
  }
  
  // Install frontend dependencies
  const frontendDir = path.join(rootDir, 'frontend');
  if (!installNodeDependencies(frontendDir, 'frontend')) {
    process.exit(1);
  }
  
  log('\n' + '=' .repeat(40), 'green');
  log('✓ All dependencies installed successfully!', 'green');
}

if (require.main === module) {
  main();
}