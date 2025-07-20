/**
 * Asset Propagation Service
 * STORY-089 Implementation
 * 
 * Frontend service for managing asset propagation across story hierarchy.
 */

import { api } from '$lib/api/client';
import type {
  AssetPropagationRequest,
  AssetResolutionResponse,
  GenerationContext,
  AssetUsageResponse,
  PropagationRuleRequest,
  AssetPropagationRule,
  HierarchyValidation,
  AssetPropagationState,
  HierarchyLevel,
  PropagationMode
} from '$lib/types/asset-propagation';

class AssetPropagationService {
  private baseUrl = '/api/v1/asset-propagation';

  /**
   * Add an asset to a specific hierarchy level
   */
  async addAssetToContext(request: AssetPropagationRequest): Promise<{
    success: boolean;
    assetReference: any;
    message: string;
  }> {
    try {
      const response = await api.post(`${this.baseUrl}/assets`, request);
      return response.data;
    } catch (error) {
      console.error('Failed to add asset to context:', error);
      throw error;
    }
  }

  /**
   * Resolve all assets for a specific hierarchy level
   */
  async resolveAssets(
    projectId: string,
    level: HierarchyLevel,
    levelId: string,
    assetType?: string
  ): Promise<AssetResolutionResponse> {
    try {
      const params = assetType ? { asset_type: assetType } : {};
      const response = await api.get(
        `${this.baseUrl}/resolve/${projectId}/${level}/${levelId}`,
        { params }
      );
      return response.data;
    } catch (error) {
      console.error('Failed to resolve assets:', error);
      throw error;
    }
  }

  /**
   * Resolve assets formatted for generative processes
   */
  async resolveForGeneration(
    projectId: string,
    level: HierarchyLevel,
    levelId: string
  ): Promise<GenerationContext> {
    try {
      const response = await api.get(
        `${this.baseUrl}/resolve/generation/${projectId}/${level}/${levelId}`
      );
      return response.data;
    } catch (error) {
      console.error('Failed to resolve assets for generation:', error);
      throw error;
    }
  }

  /**
   * Add a custom propagation rule
   */
  async addPropagationRule(rule: PropagationRuleRequest): Promise<{
    success: boolean;
    rule: AssetPropagationRule;
    message: string;
  }> {
    try {
      const response = await api.post(`${this.baseUrl}/rules`, rule);
      return response.data;
    } catch (error) {
      console.error('Failed to add propagation rule:', error);
      throw error;
    }
  }

