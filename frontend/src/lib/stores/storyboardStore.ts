/**
 * Storyboard/Pre-vis Store
 * STORY-087 Implementation
 * 
 * Svelte store for managing storyboard state and API interactions
 */

import { writable, derived } from 'svelte/store';
import type { 
    StoryboardSequence, 
    StoryboardShot, 
    StoryboardFrame,
    StoryboardTemplate,
    PrevisGenerationRequest,
    PrevisGenerationResult,
    FrameUpdateData,
    ShotUpdateData
} from '$lib/types/storyboard';

// Store interfaces
interface StoryboardState {
    sequences: Map<string, StoryboardSequence>;
    templates: StoryboardTemplate[];
    currentSequence: StoryboardSequence | null;
    previsResults: Map<string, PrevisGenerationResult>;
    loading: boolean;
    error: string | null;
}

interface StoryboardActions {
    createSequence: (projectId: string, sceneId: string, templateId?: string) => Promise<StoryboardSequence>;
    getSequence: (projectId: string, sceneId: string) => Promise<StoryboardSequence | null>;
    addShot: (sequenceId: string, shotData: any) => Promise<StoryboardShot>;
    updateShot: (sequenceId: string, shotId: string, updates: ShotUpdateData) => Promise<void>;
    addFrame: (sequenceId: string, shotId: string, frameData: any) => Promise<StoryboardFrame>;
    updateFrame: (sequenceId: string, shotId: string, frameId: string, updates: FrameUpdateData) => Promise<void>;
    generatePrevis: (sequenceId: string, request: Partial<PrevisGenerationRequest>) => Promise<PrevisGenerationResult>;
    getPrevisResult: (resultId: string) => Promise<PrevisGenerationResult | null>;
    getTemplates: () => Promise<StoryboardTemplate[]>;
    exportSequence: (sequenceId: string, format: string) => Promise<any>;
    syncWithShotlist: (sequenceId: string, shotlist: any[]) => Promise<void>;
}

// API endpoints
const API_BASE = '/api/v1/storyboard';

