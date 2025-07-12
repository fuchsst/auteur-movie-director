# Story: End-to-End Project Flow

**Story ID**: STORY-012  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Integration  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

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
- [ ] Character assets can be created and managed through full lifecycle
- [ ] Character base face uploads route to 01_Assets/Characters directory
- [ ] LoRA training tasks execute through worker with progress tracking
- [ ] Character variations generate and store in proper subdirectories
- [ ] Character usage tracking works across scenes and shots
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
11. **WebSocket Task Execution**: Validate async task lifecycle (start_generation → progress → success)
12. **Quality Mapping**: Verify project quality affects task execution parameters
13. **Redis Event Relay**: Confirm pub/sub broadcasts task updates correctly
14. **Output Path Validation**: Ensure renders go to 03_Renders directory
15. **Node State Sync**: UI reflects real-time task progress and completion
16. **Character Creation**: Full character asset lifecycle from creation to usage
17. **LoRA Training**: Async LoRA training with WebSocket progress updates
18. **Character Variations**: Generation of character emotional variations
19. **Character Sheet UI**: Display of character with all variations and metadata
20. **Character Usage**: Track character usage across multiple shots/scenes

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
  
  test('WebSocket task execution flow with quality mapping', async ({ page }) => {
    const projectName = `task-execution-test-${Date.now()}`;
    
    // Create project with specific quality
    const response = await api.post('http://localhost:8000/api/v1/projects', {
      name: projectName,
      quality: 'premium'  // This should affect task parameters
    });
    const project = response.json();
    
    // Navigate to project and trigger a mock text-to-image generation
    await page.goto(`http://localhost:3000/project/${project.id}`);
    
    // Listen for WebSocket messages
    const wsMessages = [];
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        const data = JSON.parse(event.payload);
        wsMessages.push(data);
      });
    });
    
    // Trigger generation task (simulated)
    const taskPayload = {
      type: 'text_to_image',
      prompt: 'A cinematic shot of a sunset',
      node_id: 'test-node-123',
      quality_preset: project.quality  // Should map to specific parameters
    };
    
    const taskResponse = await api.post(
      `http://localhost:8000/api/v1/projects/${project.id}/tasks`,
      taskPayload
    );
    const task = taskResponse.json();
    
    // Verify task started
    expect(task.status).toBe('pending');
    expect(task.type).toBe('text_to_image');
    
    // Wait for WebSocket updates
    await page.waitForTimeout(1000);
    
    // Verify WebSocket message flow
    const startMsg = wsMessages.find(m => m.type === 'task.started');
    expect(startMsg).toBeDefined();
    expect(startMsg.data.task_id).toBe(task.id);
    expect(startMsg.data.node_id).toBe('test-node-123');
    
    // Verify Redis pub/sub relayed the event
    const redisLogs = await docker.exec('redis', `redis-cli PUBSUB CHANNELS task:*`);
    expect(redisLogs).toContain(`task:${project.id}`);
    
    // Verify quality mapping affected parameters
    const taskDetails = await api.get(`http://localhost:8000/api/v1/tasks/${task.id}`);
    expect(taskDetails.parameters.steps).toBe(50);  // Premium = 50 steps
    expect(taskDetails.parameters.cfg_scale).toBe(7.5);
    
    // Wait for task completion (mocked worker)
    await page.waitForFunction(
      () => document.querySelector('[data-task-status="completed"]'),
      { timeout: 10000 }
    );
    
    // Verify completion message
    const completeMsg = wsMessages.find(m => m.type === 'task.completed');
    expect(completeMsg).toBeDefined();
    expect(completeMsg.data.output_path).toContain('/03_Renders/');
    
    // Verify output file in correct directory
    const outputCheck = await docker.exec(
      'backend', 
      `ls -la /workspace/${projectName}/03_Renders/`
    );
    expect(outputCheck).toContain('.png');
    
    // Verify node state updated in UI
    const nodeElement = page.locator(`[data-node-id="test-node-123"]`);
    await expect(nodeElement).toHaveAttribute('data-status', 'completed');
    await expect(nodeElement.locator('.output-preview')).toBeVisible();
  });
  
  test('Function Runner infrastructure validation', async ({ page }) => {
    const projectName = `function-runner-test-${Date.now()}`;
    
    // Create project
    const project = await api.post('http://localhost:8000/api/v1/projects', {
      name: projectName,
      quality: 'draft'  // Fast execution for testing
    });
    
    // Test multiple concurrent tasks
    const tasks = [];
    for (let i = 0; i < 3; i++) {
      tasks.push(api.post(`http://localhost:8000/api/v1/projects/${project.id}/tasks`, {
        type: 'text_to_image',
        prompt: `Test prompt ${i}`,
        node_id: `node-${i}`
      }));
    }
    
    const taskResponses = await Promise.all(tasks);
    const taskIds = taskResponses.map(r => r.json().id);
    
    // Monitor task execution via WebSocket
    await page.goto(`http://localhost:3000/project/${project.id}`);
    
    // Verify tasks queued in Redis
    const queueStatus = await docker.exec(
      'redis',
      'redis-cli LLEN task:queue:default'
    );
    expect(parseInt(queueStatus)).toBeGreaterThanOrEqual(3);
    
    // Verify worker picks up tasks
    const workerLogs = await docker.logs('worker', { tail: 100 });
    for (const taskId of taskIds) {
      expect(workerLogs).toContain(`Processing task ${taskId}`);
    }
    
    // Wait for all tasks to complete
    await page.waitForFunction(
      () => {
        const completedNodes = document.querySelectorAll('[data-status="completed"]');
        return completedNodes.length >= 3;
      },
      { timeout: 30000 }
    );
    
    // Verify all outputs in correct directory structure
    const outputs = await docker.exec(
      'backend',
      `find /workspace/${projectName}/03_Renders -name "*.png" | wc -l`
    );
    expect(parseInt(outputs.trim())).toBe(3);
    
    // Verify worker can access shared volume
    const volumeTest = await docker.exec(
      'worker',
      `ls -la /workspace/${projectName}/03_Renders/`
    );
    expect(volumeTest).not.toContain('Permission denied');
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
  
  test('character asset lifecycle across containers', async ({ page }) => {
    const projectName = `character-test-${Date.now()}`;
    
    // 1. Create project
    const response = await api.post('http://localhost:8000/api/v1/projects', {
      name: projectName,
      quality: 'standard'
    });
    const project = response.json();
    
    // 2. Navigate to project
    await page.goto(`http://localhost:3000/project/${project.id}`);
    
    // 3. Create new character through UI
    await page.click('button:has-text("New Character")');
    await page.fill('input[name="characterName"]', 'Sarah Connor');
    await page.fill('textarea[name="description"]', 'Strong female protagonist');
    await page.fill('input[name="triggerWord"]', 'sarahconnor_lora');
    await page.click('button[type="submit"]');
    
    // 4. Verify character created in backend
    const characters = await api.get(`http://localhost:8000/api/v1/projects/${project.id}/characters`);
    expect(characters.length).toBe(1);
    expect(characters[0].name).toBe('Sarah Connor');
    
    // 5. Upload base face image
    const characterId = characters[0].assetId;
    const baseFaceInput = page.locator('input[data-character-base-face]');
    await baseFaceInput.setInputFiles('./tests/fixtures/sarah_base_face.png');
    
    // 6. Verify file stored in correct directory
    const baseFaceCheck = await docker.exec(
      'backend',
      `ls -la /workspace/${projectName}/01_Assets/Characters/${characterId}/`
    );
    expect(baseFaceCheck).toContain('base_face.png');
    
    // 7. Trigger LoRA training
    await page.click('button:has-text("Train LoRA")');
    
    // 8. Monitor WebSocket for training progress
    const wsMessages = [];
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        const data = JSON.parse(event.payload);
        if (data.type === 'character.lora.status') {
          wsMessages.push(data);
        }
      });
    });
    
    // 9. Verify training task queued in Redis
    const trainingTask = await docker.exec(
      'redis',
      `redis-cli LRANGE task:queue:lora 0 -1`
    );
    expect(trainingTask).toContain(characterId);
    
    // 10. Wait for training progress updates
    await page.waitForTimeout(2000);
    
    // Verify progress messages received
    const progressMsg = wsMessages.find(m => m.status === 'training');
    expect(progressMsg).toBeDefined();
    expect(progressMsg.char_id).toBe(characterId);
    expect(progressMsg.progress).toBeGreaterThan(0);
    
    // 11. Generate character variations
    await page.click('button:has-text("Generate Variations")');
    const variations = ['happy', 'sad', 'angry', 'surprised', 'neutral'];
    
    // 12. Wait for variations to complete
    await page.waitForSelector('[data-variations-complete]', { timeout: 30000 });
    
    // 13. Verify variations stored in subdirectory
    const variationsCheck = await docker.exec(
      'backend',
      `ls -la /workspace/${projectName}/01_Assets/Characters/${characterId}/variations/`
    );
    for (const variation of variations) {
      expect(variationsCheck).toContain(`${variation}.png`);
    }
    
    // 14. Test character usage in composite prompt
    await page.goto(`http://localhost:3000/project/${project.id}/canvas`);
    await page.click('button:has-text("Add Text to Image Node")');
    
    // Select character in node
    await page.click('[data-node-character-select]');
    await page.click(`text="Sarah Connor"`);
    
    // Generate image with character
    await page.fill('[data-node-prompt]', 'A woman in a post-apocalyptic setting');
    await page.click('button:has-text("Generate")');
    
    // 15. Verify character usage tracked
    const usage = await api.get(
      `http://localhost:8000/api/v1/projects/${project.id}/characters/${characterId}/usage`
    );
    expect(usage.totalUsages).toBe(1);
    expect(usage.shotIds.length).toBeGreaterThan(0);
    
    // 16. Verify Character Sheet UI displays all data
    await page.goto(`http://localhost:3000/project/${project.id}/characters/${characterId}`);
    
    // Check base face displayed
    await expect(page.locator('img[data-base-face]')).toBeVisible();
    
    // Check all variations displayed
    for (const variation of variations) {
      await expect(page.locator(`img[data-variation="${variation}"]`)).toBeVisible();
    }
    
    // Check LoRA status
    await expect(page.locator('[data-lora-status]')).toContainText('completed');
    
    // Check usage stats
    await expect(page.locator('[data-usage-count]')).toContainText('1');
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
async def test_character_lifecycle_containerized(client, tmp_workspace):
    """Test complete character asset lifecycle in containers"""
    
    # 1. Create project
    response = await client.post("/api/v1/projects", json={
        "name": "character-backend-test",
        "quality": "standard"
    })
    assert response.status_code == 201
    project = response.json()
    project_path = Path("/workspace") / "character-backend-test"
    
    # 2. Create character
    response = await client.post(f"/api/v1/projects/{project['id']}/characters", json={
        "name": "John Wick",
        "description": "Professional assassin, dark suit, intense gaze",
        "triggerWord": "johnwick_lora"
    })
    assert response.status_code == 201
    character = response.json()
    assert character["name"] == "John Wick"
    assert character["loraTrainingStatus"] == "untrained"
    
    # 3. Verify character directory structure
    char_path = project_path / "01_Assets" / "Characters" / character["assetId"]
    assert char_path.exists()
    assert (char_path / "variations").exists()
    
    # 4. Upload base face via multipart
    with open("tests/fixtures/john_base_face.png", "rb") as f:
        response = await client.post(
            f"/api/v1/projects/{project['id']}/characters/{character['assetId']}/base-face",
            files={"file": ("base_face.png", f, "image/png")}
        )
    assert response.status_code == 200
    
    # 5. Verify base face stored correctly
    base_face_path = char_path / "base_face.png"
    assert base_face_path.exists()
    assert base_face_path.stat().st_size > 1000  # Not empty
    
    # 6. Trigger LoRA training task
    response = await client.post(
        f"/api/v1/projects/{project['id']}/characters/{character['assetId']}/lora/train",
        json={
            "epochs": 10,
            "learningRate": 0.0001,
            "batchSize": 4
        }
    )
    assert response.status_code == 202
    task = response.json()
    assert task["status"] == "pending"
    
    # 7. Verify task queued in Redis
    redis = await RedisService.get_client()
    task_data = await redis.get(f"task:{task['task_id']}")
    assert task_data is not None
    task_obj = json.loads(task_data)
    assert task_obj["type"] == "lora_training"
    assert task_obj["character_id"] == character["assetId"]
    
    # 8. Simulate worker updating status
    await redis.publish(
        f"task:{project['id']}",
        json.dumps({
            "type": "character.lora.status",
            "data": {
                "char_id": character["assetId"],
                "status": "training",
                "progress": 50,
                "currentStep": 5,
                "totalSteps": 10
            }
        })
    )
    
    # 9. Check character status updated
    response = await client.get(
        f"/api/v1/projects/{project['id']}/characters/{character['assetId']}"
    )
    updated_char = response.json()
    assert updated_char["loraTrainingStatus"] == "training"
    
    # 10. Generate variations
    response = await client.post(
        f"/api/v1/projects/{project['id']}/characters/{character['assetId']}/variations/generate",
        json={"variation_types": ["happy", "sad", "angry"]}
    )
    assert response.status_code == 202
    variations_task = response.json()
    
    # 11. Simulate variation generation completion
    for variation_type in ["happy", "sad", "angry"]:
        variation_path = char_path / "variations" / f"{variation_type}.png"
        variation_path.parent.mkdir(exist_ok=True)
        variation_path.write_bytes(b"mock image data")
    
    # 12. Verify variations accessible
    response = await client.get(
        f"/api/v1/projects/{project['id']}/characters/{character['assetId']}/variations"
    )
    variations = response.json()
    assert len(variations) == 3
    assert "happy" in variations
    
    # 13. Test character usage tracking
    # Simulate usage in a shot
    await client.post(
        f"/api/v1/projects/{project['id']}/characters/{character['assetId']}/usage",
        json={
            "shotId": "shot_001",
            "sceneId": "scene_001",
            "takeId": "take_001"
        }
    )
    
    # 14. Verify usage tracked
    response = await client.get(
        f"/api/v1/projects/{project['id']}/characters/{character['assetId']}/usage"
    )
    usage = response.json()
    assert usage["totalUsages"] == 1
    assert "shot_001" in usage["shotIds"]
    
    # 15. Test composite prompt building with character
    response = await client.post(
        "/api/v1/assets/composite-prompt",
        json={
            "base_prompt": "A man in a nightclub",
            "characterIds": [character["assetId"]],
            "emotionalBeat": "intense"
        }
    )
    composite = response.json()
    assert character["triggerWord"] in composite["final_prompt"]
    assert len(composite["lora_models"]) == 1

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
async def test_websocket_task_execution_lifecycle(client, websocket_client):
    """Test complete async task lifecycle with WebSocket updates"""
    
    # 1. Create project with quality mapping
    response = await client.post("/api/v1/projects", json={
        "name": "websocket-task-test",
        "quality": "premium"
    })
    project = response.json()
    
    # 2. Connect WebSocket client
    ws_messages = []
    async def message_handler(message):
        ws_messages.append(json.loads(message))
    
    await websocket_client.connect(f"/ws/projects/{project['id']}")
    websocket_client.on_message = message_handler
    
    # 3. Submit text-to-image task
    task_response = await client.post(
        f"/api/v1/projects/{project['id']}/tasks",
        json={
            "type": "text_to_image",
            "prompt": "A dramatic landscape",
            "node_id": "test-node-001",
            "parameters": {
                "seed": 12345,
                "width": 1024,
                "height": 1024
            }
        }
    )
    task = task_response.json()
    assert task["status"] == "pending"
    assert task["quality_preset"] == "premium"
    
    # 4. Verify task queued in Redis
    redis = await RedisService.get_client()
    task_data = await redis.get(f"task:{task['id']}")
    assert task_data is not None
    task_obj = json.loads(task_data)
    assert task_obj["parameters"]["steps"] == 50  # Premium quality
    
    # 5. Wait for WebSocket updates
    await asyncio.sleep(0.5)
    
    # Verify start message
    start_msg = next((m for m in ws_messages if m["type"] == "task.started"), None)
    assert start_msg is not None
    assert start_msg["data"]["task_id"] == task["id"]
    assert start_msg["data"]["node_id"] == "test-node-001"
    
    # 6. Simulate worker progress updates
    for progress in [25, 50, 75, 100]:
        await redis.publish(
            f"task:{project['id']}",
            json.dumps({
                "type": "task.progress",
                "data": {
                    "task_id": task["id"],
                    "progress": progress,
                    "node_id": "test-node-001"
                }
            })
        )
        await asyncio.sleep(0.1)
    
    # 7. Simulate task completion
    output_path = f"/workspace/websocket-task-test/03_Renders/output_{task['id']}.png"
    await redis.publish(
        f"task:{project['id']}",
        json.dumps({
            "type": "task.completed",
            "data": {
                "task_id": task["id"],
                "node_id": "test-node-001",
                "output_path": output_path,
                "duration": 15.5
            }
        })
    )
    
    # 8. Verify completion message received
    await asyncio.sleep(0.5)
    complete_msg = next((m for m in ws_messages if m["type"] == "task.completed"), None)
    assert complete_msg is not None
    assert complete_msg["data"]["output_path"] == output_path
    assert "/03_Renders/" in complete_msg["data"]["output_path"]
    
    # 9. Verify task status updated
    status_response = await client.get(f"/api/v1/tasks/{task['id']}")
    updated_task = status_response.json()
    assert updated_task["status"] == "completed"
    assert updated_task["output_path"] == output_path

