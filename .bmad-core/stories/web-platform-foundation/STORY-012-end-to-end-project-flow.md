# Story: End-to-End Project Flow

**Story ID**: STORY-012  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Integration  
**Points**: 3 (Small)  
**Priority**: High  

## Story Description
As a developer, I need to verify that the complete project creation flow works end-to-end, from creating a new project through the UI to verifying the file structure and Git initialization on disk, ensuring all components integrate correctly.

## Acceptance Criteria

### Functional Requirements
- [ ] User can create project through UI
- [ ] Project directory structure is created correctly
- [ ] Project.json contains all required fields
- [ ] Git repository initializes with proper .gitignore
- [ ] Project appears in gallery after creation
- [ ] WebSocket broadcasts project creation event
- [ ] Files can be uploaded to the new project
- [ ] Project can be deleted and cleaned up

### Integration Points
- [ ] Frontend form submission to API
- [ ] Backend creates directory structure
- [ ] Git service initializes repository
- [ ] WebSocket notifies connected clients
- [ ] File system reflects expected state
- [ ] API returns consistent responses

### Test Scenarios
1. **Happy Path**: Create project with valid name
2. **Validation**: Reject invalid project names
3. **Duplicate**: Handle existing project names
4. **Cleanup**: Delete removes all files
5. **Concurrent**: Multiple users creating projects
6. **Recovery**: Handle partial failures gracefully

## Implementation Notes

### Integration Test Suite
```typescript
// tests/integration/project-flow.test.ts
import { test, expect } from '@playwright/test';
import { api } from '../helpers/api';
import { fileSystem } from '../helpers/filesystem';

test.describe('End-to-End Project Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });
  
  test('complete project creation flow', async ({ page }) => {
    const projectName = `test-project-${Date.now()}`;
    
    // 1. Create project through UI
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="name"]', projectName);
    await page.selectOption('select[name="quality"]', 'standard');
    await page.click('button[type="submit"]');
    
    // 2. Verify navigation to project page
    await expect(page).toHaveURL(/\/project\/[\w-]+/);
    
    // 3. Verify project in gallery
    await page.goto('/');
    await expect(page.locator(`text=${projectName}`)).toBeVisible();
    
    // 4. Verify API response
    const projects = await api.get('/projects');
    const project = projects.find(p => p.name === projectName);
    expect(project).toBeDefined();
    expect(project.quality).toBe('standard');
    
    // 5. Verify file structure
    const projectPath = `workspace/${projectName}`;
    expect(await fileSystem.exists(`${projectPath}/project.json`)).toBe(true);
    expect(await fileSystem.exists(`${projectPath}/.git`)).toBe(true);
    expect(await fileSystem.exists(`${projectPath}/assets/scripts`)).toBe(true);
    
    // 6. Verify project.json contents
    const manifest = await fileSystem.readJson(`${projectPath}/project.json`);
    expect(manifest.name).toBe(projectName);
    expect(manifest.quality).toBe('standard');
    expect(manifest.version).toBe('1.0.0');
    
    // 7. Verify Git initialization
    const gitStatus = await api.get(`/projects/${project.id}/git/status`);
    expect(gitStatus.current_commit).toBeDefined();
    expect(gitStatus.is_dirty).toBe(false);
    
    // 8. Test file upload
    await page.goto(`/project/${project.id}`);
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/test-script.txt');
    
    // 9. Verify file upload
    await page.waitForSelector('.upload-item[data-status="completed"]');
    const files = await api.get(`/projects/${project.id}/assets`);
    expect(files.length).toBeGreaterThan(0);
    
    // 10. Clean up - delete project
    await api.delete(`/projects/${project.id}`);
    expect(await fileSystem.exists(projectPath)).toBe(false);
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
  
  test('WebSocket updates on project creation', async ({ page, context }) => {
    // Open second tab
    const page2 = await context.newPage();
    await page2.goto('/');
    
    // Create project in first tab
    await page.goto('/');
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="name"]', 'websocket-test');
    await page.click('button[type="submit"]');
    
    // Verify project appears in second tab
    await expect(page2.locator('text=websocket-test')).toBeVisible({
      timeout: 5000
    });
  });
});
```

