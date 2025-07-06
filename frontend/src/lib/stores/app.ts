/**
 * Global application state store
 */

import { writable, derived } from 'svelte/store';
import type { Writable, Readable } from 'svelte/store';
import type { WorkspaceProject, ProjectManifest } from '$lib/types/project';
import type { WebSocketState } from '$lib/types/websocket';

// Application state
export interface AppState {
  initialized: boolean;
  loading: boolean;
  error: string | null;
}

// Create stores
export const appState: Writable<AppState> = writable({
  initialized: false,
  loading: false,
  error: null
});

// WebSocket connection state
export const wsState: Writable<WebSocketState> = writable({
  connected: false,
  connecting: false,
  error: null,
  reconnectAttempts: 0,
  lastHeartbeat: null
});

// Projects in workspace
export const projects: Writable<WorkspaceProject[]> = writable([]);

// Currently selected project
export const currentProject: Writable<ProjectManifest | null> = writable(null);

// Derived stores
export const isConnected: Readable<boolean> = derived(wsState, ($wsState) => $wsState.connected);

export const hasProject: Readable<boolean> = derived(
  currentProject,
  ($currentProject) => $currentProject !== null
);

// Helper functions
export function setLoading(loading: boolean) {
  appState.update((state) => ({ ...state, loading }));
}

export function setError(error: string | null) {
  appState.update((state) => ({ ...state, error }));
}

export function clearError() {
  setError(null);
}

export function selectProject(project: ProjectManifest | null) {
  currentProject.set(project);
  if (project) {
    // Store in session storage for persistence
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('current-project-id', project.id);
    }
  }
}

// Initialize app state
export function initializeApp() {
  appState.update((state) => ({ ...state, initialized: true }));

  // Restore selected project from session storage
  if (typeof window !== 'undefined') {
    const projectId = sessionStorage.getItem('current-project-id');
    if (projectId) {
      // TODO: Load project by ID when API is ready
    }
  }
}