@pytest.mark.asyncio
async def test_quality_mapping_affects_execution(client):
    """Test that project quality properly maps to execution parameters"""
    
    quality_mappings = {
        "draft": {"steps": 20, "cfg_scale": 7.0, "sampler": "euler"},
        "standard": {"steps": 30, "cfg_scale": 7.5, "sampler": "euler_a"},
        "premium": {"steps": 50, "cfg_scale": 7.5, "sampler": "dpm++_2m"}
    }
    
    for quality, expected_params in quality_mappings.items():
        # Create project with specific quality
        response = await client.post("/api/v1/projects", json={
            "name": f"quality-test-{quality}",
            "quality": quality
        })
        project = response.json()
        
        # Submit task
        task_response = await client.post(
            f"/api/v1/projects/{project['id']}/tasks",
            json={
                "type": "text_to_image",
                "prompt": "Test prompt",
                "node_id": f"node-{quality}"
            }
        )
        task = task_response.json()
        
        # Verify parameters mapped correctly
        assert task["parameters"]["steps"] == expected_params["steps"]
        assert task["parameters"]["cfg_scale"] == expected_params["cfg_scale"]
        assert task["parameters"]["sampler"] == expected_params["sampler"]

@pytest.mark.asyncio
async def test_redis_pubsub_event_relay(client, redis_client):
    """Test Redis pub/sub correctly relays events between services"""
    
    # 1. Create project
    project = await client.post("/api/v1/projects", json={
        "name": "redis-relay-test",
        "quality": "standard"
    })
    project_id = project.json()["id"]
    
    # 2. Subscribe to project channel
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"task:{project_id}")
    
    # 3. Submit task via API
    task_response = await client.post(
        f"/api/v1/projects/{project_id}/tasks",
        json={
            "type": "text_to_image",
            "prompt": "Redis test",
            "node_id": "redis-test-node"
        }
    )
    task = task_response.json()
    
    # 4. Verify task creation event published
    message = await pubsub.get_message(timeout=5)
    assert message is not None
    event = json.loads(message["data"])
    assert event["type"] == "task.created"
    assert event["data"]["task_id"] == task["id"]
    
    # 5. Test cross-service communication
    # Simulate worker picking up task
    await redis_client.publish(
        f"task:{project_id}",
        json.dumps({
            "type": "task.started",
            "data": {"task_id": task["id"], "worker_id": "worker-001"}
        })
    )
    
    # Verify backend receives and processes event
    await asyncio.sleep(0.5)
    status_response = await client.get(f"/api/v1/tasks/{task['id']}")
    assert status_response.json()["status"] == "processing"

