/**
 * Git LFS state management
 */

import { writable, derived } from 'svelte/store';
import { gitLFSApi } from '$lib/api/git';
import type { LFSValidation } from '$lib/api/git';

interface LFSState {
  validation: LFSValidation | null;
  checking: boolean;
  showSetupDialog: boolean;
}

function createLFSStore() {
  const { subscribe, set, update } = writable<LFSState>({
    validation: null,
    checking: false,
    showSetupDialog: false
  });

  return {
    subscribe,

    async checkLFS() {
      update((state) => ({ ...state, checking: true }));

      try {
        const validation = await gitLFSApi.validateSetup();
        update((state) => ({
          ...state,
          validation,
          checking: false,
          showSetupDialog: !validation.lfs_installed
        }));
      } catch (error) {
        console.error('Failed to check Git LFS:', error);
        update((state) => ({ ...state, checking: false }));
      }
    },

    hideSetupDialog() {
      update((state) => ({ ...state, showSetupDialog: false }));
    },

    showSetupDialog() {
      update((state) => ({ ...state, showSetupDialog: true }));
    }
  };
}

export const lfsStore = createLFSStore();

// Derived store for LFS availability
export const lfsAvailable = derived(lfsStore, ($lfs) => $lfs.validation?.lfs_installed ?? false);