  /**
   * Get usage information for a specific asset
   */
  async getAssetUsage(projectId: string, assetId: string): Promise<AssetUsageResponse> {
    try {
      const response = await api.get(`${this.baseUrl}/usage/${projectId}/${assetId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get asset usage:', error);
      throw error;
    }
  }

  /**
   * Validate asset consistency across the project
   */
  async validateConsistency(projectId: string): Promise<HierarchyValidation> {
    try {
      const response = await api.get(`${this.baseUrl}/validate/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to validate consistency:', error);
      throw error;
    }
  }

  /**
   * Get available hierarchy levels
   */
  async getHierarchyLevels(): Promise<{
    levels: HierarchyLevel[];
    description: string;
  }> {
    try {
      const response = await api.get(`${this.baseUrl}/hierarchy/levels`);
      return response.data;
    } catch (error) {
      console.error('Failed to get hierarchy levels:', error);
      throw error;
    }
  }

  /**
   * Save propagation state for a project
   */
  async savePropagationState(projectId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    try {
      const response = await api.post(`${this.baseUrl}/save/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to save propagation state:', error);
      throw error;
    }
  }

  /**
   * Load propagation state for a project
   */
  async loadPropagationState(projectId: string): Promise<{
    success: boolean;
    message: string;
  }> {
    try {
      const response = await api.post(`${this.baseUrl}/load/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to load propagation state:', error);
      throw error;
    }
  }

  /**
   * Export complete propagation state for a project
   */
  async exportPropagationState(projectId: string): Promise<AssetPropagationState> {
    try {
      const response = await api.get(`${this.baseUrl}/export/${projectId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to export propagation state:', error);
      throw error;
    }
  }

  /**
   * Batch resolve assets for multiple levels
   */
  async batchResolveAssets(
    projectId: string,
    levels: Array<{ level: HierarchyLevel; levelId: string }>
  ): Promise<Array<AssetResolutionResponse>> {
    const promises = levels.map(({ level, levelId }) =>
      this.resolveAssets(projectId, level, levelId)
    );
    
    try {
      return await Promise.all(promises);
    } catch (error) {
      console.error('Failed to batch resolve assets:', error);
      throw error;
    }
  }

  /**
   * Get asset dependencies (where an asset is used)
   */
  async getAssetDependencies(projectId: string, assetId: string): Promise<string[]> {
    try {
      const usage = await this.getAssetUsage(projectId, assetId);
      return usage.usageLocations.map(location => `${location.level}:${location.levelId}`);
    } catch (error) {
      console.error('Failed to get asset dependencies:', error);
      throw error;
    }
  }

  /**
   * Check if an asset is used consistently across the project
   */
  async checkAssetConsistency(projectId: string, assetId: string): Promise<{
    assetId: string;
    usageCount: number;
    levels: HierarchyLevel[];
    consistent: boolean;
    issues: string[];
    warnings?: string[];
  }> {
    try {
      const usage = await this.getAssetUsage(projectId, assetId);
      const validation = await this.validateConsistency(projectId);
      
      // Filter validation issues for this specific asset
      const assetIssues = validation.issues.filter(issue => 
        issue.includes(assetId)
      );
      
      return {
        assetId,
        usageCount: usage.usageCount,
        levels: [...new Set(usage.usageLocations.map(loc => loc.level))],
        consistent: assetIssues.length === 0,
        issues: assetIssues,
        warnings: validation.warnings.filter(warning => 
          warning.includes(assetId)
        )
      };
    } catch (error) {
      console.error('Failed to check asset consistency:', error);
      throw error;
    }
  }

  /**
   * Create default propagation rules for a new project
   */
  async setupDefaultRules(projectId: string): Promise<void> {
    const defaultRules = [
      {
        assetType: 'character',
        sourceLevel: HierarchyLevel.PROJECT,
        targetLevel: HierarchyLevel.TAKE,
        propagationMode: PropagationMode.INHERIT,
        priority: 1
      },
      {
        assetType: 'style',
        sourceLevel: HierarchyLevel.PROJECT,
        targetLevel: HierarchyLevel.TAKE,
        propagationMode: PropagationMode.INHERIT,
        priority: 1
      },
      {
        assetType: 'location',
        sourceLevel: HierarchyLevel.SCENE,
        targetLevel: HierarchyLevel.TAKE,
        propagationMode: PropagationMode.INHERIT,
        priority: 2
      },
      {
        assetType: 'prop',
        sourceLevel: HierarchyLevel.SCENE,
        targetLevel: HierarchyLevel.SHOT,
        propagationMode: PropagationMode.OVERRIDE,
        priority: 3
      },
      {
        assetType: 'wardrobe',
        sourceLevel: HierarchyLevel.PROJECT,
        targetLevel: HierarchyLevel.SHOT,
        propagationMode: PropagationMode.OVERRIDE,
        priority: 4
      }
    ];

    for (const rule of defaultRules) {
      try {
        await this.addPropagationRule(rule);
      } catch (error) {
        console.warn('Failed to add default rule:', rule, error);
      }
    }
  }

  /**
   * Utility method to get asset references for a specific type
   */
  async getAssetsByType(
    projectId: string,
    level: HierarchyLevel,
    levelId: string,
    assetType: string
  ): Promise<AssetReference[]> {
    const resolved = await this.resolveAssets(projectId, level, levelId);
    return resolved.resolvedAssets[assetType] || [];
  }

  /**
   * Utility method to check if an asset exists at a specific level
   */
  async hasAssetAtLevel(
    projectId: string,
    level: HierarchyLevel,
    levelId: string,
    assetId: string
  ): Promise<boolean> {
    try {
      const resolved = await this.resolveAssets(projectId, level, levelId);
      return Object.values(resolved.resolvedAssets).some(assets => 
        assets.some(asset => asset.assetId === assetId)
      );
    } catch {
      return false;
    }
  }
}

// Export singleton instance
export const assetPropagationService = new AssetPropagationService();

// Export for dependency injection
export { AssetPropagationService };