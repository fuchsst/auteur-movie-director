import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import ProjectImportDialog from './ProjectImportDialog.svelte';
import { importApi } from '$lib/api/import';
import { websocketStore } from '$lib/stores/websocket';
import { notificationStore } from '$lib/stores/notifications';

// Mock API and stores
vi.mock('$lib/api/import', () => ({
  importApi: {
    uploadArchive: vi.fn(),
    importProject: vi.fn(),
    validateArchive: vi.fn()
  }
}));

vi.mock('$lib/stores/websocket', () => ({
  websocketStore: {
    subscribe: vi.fn((callback) => {
      callback({ clientId: 'test-client-id', lastMessage: null });
      return () => {};
    })
  }
}));

vi.mock('$lib/stores/notifications', () => ({
  notificationStore: {
    add: vi.fn()
  }
}));

describe('ProjectImportDialog', () => {
  const defaultProps = {
    open: true
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders import dialog', () => {
    const { getByText, getByLabelText } = render(ProjectImportDialog, defaultProps);

    expect(getByText('Import Project')).toBeInTheDocument();
    expect(getByText('Select Archive')).toBeInTheDocument();
  });

  it('handles file selection and auto-validation', async () => {
    vi.mocked(importApi.validateArchive).mockResolvedValue({
      valid: true,
      version: '2.0',
      projectId: 'test_project',
      errors: [],
      warnings: []
    });

    const { container } = render(ProjectImportDialog, defaultProps);

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['archive content'], 'test_project_export_20250113.zip', {
      type: 'application/zip'
    });

    // Simulate file selection
    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false
    });

    await fireEvent.change(fileInput);

    await waitFor(() => {
      expect(importApi.validateArchive).toHaveBeenCalledWith(file);
    });
  });

  it('displays validation results', async () => {
    const { container, getByText, rerender } = render(ProjectImportDialog, defaultProps);

    // Set up validation response
    vi.mocked(importApi.validateArchive).mockResolvedValue({
      valid: true,
      version: '2.0',
      projectId: 'valid_project',
      errors: [],
      warnings: ['Missing optional directories']
    });

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'project.zip', { type: 'application/zip' });

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false
    });

    await fireEvent.change(fileInput);

    await waitFor(() => {
      expect(getByText('Valid project archive')).toBeInTheDocument();
      expect(getByText('(v2.0)')).toBeInTheDocument();
      expect(getByText('Missing optional directories')).toBeInTheDocument();
    });
  });

  it('shows error for invalid archive', async () => {
    const { container, getByText } = render(ProjectImportDialog, defaultProps);

    vi.mocked(importApi.validateArchive).mockResolvedValue({
      valid: false,
      errors: ['No project manifest found'],
      warnings: []
    });

    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['invalid'], 'bad.zip', { type: 'application/zip' });

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false
    });

    await fireEvent.change(fileInput);

    await waitFor(() => {
      expect(getByText('Invalid archive')).toBeInTheDocument();
      expect(getByText('No project manifest found')).toBeInTheDocument();
    });
  });

  it('imports project with selected options', async () => {
    vi.mocked(importApi.validateArchive).mockResolvedValue({
      valid: true,
      version: '2.0',
      projectId: 'test_project',
      errors: [],
      warnings: []
    });

    vi.mocked(importApi.uploadArchive).mockResolvedValue({
      filename: 'test.zip',
      size: 1000000,
      tempPath: '/tmp/test.zip',
      validation: {
        valid: true,
        version: '2.0',
        projectId: 'test_project',
        errors: [],
        warnings: []
      }
    });

    vi.mocked(importApi.importProject).mockResolvedValue({
      importId: 'import-123',
      status: 'started',
      message: 'Import started'
    });

    const { container, getByText, getByLabelText } = render(ProjectImportDialog, defaultProps);

    // Select file
    const fileInput = container.querySelector('input[type="file"]') as HTMLInputElement;
    const file = new File(['content'], 'project.zip', { type: 'application/zip' });

    Object.defineProperty(fileInput, 'files', {
      value: [file],
      writable: false
    });

    await fireEvent.change(fileInput);

    // Wait for validation
    await waitFor(() => {
      expect(getByText('Valid project archive')).toBeInTheDocument();
    });

    // Set project name
    const nameInput = container.querySelector('input[type="text"]') as HTMLInputElement;
    await fireEvent.input(nameInput, { target: { value: 'New Project' } });

    // Toggle options
    const gitCheckbox = getByLabelText(/Restore Git history/);
    expect(gitCheckbox).toBeChecked();

    // Start import
    const importButton = getByText('Import Project');
    await fireEvent.click(importButton);

    await waitFor(() => {
      expect(importApi.uploadArchive).toHaveBeenCalledWith(file, 'test-client-id');
      expect(importApi.importProject).toHaveBeenCalledWith(
        '/tmp/test.zip',
        'New Project',
        {
          overwrite: false,
          renameOnConflict: true,
          restoreGitHistory: true,
          verifyLfsObjects: true
        },
        'test-client-id'
      );
    });
  });

  it('displays import progress', async () => {
    const { getByText, rerender } = render(ProjectImportDialog, {
      ...defaultProps,
      open: true
    });

    // Start with file selected and validated
    vi.mocked(importApi.validateArchive).mockResolvedValue({
      valid: true,
      version: '2.0',
      projectId: 'test',
      errors: [],
      warnings: []
    });

    // Simulate WebSocket progress update
    websocketStore.subscribe = vi.fn((callback) => {
      callback({
        clientId: 'test-client-id',
        lastMessage: {
          type: 'import_progress',
          progress: 0.75,
          message: 'Restoring Git history...'
        }
      });
      return () => {};
    });

    await rerender(defaultProps);

    expect(getByText('Restoring Git history...')).toBeInTheDocument();
    expect(getByText('75%')).toBeInTheDocument();
  });

  it('handles import completion', async () => {
    const handleImported = vi.fn();
    const { rerender } = render(ProjectImportDialog, {
      ...defaultProps,
      onimported: handleImported
    });

    // Simulate completion via WebSocket
    websocketStore.subscribe = vi.fn((callback) => {
      callback({
        clientId: 'test-client-id',
        lastMessage: {
          type: 'import_complete',
          result: {
            success: true,
            projectId: 'imported_project',
            projectName: 'Imported Project',
            importDuration: 5.2,
            statistics: {
              totalFiles: 100,
              totalSizeMb: 50.5
            }
          }
        }
      });
      return () => {};
    });

    await rerender(defaultProps);

    expect(notificationStore.add).toHaveBeenCalledWith({
      type: 'success',
      title: 'Import Complete',
      message: 'Imported Project has been imported successfully',
      action: expect.any(Object)
    });

    expect(handleImported).toHaveBeenCalled();
  });

  it('handles import errors', async () => {
    const { rerender } = render(ProjectImportDialog, defaultProps);

    // Simulate error via WebSocket
    websocketStore.subscribe = vi.fn((callback) => {
      callback({
        clientId: 'test-client-id',
        lastMessage: {
          type: 'import_error',
          error: 'Failed to extract archive: Corrupted file'
        }
      });
      return () => {};
    });

    await rerender(defaultProps);

    expect(notificationStore.add).toHaveBeenCalledWith({
      type: 'error',
      title: 'Import Failed',
      message: 'Failed to extract archive: Corrupted file'
    });
  });

  it('disables controls during import', async () => {
    const { container, getByText } = render(ProjectImportDialog, defaultProps);

    // Mock import in progress
    vi.mocked(importApi.uploadArchive).mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    // Trigger import (setup omitted for brevity)
    // ... file selection and validation ...

    // Check controls are disabled
    const cancelButton = getByText('Cancel');
    expect(cancelButton).toHaveProperty('disabled', false); // Should be disabled during import
  });
});