@pytest.mark.asyncio
async def test_output_directory_structure(client, tmp_workspace):
    """Test outputs are correctly placed in 03_Renders directory"""
    
    # 1. Create project
    response = await client.post("/api/v1/projects", json={
        "name": "output-structure-test",
        "quality": "standard"
    })
    project = response.json()
    project_path = Path("/workspace/output-structure-test")
    
    # 2. Verify 03_Renders directory exists
    renders_dir = project_path / "03_Renders"
    assert renders_dir.exists()
    assert renders_dir.is_dir()
    
    # 3. Submit multiple tasks
    task_ids = []
    for i in range(3):
        task_response = await client.post(
            f"/api/v1/projects/{project['id']}/tasks",
            json={
                "type": "text_to_image",
                "prompt": f"Test render {i}",
                "node_id": f"node-{i}"
            }
        )
        task_ids.append(task_response.json()["id"])
    
    # 4. Simulate task completion with outputs
    for task_id in task_ids:
        output_file = renders_dir / f"render_{task_id}.png"
        output_file.write_text("mock image data")
        
        # Update task with output path
        await client.patch(
            f"/api/v1/tasks/{task_id}",
            json={
                "status": "completed",
                "output_path": str(output_file)
            }
        )
    
    # 5. Verify all outputs in correct location
    render_files = list(renders_dir.glob("*.png"))
    assert len(render_files) == 3
    
    # 6. Verify outputs accessible via API
    assets_response = await client.get(
        f"/api/v1/projects/{project['id']}/assets?asset_type=renders"
    )
    renders = assets_response.json()
    assert len(renders) == 3
    for render in renders:
        assert "/03_Renders/" in render["path"]

