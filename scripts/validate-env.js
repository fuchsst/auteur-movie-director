#!/usr/bin/env node

/**
 * Validate environment configuration
 * Checks that all required services are accessible
 */

const fs = require('fs');
const path = require('path');
const http = require('http');
const { execSync } = require('child_process');

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

function loadEnv() {
  const envPath = path.join(__dirname, '..', '.env');
  if (!fs.existsSync(envPath)) {
    log('⚠ .env file not found, using defaults', 'yellow');
    return {};
  }
  
  const envContent = fs.readFileSync(envPath, 'utf-8');
  const env = {};
  
  envContent.split('\n').forEach(line => {
    const trimmedLine = line.trim();
    if (trimmedLine && !trimmedLine.startsWith('#')) {
      const [key, ...valueParts] = trimmedLine.split('=');
      if (key) {
        const value = valueParts.join('=').trim();
        env[key.trim()] = value.replace(/^["']|["']$/g, '');
      }
    }
  });
  
  return env;
}

function checkPort(host, port, serviceName) {
  return new Promise((resolve) => {
    const options = {
      host,
      port,
      timeout: 2000,
      path: '/'
    };
    
    const req = http.get(options, (res) => {
      log(`  ✓ ${serviceName} is running on ${host}:${port}`, 'green');
      resolve(true);
    });
    
    req.on('error', (err) => {
      if (err.code === 'ECONNREFUSED') {
        log(`  ⚠ ${serviceName} is not running on ${host}:${port}`, 'yellow');
      } else {
        log(`  ✗ ${serviceName} error: ${err.message}`, 'red');
      }
      resolve(false);
    });
    
    req.on('timeout', () => {
      log(`  ⚠ ${serviceName} timeout on ${host}:${port}`, 'yellow');
      req.abort();
      resolve(false);
    });
    
    req.setTimeout(2000);
  });
}

function checkDirectory(dirPath, name) {
  const fullPath = path.resolve(dirPath);
  if (fs.existsSync(fullPath)) {
    const stats = fs.statSync(fullPath);
    if (stats.isDirectory()) {
      // Check if writable
      try {
        const testFile = path.join(fullPath, '.write-test');
        fs.writeFileSync(testFile, 'test');
        fs.unlinkSync(testFile);
        log(`  ✓ ${name} directory exists and is writable: ${fullPath}`, 'green');
        return true;
      } catch (error) {
        log(`  ✗ ${name} directory is not writable: ${fullPath}`, 'red');
        return false;
      }
    } else {
      log(`  ✗ ${name} exists but is not a directory: ${fullPath}`, 'red');
      return false;
    }
  } else {
    log(`  ⚠ ${name} directory does not exist: ${fullPath}`, 'yellow');
    return false;
  }
}

function checkDockerRunning() {
  try {
    execSync('docker info', { stdio: 'ignore' });
    log('  ✓ Docker is running', 'green');
    return true;
  } catch (error) {
    log('  ⚠ Docker is not running (optional)', 'yellow');
    return false;
  }
}

function checkGitLFS() {
  try {
    const output = execSync('git lfs version', { encoding: 'utf-8' });
    log(`  ✓ Git LFS installed: ${output.trim()}`, 'green');
    return true;
  } catch (error) {
    log('  ⚠ Git LFS not installed (recommended for large files)', 'yellow');
    return false;
  }
}

async function main() {
  log('\nValidating environment configuration...', 'blue');
  log('=' .repeat(50), 'blue');
  
  const env = loadEnv();
  const issues = [];
  
  // Check directories
  log('\n📁 Checking directories...', 'blue');
  const workspaceRoot = env.WORKSPACE_ROOT || './workspace';
  if (!checkDirectory(workspaceRoot, 'Workspace')) {
    issues.push('Workspace directory not accessible');
  }
  if (!checkDirectory('./logs', 'Logs')) {
    // Try to create it
    try {
      fs.mkdirSync('./logs', { recursive: true });
      log('  ✓ Created logs directory', 'green');
    } catch (error) {
      issues.push('Could not create logs directory');
    }
  }
  
  // Check services
  log('\n🔌 Checking services...', 'blue');
  
  // Check if backend is running
  const backendHost = env.BACKEND_HOST || 'localhost';
  const backendPort = env.BACKEND_PORT || 8000;
  await checkPort(backendHost, backendPort, 'Backend API');
  
  // Check if frontend is running
  const frontendHost = env.FRONTEND_HOST || 'localhost';
  const frontendPort = env.FRONTEND_PORT || 3000;
  await checkPort(frontendHost, frontendPort, 'Frontend');
  
  // Check AI services (optional)
  log('\n🤖 Checking AI services (optional)...', 'blue');
  const services = [
    { name: 'ComfyUI', host: env.COMFYUI_HOST || 'localhost', port: env.COMFYUI_PORT || 8188 },
    { name: 'Wan2GP', host: env.WAN2GP_HOST || 'localhost', port: env.WAN2GP_PORT || 7860 },
    { name: 'RVC', host: env.RVC_HOST || 'localhost', port: env.RVC_PORT || 7865 },
    { name: 'AudioLDM', host: env.AUDIOLDM_HOST || 'localhost', port: env.AUDIOLDM_PORT || 7863 }
  ];
  
  for (const service of services) {
    await checkPort(service.host, service.port, service.name);
  }
  
  // Check tools
  log('\n🔧 Checking tools...', 'blue');
  checkDockerRunning();
  checkGitLFS();
  
  // Check environment variables
  log('\n🔐 Checking configuration...', 'blue');
  const requiredEnvVars = ['WORKSPACE_ROOT', 'BACKEND_PORT', 'FRONTEND_PORT'];
  const missingVars = requiredEnvVars.filter(varName => !env[varName]);
  
  if (missingVars.length > 0) {
    log(`  ⚠ Missing environment variables: ${missingVars.join(', ')}`, 'yellow');
    issues.push(`Missing environment variables: ${missingVars.join(', ')}`);
  } else {
    log('  ✓ All required environment variables are set', 'green');
  }
  
  // Summary
  log('\n' + '=' .repeat(50), 'blue');
  if (issues.length === 0) {
    log('✅ Environment validation passed!', 'green');
    log('\nYour development environment is properly configured.', 'green');
  } else {
    log('⚠️  Environment validation completed with warnings:', 'yellow');
    issues.forEach(issue => {
      log(`  - ${issue}`, 'yellow');
    });
    log('\nThe application can still run, but some features may not work.', 'yellow');
  }
  
  log('\n💡 Tips:', 'blue');
  log('  - Run "npm run docker:up" to start AI services', 'blue');
  log('  - Check .env file for configuration options', 'blue');
  log('  - See logs/ directory for service logs', 'blue');
}

if (require.main === module) {
  main().catch(error => {
    log(`\n✗ Validation failed: ${error.message}`, 'red');
    process.exit(1);
  });
}