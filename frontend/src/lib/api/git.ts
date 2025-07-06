/**
 * Git and Git LFS API client
 */

import { api } from './client';

export interface GitCommit {
  hash: string;
  message: string;
  author: string;
  email: string;
  date: string;
  files_changed: number;
}

export interface GitStatus {
  initialized: boolean;
  branch?: string;
  is_dirty?: boolean;
  untracked_files?: string[];
  modified_files?: string[];
  staged_files?: string[];
  lfs_files?: string[];
  lfs_patterns?: string[];
  error?: string;
}

export interface LFSFile {
  oid: string;
  size: number;
  path: string;
}

export interface LFSStatus {
  enabled: boolean;
  installed: boolean;
  initialized?: boolean;
  tracked_patterns?: string[];
  tracked_files?: LFSFile[];
  file_count?: number;
  total_size?: number;
  error?: string;
}

export interface LFSValidation {
  git_installed: boolean;
  lfs_installed: boolean;
  git_version?: string;
  lfs_version?: string;
  issues: string[];
}

export interface CommitRequest {
  message: string;
  prefix?: string;
  files?: string[];
}

export const gitApi = {
  async getStatus(projectId: string): Promise<GitStatus> {
    return api.get<GitStatus>(`/git/projects/${projectId}/status`);
  },

  async commit(projectId: string, request: CommitRequest): Promise<void> {
    await api.post(`/git/projects/${projectId}/commit`, request);
  },

  async getHistory(projectId: string, limit = 20, file?: string): Promise<GitCommit[]> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (file) params.append('file', file);
    return api.get<GitCommit[]>(`/git/projects/${projectId}/history?${params}`);
  }
};

export const gitLFSApi = {
  async validateSetup(): Promise<LFSValidation> {
    return api.get<LFSValidation>('/git/lfs/validate');
  },

  async initializeProject(projectId: string): Promise<void> {
    await api.post(`/git/lfs/projects/${projectId}/initialize`);
  },

  async getStatus(projectId: string): Promise<LFSStatus> {
    return api.get<LFSStatus>(`/git/lfs/projects/${projectId}/status`);
  },

  async trackPattern(projectId: string, pattern: string): Promise<void> {
    await api.post(`/git/lfs/projects/${projectId}/track`, { pattern });
  },

  async untrackPattern(projectId: string, pattern: string): Promise<void> {
    await api.post(`/git/lfs/projects/${projectId}/untrack`, { pattern });
  },

  async getTrackedFiles(projectId: string): Promise<LFSFile[]> {
    return api.get<LFSFile[]>(`/git/lfs/projects/${projectId}/files`);
  }
};
