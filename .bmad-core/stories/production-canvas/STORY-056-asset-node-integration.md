# Story: Asset Node Integration

**Story ID**: STORY-056  
**Epic**: EPIC-004-production-canvas  
**Type**: Feature  
**Points**: 5 (Medium)  
**Priority**: High  
**Status**: 🔲 Not Started  

## Story Description

As a filmmaker, I want to visually connect my project assets (Characters, Styles, Locations) to my story structure so that I can build AI generation workflows that automatically use the right assets at the right narrative moments.

## Acceptance Criteria

### Asset Node Types
- [ ] **CharacterAssetNode**: Visual representation of character assets
  - Display character name and thumbnail preview
  - Show LoRA model status and trigger word
  - Connect to character variations gallery
  - Real-time preview of character images
  - Usage tracking showing where character is used

- [ ] **StyleAssetNode**: Visual style template nodes
  - Display style name and preview thumbnail
  - Show style keywords and parameters
  - Connect to style variations and presets
  - Real-time style preview capability
  - Visual indicators for active/inactive styles

- [ ] **LocationAssetNode**: Environment and setting assets
  - Display location name and preview image
  - Show location properties and metadata
  - Connect to location variations
  - Real-time location preview
  - Scene context indicators

### Asset Integration Features
- [ ] **Drag-and-drop asset creation** from Asset Browser
- [ ] **Real-time asset preview** with live thumbnails
- [ ] **Asset variation gallery** within node interface
- [ ] **Usage tracking** showing asset dependencies
- [ ] **Asset validation** ensuring assets exist and are ready

### Takes System Integration
- [ ] **Takes gallery integration** within asset nodes
- [ ] **Non-destructive variation management**
- [ ] **Active take selection** with visual indicators
- [ ] **Take comparison** within node context
- [ ] **Take export** capabilities

### Quality Tier Support
- [ ] **Progressive quality selection** (Draft → Standard → High → Ultra)
- [ ] **Quality indicator** within asset nodes
- [ ] **Quality-based preview generation**
- [ ] **Quality validation** for asset readiness

## Implementation Notes

### Technical Architecture
```typescript
// Asset node types
enum AssetNodeType {
  CHARACTER = 'asset-character',
  STYLE = 'asset-style',
  LOCATION = 'asset-location'
}

// Asset node data interface
interface AssetNodeData {
  assetId: string;
  assetType: AssetNodeType;
  assetName: string;
  thumbnailUrl: string;
  status: 'ready' | 'processing' | 'error';
  variations: AssetVariation[];
  usage: string[]; // Node IDs where this asset is used
  qualityTier: 'draft' | 'standard' | 'high' | 'ultra';
  takes: Take[];
}

// Asset variation interface
interface AssetVariation {
  variationId: string;
  name: string;
  thumbnail: string;
  parameters: Record<string, any>;
  quality: string;
}

// Take interface
interface Take {
  takeId: string;
  takeNumber: number;
  thumbnail: string;
  status: 'active' | 'archived';
  metadata: Record<string, any>;
}
```

### Asset Node Components
```svelte
<!-- CharacterAssetNode component -->
<script lang="ts">
  import { Node, Handle } from '@xyflow/svelte';
  import AssetGallery from './AssetGallery.svelte';
  import TakesGallery from './TakesGallery.svelte';
  
  export let data: AssetNodeData;
</script>

<Node class="asset-node character-asset" data-type="character">
  <div class="asset-header">
    <img src={data.thumbnailUrl} alt={data.assetName} class="asset-thumbnail" />
    <div class="asset-info">
      <h4>{data.assetName}</h4>
      <span class="asset-status {data.status}">{data.status}</span>
      <span class="quality-tier">{data.qualityTier}</span>
    </div>
  </div>
  
  <div class="asset-controls">
    <button on:click={() => showGallery()} class="gallery-btn">Variations</button>
    <button on:click={() => showTakes()} class="takes-btn">Takes ({data.takes.length})</button>
  </div>
  
  <Handle type="source" position="bottom" id="character-output" />
  <Handle type="target" position="top" id="character-input" />
</Node>

<!-- AssetGallery component -->
<script lang="ts">
  export let variations: AssetVariation[];
  export let onSelect: (variation: AssetVariation) => void;
</script>

<div class="asset-gallery">
  <div class="gallery-grid">
    {#each variations as variation}
      <div class="variation-item" on:click={() => onSelect(variation)}>
        <img src={variation.thumbnail} alt={variation.name} />
        <span>{variation.name}</span>
      </div>
    {/each}
  </div>
</div>
```

