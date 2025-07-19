<script lang="ts">
  import { currentProject } from '$lib/stores';
  import SceneHierarchy from '../scene/SceneHierarchy.svelte';
  import ShotList from '../scene/ShotList.svelte';

</script>

<div class="scene-view">
  <div class="scene-header">
    <h2>Scene Management</h2>
    <button type="button">Add Chapter</button>
  </div>

  <div class="scene-content">
    <div class="scene-sidebar">
      <SceneHierarchy project={$currentProject} />
    </div>

    <div class="shot-details">
      <ShotList />
    </div>
  </div>
</div>

<style>
  .scene-view {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .scene-header {
    padding: 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .scene-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .scene-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  .scene-sidebar {
    width: 300px;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    overflow-y: auto;
  }

  .shot-details {
    flex: 1;
    padding: 16px;
    overflow-y: auto;
  }
</style>
