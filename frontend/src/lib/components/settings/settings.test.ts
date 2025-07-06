import { describe, it, expect, vi } from 'vitest';
import { render, fireEvent } from '@testing-library/svelte';
import { get } from 'svelte/store';
import ProjectSettings from './ProjectSettings.svelte';
import WorkspaceSettings from './WorkspaceSettings.svelte';
import SystemInfo from './SystemInfo.svelte';
import { currentProject } from '$lib/stores';

// Mock API calls
vi.mock('$lib/api/workspace', () => ({
  workspaceApi: {
    getConfig: vi.fn().mockResolvedValue({
      root_path: '/workspace',
      projects_count: 5,
      available_space_gb: 100.5,
      enforced_structure: ['01_Assets', '02_Source_Creative'],
      narrative_structures: ['three-act', 'hero-journey']
    }),
    updateProjectSettings: vi.fn().mockResolvedValue(undefined)
  }
}));

vi.mock('$lib/api/system', () => ({
  systemApi: {
    getSystemInfo: vi.fn().mockResolvedValue({
      version: '0.1.0',
      pythonVersion: '3.12.0',
      nodeVersion: '20.0.0',
      platform: 'Linux 5.10',
      gitVersion: '2.34.0',
      gitLFSInstalled: true,
      dockerVersion: '20.10.0',
      workspacePath: '/workspace',
      apiEndpoint: 'http://localhost:8000',
      gpuSupport: true
    })
  }
}));

describe('ProjectSettings', () => {
  it('should render project settings when project is selected', () => {
    // Set a mock project
    currentProject.set({
      id: 'test-project',
      name: 'Test Project',
      settings: {
        fps: 24,
        resolution: [1920, 1080],
        aspectRatio: '16:9',
        defaultQuality: 'standard',
        outputFormat: 'mp4'
      }
    } as any);

    const { getByText, getByLabelText } = render(ProjectSettings);

    expect(getByText('Project Settings')).toBeInTheDocument();
    expect(getByLabelText('Frame Rate (FPS)')).toBeInTheDocument();
    expect(getByText('Resolution')).toBeInTheDocument();
    expect(getByText('Quality Tier')).toBeInTheDocument();
  });

  it('should show no project message when no project selected', () => {
    currentProject.set(null);

    const { getByText } = render(ProjectSettings);
    expect(getByText('No project selected')).toBeInTheDocument();
  });

  it('should enable save button when changes are made', async () => {
    currentProject.set({
      id: 'test-project',
      name: 'Test Project',
      settings: {
        fps: 24,
        resolution: [1920, 1080],
        aspectRatio: '16:9',
        defaultQuality: 'standard',
        outputFormat: 'mp4'
      }
    } as any);

    const { getByLabelText, queryByText } = render(ProjectSettings);

    // Initially no save button
    expect(queryByText('Save Changes')).not.toBeInTheDocument();

    // Change FPS
    const fpsInput = getByLabelText('Frame Rate (FPS)');
    await fireEvent.change(fpsInput, { target: { value: '30' } });

    // Save button should appear
    expect(queryByText('Save Changes')).toBeInTheDocument();
  });
});

describe('WorkspaceSettings', () => {
  it('should load and display workspace configuration', async () => {
    const { findByText } = render(WorkspaceSettings);

    expect(await findByText('Workspace Information')).toBeInTheDocument();
    expect(await findByText('/workspace')).toBeInTheDocument();
    expect(await findByText('5')).toBeInTheDocument(); // projects count
    expect(await findByText('100.50 GB')).toBeInTheDocument(); // available space
  });

  it('should show preferences section', async () => {
    const { findByLabelText } = render(WorkspaceSettings);

    expect(await findByLabelText('Default Quality for New Projects')).toBeInTheDocument();
    expect(await findByLabelText('Auto-save Interval (minutes)')).toBeInTheDocument();
  });
});

describe('SystemInfo', () => {
  it('should display system information', async () => {
    const { findByText } = render(SystemInfo);

    expect(await findByText('System Information')).toBeInTheDocument();
    expect(await findByText('0.1.0')).toBeInTheDocument(); // version
    expect(await findByText('3.12.0')).toBeInTheDocument(); // python version
    expect(await findByText('✓ Installed')).toBeInTheDocument(); // Git LFS
  });

  it('should show system requirements table', async () => {
    const { findByText } = render(SystemInfo);

    expect(await findByText('System Requirements')).toBeInTheDocument();
    expect(await findByText('Git')).toBeInTheDocument();
    expect(await findByText('Docker')).toBeInTheDocument();
    expect(await findByText('GPU')).toBeInTheDocument();
  });

  it('should have working action buttons', async () => {
    const { findByText } = render(SystemInfo);

    const refreshButton = await findByText('Refresh');
    const copyButton = await findByText('Copy to Clipboard');

    expect(refreshButton).toBeInTheDocument();
    expect(copyButton).toBeInTheDocument();
  });
});