@pytest.mark.asyncio
async def test_worker_shared_volume_access(docker_client):
    """Test worker container can properly access shared workspace volume"""
    
    # 1. Create test directory via backend
    backend_container = docker_client.containers.get("auteur-backend")
    backend_container.exec_run(
        "mkdir -p /workspace/worker-access-test/03_Renders"
    )
    
    # 2. Write test file via backend
    backend_container.exec_run(
        "echo 'test data' > /workspace/worker-access-test/03_Renders/test.txt"
    )
    
    # 3. Verify worker can read the file
    worker_container = docker_client.containers.get("auteur-worker")
    result = worker_container.exec_run(
        "cat /workspace/worker-access-test/03_Renders/test.txt"
    )
    assert result.exit_code == 0
    assert b"test data" in result.output
    
    # 4. Test worker can write files
    worker_container.exec_run(
        "echo 'worker output' > /workspace/worker-access-test/03_Renders/worker.txt"
    )
    
    # 5. Verify backend can read worker's file
    result = backend_container.exec_run(
        "cat /workspace/worker-access-test/03_Renders/worker.txt"
    )
    assert result.exit_code == 0
    assert b"worker output" in result.output
    
    # 6. Test permissions
    result = worker_container.exec_run(
        "ls -la /workspace/worker-access-test/03_Renders/"
    )
    assert result.exit_code == 0
    assert b"test.txt" in result.output
    assert b"worker.txt" in result.output

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
- [ ] Check agent endpoints at http://localhost:8000/api/v1/agents/*/capabilities

