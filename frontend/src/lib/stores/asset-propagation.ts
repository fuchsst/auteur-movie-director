/**
 * Asset Propagation Store
 * STORY-089 Implementation
 * 
 * Svelte store for managing asset propagation across story hierarchy.
 */

import { writable, derived } from 'svelte/store';
import type {
  AssetResolutionResponse,
  GenerationContext,
  AssetUsageResponse,
  AssetPropagationRule,
  HierarchyValidation,
  HierarchyLevel
} from '$lib/types/asset-propagation';
import { assetPropagationService } from '$lib/services/asset-propagation';

// Main store for asset propagation state
interface AssetPropagationState {
  projectId: string | null;
  contexts: Map<string, AssetResolutionResponse>;
  rules: AssetPropagationRule[];
  validation: HierarchyValidation | null;
  loading: boolean;
  error: string | null;
}

const initialState: AssetPropagationState = {
  projectId: null,
  contexts: new Map(),
  rules: [],
  validation: null,
  loading: false,
  error: null
};

// Create the writable store
const store = writable<AssetPropagationState>(initialState);

// Store actions
const assetPropagationStore = {
  subscribe: store.subscribe,

  /**
   * Initialize the store for a specific project
   */
  async initialize(projectId: string) {
    store.update(state => ({ ...state, loading: true, error: null, projectId }));
    
    try {
      // Load validation and rules
      const [validation] = await Promise.all([
        assetPropagationService.validateConsistency(projectId)
      ]);
      
      store.update(state => ({
        ...state,
        validation,
        loading: false
      }));
    } catch (error) {
      store.update(state => ({
        ...state,
        error: error.message,
        loading: false
      }));
    }
  },

  /**
   * Resolve assets for a specific hierarchy level
   */
  async resolveAssets(
    projectId: string,
    level: HierarchyLevel,
    levelId: string,
    assetType?: string
  ) {
    store.update(state => ({ ...state, loading: true }));
    
    try {
      const resolved = await assetPropagationService.resolveAssets(
        projectId, level, levelId, assetType
      );
      
      const contextKey = `${projectId}:${level}:${levelId}`;
      store.update(state => {
        const newContexts = new Map(state.contexts);
        newContexts.set(contextKey, resolved);
        return { ...state, contexts: newContexts, loading: false };
      });
      
      return resolved;
    } catch (error) {
      store.update(state => ({ ...state, error: error.message, loading: false }));
      throw error;
    }
  },

  /**
   * Resolve assets for generation
   */
  async resolveForGeneration(
    projectId: string,
    level: HierarchyLevel,
    levelId: string
  ): Promise<GenerationContext> {
    store.update(state => ({ ...state, loading: true }));
    
    try {
      const context = await assetPropagationService.resolveForGeneration(
        projectId, level, levelId
      );
      
      store.update(state => ({ ...state, loading: false }));
      return context;
    } catch (error) {
      store.update(state => ({ ...state, error: error.message, loading: false }));
      throw error;
    }
  },

  /**
   * Add an asset to a specific context
   */
  async addAsset(request: {
    projectId: string;
    level: HierarchyLevel;
    levelId: string;
    assetId: string;
    assetType: string;
    overrideData?: Record<string, any>;
  }) {
    store.update(state => ({ ...state, loading: true }));
    
    try {
      await assetPropagationService.addAssetToContext(request);
      
      // Refresh the context
      await this.resolveAssets(request.projectId, request.level, request.levelId);
      
      // Refresh validation
      const validation = await assetPropagationService.validateConsistency(request.projectId);
      store.update(state => ({ ...state, validation, loading: false }));
      
    } catch (error) {
      store.update(state => ({ ...state, error: error.message, loading: false }));
      throw error;
    }
  },

  /**
   * Add a propagation rule
   */
  async addRule(rule: PropagationRuleRequest) {
    store.update(state => ({ ...state, loading: true }));
    
    try {
      await assetPropagationService.addPropagationRule(rule);
      
      // Refresh rules and validation
      const validation = await assetPropagationService.validateConsistency(
        store.getState()?.projectId || ''
      );
      
      store.update(state => ({ ...state, validation, loading: false }));
    } catch (error) {
      store.update(state => ({ ...state, error: error.message, loading: false }));
      throw error;
    }
  },

  /**
   * Get asset usage information
   */
  async getAssetUsage(projectId: string, assetId: string): Promise<AssetUsageResponse> {
    return await assetPropagationService.getAssetUsage(projectId, assetId);
  },

  /**
   * Validate asset consistency
   */
  async validateConsistency(projectId: string): Promise<HierarchyValidation> {
    store.update(state => ({ ...state, loading: true }));
    
    try {
      const validation = await assetPropagationService.validateConsistency(projectId);
      store.update(state => ({ ...state, validation, loading: false }));
      return validation;
    } catch (error) {
      store.update(state => ({ ...state, error: error.message, loading: false }));
      throw error;
    }
  },

  /**
   * Save current state
   */
  async saveState(projectId: string) {
    return await assetPropagationService.savePropagationState(projectId);
  },

  /**
   * Load state
   */
  async loadState(projectId: string) {
    return await assetPropagationService.loadPropagationState(projectId);
  },

  /**
   * Clear error
   */
  clearError() {
    store.update(state => ({ ...state, error: null }));
  },

  /**
   * Reset store
   */
  reset() {
    store.set(initialState);
  }
};

// Derived stores for specific use cases

// Store for current project's resolved assets
export const currentProjectAssets = derived(
  store,
  $store => ({
    projectId: $store.projectId,
    contexts: $store.contexts,
    loading: $store.loading,
    error: $store.error
  })
);

// Store for validation results
export const validationStore = derived(
  store,
  $store => ({
    validation: $store.validation,
    loading: $store.loading,
    error: $store.error
  })
);

// Utility function to get assets for a specific level
export const getAssetsForLevel = derived(
  store,
  $store => (projectId: string, level: HierarchyLevel, levelId: string) => {
    const contextKey = `${projectId}:${level}:${levelId}`;
    return $store.contexts.get(contextKey);
  }
);

// Utility function to get all assets of a specific type
export const getAssetsByType = derived(
  store,
  $store => (projectId: string, level: HierarchyLevel, levelId: string, assetType: string) => {
    const contextKey = `${projectId}:${level}:${levelId}`;
    const context = $store.contexts.get(contextKey);
    return context?.resolvedAssets[assetType] || [];
  }
);

// Utility function to check if store has any resolved assets
export const hasResolvedAssets = derived(
  store,
  $store => $store.contexts.size > 0
);

export default assetPropagationStore;