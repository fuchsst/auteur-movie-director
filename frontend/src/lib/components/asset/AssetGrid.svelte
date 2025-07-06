<script lang="ts">
  import { onMount } from 'svelte';
  import { currentProject } from '$lib/stores';
  import { gitLFSApi } from '$lib/api/git';

  export let assets: any[] = [];

  let lfsFiles = new Set<string>();
  const SIZE_THRESHOLD = 50 * 1024 * 1024; // 50MB

  // Load LFS tracked files
  onMount(async () => {
    if ($currentProject) {
      try {
        const tracked = await gitLFSApi.getTrackedFiles($currentProject.id);
        lfsFiles = new Set(tracked.map((f) => f.path));
      } catch (error) {
        console.error('Failed to load LFS files:', error);
      }
    }
  });

  function isLFSTracked(filePath: string): boolean {
    return lfsFiles.has(filePath);
  }

  function formatFileSize(bytes: number): string {
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unit = 0;
    while (size > 1024 && unit < units.length - 1) {
      size /= 1024;
      unit++;
    }
    return `${size.toFixed(1)} ${units[unit]}`;
  }
</script>

<div class="asset-grid">
  {#if assets.length > 0}
    <div class="grid">
      {#each assets as asset (asset.id)}
        <div class="asset-card">
          <div class="asset-preview">
            <span class="asset-icon">📄</span>
            {#if asset.size && asset.size > SIZE_THRESHOLD && !isLFSTracked(asset.path)}
              <span class="lfs-warning" title="Large file - consider using LFS">⚠️</span>
            {/if}
          </div>
          <div class="asset-info">
            <div class="asset-name" title={asset.name}>{asset.name}</div>
            <div class="asset-meta">
              <span class="asset-category">{asset.category}</span>
              {#if asset.size}
                <span class="asset-size">{formatFileSize(asset.size)}</span>
              {/if}
            </div>
            {#if isLFSTracked(asset.path)}
              <span class="lfs-badge" title="Tracked by Git LFS">LFS</span>
            {/if}
          </div>
        </div>
      {/each}
    </div>
  {:else}
    <div class="empty-state">
      <p>No assets found</p>
    </div>
  {/if}
</div>

<style>
  .asset-grid {
    width: 100%;
  }

  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
    gap: 16px;
  }

  .asset-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    cursor: pointer;
    transition: all 0.2s;
  }

  .asset-card:hover {
    border-color: var(--color-primary);
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  }

  .asset-preview {
    aspect-ratio: 1;
    background: var(--bg-tertiary);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 48px;
    position: relative;
  }

  .asset-info {
    padding: 12px;
    position: relative;
  }

  .asset-name {
    font-size: 13px;
    font-weight: 500;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .asset-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 4px;
  }

  .asset-category {
    font-size: 11px;
    color: var(--text-secondary);
  }

  .asset-size {
    font-size: 11px;
    color: var(--text-tertiary);
  }

  .lfs-badge {
    position: absolute;
    top: 8px;
    right: 8px;
    background: var(--color-primary);
    color: white;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 0.5px;
  }

  .lfs-warning {
    position: absolute;
    top: 8px;
    right: 8px;
    font-size: 20px;
    filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.3));
  }

  .empty-state {
    text-align: center;
    padding: 48px;
    color: var(--text-secondary);
  }
</style>