### Project Creation (Containerized)
- [ ] Create project with short name (< 10 chars)
- [ ] Create project with long name (> 50 chars)
- [ ] Create project with special characters (spaces, dashes)
- [ ] Try to create duplicate project name
- [ ] Create projects with each quality tier
- [ ] Select narrative structure (three-act, hero-journey, etc.)
- [ ] Verify project appears in shared volume
- [ ] Check asset subdirectories created (Characters, Styles, Locations, Music)
- [ ] Verify narrative structure in project.json

### File Operations (with Git LFS)
- [ ] Upload single small file (< 1MB)
- [ ] Upload single large file (> 50MB) - verify Git LFS
- [ ] Upload character LoRA (.safetensors) - verify metadata extraction
- [ ] Upload style model - check Art Director compatibility
- [ ] Upload location HDR - verify environment detection
- [ ] Upload music file - check BPM/mood extraction
- [ ] Upload screenplay (.fountain) - verify Screenwriter compatibility
- [ ] Upload beat sheet - check emotional beat detection
- [ ] Upload multiple files at once
- [ ] Cancel upload in progress
- [ ] Verify files accessible across containers
- [ ] Check assets routed to correct directories

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

### WebSocket Task Execution
- [ ] Submit text-to-image task and monitor WebSocket messages
- [ ] Verify task.started message received with correct node_id
- [ ] Progress updates appear in real-time (25%, 50%, 75%, 100%)
- [ ] Task completion message includes output path
- [ ] Output file appears in 03_Renders directory
- [ ] Node UI updates to show completed status
- [ ] Multiple concurrent tasks execute properly
- [ ] Task cancellation works and updates UI

