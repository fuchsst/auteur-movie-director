<script lang="ts">
  import type { Project } from '$lib/types/project';

  export let project: Project | undefined;
</script>

<div class="scene-hierarchy">
  <h3>Scene Hierarchy</h3>
  {#if project}
    <div class="hierarchy-tree">
      <div class="tree-item">
        <span class="tree-icon">📁</span>
        <span class="tree-label">{project.name}</span>
      </div>
      <div class="tree-children">
        <div class="tree-item">
          <span class="tree-icon">📑</span>
          <span class="tree-label">Chapter 1</span>
        </div>
        <div class="tree-item">
          <span class="tree-icon">🎬</span>
          <span class="tree-label">Scene 1</span>
        </div>
      </div>
    </div>
  {:else}
    <p class="no-project">No project selected</p>
  {/if}
</div>

<style>
  .scene-hierarchy {
    padding: 16px;
  }

  .scene-hierarchy h3 {
    margin: 0 0 16px 0;
    font-size: 14px;
    font-weight: 600;
  }

  .hierarchy-tree {
    font-size: 13px;
  }

  .tree-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 4px 8px;
    cursor: pointer;
    border-radius: 4px;
  }

  .tree-item:hover {
    background: var(--bg-hover);
  }

  .tree-children {
    margin-left: 20px;
  }

  .tree-icon {
    font-size: 16px;
  }

  .no-project {
    color: var(--text-secondary);
    font-size: 13px;
  }
</style>
