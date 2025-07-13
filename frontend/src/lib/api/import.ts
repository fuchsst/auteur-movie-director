/**
 * Project import API client
 */

import { apiClient } from './client';

export interface ImportOptions {
  overwrite: boolean;
  renameOnConflict: boolean;
  restoreGitHistory: boolean;
  verifyLfsObjects: boolean;
}

export interface ValidationResult {
  valid: boolean;
  version?: string;
  projectId?: string;
  errors: string[];
  warnings: string[];
}

export interface ImportResult {
  success: boolean;
  projectId: string;
  projectName: string;
  importDuration: number;
  statistics: Record<string, any>;
  errors: string[];
  warnings: string[];
}

export interface UploadResult {
  filename: string;
  size: number;
  tempPath: string;
  validation: ValidationResult;
}

export interface ImportProgress {
  type: 'import_progress' | 'import_complete' | 'import_error';
  progress?: number;
  message?: string;
  result?: ImportResult;
  error?: string;
  importId?: string;
}

export const importApi = {
  /**
   * Upload a project archive
   */
  async uploadArchive(file: File, clientId?: string): Promise<UploadResult> {
    const formData = new FormData();
    formData.append('file', file);

    const params = new URLSearchParams();
    if (clientId) {
      params.append('client_id', clientId);
    }

    const response = await apiClient('/api/v1/import/upload', {
      method: 'POST',
      body: formData,
      params
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  },

  /**
   * Import a project from uploaded archive
   */
  async importProject(
    tempPath: string,
    targetName: string,
    options: ImportOptions = {
      overwrite: false,
      renameOnConflict: true,
      restoreGitHistory: true,
      verifyLfsObjects: true
    },
    clientId?: string
  ): Promise<{ importId: string; status: string; message: string }> {
    const formData = new FormData();
    formData.append('temp_path', tempPath);
    formData.append('target_name', targetName);
    formData.append('options', JSON.stringify(options));

    const params = new URLSearchParams();
    if (clientId) {
      params.append('client_id', clientId);
    }

    const response = await apiClient('/api/v1/import/', {
      method: 'POST',
      body: formData,
      params
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Import failed');
    }

    return response.json();
  },

  /**
   * Validate an archive without importing
   */
  async validateArchive(file: File): Promise<ValidationResult> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient('/api/v1/import/validate', {
      method: 'POST',
      body: formData
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Validation failed');
    }

    return response.json();
  },

  /**
   * Clean up old temporary files
   */
  async cleanupTempFiles(
    days: number = 1
  ): Promise<{ status: string; deletedFiles: number; message: string }> {
    const response = await apiClient(`/api/v1/import/cleanup?days=${days}`, {
      method: 'DELETE'
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Cleanup failed');
    }

    return response.json();
  }
};
