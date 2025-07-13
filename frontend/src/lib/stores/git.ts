/**
 * Git Store
 * 
 * Manages Git-related state including commit history,
 * repository status, and ongoing operations
 */

import { writable, derived, get } from 'svelte/store';
import type { EnhancedGitCommit, GitStatus } from '$lib/api/git';

interface GitState {
  // Commit history cache by project ID
  history: Map<string, EnhancedGitCommit[]>;
  
  // Repository status by project ID
  status: Map<string, GitStatus>;
  
  // Ongoing operations
  operations: {
    rollback: boolean;
    commit: boolean;
    tag: boolean;
  };
  
  // Error states
  errors: Map<string, string>;
}

function createGitStore() {
  const { subscribe, update, set } = writable<GitState>({
    history: new Map(),
    status: new Map(),
    operations: {
      rollback: false,
      commit: false,
      tag: false
    },
    errors: new Map()
  });

  return {
    subscribe,

    // Set commit history for a project
    setHistory(projectId: string, commits: EnhancedGitCommit[]) {
      update(state => {
        state.history.set(projectId, commits);
        return state;
      });
    },

    // Get commit history for a project
    getHistory(projectId: string): EnhancedGitCommit[] {
      const state = get({ subscribe });
      return state.history.get(projectId) || [];
    },

    // Set repository status
    setStatus(projectId: string, status: GitStatus) {
      update(state => {
        state.status.set(projectId, status);
        return state;
      });
    },

    // Get repository status
    getStatus(projectId: string): GitStatus | undefined {
      const state = get({ subscribe });
      return state.status.get(projectId);
    },

    // Set operation state
    setOperation(operation: keyof GitState['operations'], isActive: boolean) {
      update(state => {
        state.operations[operation] = isActive;
        return state;
      });
    },

    // Set error for a project
    setError(projectId: string, error: string | null) {
      update(state => {
        if (error) {
          state.errors.set(projectId, error);
        } else {
          state.errors.delete(projectId);
        }
        return state;
      });
    },

    // Clear all data for a project
    clearProject(projectId: string) {
      update(state => {
        state.history.delete(projectId);
        state.status.delete(projectId);
        state.errors.delete(projectId);
        return state;
      });
    },

    // Clear all cached data
    clearAll() {
      set({
        history: new Map(),
        status: new Map(),
        operations: {
          rollback: false,
          commit: false,
          tag: false
        },
        errors: new Map()
      });
    }
  };
}

export const gitStore = createGitStore();

// Derived store for checking if any operation is in progress
export const gitOperationInProgress = derived(
  gitStore,
  $git => Object.values($git.operations).some(op => op)
);

// Derived store for checking if a project has uncommitted changes
export const hasUncommittedChanges = (projectId: string) => derived(
  gitStore,
  $git => {
    const status = $git.status.get(projectId);
    return status?.is_dirty || false;
  }
);