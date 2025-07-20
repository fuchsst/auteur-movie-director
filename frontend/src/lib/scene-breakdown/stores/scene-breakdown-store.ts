/**
 * Scene Breakdown Store
 * =====================
 * Svelte store for managing scene breakdown data
 */

import { writable, derived } from 'svelte/store';
import type { SceneBreakdown, SceneSummary, SceneReorderRequest } from '../types/scene-breakdown';

interface SceneBreakdownStore {
  scenes: SceneSummary[];
  currentScene: SceneBreakdown | null;
  isLoading: boolean;
  error: string | null;
  projectId: string | null;
}

function createSceneBreakdownStore() {
  const { subscribe, set, update } = writable<SceneBreakdownStore>({
    scenes: [],
    currentScene: null,
    isLoading: false,
    error: null,
    projectId: null
  });

  return {
    subscribe,
    
    async loadProjectScenes(projectId: string) {
      update(state => ({ ...state, isLoading: true, error: null, projectId }));
      
      try {
        const response = await fetch(`/api/v1/scene-breakdown/project/${projectId}/scenes`);
        if (!response.ok) {
          throw new Error(`Failed to load scenes: ${response.statusText}`);
        }
        
        const scenes = await response.json();
        update(state => ({ 
          ...state, 
          scenes, 
          isLoading: false,
          error: null 
        }));
      } catch (error) {
        update(state => ({ 
          ...state, 
          isLoading: false, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
      }
    },

    async loadScene(sceneId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}`);
        if (!response.ok) {
          throw new Error(`Failed to load scene: ${response.statusText}`);
        }
        
        const scene = await response.json();
        update(state => ({ ...state, currentScene: scene }));
        return scene;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async createScene(projectId: string, sceneData: Partial<SceneBreakdown>) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/project/${projectId}/scenes`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(sceneData)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to create scene: ${response.statusText}`);
        }
        
        const newScene = await response.json();
        update(state => ({ 
          ...state, 
          scenes: [...state.scenes, newScene] 
        }));
        
        return newScene;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async updateScene(sceneId: string, updates: Partial<SceneBreakdown>) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}`, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(updates)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to update scene: ${response.statusText}`);
        }
        
        const updatedScene = await response.json();
        update(state => ({ 
          ...state, 
          scenes: state.scenes.map(s => 
            s.scene_id === sceneId ? { ...s, ...updatedScene } : s
          ),
          currentScene: state.currentScene?.scene_id === sceneId 
            ? { ...state.currentScene, ...updatedScene } 
            : state.currentScene
        }));
        
        return updatedScene;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async deleteScene(sceneId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Failed to delete scene: ${response.statusText}`);
        }
        
        update(state => ({ 
          ...state, 
          scenes: state.scenes.filter(s => s.scene_id !== sceneId),
          currentScene: state.currentScene?.scene_id === sceneId 
            ? null 
            : state.currentScene
        }));
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async reorderScene(reorderData: SceneReorderRequest) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${reorderData.scene_id}/reorder`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(reorderData)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to reorder scene: ${response.statusText}`);
        }
        
        const updatedScenes = await response.json();
        update(state => ({ ...state, scenes: updatedScenes }));
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async bulkUpdateScenes(sceneIds: string[], updates: Partial<SceneBreakdown>) {
      try {
        const response = await fetch('/api/v1/scene-breakdown/scenes/bulk-update', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ scene_ids: sceneIds, updates })
        });
        
        if (!response.ok) {
          throw new Error(`Failed to bulk update scenes: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        // Reload scenes to get updated data
        const projectId = get({ subscribe }).projectId;
        if (projectId) {
          await this.loadProjectScenes(projectId);
        }
        
        return result;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async addSceneCharacter(sceneId: string, characterData: any) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/character`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(characterData)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to add character: ${response.statusText}`);
        }
        
        const updatedScene = await response.json();
        return updatedScene;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async removeSceneCharacter(sceneId: string, characterId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/character/${characterId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Failed to remove character: ${response.statusText}`);
        }
        
        await this.loadScene(sceneId);
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async addSceneAsset(sceneId: string, assetData: any) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/asset`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(assetData)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to add asset: ${response.statusText}`);
        }
        
        const updatedScene = await response.json();
        return updatedScene;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async removeSceneAsset(sceneId: string, assetId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/asset/${assetId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Failed to remove asset: ${response.statusText}`);
        }
        
        await this.loadScene(sceneId);
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async addStoryBeat(sceneId: string, beatData: any) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/story-beat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(beatData)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to add story beat: ${response.statusText}`);
        }
        
        const updatedScene = await response.json();
        return updatedScene;
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async removeStoryBeat(sceneId: string, beatId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/story-beat/${beatId}`, {
          method: 'DELETE'
        });
        
        if (!response.ok) {
          throw new Error(`Failed to remove story beat: ${response.statusText}`);
        }
        
        await this.loadScene(sceneId);
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async analyzeScene(sceneId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/scene/${sceneId}/analysis`);
        if (!response.ok) {
          throw new Error(`Failed to analyze scene: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async analyzeProject(projectId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/project/${projectId}/analysis`);
        if (!response.ok) {
          throw new Error(`Failed to analyze project: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async getCanvasData(projectId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/project/${projectId}/canvas`);
        if (!response.ok) {
          throw new Error(`Failed to get canvas data: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async saveCanvasLayout(projectId: string, layoutData: any) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/project/${projectId}/canvas/save`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(layoutData)
        });
        
        if (!response.ok) {
          throw new Error(`Failed to save canvas layout: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    async getStoryCircleMapping(projectId: string) {
      try {
        const response = await fetch(`/api/v1/scene-breakdown/project/${projectId}/story-circle`);
        if (!response.ok) {
          throw new Error(`Failed to get story circle mapping: ${response.statusText}`);
        }
        
        return await response.json();
      } catch (error) {
        update(state => ({ 
          ...state, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        }));
        throw error;
      }
    },

    clearError() {
      update(state => ({ ...state, error: null }));
    },

    reset() {
      set({
        scenes: [],
        currentScene: null,
        isLoading: false,
        error: null,
        projectId: null
      });
    }
  };
}

export const sceneBreakdownStore = createSceneBreakdownStore();

// Derived stores
export const actSummary = derived(sceneBreakdownStore, $store => {
  const summary: Record<number, {
    scenes: number;
    duration: number;
    complete: number;
    total: number;
  }> = {};

  $store.scenes.forEach(scene => {
    if (!summary[scene.act_number]) {
      summary[scene.act_number] = {
        scenes: 0,
        duration: 0,
        complete: 0,
        total: 0
      };
    }

    summary[scene.act_number].scenes++;
    summary[scene.act_number].duration += scene.duration_minutes;
    summary[scene.act_number].total++;
    
    if (scene.status === 'complete') {
      summary[scene.act_number].complete++;
    }
  });

  return summary;
});

export const projectProgress = derived(sceneBreakdownStore, $store => {
  const total = $store.scenes.length;
  const complete = $store.scenes.filter(s => s.status === 'complete').length;
  const totalDuration = $store.scenes.reduce((sum, s) => sum + s.duration_minutes, 0);

  return {
    total,
    complete,
    progress: total > 0 ? Math.round((complete / total) * 100) : 0,
    totalDuration: Math.round(totalDuration * 100) / 100
  };
});