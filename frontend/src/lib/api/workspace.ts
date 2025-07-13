/**
 * Workspace API client using STORY-027 endpoints
 */

import { api } from './client';
import type { ProjectSettings } from '$lib/types/project';

export interface WorkspaceConfig {
  root_path: string;
  projects_count: number;
  available_space_gb: number;
  enforced_structure: string[];
  narrative_structures: string[];
}

export interface ProjectResponse {
  id: string;
  name: string;
  path: string;
  created: string;
  modified: string;
  size_bytes: number;
  quality: string;
  narrative_structure: string;
  git_status: string | null;
  manifest: any;
}

export interface ProjectListParams {
  skip?: number;
  limit?: number;
  sort_by?: 'name' | 'created' | 'modified';
  order?: 'asc' | 'desc';
  quality?: string;
  structure?: string;
}

export interface ProjectSearchParams {
  q: string;
  skip?: number;
  limit?: number;
}

export interface ProjectCreateRequest {
  name: string;
  narrative_structure: string;
  quality: string;
  director?: string;
  description?: string;
}

export interface ProjectUpdateRequest {
  name?: string;
  quality?: string;
  description?: string;
  tags?: string[];
}

export interface ProjectStructureValidation {
  valid: boolean;
  missing_directories: string[];
  unexpected_directories: string[];
  git_initialized: boolean;
  git_lfs_enabled: boolean;
  project_json_valid: boolean;
  errors: string[];
}

export interface DeleteResponse {
  success: boolean;
  message: string;
  deleted_path: string;
}

export const workspaceApi = {
  /**
   * Get workspace configuration
   */
  async getConfig(): Promise<WorkspaceConfig> {
    return api.get<WorkspaceConfig>('/workspace/config');
  },

  /**
   * List all projects with filtering, sorting, and pagination
   */
  async listProjects(params?: ProjectListParams): Promise<ProjectResponse[]> {
    const searchParams = new URLSearchParams();
    if (params?.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params?.limit !== undefined) searchParams.append('limit', params.limit.toString());
    if (params?.sort_by) searchParams.append('sort_by', params.sort_by);
    if (params?.order) searchParams.append('order', params.order);
    if (params?.quality) searchParams.append('quality', params.quality);
    if (params?.structure) searchParams.append('structure', params.structure);

    const query = searchParams.toString();
    return api.get<ProjectResponse[]>(`/projects${query ? `?${query}` : ''}`);
  },

  /**
   * Search projects by name
   */
  async searchProjects(params: ProjectSearchParams): Promise<ProjectResponse[]> {
    const searchParams = new URLSearchParams();
    searchParams.append('q', params.q);
    if (params.skip !== undefined) searchParams.append('skip', params.skip.toString());
    if (params.limit !== undefined) searchParams.append('limit', params.limit.toString());

    return api.get<ProjectResponse[]>(`/projects/search?${searchParams.toString()}`);
  },

  /**
   * Get single project details
   */
  async getProject(projectId: string): Promise<ProjectResponse> {
    return api.get<ProjectResponse>(`/projects/${projectId}`);
  },

  /**
   * Create a new project
   */
  async createProject(data: ProjectCreateRequest): Promise<ProjectResponse> {
    return api.post<ProjectResponse>('/projects', data);
  },

  /**
   * Update project metadata
   */
  async updateProject(projectId: string, data: ProjectUpdateRequest): Promise<ProjectResponse> {
    return api.patch<ProjectResponse>(`/projects/${projectId}`, data);
  },

  /**
   * Delete project with confirmation
   */
  async deleteProject(projectId: string, confirm: boolean = true): Promise<DeleteResponse> {
    const params = new URLSearchParams();
    params.append('confirm', confirm.toString());
    return api.delete<DeleteResponse>(`/projects/${projectId}?${params.toString()}`);
  },

  /**
   * Validate project structure
   */
  async validateProjectStructure(projectId: string): Promise<ProjectStructureValidation> {
    return api.post<ProjectStructureValidation>(`/projects/${projectId}/validate`, {});
  },

  /**
   * Update project settings (legacy)
   */
  async updateProjectSettings(projectId: string, settings: ProjectSettings): Promise<void> {
    // TODO: Implement when backend endpoint is available
    // For now, just simulate the API call
    await new Promise((resolve) => setTimeout(resolve, 500));
    console.log('Updating project settings:', projectId, settings);
  }
};
