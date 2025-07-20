/**
 * Breakdown Store
 * STORY-086: Professional Script Breakdown Store
 * 
 * Manages breakdown data, script parsing, and element management
 * for the professional script breakdown interface.
 */

import { writable, derived } from 'svelte/store';
import { getApiClient } from '$lib/api/client';
import type { ScriptBreakdown, SceneBreakdown, BreakdownElement } from '$lib/types/breakdown';

interface BreakdownStore {
  breakdowns: Record<string, ScriptBreakdown>;
  loading: boolean;
  error: string | null;
}

interface BreakdownState {
  breakdowns: Record<string, ScriptBreakdown>;
  loading: Record<string, boolean>;
  errors: Record<string, string>;
}

const initialState: BreakdownState = {
  breakdowns: {},
  loading: {},
  errors: {}
};

function createBreakdownStore() {
  const { subscribe, set, update } = writable<BreakdownState>(initialState);
  const api = getApiClient();

  return {
    subscribe,

    /**
     * Load breakdown data for a project
     */
    async loadBreakdown(projectId: string): Promise<void> {
      update(state => ({
        ...state,
        loading: { ...state.loading, [projectId]: true },
        errors: { ...state.errors, [projectId]: null }
      }));

      try {
        const response = await api.get(`/breakdown/${projectId}`);
        const breakdown = response.data?.breakdown;
        
        if (breakdown) {
          update(state => ({
            ...state,
            breakdowns: { ...state.breakdowns, [projectId]: breakdown },
            loading: { ...state.loading, [projectId]: false }
          }));
        }
      } catch (error) {
        update(state => ({
          ...state,
          loading: { ...state.loading, [projectId]: false },
          errors: { ...state.errors, [projectId]: error.message || 'Failed to load breakdown' }
        }));
      }
    },

    /**
     * Parse script file and create breakdown
     */
    async parseScript(projectId: string, file: File, projectName: string): Promise<void> {
      update(state => ({
        ...state,
        loading: { ...state.loading, [projectId]: true },
        errors: { ...state.errors, [projectId]: null }
      }));

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('project_id', projectId);
        formData.append('project_name', projectName);

        const response = await api.post('/breakdown/parse-script', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });

        const breakdown = response.data?.breakdown;
        if (breakdown) {
          update(state => ({
            ...state,
            breakdowns: { ...state.breakdowns, [projectId]: breakdown },
            loading: { ...state.loading, [projectId]: false }
          }));
        }
      } catch (error) {
        update(state => ({
          ...state,
          loading: { ...state.loading, [projectId]: false },
          errors: { ...state.errors, [projectId]: error.message || 'Failed to parse script' }
        }));
        throw error;
      }
    },

    /**
     * Update element status
     */
    async updateElement(
      projectId: string,
      sceneId: string,
      elementId: string,
      updates: Partial<BreakdownElement>
    ): Promise<void> {
      try {
        const response = await api.put(
          `/breakdown/element/${projectId}/${sceneId}/${elementId}`,
          updates
        );

        if (response.success) {
          // Refresh breakdown data
          await this.loadBreakdown(projectId);
        }
      } catch (error) {
        throw new Error(error.message || 'Failed to update element');
      }
    },

    /**
     * Add custom element to scene
     */
    async addElement(
      projectId: string,
      sceneId: string,
      elementData: Partial<BreakdownElement>
    ): Promise<void> {
      try {
        const response = await api.post(
          `/breakdown/element/${projectId}/${sceneId}`,
          elementData
        );

        if (response.success) {
          // Refresh breakdown data
          await this.loadBreakdown(projectId);
        }
      } catch (error) {
        throw new Error(error.message || 'Failed to add element');
      }
    },

    /**
     * Update scene notes
     */
    async updateSceneNotes(
      projectId: string,
      sceneId: string,
      notes: { continuity_notes?: string; special_notes?: string }
    ): Promise<void> {
      try {
        const breakdown = get(this).breakdowns[projectId];
        if (!breakdown) return;

        const scene = breakdown.scenes[sceneId];
        if (scene) {
          scene.continuity_notes = notes.continuity_notes || scene.continuity_notes;
          scene.special_notes = notes.special_notes || scene.special_notes;
          
          update(state => ({
            ...state,
            breakdowns: {
              ...state.breakdowns,
              [projectId]: {
                ...breakdown,
                scenes: {
                  ...breakdown.scenes,
                  [sceneId]: scene
                }
              }
            }
          }));
        }
      } catch (error) {
        throw new Error(error.message || 'Failed to update scene notes');
      }
    },

    /**
     * Export breakdown data
     */
    async exportBreakdown(
      projectId: string,
      format: string,
      options: any = {}
    ): Promise<any> {
      try {
        const response = await api.post(`/breakdown/export/${projectId}`, {
          export_format: format,
          ...options
        });
        return response.data?.export;
      } catch (error) {
        throw new Error(error.message || 'Failed to export breakdown');
      }
    },

    /**
     * Get summary statistics
     */
    async getSummary(projectId: string): Promise<any> {
      try {
        const response = await api.get(`/breakdown/summary/${projectId}`);
        return response.data?.summary;
      } catch (error) {
        throw new Error(error.message || 'Failed to get summary');
      }
    },

    /**
     * Get elements by category across all scenes
     */
    async getElementsByCategory(projectId: string, category: string): Promise<any[]> {
      try {
        const response = await api.get(`/breakdown/elements/${projectId}/${category}`);
        return response.data?.elements || [];
      } catch (error) {
        throw new Error(error.message || 'Failed to get elements by category');
      }
    },

    /**
     * Clear breakdown for a project
     */
    clearBreakdown(projectId: string): void {
      update(state => {
        const newBreakdowns = { ...state.breakdowns };
        delete newBreakdowns[projectId];
        return {
          ...state,
          breakdowns: newBreakdowns
        };
      });
    },

    /**
     * Clear all breakdowns
     */
    clearAll(): void {
      set(initialState);
    }
  };
}

export const breakdownStore = createBreakdownStore();

// Derived stores for convenience
export const currentBreakdown = (projectId: string) => 
  derived(breakdownStore, $store => $store.breakdowns[projectId]);

export const isLoading = (projectId: string) =>
  derived(breakdownStore, $store => $store.loading[projectId] || false);

export const hasError = (projectId: string) =>
  derived(breakdownStore, $store => $store.errors[projectId] || null);