### Backend Integration Tests
```python
# tests/integration/test_project_flow.py
import pytest
import asyncio
from pathlib import Path
from app.main import app
from app.services.workspace import WorkspaceService

@pytest.mark.asyncio
async def test_complete_project_flow(client, tmp_workspace):
    """Test complete project creation and management flow"""
    
    # 1. Create project
    response = await client.post("/api/v1/projects", json={
        "name": "integration-test",
        "quality": "standard"
    })
    assert response.status_code == 201
    project = response.json()
    
    # 2. Verify project structure
    project_path = tmp_workspace / "integration-test"
    assert project_path.exists()
    assert (project_path / "project.json").exists()
    assert (project_path / ".git").exists()
    assert (project_path / "assets" / "scripts").exists()
    
    # 3. Verify Git initialization
    response = await client.get(f"/api/v1/projects/{project['id']}/git/status")
    assert response.status_code == 200
    git_status = response.json()
    assert not git_status["is_dirty"]
    assert git_status["current_commit"]
    
    # 4. Upload file
    with open("tests/fixtures/test.txt", "rb") as f:
        response = await client.post(
            f"/api/v1/projects/{project['id']}/assets?asset_type=scripts",
            files={"files": ("test.txt", f, "text/plain")}
        )
    assert response.status_code == 200
    
    # 5. Verify file exists
    assert (project_path / "assets" / "scripts" / "test.txt").exists()
    
    # 6. Delete project
    response = await client.delete(f"/api/v1/projects/{project['id']}")
    assert response.status_code == 204
    assert not project_path.exists()

@pytest.mark.asyncio
async def test_concurrent_project_creation(client):
    """Test multiple projects can be created concurrently"""
    
    async def create_project(name: str):
        return await client.post("/api/v1/projects", json={
            "name": name,
            "quality": "draft"
        })
    
    # Create 5 projects concurrently
    tasks = [create_project(f"concurrent-{i}") for i in range(5)]
    responses = await asyncio.gather(*tasks)
    
    # Verify all succeeded
    for response in responses:
        assert response.status_code == 201
    
    # Verify all projects exist
    response = await client.get("/api/v1/projects")
    projects = response.json()
    created_names = {p["name"] for p in projects if p["name"].startswith("concurrent-")}
    assert len(created_names) == 5
```

### Manual Test Checklist
```markdown
## Manual Testing Checklist

### Project Creation
- [ ] Create project with short name (< 10 chars)
- [ ] Create project with long name (> 50 chars)
- [ ] Create project with special characters (spaces, dashes)
- [ ] Try to create duplicate project name
- [ ] Create projects with each quality tier

### File Operations
- [ ] Upload single small file (< 1MB)
- [ ] Upload single large file (> 50MB)
- [ ] Upload multiple files at once
- [ ] Upload unsupported file type
- [ ] Cancel upload in progress

### Project Management
- [ ] View project in gallery
- [ ] Search for project by name
- [ ] Sort projects by date/name/size
- [ ] Delete project and verify cleanup
- [ ] Create project, close browser, return

### Cross-Browser Testing
- [ ] Chrome/Chromium
- [ ] Firefox
- [ ] Safari
- [ ] Edge

### Performance Testing
- [ ] Create 50+ projects
- [ ] Upload 100+ files to project
- [ ] Multiple tabs with same project
- [ ] Slow network conditions
```

### Monitoring Setup
```typescript
// src/lib/monitoring/flow.ts
export function trackProjectFlow() {
  // Track key metrics
  performance.mark('project_create_start');
  
  // After creation
  performance.mark('project_create_end');
  performance.measure('project_creation_time', 
    'project_create_start', 
    'project_create_end'
  );
  
  // Log to analytics
  analytics.track('project_created', {
    duration: performance.getEntriesByName('project_creation_time')[0].duration,
    quality: projectData.quality,
    timestamp: new Date().toISOString()
  });
}
```

## Dependencies
- All previous stories completed
- Test fixtures and helpers
- Integration test framework

## Testing Criteria
- [ ] Full flow works without manual intervention
- [ ] All integration points verified
- [ ] Error scenarios handled gracefully
- [ ] Performance within acceptable limits
- [ ] No orphaned files or processes
- [ ] Concurrent operations don't conflict

## Definition of Done
- [ ] Integration tests pass consistently
- [ ] Manual test checklist completed
- [ ] Performance benchmarks established
- [ ] Error recovery verified
- [ ] Documentation includes troubleshooting
- [ ] Monitoring alerts configured

## Story Links
- **Depends On**: All other stories in epic
- **Validates**: Complete web platform foundation
- **Related PRD**: PRD-001-web-platform-foundation