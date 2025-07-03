# Story: End-to-End Project Flow

**Story ID**: STORY-012  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Integration  
**Points**: 5 (Medium)  
**Priority**: High  

## Story Description
As a developer, I need to verify that the complete project creation flow works end-to-end in a containerized environment, from creating a new project through the UI to verifying the file structure and Git initialization on disk, ensuring all distributed components integrate correctly across Docker containers.

## Acceptance Criteria

### Functional Requirements
- [ ] User can create project through UI in containerized frontend
- [ ] Project directory structure is created correctly in shared volume
- [ ] Project.json contains all required fields with proper validation
- [ ] Git repository initializes with proper .gitignore and LFS configuration
- [ ] Project appears in gallery after creation with real-time updates
- [ ] WebSocket broadcasts project creation event across containers
- [ ] Files can be uploaded to the new project (including large media files via Git LFS)
- [ ] Project can be deleted and cleaned up from all containers
- [ ] Structure enforcement validates project organization

### Container Orchestration
- [ ] Docker Compose brings up all services (frontend, backend, worker, redis)
- [ ] Workspace volume mounts correctly across containers
- [ ] Cross-container networking functions properly
- [ ] Redis message queue handles async tasks
- [ ] Worker processes background jobs successfully
- [ ] Health checks pass for all containers
- [ ] Graceful shutdown preserves data integrity

### Integration Points
- [ ] Frontend (port 3000) communicates with backend (port 8000)
- [ ] Backend creates directory structure in shared volume
- [ ] Git service initializes repository with LFS support
- [ ] WebSocket notifies connected clients via Redis pub/sub
- [ ] File system reflects expected state across containers
- [ ] API returns consistent responses under load
- [ ] Worker processes handle async operations
- [ ] Makefile commands orchestrate multi-container operations

### Test Scenarios
1. **Happy Path**: Create project with valid name across containers
2. **Validation**: Reject invalid project names with proper error messages
3. **Duplicate**: Handle existing project names across distributed system
4. **Cleanup**: Delete removes all files from shared volume
5. **Concurrent**: Multiple users creating projects via different containers
6. **Recovery**: Handle partial failures gracefully (container restart)
7. **Volume Persistence**: Data survives container recreation
8. **Git LFS**: Large file uploads work correctly
9. **Network Partition**: Handle temporary container disconnection
10. **Resource Limits**: Respect container memory/CPU constraints

## Implementation Notes

### Container Orchestration Tests
```bash
# tests/container/docker-compose-test.sh
#!/bin/bash

echo "Testing container orchestration..."

# 1. Verify all containers are running
make docker-up
sleep 10  # Wait for services to initialize

# 2. Check container health
docker-compose ps | grep -E "(frontend|backend|worker|redis)" | grep -v "Exit"
if [ $? -ne 0 ]; then
  echo "ERROR: Not all containers are healthy"
  exit 1
fi

# 3. Test cross-container communication
curl -f http://localhost:3000 || exit 1
curl -f http://localhost:8000/health || exit 1

# 4. Verify volume mounts
docker-compose exec backend ls -la /workspace || exit 1
docker-compose exec worker ls -la /workspace || exit 1

# 5. Test Redis connectivity
docker-compose exec redis redis-cli ping || exit 1

# 6. Graceful shutdown test
make docker-down
```