### Quality Mapping and Parameters
- [ ] Draft quality uses 20 steps, 7.0 cfg_scale
- [ ] Standard quality uses 30 steps, 7.5 cfg_scale  
- [ ] Premium quality uses 50 steps, 7.5 cfg_scale
- [ ] Quality setting persists in task parameters
- [ ] Backend correctly maps quality to execution settings

### Redis Pub/Sub Testing
- [ ] Task events published to correct Redis channel
- [ ] Multiple clients receive same event via pub/sub
- [ ] Events relay between backend and worker correctly
- [ ] Message format follows expected schema
- [ ] No message loss under high load

### Function Runner Infrastructure
- [ ] Worker picks up tasks from Redis queue
- [ ] Task status updates propagate correctly
- [ ] Output files written to shared volume
- [ ] Worker can access project directories
- [ ] Concurrent task execution doesn't conflict
- [ ] Task retry on failure works properly

### Character Asset Testing
- [ ] Create character with name, description, trigger word
- [ ] Upload base face image - verify stored in 01_Assets/Characters/{id}/
- [ ] Base face appears in Character Sheet UI
- [ ] Train LoRA - monitor WebSocket progress updates
- [ ] LoRA training status transitions: untrained → training → completed
- [ ] Generate character variations (happy, sad, angry, etc.)
- [ ] All variations display in Character Sheet grid
- [ ] Variations stored in /variations subdirectory
- [ ] Use character in text-to-image node
- [ ] Character trigger word injected into prompt
- [ ] Track character usage across multiple shots
- [ ] Character usage statistics display correctly
- [ ] Delete character removes all associated files
- [ ] Character persists across container restarts

