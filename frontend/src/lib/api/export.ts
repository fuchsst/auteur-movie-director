/**
 * Project export API client
 */

import { apiClient } from './client';

export interface ExportOptions {
  format: 'zip' | 'tar.gz';
  includeHistory: boolean;
  includeCache: boolean;
  compressMedia: boolean;
  splitSizeMb?: number;
}

export interface ExportTask {
  exportId: string;
  projectId: string;
  status: string;
  message: string;
}

export interface ExportFile {
  filename: string;
  size: number;
  created: string;
}

export interface ExportProgress {
  type: 'export_progress' | 'export_complete' | 'export_error';
  projectId: string;
  exportId?: string;
  progress?: number;
  message?: string;
  archivePath?: string;
  filename?: string;
  error?: string;
}

class ExportApi {
  /**
   * Start project export
   */
  async exportProject(
    projectId: string,
    options: ExportOptions,
    clientId?: string
  ): Promise<ExportTask> {
    const params = clientId ? `?client_id=${clientId}` : '';
    const response = await apiClient.post(`/export/${projectId}${params}`, {
      format: options.format,
      include_history: options.includeHistory,
      include_cache: options.includeCache,
      compress_media: options.compressMedia,
      split_size_mb: options.splitSizeMb
    });
    return response.data;
  }

  /**
   * Download exported archive
   */
  getDownloadUrl(projectId: string, filename: string): string {
    return `${apiClient.defaults.baseURL}/export/${projectId}/download/${filename}`;
  }

  /**
   * List available exports
   */
  async listExports(): Promise<{ exports: ExportFile[]; count: number }> {
    const response = await apiClient.get('/export/list');
    return response.data;
  }

  /**
   * Clean up old exports
   */
  async cleanupExports(days: number = 7): Promise<{ status: string; message: string }> {
    const response = await apiClient.delete(`/export/cleanup?days=${days}`);
    return response.data;
  }
}

export const exportApi = new ExportApi();