### Integration Test Suite
```typescript
// tests/integration/project-flow.test.ts
import { test, expect } from '@playwright/test';
import { api } from '../helpers/api';
import { fileSystem } from '../helpers/filesystem';
import { docker } from '../helpers/docker';

test.describe('End-to-End Project Flow - Containerized', () => {
  test.beforeAll(async () => {
    // Ensure containers are running
    await docker.ensureRunning(['frontend', 'backend', 'worker', 'redis']);
  });

  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });
  
  test('complete project creation flow across containers', async ({ page }) => {
    const projectName = `test-project-${Date.now()}`;
    
    // 1. Create project through containerized UI
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="name"]', projectName);
    await page.selectOption('select[name="quality"]', 'standard');
    await page.click('button[type="submit"]');
    
    // 2. Verify navigation to project page
    await expect(page).toHaveURL(/\/project\/[\w-]+/);
    
    // 3. Verify project in gallery (tests frontend-backend communication)
    await page.goto('http://localhost:3000');
    await expect(page.locator(`text=${projectName}`)).toBeVisible();
    
    // 4. Verify API response from backend container
    const projects = await api.get('http://localhost:8000/api/v1/projects');
    const project = projects.find(p => p.name === projectName);
    expect(project).toBeDefined();
    expect(project.quality).toBe('standard');
    
    // 5. Verify file structure in shared volume
    const projectPath = `workspace/${projectName}`;
    const volumeCheck = await docker.exec('backend', `ls -la /workspace/${projectName}`);
    expect(volumeCheck).toContain('project.json');
    expect(volumeCheck).toContain('.git');
    expect(volumeCheck).toContain('assets');
    
    // 6. Verify project.json contents via container
    const manifest = await docker.readFile('backend', `/workspace/${projectName}/project.json`);
    expect(JSON.parse(manifest).name).toBe(projectName);
    expect(JSON.parse(manifest).quality).toBe('standard');
    expect(JSON.parse(manifest).version).toBe('1.0.0');
    
    // 7. Verify Git initialization with LFS
    const gitStatus = await api.get(`http://localhost:8000/api/v1/projects/${project.id}/git/status`);
    expect(gitStatus.current_commit).toBeDefined();
    expect(gitStatus.is_dirty).toBe(false);
    
    // Check Git LFS is configured
    const gitAttributes = await docker.readFile('backend', `/workspace/${projectName}/.gitattributes`);
    expect(gitAttributes).toContain('*.mp4 filter=lfs');
    expect(gitAttributes).toContain('*.wav filter=lfs');
    
    // 8. Test large file upload (Git LFS)
    await page.goto(`http://localhost:3000/project/${project.id}`);
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/test-video.mp4');
    
    // 9. Verify file upload handled by worker
    await page.waitForSelector('.upload-item[data-status="completed"]', { timeout: 30000 });
    const files = await api.get(`http://localhost:8000/api/v1/projects/${project.id}/assets`);
    expect(files.length).toBeGreaterThan(0);
    
    // 10. Verify worker processed the job
    const workerLogs = await docker.logs('worker', { tail: 50 });
    expect(workerLogs).toContain(`Processing upload for project ${project.id}`);
    
    // 11. Clean up - delete project from all containers
    await api.delete(`http://localhost:8000/api/v1/projects/${project.id}`);
    const cleanupCheck = await docker.exec('backend', `ls /workspace/${projectName} 2>&1`);
    expect(cleanupCheck).toContain('No such file or directory');
  });
  
  test('handles invalid project names', async ({ page }) => {
    await page.click('button:has-text("New Project")');
    
    // Test empty name
    await page.fill('input[name="name"]', '');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error')).toContainText('required');
    
    // Test invalid characters
    await page.fill('input[name="name"]', 'test/project');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error')).toContainText('Invalid');
  });
  
  test('WebSocket updates across containers via Redis', async ({ page, context }) => {
    // Open second tab (simulating different container connection)
    const page2 = await context.newPage();
    await page2.goto('http://localhost:3000');
    
    // Create project in first tab
    await page.goto('http://localhost:3000');
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="name"]', 'websocket-redis-test');
    await page.click('button[type="submit"]');
    
    // Verify project appears in second tab via Redis pub/sub
    await expect(page2.locator('text=websocket-redis-test')).toBeVisible({
      timeout: 5000
    });
    
    // Verify Redis handled the message
    const redisLogs = await docker.exec('redis', 'redis-cli --scan --pattern "project:*"');
    expect(redisLogs).toContain('project:created');
  });
  
  test('container restart recovery', async ({ page }) => {
    const projectName = `recovery-test-${Date.now()}`;
    
    // Create project
    await api.post('http://localhost:8000/api/v1/projects', {
      name: projectName,
      quality: 'draft'
    });
    
    // Restart backend container
    await docker.restart('backend');
    await docker.waitForHealthy('backend');
    
    // Verify project still accessible
    const projects = await api.get('http://localhost:8000/api/v1/projects');
    const project = projects.find(p => p.name === projectName);
    expect(project).toBeDefined();
    
    // Verify volume data persisted
    const volumeCheck = await docker.exec('backend', `ls -la /workspace/${projectName}`);
    expect(volumeCheck).toContain('project.json');
  });
  
  test('structure enforcement validation', async ({ page }) => {
    const projectName = `structure-test-${Date.now()}`;
    
    // Create project
    const response = await api.post('http://localhost:8000/api/v1/projects', {
      name: projectName,
      quality: 'standard'
    });
    const project = response.data;
    
    // Verify enforced structure
    const structure = await docker.exec('backend', `find /workspace/${projectName} -type d | sort`);
    expect(structure).toContain('/assets');
    expect(structure).toContain('/assets/scripts');
    expect(structure).toContain('/assets/storyboards');
    expect(structure).toContain('/assets/characters');
    expect(structure).toContain('/assets/locations');
    expect(structure).toContain('/assets/styles');
    expect(structure).toContain('/assets/audio');
    expect(structure).toContain('/outputs');
    expect(structure).toContain('/outputs/renders');
    expect(structure).toContain('/outputs/edits');
    expect(structure).toContain('/temp');
    
    // Verify .gitignore includes temp directory
    const gitignore = await docker.readFile('backend', `/workspace/${projectName}/.gitignore`);
    expect(gitignore).toContain('/temp/');
  });
});
```

### Backend Integration Tests
```python
# tests/integration/test_project_flow.py
import pytest
import asyncio
import os
from pathlib import Path
from app.main import app
from app.services.workspace import WorkspaceService
from app.services.redis import RedisService
import docker

