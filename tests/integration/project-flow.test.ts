/**
 * End-to-End Project Flow Integration Tests
 * Tests complete project creation and management across frontend and backend
 */

import { test, expect } from '@playwright/test';
import { api } from '../helpers/api';
import { generateProjectName } from '../helpers/utils';

test.describe('End-to-End Project Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('http://localhost:3000');
  });

  test('complete project creation flow', async ({ page }) => {
    const projectName = generateProjectName();

    // 1. Click new project button
    await page.click('button:has-text("New Project")');

    // 2. Fill project form
    await page.fill('input[name="projectName"]', projectName);
    await page.selectOption('select[name="quality"]', 'standard');
    await page.selectOption('select[name="narrativeStructure"]', 'three-act');
    
    // 3. Submit form
    await page.click('button[type="submit"]');

    // 4. Verify navigation to project page
    await expect(page).toHaveURL(/\/project\/[\w-]+/);
    
    // 5. Verify project appears in sidebar
    await expect(page.locator(`text=${projectName}`)).toBeVisible();

    // 6. Verify project structure in UI
    await expect(page.locator('[data-testid="project-tree"]')).toBeVisible();
    await expect(page.locator('text=01_Assets')).toBeVisible();
    await expect(page.locator('text=02_Source_Creative')).toBeVisible();
    await expect(page.locator('text=03_Renders')).toBeVisible();

    // 7. Verify API response
    const projects = await api.get('/projects');
    const project = projects.find(p => p.name === projectName);
    expect(project).toBeDefined();
    expect(project.quality).toBe('standard');
    expect(project.narrative.structure).toBe('three-act');

    // 8. Test file upload
    await page.click('text=Assets');
    await page.click('button:has-text("Upload Files")');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/test-image.png');
    
    // Wait for upload to complete
    await page.waitForSelector('[data-testid="upload-complete"]', { timeout: 10000 });
    
    // Verify file appears in asset browser
    await expect(page.locator('text=test-image.png')).toBeVisible();

    // 9. Clean up - delete project
    await page.click('[data-testid="project-menu"]');
    await page.click('text=Delete Project');
    await page.click('button:has-text("Confirm Delete")');

    // Verify redirect to home
    await expect(page).toHaveURL('http://localhost:3000');
  });

  test('handles invalid project names', async ({ page }) => {
    await page.click('button:has-text("New Project")');

    // Test empty name
    await page.fill('input[name="projectName"]', '');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error-message')).toContainText('required');

    // Test invalid characters
    await page.fill('input[name="projectName"]', 'test/project');
    await page.click('button[type="submit"]');
    await expect(page.locator('.error-message')).toContainText('Invalid');
  });

  test('WebSocket updates across tabs', async ({ page, context }) => {
    // Open second tab
    const page2 = await context.newPage();
    await page2.goto('http://localhost:3000');

    // Create project in first tab
    const projectName = generateProjectName();
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="projectName"]', projectName);
    await page.click('button[type="submit"]');

    // Verify project appears in second tab
    await expect(page2.locator(`text=${projectName}`)).toBeVisible({ timeout: 5000 });
  });

  test('character asset lifecycle', async ({ page }) => {
    // Create project
    const projectName = generateProjectName();
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="projectName"]', projectName);
    await page.click('button[type="submit"]');

    // Navigate to assets
    await page.click('text=Assets');
    await page.click('[data-testid="tab-characters"]');

    // Create new character
    await page.click('button:has-text("New Character")');
    await page.fill('input[name="characterName"]', 'John Doe');
    await page.fill('textarea[name="description"]', 'Main protagonist');
    await page.fill('input[name="triggerWord"]', 'johndoe_v1');
    await page.click('button[type="submit"]');

    // Verify character created
    await expect(page.locator('text=John Doe')).toBeVisible();

    // Upload base face
    await page.click('[data-testid="character-card-John Doe"]');
    const baseFaceInput = page.locator('input[data-testid="base-face-upload"]');
    await baseFaceInput.setInputFiles('./tests/fixtures/john-base-face.png');

    // Wait for upload
    await page.waitForSelector('[data-testid="base-face-uploaded"]');

    // Verify character sheet displays correctly
    await expect(page.locator('[data-testid="character-sheet"]')).toBeVisible();
    await expect(page.locator('img[data-testid="base-face-preview"]')).toBeVisible();
    await expect(page.locator('text=johndoe_v1')).toBeVisible();
  });

  test('task execution with WebSocket updates', async ({ page }) => {
    // Create project
    const projectName = generateProjectName();
    const response = await api.post('/projects', {
      name: projectName,
      quality: 'high'
    });
    const project = response.data;

    // Navigate to project
    await page.goto(`http://localhost:3000/project/${project.id}`);

    // Switch to canvas view (placeholder for now)
    await page.click('[data-testid="tab-canvas"]');

    // Simulate task submission
    const taskPayload = {
      type: 'text_to_image',
      prompt: 'A beautiful landscape',
      node_id: 'test-node-001'
    };

    // Listen for WebSocket messages
    const wsMessages = [];
    page.on('websocket', ws => {
      ws.on('framereceived', event => {
        const data = JSON.parse(event.payload);
        wsMessages.push(data);
      });
    });

    // Submit task via API
    const taskResponse = await api.post(`/projects/${project.id}/tasks`, taskPayload);
    const task = taskResponse.data;

    // Wait for task progress updates
    await page.waitForTimeout(2000);

    // Verify WebSocket messages received
    const progressMessages = wsMessages.filter(m => m.type === 'task.progress');
    expect(progressMessages.length).toBeGreaterThan(0);

    // Verify UI updates (when canvas is implemented)
    // await expect(page.locator(`[data-node-id="${taskPayload.node_id}"]`))
    //   .toHaveAttribute('data-status', 'running');
  });

  test('takes system versioning', async ({ page }) => {
    // Create project
    const projectName = generateProjectName();
    const response = await api.post('/projects', {
      name: projectName,
      quality: 'standard',
      takes_system_enabled: true
    });
    const project = response.data;

    // Navigate to project
    await page.goto(`http://localhost:3000/project/${project.id}`);

    // Create a take via API (UI not implemented yet)
    const takeResponse = await api.post(`/projects/${project.id}/shots/S01_S01/takes`, {
      shot_id: 'S01_S01',
      description: 'First take'
    });
    const take = takeResponse.data;

    expect(take.take_number).toBe(1);
    expect(take.take_path).toContain('take_001');

    // Create second take
    const take2Response = await api.post(`/projects/${project.id}/shots/S01_S01/takes`, {
      shot_id: 'S01_S01',
      description: 'Second take'
    });
    const take2 = take2Response.data;

    expect(take2.take_number).toBe(2);
    expect(take2.take_path).toContain('take_002');
  });

  test('quality mapping affects execution parameters', async ({ page }) => {
    const qualities = ['low', 'standard', 'high'];
    const expectedParams = {
      low: { steps: 20, cfg_scale: 7.0 },
      standard: { steps: 30, cfg_scale: 7.5 },
      high: { steps: 50, cfg_scale: 7.5 }
    };

    for (const quality of qualities) {
      // Create project with specific quality
      const projectName = `${generateProjectName()}-${quality}`;
      const response = await api.post('/projects', {
        name: projectName,
        quality: quality
      });
      const project = response.data;

      // Submit task
      const taskResponse = await api.post(`/projects/${project.id}/tasks`, {
        type: 'text_to_image',
        prompt: 'Test prompt',
        node_id: `node-${quality}`
      });
      const task = taskResponse.data;

      // Verify parameters
      expect(task.parameters.steps).toBe(expectedParams[quality].steps);
      expect(task.parameters.cfg_scale).toBe(expectedParams[quality].cfg_scale);
    }
  });

  test('project structure enforcement', async ({ page }) => {
    const projectName = generateProjectName();
    
    // Create project
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="projectName"]', projectName);
    await page.click('button[type="submit"]');

    // Verify directory structure in UI
    const expectedDirs = [
      '01_Assets',
      'Characters',
      'Locations',
      'Styles', 
      'Music',
      '02_Source_Creative',
      'Treatments',
      'Scripts',
      'ShotLists',
      'Canvas',
      '03_Renders'
    ];

    for (const dir of expectedDirs) {
      await expect(page.locator(`text=${dir}`).first()).toBeVisible({ timeout: 10000 });
    }

    // Verify via API
    const projects = await api.get('/projects');
    const project = projects.find(p => p.name === projectName);
    const structure = await api.get(`/projects/${project.id}/structure`);
    
    expect(structure.enforced_structure).toContain('01_Assets/Characters');
    expect(structure.enforced_structure).toContain('02_Source_Creative/Scripts');
    expect(structure.enforced_structure).toContain('03_Renders');
  });

  test('file upload to correct categories', async ({ page }) => {
    // Create project
    const projectName = generateProjectName();
    await page.click('button:has-text("New Project")');
    await page.fill('input[name="projectName"]', projectName);
    await page.click('button[type="submit"]');

    // Test character upload
    await page.click('text=Assets');
    await page.click('[data-testid="tab-characters"]');
    await page.click('button:has-text("Upload Files")');
    
    const charInput = page.locator('input[type="file"]');
    await charInput.setInputFiles('./tests/fixtures/character.png');
    await page.waitForSelector('[data-testid="upload-complete"]');
    
    // Verify in characters section
    await expect(page.locator('[data-testid="character-assets"] text=character.png')).toBeVisible();

    // Test style upload
    await page.click('[data-testid="tab-styles"]');
    await page.click('button:has-text("Upload Files")');
    
    const styleInput = page.locator('input[type="file"]');
    await styleInput.setInputFiles('./tests/fixtures/style.safetensors');
    await page.waitForSelector('[data-testid="upload-complete"]');
    
    // Verify in styles section
    await expect(page.locator('[data-testid="style-assets"] text=style.safetensors')).toBeVisible();
  });

  test('git integration with LFS', async ({ page }) => {
    const projectName = generateProjectName();
    
    // Create project
    const response = await api.post('/projects', {
      name: projectName,
      quality: 'standard'
    });
    const project = response.data;

    // Check git status
    const gitStatus = await api.get(`/projects/${project.id}/git/status`);
    expect(gitStatus.initialized).toBe(true);
    expect(gitStatus.lfs_enabled).toBe(true);
    expect(gitStatus.is_dirty).toBe(false);

    // Upload large file to trigger LFS
    await page.goto(`http://localhost:3000/project/${project.id}`);
    await page.click('text=Assets');
    await page.click('button:has-text("Upload Files")');
    
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles('./tests/fixtures/large-video.mp4');
    await page.waitForSelector('[data-testid="upload-complete"]', { timeout: 30000 });

    // Verify LFS handled the file
    const updatedStatus = await api.get(`/projects/${project.id}/git/status`);
    expect(updatedStatus.lfs_files).toContain('large-video.mp4');
  });
});