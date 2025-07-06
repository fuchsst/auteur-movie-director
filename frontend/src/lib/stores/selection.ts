import { writable, derived } from 'svelte/store';
import type { SelectionContext } from '$lib/types/properties';

// Current selection store
function createSelectionStore() {
  const { subscribe, set } = writable<SelectionContext | null>(null);

  return {
    subscribe,

    // Set selection
    select: (context: SelectionContext | null) => {
      set(context);
    },

    // Clear selection
    clear: () => {
      set(null);
    },

    // Select project
    selectProject: (projectId: string) => {
      set({
        type: 'project',
        id: projectId
      });
    },

    // Select asset
    selectAsset: (assetId: string, assetType: 'character' | 'location' | 'style' | 'music') => {
      set({
        type: 'asset',
        id: assetId,
        assetType
      });
    },

    // Select node (for future use)
    selectNode: (nodeId: string, metadata?: Record<string, unknown>) => {
      set({
        type: 'node',
        id: nodeId,
        metadata
      });
    }
  };
}

export const selectionStore = createSelectionStore();

// Derived store for selection type
export const selectionType = derived(selectionStore, ($selection) => $selection?.type || null);

// Derived store for checking if something is selected
export const hasSelection = derived(selectionStore, ($selection) => $selection !== null);
