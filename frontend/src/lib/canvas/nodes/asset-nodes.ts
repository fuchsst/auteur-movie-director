import type { Node } from '$lib/canvas/types/canvas';

// Asset node types for Production Canvas integration with EPIC-002

export const assetNodeTypes = {
  // Character assets
  'character-asset': {
    component: 'CharacterAssetNode',
    label: 'Character',
    category: 'asset',
    color: '#f59e0b',
    icon: '👤',
    defaultData: {
      assetType: 'character',
      assetName: 'New Character',
      quality: 'standard',
      style: 'realistic',
      tags: [],
      metadata: {}
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Style assets
  'style-asset': {
    component: 'StyleAssetNode',
    label: 'Style',
    category: 'asset',
    color: '#8b5cf6',
    icon: '🎨',
    defaultData: {
      assetType: 'style',
      assetName: 'New Style',
      styleType: 'cinematic',
      tags: [],
      metadata: {}
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Location assets
  'location-asset': {
    component: 'LocationAssetNode',
    label: 'Location',
    category: 'asset',
    color: '#06b6d4',
    icon: '🏞️',
    defaultData: {
      assetType: 'location',
      assetName: 'New Location',
      locationType: 'interior',
      tags: [],
      metadata: {}
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Prop assets
  'prop-asset': {
    component: 'PropAssetNode',
    label: 'Prop',
    category: 'asset',
    color: '#10b981',
    icon: '📦',
    defaultData: {
      assetType: 'prop',
      assetName: 'New Prop',
      propType: 'object',
      tags: [],
      metadata: {}
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Voice assets
  'voice-asset': {
    component: 'VoiceAssetNode',
    label: 'Voice',
    category: 'asset',
    color: '#ec4899',
    icon: '🎤',
    defaultData: {
      assetType: 'voice',
      assetName: 'New Voice',
      voiceType: 'character',
      gender: 'neutral',
      age: 'adult',
      tags: [],
      metadata: {}
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  },

  // Template assets
  'template-asset': {
    component: 'TemplateAssetNode',
    label: 'Template',
    category: 'asset',
    color: '#64748b',
    icon: '📋',
    defaultData: {
      assetType: 'template',
      assetName: 'New Template',
      templateType: 'story',
      tags: [],
      metadata: {}
    },
    handles: [
      { type: 'source', position: 'right', id: 'output' },
      { type: 'target', position: 'left', id: 'input' }
    ]
  }
};

// Asset integration with EPIC-002
export interface AssetIntegration {
  assetId: string;
  assetType: AssetType;
  quality: 'low' | 'standard' | 'high' | 'ultra';
  status: 'pending' | 'processing' | 'ready' | 'error';
  thumbnail?: string;
  metadata: Record<string, any>;
  takes?: string[];
  lastUpdated: Date;
}

type AssetType = 'character' | 'style' | 'location' | 'prop' | 'voice' | 'template';

// Helper function to create asset nodes
export function createAssetNode(
  type: string, 
  position: { x: number; y: number }, 
  assetData: any = {}
): Omit<Node, 'id'> {
  const nodeType = assetNodeTypes[type];
  if (!nodeType) {
    throw new Error(`Unknown asset node type: ${type}`);
  }

  return {
    type,
    position,
    data: { ...nodeType.defaultData, ...assetData },
    style: {
      background: nodeType.color,
      color: 'white',
      borderRadius: '8px',
      padding: '8px',
      fontSize: '11px',
      fontWeight: 'bold',
      border: '2px solid transparent',
      cursor: 'pointer',
      minWidth: '140px',
      textAlign: 'center'
    }
  };
}

// Helper function to get asset node metadata
export function getAssetNodeMetadata(type: string) {
  return assetNodeTypes[type] || null;
}

// Helper function to get assets by category
export function getAssetNodesByType(type: AssetType) {
  return Object.entries(assetNodeTypes)
    .filter(([_, config]) => config.defaultData.assetType === type)
    .map(([type, config]) => ({ type, ...config }));
}

// Asset synchronization with EPIC-002
export class AssetSynchronizer {
  private syncInterval: NodeJS.Timeout | null = null;
  private assetCache: Map<string, AssetIntegration> = new Map();

  constructor(private projectId: string) {}

  async syncAssets(): Promise<void> {
    try {
      const response = await fetch(`/api/v1/assets/${this.projectId}`);
      const assets = await response.json();
      
      this.updateAssetCache(assets);
      this.notifyCanvas(assets);
    } catch (error) {
      console.error('Failed to sync assets:', error);
    }
  }

  private updateAssetCache(assets: AssetIntegration[]): void {
    this.assetCache.clear();
    assets.forEach(asset => {
      this.assetCache.set(asset.assetId, asset);
    });
  }

  private notifyCanvas(assets: AssetIntegration[]): void {
    // Dispatch custom event to notify canvas of asset updates
    window.dispatchEvent(new CustomEvent('assets-updated', {
      detail: { assets, projectId: this.projectId }
    }));
  }

  startAutoSync(intervalMs: number = 30000): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
    }

    this.syncInterval = setInterval(() => {
      this.syncAssets();
    }, intervalMs);
  }

  stopAutoSync(): void {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }

  getAsset(assetId: string): AssetIntegration | undefined {
    return this.assetCache.get(assetId);
  }

  getAssetsByType(type: AssetType): AssetIntegration[] {
    return Array.from(this.assetCache.values())
      .filter(asset => asset.assetType === type);
  }

  async updateAsset(assetId: string, updates: Partial<AssetIntegration>): Promise<void> {
    try {
      await fetch(`/api/v1/assets/${this.projectId}/${assetId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      
      await this.syncAssets();
    } catch (error) {
      console.error('Failed to update asset:', error);
    }
  }
}

// Asset validation
export function validateAssetNode(data: any): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];

  if (!data.assetId) {
    errors.push('Asset ID is required');
  }

  if (!data.assetType) {
    errors.push('Asset type is required');
  }

  if (!['character', 'style', 'location', 'prop', 'voice', 'template'].includes(data.assetType)) {
    errors.push('Invalid asset type');
  }

  if (!data.assetName || data.assetName.trim().length === 0) {
    errors.push('Asset name is required');
  }

  return {
    isValid: errors.length === 0,
    errors
  };
}

// Asset linking to story nodes
export function linkAssetToStory(
  storyNode: Node,
  assetNode: Node,
  linkType: 'character' | 'style' | 'location' | 'prop' | 'voice' | 'template'
): void {
  if (!storyNode.data.assets) {
    storyNode.data.assets = [];
  }

  const assetId = assetNode.data.assetId;
  if (!storyNode.data.assets.includes(assetId)) {
    storyNode.data.assets.push(assetId);
  }

  // Update asset metadata with link information
  if (!assetNode.data.metadata) {
    assetNode.data.metadata = {};
  }

  assetNode.data.metadata.linkedTo = assetNode.data.metadata.linkedTo || [];
  if (!assetNode.data.metadata.linkedTo.includes(storyNode.id)) {
    assetNode.data.metadata.linkedTo.push(storyNode.id);
  }
}

// Asset quality tiers
export const QUALITY_TIERS = {
  low: {
    resolution: '512x512',
    fileSize: '~1MB',
    quality: 'Fast',
    description: 'Low quality, fast generation'
  },
  standard: {
    resolution: '1024x1024',
    fileSize: '~4MB',
    quality: 'Balanced',
    description: 'Standard quality, good balance'
  },
  high: {
    resolution: '2048x2048',
    fileSize: '~8MB',
    quality: 'High',
    description: 'High quality, detailed results'
  },
  ultra: {
    resolution: '4096x4096',
    fileSize: '~32MB',
    quality: 'Ultra',
    description: 'Ultra quality, maximum detail'
  }
};

// Asset status indicators
export const ASSET_STATUS = {
  pending: { color: '#f59e0b', label: 'Pending' },
  processing: { color: '#3b82f6', label: 'Processing' },
  ready: { color: '#10b981', label: 'Ready' },
  error: { color: '#ef4444', label: 'Error' }
};