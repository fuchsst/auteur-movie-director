import { writable } from 'svelte/store';
import { api } from '../../api/client';
import type { 
  SceneTimelineData, 
  StoryBeat, 
  NarrativeAnalytics, 
  CharacterArcData,
  DigitalAssetUsage,
  StoryStructureValidation
} from '../types/story-visualization';

interface StoryVisualizationState {
  timelineData: SceneTimelineData[];
  storyBeats: StoryBeat[];
  characterArcs: CharacterArcData[];
  assetUsage: DigitalAssetUsage[];
  analytics: NarrativeAnalytics | null;
  validation: StoryStructureValidation | null;
  loading: boolean;
  error: string | null;
}

const initialState: StoryVisualizationState = {
  timelineData: [],
  storyBeats: [],
  characterArcs: [],
  assetUsage: [],
  analytics: null,
  validation: null,
  loading: false,
  error: null
};

function createStoryVisualizationStore() {
  const { subscribe, set, update } = writable<StoryVisualizationState>(initialState);

  return {
    subscribe,
    
    async loadTimelineData(projectId: string) {
      update(state => ({ ...state, loading: true, error: null }));
      
      try {
        const response = await api.get(`/api/v1/story/${projectId}/timeline`);
        const data = response.data;
        
        update(state => ({
          ...state,
          timelineData: data.scenes || [],
          storyBeats: data.beats || [],
          characterArcs: data.characterArcs || [],
          loading: false
        }));
      } catch (error) {
        update(state => ({
          ...state,
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to load timeline data'
        }));
      }
    },

    async getStoryBeats(projectId: string): Promise<StoryBeat[]> {
      try {
        const response = await api.get(`/api/v1/story/${projectId}/beats`);
        return response.data.beats || [];
      } catch (error) {
        console.error('Failed to load story beats:', error);
        return [];
      }
    },

    async getCharacterArcs(projectId: string): Promise<CharacterArcData[]> {
      try {
        const response = await api.get(`/api/v1/characters/${projectId}/arcs`);
        return response.data.characterArcs || [];
      } catch (error) {
        console.error('Failed to load character arcs:', error);
        return [];
      }
    },

    async getAssetUsage(projectId: string): Promise<DigitalAssetUsage[]> {
      try {
        const response = await api.get(`/api/v1/assets/${projectId}/usage-analysis`);
        return response.data.assetUsage || [];
      } catch (error) {
        console.error('Failed to load asset usage:', error);
        return [];
      }
    },

    async getAnalytics(projectId: string): Promise<NarrativeAnalytics | null> {
      try {
        const response = await api.get(`/api/v1/projects/${projectId}/narrative-quality`);
        return response.data.analytics || null;
      } catch (error) {
        console.error('Failed to load analytics:', error);
        return null;
      }
    },

    async validateStructure(projectId: string): Promise<StoryStructureValidation | null> {
      try {
        const response = await api.get(`/api/v1/story/${projectId}/validate-structure`);
        return response.data.validation || null;
      } catch (error) {
        console.error('Failed to validate structure:', error);
        return null;
      }
    },

    async optimizePacing(projectId: string) {
      try {
        const response = await api.post(`/api/v1/projects/${projectId}/optimize-pacing`);
        const newData = response.data;
        
        update(state => ({
          ...state,
          timelineData: newData.scenes || state.timelineData,
          analytics: newData.analytics || state.analytics
        }));
      } catch (error) {
        console.error('Failed to optimize pacing:', error);
      }
    },

    async updateSceneBeat(sceneId: string, beatData: Partial<StoryBeat>) {
      try {
        const response = await api.put(`/api/v1/story/${sceneId}/beat-analysis`, beatData);
        const updatedScene = response.data.scene;
        
        update(state => ({
          ...state,
          timelineData: state.timelineData.map(scene => 
            scene.id === sceneId ? { ...scene, ...updatedScene } : scene
          )
        }));
      } catch (error) {
        console.error('Failed to update scene beat:', error);
      }
    },

    async exportStoryReport(projectId: string, format: 'pdf' | 'json' = 'pdf') {
      try {
        const response = await api.get(`/api/v1/projects/${projectId}/export-story-report`, {
          params: { format }
        });
        return response.data.url;
      } catch (error) {
        console.error('Failed to export story report:', error);
        throw error;
      }
    },

    reset() {
      set(initialState);
    }
  };
}

export const storyVisualizationStore = createStoryVisualizationStore();