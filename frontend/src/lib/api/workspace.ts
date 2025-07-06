/**
 * Workspace API client
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

export interface ProjectListItem {
  id: string;
  name: string;
  path: string;
  created: string;
  modified: string;
  quality: string;
  narrative_structure: string;
  git_status: string;
}

export const workspaceApi = {
  /**
   * Get workspace configuration
   */
  async getConfig(): Promise<WorkspaceConfig> {
    return api.get<WorkspaceConfig>('/workspace/config');
  },

  /**
   * List all projects in workspace
   */
  async listProjects(filters?: {
    quality?: string;
    structure?: string;
  }): Promise<ProjectListItem[]> {
    const params = new URLSearchParams();
    if (filters?.quality) params.append('quality', filters.quality);
    if (filters?.structure) params.append('structure', filters.structure);

    const query = params.toString();
    return api.get<ProjectListItem[]>(`/workspace/projects${query ? `?${query}` : ''}`);
  },

  /**
   * Create a new project
   */
  async createProject(data: {
    name: string;
    narrative_structure: string;
    quality: string;
    director?: string;
    description?: string;
  }): Promise<{ id: string; name: string; path: string }> {
    return api.post('/workspace/projects', data);
  },

  /**
   * Update project settings
   */
  async updateProjectSettings(projectId: string, settings: ProjectSettings): Promise<void> {
    // TODO: Implement when backend endpoint is available
    // For now, just simulate the API call
    await new Promise((resolve) => setTimeout(resolve, 500));
    console.log('Updating project settings:', projectId, settings);
  },

  /**
   * Validate project structure
   */
  async validateProjectStructure(projectId: string): Promise<{
    valid: boolean;
    missing_directories: string[];
    unexpected_directories: string[];
    git_initialized: boolean;
    git_lfs_enabled: boolean;
    project_json_valid: boolean;
    errors: string[];
  }> {
    return api.get(`/workspace/projects/${projectId}/structure`);
  }
};
