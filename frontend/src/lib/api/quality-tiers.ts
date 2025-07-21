/**
 * Quality Tier API Client
 * 
 * Handles API calls for the three-tier quality system (Low/Standard/High)
 * with fixed quality-to-workflow mappings.
 */

import { API_BASE_URL } from '$lib/config';

export interface QualityTier {
  tier: string;
  description: string;
  estimated_time: string;
  parameters_preview: Record<string, any>;
}

export interface QualityTiersResponse {
  task_type: string;
  available_tiers: QualityTier[];
}

class QualityTiersApi {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = `${baseUrl}/api/v1/quality`;
  }

  private async request<T>(
    path: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers
      }
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  /**
   * Get available quality tiers for a specific task type
   */
  async getQualityTiers(taskType: string): Promise<QualityTiersResponse> {
    return this.request<QualityTiersResponse>(`/tiers/${taskType}`);
  }

  /**
   * Get workflow path for a specific task and quality tier
   */
  async getWorkflowPath(taskType: string, tier: string): Promise<{
    task_type: string;
    tier: string;
    workflow_path: string;
    parameters: Record<string, any>;
  }> {
    return this.request(`/workflow/${taskType}/${tier}`);
  }
}

// Export singleton instance
export const qualityTiersApi = new QualityTiersApi();