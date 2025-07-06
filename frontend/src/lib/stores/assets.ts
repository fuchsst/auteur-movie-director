/**
 * Asset management store
 */

import { writable, derived } from 'svelte/store';

interface Asset {
  id: string;
  projectId: string;
  name: string;
  category: string;
  path: string;
  metadata?: Record<string, any>;
  createdAt: number;
}

function createAssetStore() {
  const { subscribe, update } = writable<Asset[]>([]);

  return {
    subscribe,

    addAsset(asset: Omit<Asset, 'id' | 'createdAt'>) {
      const newAsset: Asset = {
        ...asset,
        id: crypto.randomUUID(),
        createdAt: Date.now()
      };

      update((assets) => [...assets, newAsset]);
      return newAsset.id;
    },

    removeAsset(assetId: string) {
      update((assets) => assets.filter((a) => a.id !== assetId));
    },

    getProjectAssets(projectId: string) {
      let projectAssets: Asset[] = [];
      const unsubscribe = subscribe((assets) => {
        projectAssets = assets.filter((a) => a.projectId === projectId);
      });
      unsubscribe();
      return projectAssets;
    }
  };
}

export const assetStore = createAssetStore();
