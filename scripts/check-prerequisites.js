#!/usr/bin/env node

/**
 * Check if all prerequisites are installed with correct versions
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const REQUIRED_NODE_VERSION = 18;
const REQUIRED_PYTHON_VERSION = [3, 11];

// Colors for console output
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

function checkCommand(command, versionFlag = '--version') {
  try {
    const output = execSync(`${command} ${versionFlag}`, { encoding: 'utf-8' });
    return output.trim();
  } catch (error) {
    return null;
  }
}

function checkNodeVersion() {
  const nodeVersion = process.version;
  const majorVersion = parseInt(nodeVersion.split('.')[0].substring(1));
  
  if (majorVersion >= REQUIRED_NODE_VERSION) {
    log(`✓ Node.js ${nodeVersion} installed`, 'green');
    return true;
  } else {
    log(`✗ Node.js ${REQUIRED_NODE_VERSION}+ required (found ${nodeVersion})`, 'red');
    return false;
  }
}

function checkPythonVersion() {
  const pythonCommands = ['python3.11', 'python3', 'python'];
  
  for (const cmd of pythonCommands) {
    const version = checkCommand(cmd);
    if (version) {
      const match = version.match(/Python (\d+)\.(\d+)\.(\d+)/);
      if (match) {
        const major = parseInt(match[1]);
        const minor = parseInt(match[2]);
        
        if (major === REQUIRED_PYTHON_VERSION[0] && minor >= REQUIRED_PYTHON_VERSION[1]) {
          log(`✓ Python ${major}.${minor} installed (${cmd})`, 'green');
          
          // Create a python symlink if needed
          if (cmd !== 'python') {
            log(`  Tip: You may want to alias 'python' to '${cmd}'`, 'yellow');
          }
          return true;
        }
      }
    }
  }
  
  log(`✗ Python ${REQUIRED_PYTHON_VERSION.join('.')}+ required`, 'red');
  return false;
}

function checkGit() {
  const gitVersion = checkCommand('git');
  if (gitVersion) {
    log(`✓ Git installed: ${gitVersion}`, 'green');
    return true;
  } else {
    log('✗ Git is required for project management', 'red');
    return false;
  }
}

function checkDocker() {
  const dockerVersion = checkCommand('docker', '--version');
  if (dockerVersion) {
    log(`✓ Docker installed: ${dockerVersion}`, 'green');
    return true;
  } else {
    log('⚠ Docker not found (optional, needed for production)', 'yellow');
    return true; // Optional for now
  }
}

function checkFFmpeg() {
  const ffmpegVersion = checkCommand('ffmpeg', '-version');
  if (ffmpegVersion) {
    const firstLine = ffmpegVersion.split('\n')[0];
    log(`✓ FFmpeg installed: ${firstLine}`, 'green');
    return true;
  } else {
    log('⚠ FFmpeg not found (optional, needed for video processing)', 'yellow');
    return true; // Optional for now
  }
}

function main() {
  log('\nChecking prerequisites for Generative Media Studio...', 'blue');
  log('=' .repeat(50), 'blue');
  
  const checks = [
    checkNodeVersion(),
    checkPythonVersion(),
    checkGit(),
    checkDocker(),
    checkFFmpeg()
  ];
  
  const allRequired = checks.slice(0, 3).every(result => result === true);
  
  log('=' .repeat(50), 'blue');
  
  if (allRequired) {
    log('✓ All required prerequisites are installed!', 'green');
    log('\nNext steps:', 'blue');
    log('1. Run "npm run setup" to install dependencies', 'blue');
    log('2. Run "npm run dev" to start development servers', 'blue');
    process.exit(0);
  } else {
    log('✗ Some prerequisites are missing. Please install them first.', 'red');
    log('\nInstallation guides:', 'yellow');
    log('- Node.js: https://nodejs.org/', 'yellow');
    log('- Python: https://www.python.org/', 'yellow');
    log('- Git: https://git-scm.com/', 'yellow');
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}