class StoryboardAPI {
    private async request(endpoint: string, options?: RequestInit) {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options?.headers
            },
            ...options
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || error.message || 'API request failed');
        }

        return response.json();
    }

    async createSequence(projectId: string, sceneId: string, templateId?: string) {
        return this.request('/sequences', {
            method: 'POST',
            body: JSON.stringify({ project_id: projectId, scene_id: sceneId, template_id: templateId })
        });
    }

    async getSequence(sequenceId: string) {
        return this.request(`/sequences/${sequenceId}`);
    }

    async getSequenceByScene(projectId: string, sceneId: string) {
        // This would need to be implemented in the backend
        const sequences = await this.request(`/sequences?project_id=${projectId}&scene_id=${sceneId}`);
        return sequences.data?.[0] || null;
    }

    async addShot(sequenceId: string, shotData: any) {
        return this.request(`/sequences/${sequenceId}/shots`, {
            method: 'POST',
            body: JSON.stringify(shotData)
        });
    }

    async updateShot(sequenceId: string, shotId: string, updates: ShotUpdateData) {
        return this.request(`/sequences/${sequenceId}/shots/${shotId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    async addFrame(sequenceId: string, shotId: string, frameData: any) {
        return this.request(`/sequences/${sequenceId}/shots/${shotId}/frames`, {
            method: 'POST',
            body: JSON.stringify(frameData)
        });
    }

    async updateFrame(sequenceId: string, shotId: string, frameId: string, updates: FrameUpdateData) {
        return this.request(`/sequences/${sequenceId}/shots/${shotId}/frames/${frameId}`, {
            method: 'PUT',
            body: JSON.stringify(updates)
        });
    }

    async generatePrevis(request: PrevisGenerationRequest) {
        return this.request('/previs/generate', {
            method: 'POST',
            body: JSON.stringify(request)
        });
    }

    async getPrevisResult(resultId: string) {
        return this.request(`/previs/results/${resultId}`);
    }

    async getTemplates() {
        return this.request('/templates');
    }

    async getTemplate(templateId: string) {
        return this.request(`/templates/${templateId}`);
    }

    async exportSequence(sequenceId: string, format: string = 'json') {
        return this.request(`/sequences/${sequenceId}/export`, {
            method: 'POST',
            body: JSON.stringify({ format })
        });
    }

    async syncWithShotlist(sequenceId: string, shotlist: any[]) {
        return this.request(`/sequences/${sequenceId}/sync/shotlist`, {
            method: 'POST',
            body: JSON.stringify(shotlist)
        });
    }
}

// Create API instance
const api = new StoryboardAPI();

// Create store
function createStoryboardStore() {
    const { subscribe, set, update } = writable<StoryboardState>({
        sequences: new Map(),
        templates: [],
        currentSequence: null,
        previsResults: new Map(),
        loading: false,
        error: null
    });

    const actions: StoryboardActions = {
        async createSequence(projectId: string, sceneId: string, templateId: string = 'standard') {
            update(state => ({ ...state, loading: true, error: null }));
            
            try {
                const result = await api.createSequence(projectId, sceneId, templateId);
                const sequence = result.sequence || result;
                
                update(state => {
                    const newSequences = new Map(state.sequences);
                    newSequences.set(sequence.sequence_id, sequence);
                    
                    return {
                        ...state,
                        sequences: newSequences,
                        currentSequence: sequence,
                        loading: false,
                        error: null
                    };
                });
                
                return sequence;
            } catch (error) {
                update(state => ({
                    ...state,
                    loading: false,
                    error: error instanceof Error ? error.message : 'Unknown error'
                }));
                throw error;
            }
        },

        async getSequence(projectId: string, sceneId: string) {
            update(state => ({ ...state, loading: true, error: null }));
            
            try {
                // Try to find existing sequence by scene_id
                let foundSequence = null;
                get(storyboardStore).sequences.forEach(seq => {
                    if (seq.scene_id === sceneId) {
                        foundSequence = seq;
                    }
                });
                
                if (foundSequence) {
                    update(state => ({ ...state, currentSequence: foundSequence, loading: false }));
                    return foundSequence;
                }
                
                // Otherwise, create new sequence
                const sequence = await this.createSequence(projectId, sceneId);
                return sequence;
            } catch (error) {
                update(state => ({
                    ...state,
                    loading: false,
                    error: error instanceof Error ? error.message : 'Unknown error'
                }));
                throw error;
            }
        },

        async addShot(sequenceId: string, shotData: any) {
            try {
                const result = await api.addShot(sequenceId, shotData);
                const shot = result.shot || result;
                
                update(state => {
                    const newSequences = new Map(state.sequences);
                    const sequence = newSequences.get(sequenceId);
                    
                    if (sequence) {
                        sequence.shots.push(shot);
                        sequence.shots.sort((a, b) => a.shot_number - b.shot_number);
                        sequence._recalculate_duration?.();
                    }
                    
                    return {
                        ...state,
                        sequences: newSequences,
                        currentSequence: newSequences.get(sequenceId) || state.currentSequence
                    };
                });
                
                return shot;
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async updateShot(sequenceId: string, shotId: string, updates: ShotUpdateData) {
            try {
                await api.updateShot(sequenceId, shotId, updates);
                
                update(state => {
                    const newSequences = new Map(state.sequences);
                    const sequence = newSequences.get(sequenceId);
                    
                    if (sequence) {
                        const shot = sequence.shots.find(s => s.shot_id === shotId);
                        if (shot) {
                            Object.assign(shot, updates);
                            shot.updated_at = new Date().toISOString();
                        }
                    }
                    
                    return {
                        ...state,
                        sequences: newSequences,
                        currentSequence: newSequences.get(sequenceId) || state.currentSequence
                    };
                });
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async addFrame(sequenceId: string, shotId: string, frameData: any) {
            try {
                const result = await api.addFrame(sequenceId, shotId, frameData);
                const frame = result.frame || result;
                
                update(state => {
                    const newSequences = new Map(state.sequences);
                    const sequence = newSequences.get(sequenceId);
                    
                    if (sequence) {
                        const shot = sequence.shots.find(s => s.shot_id === shotId);
                        if (shot) {
                            shot.frames.push(frame);
                            shot.frames.sort((a, b) => a.frame_number - b.frame_number);
                        }
                    }
                    
                    return {
                        ...state,
                        sequences: newSequences,
                        currentSequence: newSequences.get(sequenceId) || state.currentSequence
                    };
                });
                
                return frame;
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async updateFrame(sequenceId: string, shotId: string, frameId: string, updates: FrameUpdateData) {
            try {
                await api.updateFrame(sequenceId, shotId, frameId, updates);
                
                update(state => {
                    const newSequences = new Map(state.sequences);
                    const sequence = newSequences.get(sequenceId);
                    
                    if (sequence) {
                        const shot = sequence.shots.find(s => s.shot_id === shotId);
                        if (shot) {
                            const frame = shot.frames.find(f => f.frame_id === frameId);
                            if (frame) {
                                Object.assign(frame, updates);
                                frame.updated_at = new Date().toISOString();
                            }
                        }
                    }
                    
                    return {
                        ...state,
                        sequences: newSequences,
                        currentSequence: newSequences.get(sequenceId) || state.currentSequence
                    };
                });
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async generatePrevis(sequenceId: string, request: Partial<PrevisGenerationRequest>) {
            const fullRequest: PrevisGenerationRequest = {
                sequence_id: sequenceId,
                scene_id: request.scene_id || '',
                style: request.style || 'realistic',
                quality: request.quality || 'standard',
                resolution: request.resolution || '1920x1080',
                frame_rate: request.frame_rate || 24.0,
                camera_preset: request.camera_preset || 'standard',
                lighting_preset: request.lighting_preset || 'natural',
                include_assets: request.include_assets !== false,
                asset_overrides: request.asset_overrides || {},
                batch_size: request.batch_size || 1,
                priority: request.priority || 5,
                ...request
            };

            try {
                const result = await api.generatePrevis(fullRequest);
                
                update(state => {
                    const newResults = new Map(state.previsResults);
                    newResults.set(result.result_id, result);
                    
                    return {
                        ...state,
                        previsResults: newResults
                    };
                });
                
                return result;
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async getPrevisResult(resultId: string) {
            try {
                const result = await api.getPrevisResult(resultId);
                
                if (result) {
                    update(state => {
                        const newResults = new Map(state.previsResults);
                        newResults.set(resultId, result);
                        
                        return {
                            ...state,
                            previsResults: newResults
                        };
                    });
                }
                
                return result;
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async getTemplates() {
            try {
                const templates = await api.getTemplates();
                
                update(state => ({
                    ...state,
                    templates
                }));
                
                return templates;
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async getTemplate(templateId: string) {
            try {
                return await api.getTemplate(templateId);
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async exportSequence(sequenceId: string, format: string = 'json') {
            try {
                return await api.exportSequence(sequenceId, format);
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        },

        async syncWithShotlist(sequenceId: string, shotlist: any[]) {
            try {
                await api.syncWithShotlist(sequenceId, shotlist);
                
                // Reload sequence after sync
                const sequence = get(storyboardStore).sequences.get(sequenceId);
                if (sequence) {
                    const updatedSequence = await api.getSequence(sequenceId);
                    if (updatedSequence) {
                        update(state => {
                            const newSequences = new Map(state.sequences);
                            newSequences.set(sequenceId, updatedSequence.sequence || updatedSequence);
                            
                            return {
                                ...state,
                                sequences: newSequences,
                                currentSequence: updatedSequence.sequence || updatedSequence
                            };
                        });
                    }
                }
            } catch (error) {
                update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
                throw error;
            }
        }
    };

    return {
        subscribe,
        ...actions,
        clear: () => set({
            sequences: new Map(),
            templates: [],
            currentSequence: null,
            previsResults: new Map(),
            loading: false,
            error: null
        })
    };
}

// Create and export the store
export const storyboardStore = createStoryboardStore();

// Derived stores
export const currentSequenceStore = derived(storyboardStore, $store => $store.currentSequence);
export const loadingStore = derived(storyboardStore, $store => $store.loading);
export const errorStore = derived(storyboardStore, $store => $store.error);

// Helper functions
export function getShotDuration(shot: { frames?: any[] }): number {
    if (!shot.frames || shot.frames.length === 0) return 3.0;
    return Math.max(1.0, shot.frames.length * 0.5);
}

export function formatDuration(seconds: number): string {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function getStatusColor(status: string): string {
    const colors: Record<string, string> = {
        'concept': 'bg-gray-500',
        'sketch': 'bg-blue-500',
        'draft': 'bg-yellow-500',
        'finalized': 'bg-green-500',
        'approved': 'bg-purple-500',
        'generated': 'bg-indigo-500'
    };
    return colors[status] || 'bg-gray-500';
}

export default storyboardStore;