@pytest.mark.asyncio
async def test_complete_project_flow_containerized(client, tmp_workspace):
    """Test complete project creation and management flow in containers"""
    
    # 1. Create project through API
    response = await client.post("/api/v1/projects", json={
        "name": "container-integration-test",
        "quality": "standard"
    })
    assert response.status_code == 201
    project = response.json()
    
    # 2. Verify project structure in shared volume
    project_path = Path("/workspace") / "container-integration-test"
    assert project_path.exists()
    assert (project_path / "project.json").exists()
    assert (project_path / ".git").exists()
    assert (project_path / ".gitattributes").exists()
    assert (project_path / "assets" / "scripts").exists()
    
    # 3. Verify Git initialization with LFS
    response = await client.get(f"/api/v1/projects/{project['id']}/git/status")
    assert response.status_code == 200
    git_status = response.json()
    assert not git_status["is_dirty"]
    assert git_status["current_commit"]
    
    # Check Git LFS configuration
    gitattributes = (project_path / ".gitattributes").read_text()
    assert "*.mp4 filter=lfs" in gitattributes
    assert "*.wav filter=lfs" in gitattributes
    assert "*.png filter=lfs" in gitattributes
    
    # 4. Upload large file (trigger Git LFS)
    with open("tests/fixtures/test-video.mp4", "rb") as f:
        response = await client.post(
            f"/api/v1/projects/{project['id']}/assets?asset_type=renders",
            files={"files": ("test-video.mp4", f, "video/mp4")}
        )
    assert response.status_code == 200
    
    # 5. Verify file handled by worker via Redis
    redis = await RedisService.get_client()
    job_key = f"upload:project:{project['id']}"
    job_status = await redis.get(job_key)
    assert job_status is not None
    
    # 6. Verify file exists and is LFS pointer
    video_path = project_path / "assets" / "renders" / "test-video.mp4"
    assert video_path.exists()
    content = video_path.read_text()
    assert content.startswith("version https://git-lfs.github.com")
    
    # 7. Test structure enforcement
    required_dirs = [
        "assets/scripts", "assets/storyboards", "assets/characters",
        "assets/locations", "assets/styles", "assets/audio",
        "outputs/renders", "outputs/edits", "temp"
    ]
    for dir_path in required_dirs:
        assert (project_path / dir_path).exists()
    
    # 8. Delete project and verify cleanup
    response = await client.delete(f"/api/v1/projects/{project['id']}")
    assert response.status_code == 204
    assert not project_path.exists()

