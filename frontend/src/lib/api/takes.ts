import { api } from './client';

export interface GenerationParams {
  model: string;
  seed: number;
  prompt: string;
  negativePrompt?: string;
  steps: number;
  cfg: number;
  extra?: Record<string, any>;
}

export interface Resolution {
  width: number;
  height: number;
}

export interface ResourceUsage {
  quality: string;
  vramUsed: number;
  generationTime: number;
}

export interface TakeMetadata {
  id: string;
  shotId: string;
  created: string;
  duration?: number;
  resolution?: Resolution;
  generationParams: GenerationParams;
  resources: ResourceUsage;
  status: 'generating' | 'complete' | 'failed';
  error?: string;
  filePath?: string;
  fileSize?: number;
  thumbnailPath?: string;
}

export interface CreateTakeRequest {
  generationParams: GenerationParams;
  quality?: string;
}

export interface CreateTakeResponse {
  takeId: string;
  takeNumber: number;
  status: string;
  taskId?: string;
}

export interface TakeListResponse {
  takes: TakeMetadata[];
  activeTakeId?: string;
  total: number;
}

export interface SetActiveTakeRequest {
  takeId: string;
}

export interface DeleteTakeResponse {
  success: boolean;
  message: string;
  newActiveTakeId?: string;
}

export interface TakeExportRequest {
  takeId: string;
  includeMetadata?: boolean;
}

export interface TakeExportResponse {
  success: boolean;
  exportPath?: string;
  message: string;
}

export interface TakeCleanupRequest {
  keepCount?: number;
  includeFailed?: boolean;
}

export interface TakeCleanupResponse {
  deletedCount: number;
  remainingCount: number;
  message: string;
}

export const takesApi = {
  /**
   * Create a new take for a shot
   */
  async createTake(
    projectId: string,
    shotId: string,
    request: CreateTakeRequest
  ): Promise<CreateTakeResponse> {
    return api.post<CreateTakeResponse>(
      `/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/takes`,
      request
    );
  },

  /**
   * List all takes for a shot
   */
  async listTakes(
    projectId: string,
    shotId: string,
    includeFailed = true
  ): Promise<TakeListResponse> {
    return api.get<TakeListResponse>(
      `/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/takes`,
      { includeFailed }
    );
  },

  /**
   * Get details for a specific take
   */
  async getTake(projectId: string, shotId: string, takeId: string): Promise<TakeMetadata> {
    return api.get<TakeMetadata>(
      `/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/takes/${takeId}`
    );
  },

  /**
   * Set the active take for a shot
   */
  async setActiveTake(
    projectId: string,
    shotId: string,
    takeId: string
  ): Promise<{ success: boolean; message: string }> {
    return api.put(`/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/active-take`, {
      takeId
    });
  },

  /**
   * Delete a take (soft delete)
   */
  async deleteTake(projectId: string, shotId: string, takeId: string): Promise<DeleteTakeResponse> {
    return api.delete<DeleteTakeResponse>(
      `/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/takes/${takeId}`
    );
  },

  /**
   * Export a take to the exports directory
   */
  async exportTake(
    projectId: string,
    shotId: string,
    request: TakeExportRequest
  ): Promise<TakeExportResponse> {
    return api.post<TakeExportResponse>(
      `/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/takes/export`,
      request
    );
  },

  /**
   * Clean up old takes for a shot
   */
  async cleanupTakes(
    projectId: string,
    shotId: string,
    request?: TakeCleanupRequest
  ): Promise<TakeCleanupResponse> {
    return api.post<TakeCleanupResponse>(
      `/takes/projects/${projectId}/shots/${encodeURIComponent(shotId)}/takes/cleanup`,
      request || { keepCount: 10 }
    );
  },

  /**
   * Get the thumbnail URL for a take
   */
  getThumbnailUrl(projectId: string, thumbnailPath?: string): string {
    if (!thumbnailPath) return '/placeholder-thumbnail.png';
    return `/api/v1/workspace/projects/${projectId}/files/${encodeURIComponent(thumbnailPath)}`;
  },

  /**
   * Get the media file URL for a take
   */
  getMediaUrl(projectId: string, filePath?: string): string {
    if (!filePath) return '';
    return `/api/v1/workspace/projects/${projectId}/files/${encodeURIComponent(filePath)}`;
  }
};
