/**
 * Git Performance API client
 * Handles performance-optimized Git operations with caching
 */

import type { GitStatus, GitCommit } from '$lib/types';

export interface GitPerformanceMetrics {
  cache_hit_rate: number;
  total_requests: number;
  cache_hits: number;
  cache_misses: number;
  average_operation_times_ms: Record<string, number>;
  thresholds: {
    status_check_ms: number;
    commit_operation_ms: number;
    history_fetch_ms: number;
    max_memory_mb: number;
    cache_hit_rate: number;
  };
  cache_enabled: boolean;
}

export interface PaginatedHistory {
  commits: GitCommit[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

export interface OptimizationResult {
  gc_run: boolean;
  pack_optimized: boolean;
  reflog_cleaned: boolean;
  size_before: number;
  size_after: number;
  duration_ms: number;
  size_reduction_mb: number;
}

export interface PerformanceHealth {
  status: 'healthy' | 'degraded' | 'error';
  cache_available: boolean;
  cache_status: string;
  metrics: GitPerformanceMetrics;
  warnings?: string[];
}

class GitPerformanceApi {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
  }

  /**
   * Get performance metrics
   */
  async getMetrics(): Promise<GitPerformanceMetrics> {
    const response = await fetch(`${this.baseUrl}/api/v1/git/performance/metrics`);
    if (!response.ok) {
      throw new Error(`Failed to get performance metrics: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get cached Git status
   */
  async getCachedStatus(projectId: string): Promise<GitStatus> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/git/performance/${projectId}/status`
    );
    if (!response.ok) {
      throw new Error(`Failed to get cached status: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Get cached commit history with pagination
   */
  async getCachedHistory(
    projectId: string,
    page: number = 1,
    limit: number = 50,
    branch?: string
  ): Promise<PaginatedHistory> {
    const params = new URLSearchParams({
      page: page.toString(),
      limit: limit.toString(),
    });
    if (branch) {
      params.append('branch', branch);
    }

    const response = await fetch(
      `${this.baseUrl}/api/v1/git/performance/${projectId}/history?${params}`
    );
    if (!response.ok) {
      throw new Error(`Failed to get cached history: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Trigger repository optimization
   */
  async optimizeRepository(projectId: string): Promise<{ 
    task_id?: string; 
    status: string; 
    message: string; 
  }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/git/performance/${projectId}/optimize`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to optimize repository: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Invalidate cache for a project
   */
  async invalidateCache(projectId: string, operation?: string): Promise<void> {
    const params = operation ? `?operation=${operation}` : '';
    const response = await fetch(
      `${this.baseUrl}/api/v1/git/performance/${projectId}/cache${params}`,
      {
        method: 'DELETE',
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to invalidate cache: ${response.statusText}`);
    }
  }

  /**
   * Perform background commit
   */
  async backgroundCommit(
    projectId: string,
    filePaths: string[],
    message: string
  ): Promise<{ task_id?: string; status: string; message: string }> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/git/performance/${projectId}/commit/background`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          file_paths: filePaths,
          message: message,
        }),
      }
    );
    if (!response.ok) {
      throw new Error(`Failed to create background commit: ${response.statusText}`);
    }
    return response.json();
  }

  /**
   * Check performance subsystem health
   */
  async checkHealth(): Promise<PerformanceHealth> {
    const response = await fetch(
      `${this.baseUrl}/api/v1/git/performance/health`
    );
    if (!response.ok) {
      throw new Error(`Failed to check performance health: ${response.statusText}`);
    }
    return response.json();
  }
}

export const gitPerformanceApi = new GitPerformanceApi();