@pytest.mark.asyncio
async def test_cross_container_communication(client):
    """Test communication between frontend, backend, and worker containers"""
    
    # 1. Health check all services
    health_response = await client.get("/health")
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["status"] == "healthy"
    assert health_data["redis"] == "connected"
    assert health_data["worker"] == "running"
    
    # 2. Create project that triggers worker job
    response = await client.post("/api/v1/projects", json={
        "name": "worker-test",
        "quality": "premium",
        "process_async": True
    })
    assert response.status_code == 201
    project = response.json()
    assert project["status"] == "processing"
    
    # 3. Check job queued in Redis
    redis = await RedisService.get_client()
    job_queue = await redis.llen("job:queue:default")
    assert job_queue > 0
    
    # 4. Wait for worker to process
    await asyncio.sleep(2)
    
    # 5. Verify project status updated
    response = await client.get(f"/api/v1/projects/{project['id']}")
    updated_project = response.json()
    assert updated_project["status"] == "ready"

@pytest.mark.asyncio
async def test_volume_persistence_across_restarts():
    """Test data persists when containers are restarted"""
    
    docker_client = docker.from_env()
    
    # 1. Create project
    response = await client.post("/api/v1/projects", json={
        "name": "persistence-test",
        "quality": "standard"
    })
    project = response.json()
    project_path = Path("/workspace") / "persistence-test"
    
    # 2. Write test data
    test_file = project_path / "test-data.txt"
    test_file.write_text("This should persist")
    
    # 3. Restart backend container
    backend_container = docker_client.containers.get("auteur-backend")
    backend_container.restart()
    
    # Wait for healthy status
    for _ in range(30):
        if backend_container.status == "running":
            break
        await asyncio.sleep(1)
    
    # 4. Verify data persisted
    assert project_path.exists()
    assert test_file.read_text() == "This should persist"
    
    # 5. Verify project still accessible via API
    response = await client.get(f"/api/v1/projects/{project['id']}")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_makefile_integration():
    """Test Makefile commands work with containerized environment"""
    
    import subprocess
    
    # 1. Test make commands
    commands = [
        ("make docker-health", "All services healthy"),
        ("make workspace-init", "Workspace initialized"),
        ("make project-create NAME=makefile-test", "Project created"),
        ("make project-list", "makefile-test"),
    ]
    
    for cmd, expected_output in commands:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        assert result.returncode == 0
        assert expected_output in result.stdout
```

### Manual Test Checklist
```markdown
## Manual Testing Checklist - Containerized Environment

### Container Setup
- [ ] Run `make docker-up` and verify all containers start
- [ ] Check `docker-compose ps` shows all services healthy
- [ ] Verify frontend accessible at http://localhost:3000
- [ ] Verify backend health at http://localhost:8000/health
- [ ] Check Redis connection with `docker-compose exec redis redis-cli ping`
- [ ] Verify worker logs with `docker-compose logs worker`

### Project Creation (Containerized)
- [ ] Create project with short name (< 10 chars)
- [ ] Create project with long name (> 50 chars)
- [ ] Create project with special characters (spaces, dashes)
- [ ] Try to create duplicate project name
- [ ] Create projects with each quality tier
- [ ] Verify project appears in shared volume

### File Operations (with Git LFS)
- [ ] Upload single small file (< 1MB)
- [ ] Upload single large file (> 50MB) - verify Git LFS
- [ ] Upload multiple files at once
- [ ] Upload video file (*.mp4) - check LFS pointer
- [ ] Upload audio file (*.wav) - check LFS pointer
- [ ] Cancel upload in progress
- [ ] Verify files accessible across containers

### Cross-Container Testing
- [ ] Create project in one browser, see it in another
- [ ] Upload file and verify worker processes it
- [ ] Check WebSocket updates via Redis pub/sub
- [ ] Restart backend container, verify data persists
- [ ] Stop worker, verify graceful job handling

### Makefile Commands
- [ ] `make workspace-init` creates workspace directory
- [ ] `make project-create NAME=test-project` works
- [ ] `make project-list` shows all projects
- [ ] `make docker-logs` displays container logs
- [ ] `make docker-health` shows service status
- [ ] `make docker-restart` gracefully restarts services

### Volume and Persistence
- [ ] Create project, restart containers, project still exists
- [ ] Upload files, restart containers, files still accessible
- [ ] Modify project.json, changes persist
- [ ] Delete container, recreate, data still in volume
- [ ] Backup workspace directory works

