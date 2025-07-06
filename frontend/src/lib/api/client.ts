/**
 * API client for backend communication
 */

import type { WorkspaceProject, ProjectManifest, GitStatus } from '$lib/types/project';

export class ApiClient {
  private baseUrl: string;

  constructor(baseUrl?: string) {
    this.baseUrl = baseUrl || import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  /**
   * Helper method for API requests
   */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}/api/v1${endpoint}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.statusText} - ${error}`);
    }

    return response.json();
  }

  /**
   * Workspace API
   */
  async listProjects(): Promise<WorkspaceProject[]> {
    return this.request<WorkspaceProject[]>('/workspace/projects');
  }

  async createProject(data: {
    name: string;
    narrative_structure: string;
    quality?: string;
    director?: string;
    description?: string;
  }): Promise<{ project_path: string; manifest: ProjectManifest }> {
    return this.request('/workspace/projects', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async getProject(projectId: string): Promise<ProjectManifest> {
    return this.request<ProjectManifest>(`/workspace/projects/${projectId}`);
  }

  async validateProject(projectId: string): Promise<{
    valid: boolean;
    errors: string[];
    warnings: string[];
    missing_directories: string[];
    git_initialized: boolean;
    git_lfs_enabled: boolean;
    project_json_valid: boolean;
  }> {
    return this.request(`/workspace/projects/${projectId}/validate`);
  }

  async updateProject(projectId: string, data: Partial<ProjectManifest>): Promise<ProjectManifest> {
    return this.request<ProjectManifest>(`/workspace/projects/${projectId}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  /**
   * Git API
   */
  async getGitStatus(projectId: string): Promise<GitStatus> {
    return this.request<GitStatus>(`/git/${projectId}/status`);
  }

  async commitChanges(
    projectId: string,
    data: {
      message: string;
      prefix?: string;
      files?: string[];
    }
  ): Promise<{ success: boolean; message: string }> {
    return this.request(`/git/${projectId}/commit`, {
      method: 'POST',
      body: JSON.stringify({ project_id: projectId, ...data })
    });
  }

  async getGitHistory(
    projectId: string,
    limit = 20
  ): Promise<
    Array<{
      hash: string;
      message: string;
      author: string;
      email: string;
      date: string;
      files_changed: number;
    }>
  > {
    return this.request(`/git/${projectId}/history?limit=${limit}`);
  }

  /**
   * Health check
   */
  async checkHealth(): Promise<{ status: string; version: string }> {
    return this.request<{ status: string; version: string }>('/health');
  }
}

// Create default client instance
export const api = new ApiClient();