### Performance Testing (Distributed)
- [ ] Create 50+ projects across multiple workers
- [ ] Upload 100+ files with worker processing
- [ ] Multiple containers accessing same project
- [ ] Slow network between containers
- [ ] High Redis message throughput
- [ ] Container resource limits respected
- [ ] Async task throughput meets requirements
- [ ] Train multiple LoRAs concurrently
- [ ] Generate variations for 10+ characters
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
- [ ] Async task lifecycle validated (start → progress → complete)
- [ ] Quality presets correctly map to execution parameters
- [ ] Redis pub/sub reliably broadcasts task events
- [ ] Task outputs stored in 03_Renders directory
- [ ] Node state synchronizes with backend task status
- [ ] Worker processes can access shared workspace volume
- [ ] Function Runner foundation supports concurrent tasks
- [ ] Character creation and management flows work end-to-end
- [ ] LoRA training tasks execute with progress tracking
- [ ] Character variations generate and store correctly
- [ ] Character usage tracking integrates with shot management
- [ ] Character assets persist across container lifecycle

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
- [ ] WebSocket task execution tests pass (including progress updates)
- [ ] Quality mapping integration verified across all tiers
- [ ] Redis pub/sub event flow documented and tested
- [ ] Function Runner foundation validated with concurrent tasks
- [ ] Task output directory structure enforced (03_Renders)
- [ ] Worker-backend shared volume access confirmed
- [ ] Character lifecycle tests pass (create, train, generate, track)
- [ ] Character WebSocket events broadcast correctly
- [ ] Character file structure validated (base_face.png, variations/, lora/)
- [ ] Character-node integration tested end-to-end

## Story Links
- **Depends On**: All other stories in epic
- **Validates**: Complete web platform foundation
- **Related PRD**: PRD-001-web-platform-foundation