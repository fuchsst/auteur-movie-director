import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, fireEvent, waitFor } from '@testing-library/svelte';
import ProjectExportDialog from './ProjectExportDialog.svelte';
import { exportApi } from '$lib/api/export';
import { websocketStore } from '$lib/stores/websocket';
import { notificationStore } from '$lib/stores/notifications';

// Mock API and stores
vi.mock('$lib/api/export', () => ({
  exportApi: {
    exportProject: vi.fn(),
    getDownloadUrl: vi.fn()
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

describe('ProjectExportDialog', () => {
  const defaultProps = {
    open: true,
    projectId: 'test-project',
    projectName: 'Test Project'
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders export dialog with options', () => {
    const { getByText, getByLabelText } = render(ProjectExportDialog, defaultProps);

    expect(getByText('Export Project')).toBeInTheDocument();
    expect(getByText('Test Project')).toBeInTheDocument();
    expect(getByLabelText('ZIP')).toBeInTheDocument();
    expect(getByLabelText('TAR.GZ')).toBeInTheDocument();
  });

  it('starts export with selected options', async () => {
    vi.mocked(exportApi.exportProject).mockResolvedValue({
      exportId: 'export-123',
      projectId: 'test-project',
      status: 'started',
      message: 'Export started'
    });

    const { getByText, getByLabelText } = render(ProjectExportDialog, defaultProps);

    // Select options
    const tarOption = getByLabelText('TAR.GZ');
    await fireEvent.click(tarOption);

    const historyCheckbox = getByLabelText(/Include Git History/);
    expect(historyCheckbox).toBeChecked();

    // Start export
    const exportButton = getByText('Start Export');
    await fireEvent.click(exportButton);

    await waitFor(() => {
      expect(exportApi.exportProject).toHaveBeenCalledWith(
        'test-project',
        {
          format: 'tar.gz',
          includeHistory: true,
          includeCache: false,
          compressMedia: false,
          splitSizeMb: undefined
        },
        'test-client-id'
      );
    });
  });

  it('displays progress updates', async () => {
    const { getByText, rerender } = render(ProjectExportDialog, defaultProps);

    // Start export
    await fireEvent.click(getByText('Start Export'));

    // Simulate progress update via WebSocket
    websocketStore.subscribe = vi.fn((callback) => {
      callback({
        clientId: 'test-client-id',
        lastMessage: {
          type: 'export_progress',
          projectId: 'test-project',
          progress: 0.5,
          message: 'Creating archive...'
        }
      });
      return () => {};
    });

    await rerender(defaultProps);

    expect(getByText('Creating archive...')).toBeInTheDocument();
    expect(getByText('50%')).toBeInTheDocument();
  });

  it('shows download button on completion', async () => {
    vi.mocked(exportApi.getDownloadUrl).mockReturnValue('http://localhost/download/export.zip');

    const { getByText, rerender } = render(ProjectExportDialog, defaultProps);

    // Start export
    await fireEvent.click(getByText('Start Export'));

    // Simulate completion via WebSocket
    websocketStore.subscribe = vi.fn((callback) => {
      callback({
        clientId: 'test-client-id',
        lastMessage: {
          type: 'export_complete',
          projectId: 'test-project',
          filename: 'test-project_export_20250113.zip'
        }
      });
      return () => {};
    });

    await rerender(defaultProps);

    expect(getByText('Export Complete!')).toBeInTheDocument();
    expect(getByText('Download Archive')).toBeInTheDocument();

    expect(notificationStore.add).toHaveBeenCalledWith({
      type: 'success',
      title: 'Export Complete',
      message: 'Test Project has been exported successfully',
      action: expect.any(Object)
    });
  });

  it('handles export errors', async () => {
    const { getByText, rerender } = render(ProjectExportDialog, defaultProps);

    // Start export
    await fireEvent.click(getByText('Start Export'));

    // Simulate error via WebSocket
    websocketStore.subscribe = vi.fn((callback) => {
      callback({
        clientId: 'test-client-id',
        lastMessage: {
          type: 'export_error',
          projectId: 'test-project',
          error: 'Export failed: Insufficient space'
        }
      });
      return () => {};
    });

    await rerender(defaultProps);

    expect(notificationStore.add).toHaveBeenCalledWith({
      type: 'error',
      title: 'Export Failed',
      message: 'Export failed: Insufficient space'
    });
  });

  it('closes dialog when not exporting', async () => {
    const handleClose = vi.fn();
    const { getByText } = render(ProjectExportDialog, {
      ...defaultProps,
      onclose: handleClose
    });

    const cancelButton = getByText('Cancel');
    await fireEvent.click(cancelButton);

    expect(handleClose).toHaveBeenCalled();
  });
});
