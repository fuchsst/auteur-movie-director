import { assetsStore } from '$lib/stores/assets';
import type { AssetIntegration, AssetType } from '$lib/canvas/nodes/asset-nodes';
import type { Node } from '$lib/canvas/types/canvas';

// Service for integrating assets from EPIC-002 into Production Canvas
export class AssetIntegrationService {
  private projectId: string;
  private assetCache: Map<string, AssetIntegration> = new Map();
  private syncInterval: NodeJS.Timeout | null = null;

  constructor(projectId: string) {
    this.projectId = projectId;
    this.initializeAssetSync();
  }

  // Initialize asset synchronization with EPIC-002
  private async initializeAssetSync(): Promise<void> {
    // Subscribe to assets store changes
    assetsStore.subscribe(($assets) => {
      this.updateAssetCache($assets);
    });

    // Initial sync
    await this.syncAssets();
  }

  // Sync assets from EPIC-002
  private async syncAssets(): Promise<void> {
    try {
      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets`);
      const assets = await response.json();
      
      assetsStore.setAssets(assets);
      this.updateAssetCache(assets);
    } catch (error) {
      console.error('Failed to sync assets:', error);
    }
  }

  // Update local asset cache
  private updateAssetCache(assets: any[]): void {
    this.assetCache.clear();
    
    assets.forEach(asset => {
      const integration: AssetIntegration = {
        assetId: asset.id,
        assetType: asset.type as AssetType,
        quality: asset.quality || 'standard',
        status: asset.status || 'ready',
        thumbnail: asset.thumbnail,
        metadata: asset.metadata || {},
        takes: asset.takes || [],
        lastUpdated: new Date(asset.updatedAt || Date.now())
      };
      
      this.assetCache.set(asset.id, integration);
    });
  }

  // Create asset node for canvas
  async createAssetNode(
    assetId: string, 
    position: { x: number; y: number }
  ): Promise<Node | null> {
    const asset = this.assetCache.get(assetId);
    if (!asset) {
      console.warn(`Asset ${assetId} not found`);
      return null;
    }

    const nodeData = {
      assetId: asset.assetId,
      assetType: asset.assetType,
      assetName: asset.metadata.name || asset.assetId,
      thumbnail: asset.thumbnail,
      quality: asset.quality,
      status: asset.status,
      tags: asset.metadata.tags || [],
      metadata: asset.metadata
    };

    return {
      id: `asset-${assetId}`,
      type: `${asset.assetType}-asset`,
      position,
      data: nodeData,
      style: {
        background: this.getAssetColor(asset.assetType),
        color: 'white',
        borderRadius: '8px',
        padding: '8px',
        fontSize: '11px',
        fontWeight: 'bold',
        border: '2px solid transparent',
        cursor: 'pointer',
        minWidth: '120px',
        textAlign: 'center'
      }
    };
  }

  // Link asset to story node
  async linkAssetToStory(
    storyNode: Node,
    assetId: string,
    linkType: AssetType
  ): Promise<boolean> {
    try {
      const asset = this.assetCache.get(assetId);
      if (!asset) return false;

      // Update story node data
      if (!storyNode.data.assets) {
        storyNode.data.assets = [];
      }

      if (!storyNode.data.assets.includes(assetId)) {
        storyNode.data.assets.push(assetId);
      }

      // Update asset metadata
      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets/${assetId}/link`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          nodeId: storyNode.id,
          linkType
        })
      });

      return response.ok;
    } catch (error) {
      console.error('Failed to link asset to story:', error);
      return false;
    }
  }

  // Get assets by type
  getAssetsByType(type: AssetType): AssetIntegration[] {
    return Array.from(this.assetCache.values())
      .filter(asset => asset.assetType === type);
  }

  // Get linked assets for a story node
  getLinkedAssets(nodeId: string): AssetIntegration[] {
    // This would be implemented based on EPIC-002's linking system
    return Array.from(this.assetCache.values())
      .filter(asset => 
        asset.metadata.linkedNodes?.includes(nodeId)
      );
  }

  // Update asset quality
  async updateAssetQuality(assetId: string, quality: 'low' | 'standard' | 'high' | 'ultra'): Promise<boolean> {
    try {
      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets/${assetId}/quality`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ quality })
      });

      if (response.ok) {
        await this.syncAssets();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to update asset quality:', error);
      return false;
    }
  }

  // Upload new asset
  async uploadAsset(
    file: File,
    assetType: AssetType,
    metadata: Record<string, any> = {}
  ): Promise<string | null> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('type', assetType);
      formData.append('metadata', JSON.stringify(metadata));

      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets`, {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        const result = await response.json();
        await this.syncAssets();
        return result.assetId;
      }
      return null;
    } catch (error) {
      console.error('Failed to upload asset:', error);
      return null;
    }
  }

  // Delete asset
  async deleteAsset(assetId: string): Promise<boolean> {
    try {
      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets/${assetId}`, {
        method: 'DELETE'
      });

      if (response.ok) {
        this.assetCache.delete(assetId);
        await this.syncAssets();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to delete asset:', error);
      return false;
    }
  }

  // Get asset usage statistics
  getAssetUsageStats(): {
    total: number;
    byType: Record<AssetType, number>;
    byStatus: Record<string, number>;
    byQuality: Record<string, number>;
  } {
    const stats = {
      total: this.assetCache.size,
      byType: {} as Record<AssetType, number>,
      byStatus: {} as Record<string, number>,
      byQuality: {} as Record<string, number>
    };

    // Initialize counters
    ['character', 'style', 'location', 'prop', 'voice', 'template'].forEach(type => {
      stats.byType[type as AssetType] = 0;
    });

    ['pending', 'processing', 'ready', 'error'].forEach(status => {
      stats.byStatus[status] = 0;
    });

    ['low', 'standard', 'high', 'ultra'].forEach(quality => {
      stats.byQuality[quality] = 0;
    });

    // Count assets
    this.assetCache.forEach(asset => {
      stats.byType[asset.assetType]++;
      stats.byStatus[asset.status]++;
      stats.byQuality[asset.quality]++;
    });

    return stats;
  }

  // Preview asset
  async getAssetPreview(assetId: string): Promise<string | null> {
    const asset = this.assetCache.get(assetId);
    if (!asset) return null;

    try {
      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets/${assetId}/preview`);
      if (response.ok) {
        const blob = await response.blob();
        return URL.createObjectURL(blob);
      }
      return null;
    } catch (error) {
      console.error('Failed to get asset preview:', error);
      return null;
    }
  }

  // Search assets
  async searchAssets(query: string, type?: AssetType): Promise<AssetIntegration[]> {
    try {
      const params = new URLSearchParams({ q: query });
      if (type) params.append('type', type);

      const response = await fetch(`/api/v1/workspace/${this.projectId}/assets/search?${params}`);
      const results = await response.json();

      return results.map((asset: any) => ({
        assetId: asset.id,
        assetType: asset.type as AssetType,
        quality: asset.quality || 'standard',
        status: asset.status || 'ready',
        thumbnail: asset.thumbnail,
        metadata: asset.metadata || {},
        takes: asset.takes || [],
        lastUpdated: new Date(asset.updatedAt || Date.now())
      }));
    } catch (error) {
      console.error('Failed to search assets:', error);
      return [];
    }
  }

  // Get color for asset type
  private getAssetColor(type: AssetType): string {
    const colors = {
      character: '#f59e0b',
      style: '#8b5cf6',
      location: '#06b6d4',
      prop: '#10b981',
      voice: '#ec4899',
      template: '#64748b'
    };
    return colors[type] || '#6b7280';
  }

  // Cleanup
  destroy(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }
    this.assetCache.clear();
  }
}

// Global asset integration instance
export const assetIntegrationService = new AssetIntegrationService('current-project');