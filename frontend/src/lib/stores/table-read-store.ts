/**
 * Table Read Store
 * STORY-088 Implementation
 *
 * Svelte store for managing digital table read sessions and creative bibles
 */

import { writable, derived } from 'svelte/store';
import type {
  TableReadSession,
  CreativeBible,
  TableReadRequest,
  TableReadStoreState,
  TableReadFormData,
  CharacterVoiceConfig
} from '$lib/types/table-read';

// API endpoints
const API_BASE = '/api/v1/table-read';

class TableReadAPI {
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

  async createSession(request: TableReadRequest): Promise<TableReadSession> {
    return this.request('/sessions', {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }

  async getSession(sessionId: string): Promise<TableReadSession> {
    return this.request(`/sessions/${sessionId}`);
  }

  async getSessionResults(sessionId: string): Promise<CreativeBible> {
    return this.request(`/sessions/${sessionId}/results`);
  }

  async getBible(bibleId: string): Promise<CreativeBible> {
    return this.request(`/bibles/${bibleId}/full`);
  }

  async getBibleSummary(bibleId: string) {
    return this.request(`/bibles/${bibleId}`);
  }

  async exportBible(bibleId: string, format: string, includeAudio: boolean = false) {
    return this.request(`/bibles/${bibleId}/export`, {
      method: 'POST',
      body: JSON.stringify({ format, include_audio: includeAudio })
    });
  }

  async listSessions(projectId?: string): Promise<TableReadSession[]> {
    const query = projectId ? `?project_id=${projectId}` : '';
    return this.request(`/sessions${query}`);
  }

  async generateAudio(sessionId: string, request: any) {
    return this.request(`/bibles/${sessionId}/audio`, {
      method: 'POST',
      body: JSON.stringify(request)
    });
  }
}

// Create API instance
const api = new TableReadAPI();

// Create store
function createTableReadStore() {
  const { subscribe, set, update } = writable<TableReadStoreState>({
    sessions: {},
    bibles: {},
    current_session: null,
    loading: false,
    error: null
  });

  const actions = {
    async createSession(request: TableReadRequest): Promise<TableReadSession> {
      update(state => ({ ...state, loading: true, error: null }));

      try {
        const session = await api.createSession(request);

        update(state => {
          const newSessions = { ...state.sessions };
          newSessions[session.session_id] = session;

          return {
            ...state,
            sessions: newSessions,
            current_session: session,
            loading: false,
            error: null
          };
        });

        // Start polling for results
        this.pollForResults(session.session_id);

        return session;
      } catch (error) {
        update(state => ({
          ...state,
          loading: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        }));
        throw error;
      }
    },

    async getSession(sessionId: string): Promise<TableReadSession> {
      try {
        const session = await api.getSession(sessionId);

        update(state => {
          const newSessions = { ...state.sessions };
          newSessions[sessionId] = session;

          return {
            ...state,
            sessions: newSessions,
            current_session: session
          };
        });

        return session;
      } catch (error) {
        update(state => ({ ...state, error: error instanceof Error ? error.message : 'Unknown error' }));
        throw error;
      }
    },

    async pollForResults(sessionId: string, maxAttempts = 60) {
      const pollInterval = 2000; // 2 seconds
      let attempts = 0;

      const poll = async () => {
        if (attempts >= maxAttempts) {
          update(state => ({ ...state, error: 'Analysis timeout' }));
          return;
        }

        try {
          const session = await this.getSession(sessionId);

          if (session.status === 'completed' && session.results) {
            // Fetch full results
            const bible = await api.getSessionResults(sessionId);
            update(state => {
              const newBibles = { ...state.bibles };
              newBibles[bible.bible_id] = bible;

              return {
                ...state,
                bibles: newBibles,
                current_session: { ...session, results: bible }
              };
            });
            return;
          } else if (session.status === 'error') {
            update(state => ({ ...state, error: session.error_message }));
            return;
          }

          attempts++;
          setTimeout(poll, pollInterval);
        } catch (error) {
          update(state => ({ ...state, error: error instanceof Error ? error.message : 'Polling error' }));
        }
      };

      poll();
    },

    async loadBible(bibleId: string): Promise<CreativeBible> {
      update(state => ({ ...state, loading: true, error: null }));

      try {
        const bible = await api.getBible(bibleId);

        update(state => {
          const newBibles = { ...state.bibles };
          newBibles[bibleId] = bible;

          return {
            ...state,
            bibles: newBibles,
            loading: false,
            error: null
          };
        });

        return bible;
      } catch (error) {
        update(state => ({
          ...state,
          loading: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        }));
        throw error;
      }
    },

    async loadSessions(projectId?: string): Promise<TableReadSession[]> {
      update(state => ({ ...state, loading: true, error: null }));

      try {
        const sessions = await api.listSessions(projectId);

        update(state => {
          const newSessions = { ...state.sessions };
          sessions.forEach(session => {
            newSessions[session.session_id] = session;
          });

          return {
            ...state,
            sessions: newSessions,
            loading: false,
            error: null
          };
        });

        return sessions;
      } catch (error) {
        update(state => ({
          ...state,
          loading: false,
          error: error instanceof Error ? error.message : 'Unknown error'
        }));
        throw error;
      }
    },

    async exportBible(
      bibleId: string,
      format: string = 'pdf',
      includeAudio: boolean = false
    ): Promise<any> {
      try {
        return await api.exportBible(bibleId, format, includeAudio);
      } catch (error) {
        update(state => ({ ...state, error: error instanceof Error ? error.message : 'Export error' }));
        throw error;
      }
    },

    async refreshSession(sessionId: string): Promise<void> {
      await this.getSession(sessionId);
    },

    clearSession(sessionId: string): void {
      update(state => {
        const newSessions = { ...state.sessions };
        delete newSessions[sessionId];

        return {
          ...state,
          sessions: newSessions,
          current_session: state.current_session?.session_id === sessionId ? null : state.current_session
        };
      });
    },

    clearError(): void {
      update(state => ({ ...state, error: null }));
    },

    clear(): void {
      set({
        sessions: {},
        bibles: {},
        current_session: null,
        loading: false,
        error: null
      });
    }
  };

  return {
    subscribe,
    ...actions,
    clear
  };
}

// Create and export the store
export const tableReadStore = createTableReadStore();

// Derived stores
export const currentBibleStore = derived(
  tableReadStore,
  $store => $store.current_session?.results || null
);

export const sessionsListStore = derived(
  tableReadStore,
  $store => Object.values($store.sessions).sort((a, b) => 
    new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  )
);

export const loadingStore = derived(
  tableReadStore,
  $store => $store.loading
);

export const errorStore = derived(
  tableReadStore,
  $store => $store.error
);

// Helper functions
export function formatAnalysisDepth(depth: string): string {
  const labels = {
    basic: 'Basic Analysis',
    comprehensive: 'Comprehensive Analysis',
    deep: 'Deep Dive Analysis'
  };
  return labels[depth as keyof typeof labels] || depth;
}

export function getStatusColor(status: string): string {
  const colors = {
    processing: 'text-blue-600 bg-blue-100',
    completed: 'text-green-600 bg-green-100',
    error: 'text-red-600 bg-red-100'
  };
  return colors[status as keyof typeof colors] || 'text-gray-600 bg-gray-100';
}

export function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export function getBeatDescription(beat: StoryCircleBeat): string {
  const descriptions = {
    [StoryCircleBeat.YOU]: 'Character in their comfort zone',
    [StoryCircleBeat.NEED]: 'Character wants something',
    [StoryCircleBeat.GO]: 'Character enters unfamiliar situation',
    [StoryCircleBeat.SEARCH]: 'Character adapts and learns',
    [StoryCircleBeat.FIND]: 'Character gets what they wanted',
    [StoryCircleBeat.TAKE]: 'Character pays the price',
    [StoryCircleBeat.RETURN]: 'Character returns to familiar situation',
    [StoryCircleBeat.CHANGE]: 'Character has fundamentally changed'
  };
  return descriptions[beat];
}

export function getArchetypeDescription(archetype: CharacterArchetype): string {
  const descriptions = {
    [CharacterArchetype.HERO]: 'The protagonist on a journey',
    [CharacterArchetype.MENTOR]: 'The wise guide or teacher',
    [CharacterArchetype.ALLY]: 'The supportive companion',
    [CharacterArchetype.SHADOW]: 'The antagonist or dark reflection',
    [CharacterArchetype.THRESHOLD_GUARDIAN]: 'The test or challenge',
    [CharacterArchetype.TRICKSTER]: 'The mischief-maker or catalyst',
    [CharacterArchetype.HERALD]: 'The messenger or call to adventure',
    [CharacterArchetype.SHAPESHIFTER]: 'The ambiguous or changing character'
  };
  return descriptions[archetype];
}

export default tableReadStore;