### Asset Service Integration
```typescript
class AssetNodeService {
  async loadAsset(assetId: string): Promise<AssetNodeData> {
    const asset = await api.assets.get(assetId);
    return {
      assetId: asset.id,
      assetType: this.mapAssetType(asset.type),
      assetName: asset.name,
      thumbnailUrl: asset.thumbnail,
      status: asset.status,
      variations: asset.variations || [],
      usage: await this.findAssetUsage(assetId),
      qualityTier: asset.qualityTier,
      takes: await this.getTakes(assetId)
    };
  }

  async updateAssetNode(nodeId: string, assetId: string) {
    const assetData = await this.loadAsset(assetId);
    await canvasStore.updateNode(nodeId, { assetData });
  }

  async getTakes(assetId: string): Promise<Take[]> {
    return await api.takes.list(assetId);
  }

  async findAssetUsage(assetId: string): Promise<string[]> {
    return await api.assets.findUsage(assetId);
  }
}
```

### Drag-and-Drop Integration
```typescript
// Asset drag-and-drop handler
class AssetDropHandler {
  async handleAssetDrop(asset: Asset, position: { x: number; y: number }) {
    const nodeData = await assetNodeService.createAssetNode(asset);
    
    return {
      id: generateId(),
      type: this.mapAssetTypeToNodeType(asset.type),
      position,
      data: nodeData,
      width: 200,
      height: 150
    };
  }

  private mapAssetTypeToNodeType(assetType: string): string {
    const mapping = {
      'character': 'asset-character',
      'style': 'asset-style',
      'location': 'asset-location'
    };
    return mapping[assetType] || 'asset-generic';
  }
}
```

### Quality Tier Support
```typescript
const QUALITY_TIERS = {
  draft: {
    thumbnail: true,
    preview: true,
    generation: false,
    color: '#6B7280'
  },
  standard: {
    thumbnail: true,
    preview: true,
    generation: true,
    color: '#3B82F6'
  },
  high: {
    thumbnail: true,
    preview: true,
    generation: true,
    color: '#10B981'
  },
  ultra: {
    thumbnail: true,
    preview: true,
    generation: true,
    color: '#8B5CF6'
  }
};
```

### Testing Requirements

#### Unit Tests
- [ ] Asset node creation and data loading
- [ ] Asset variation gallery functionality
- [ ] Takes system integration
- [ ] Quality tier switching
- [ ] Asset validation and error handling

#### Integration Tests
- [ ] Asset Browser drag-and-drop integration
- [ ] Real-time asset updates
- [ ] EPIC-002 asset system connectivity
- [ ] Takes system synchronization
- [ ] Quality tier persistence

#### E2E Tests
- [ ] Complete asset workflow from browser to canvas
- [ ] Asset variation selection and application
- [ ] Takes management within node context
- [ ] Quality tier progression workflow

### Dependencies
- **STORY-054**: Node System Architecture (for node type registration)
- **STORY-055**: Story Structure Node Types (for hierarchy integration)
- **EPIC-002**: Asset management system (for asset data)
- **EPIC-003**: Function runner (for generation capabilities)

### Definition of Done
- [ ] All asset node types implemented and tested
- [ ] Drag-and-drop integration working
- [ ] Real-time asset preview functional
- [ ] Takes system integration complete
- [ ] Quality tier support implemented
- [ ] Usage tracking active
- [ ] Documentation with examples provided
- [ ] Ready for STORY-057 (Three-Act Structure Support) implementation