### Performance Testing (Distributed)
- [ ] Create 50+ projects across multiple workers
- [ ] Upload 100+ files with worker processing
- [ ] Multiple containers accessing same project
- [ ] Slow network between containers
- [ ] High Redis message throughput
- [ ] Container resource limits respected
```

### Monitoring Setup
```typescript
// src/lib/monitoring/flow.ts
export interface ContainerMetrics {
  container: string;
  cpu_usage: number;
  memory_usage: number;
  network_io: {
    rx_bytes: number;
    tx_bytes: number;
  };
}

export function trackProjectFlow() {
  // Track key metrics
  performance.mark('project_create_start');
  
  // After creation
  performance.mark('project_create_end');
  performance.measure('project_creation_time', 
    'project_create_start', 
    'project_create_end'
  );
  
  // Track container metrics
  const containerMetrics = await getContainerMetrics();
  
  // Log to analytics
  analytics.track('project_created', {
    duration: performance.getEntriesByName('project_creation_time')[0].duration,
    quality: projectData.quality,
    timestamp: new Date().toISOString(),
    container_metrics: containerMetrics,
    volume_usage: await getVolumeUsage('/workspace')
  });
}

// Monitor cross-container communication
export async function trackRedisLatency() {
  const start = performance.now();
  await redis.ping();
  const latency = performance.now() - start;
  
  metrics.gauge('redis_latency_ms', latency);
  
  if (latency > 100) {
    console.warn(`High Redis latency detected: ${latency}ms`);
  }
}

// Docker health monitoring
export async function monitorContainerHealth() {
  const services = ['frontend', 'backend', 'worker', 'redis'];
  
  for (const service of services) {
    const health = await docker.getContainerHealth(service);
    
    metrics.gauge(`container_${service}_healthy`, health.status === 'healthy' ? 1 : 0);
    metrics.gauge(`container_${service}_cpu_percent`, health.cpu_percent);
    metrics.gauge(`container_${service}_memory_mb`, health.memory_usage_mb);
  }
}
```

### Docker Compose E2E Configuration
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  test-runner:
    build:
      context: .
      dockerfile: Dockerfile.test
    volumes:
      - ./tests:/app/tests
      - ./workspace:/workspace
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
      - TEST_MODE=e2e
    depends_on:
      frontend:
        condition: service_healthy
      backend:
        condition: service_healthy
      worker:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: npm run test:e2e

  frontend:
    extends:
      file: docker-compose.yml
      service: frontend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    extends:
      file: docker-compose.yml
      service: backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 5s
      timeout: 3s
      retries: 5

  worker:
    extends:
      file: docker-compose.yml
      service: worker
    healthcheck:
      test: ["CMD", "python", "-c", "import redis; r=redis.Redis('redis'); r.ping()"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    extends:
      file: docker-compose.yml
      service: redis
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

## Dependencies
- All previous stories completed
- Docker and Docker Compose installed
- Test fixtures and helpers
- Integration test framework
- Redis for cross-container messaging
- Git LFS configured
- Shared workspace volume

## Testing Criteria
- [ ] Full flow works without manual intervention
- [ ] All integration points verified across containers
- [ ] Error scenarios handled gracefully
- [ ] Performance within acceptable limits (< 2s for project creation)
- [ ] No orphaned files, processes, or containers
- [ ] Concurrent operations don't conflict
- [ ] Container health checks pass
- [ ] Volume persistence verified
- [ ] Cross-container WebSocket communication works
- [ ] Git LFS handles large files correctly
- [ ] Makefile commands integrate with Docker stack

## Definition of Done
- [ ] Integration tests pass consistently in containers
- [ ] E2E tests run via docker-compose.test.yml
- [ ] Manual test checklist completed for containerized environment
- [ ] Performance benchmarks established (container overhead < 10%)
- [ ] Error recovery verified (container restart resilience)
- [ ] Documentation includes container troubleshooting
- [ ] Monitoring alerts configured for all services
- [ ] Docker health checks implemented and passing
- [ ] Volume backup/restore procedures documented
- [ ] Resource limits defined and tested

## Story Links
- **Depends On**: All other stories in epic
- **Validates**: Complete web platform foundation
- **Related PRD**: PRD-001-web-platform-foundation