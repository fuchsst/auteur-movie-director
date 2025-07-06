<script lang="ts">
  // Placeholder for shot list component
  let shots: any[] = [];
</script>

<div class="shot-list">
  <h3>Shot List</h3>
  {#if shots.length > 0}
    <div class="shots">
      {#each shots as shot}
        <div class="shot-item">
          {shot.name}
        </div>
      {/each}
    </div>
  {:else}
    <p class="no-shots">No shots in this scene</p>
  {/if}
</div>

<style>
  .shot-list {
    padding: 16px;
  }

  .shot-list h3 {
    margin: 0 0 16px 0;
    font-size: 14px;
    font-weight: 600;
  }

  .shot-item {
    padding: 12px;
    background: var(--bg-secondary);
    border-radius: 4px;
    margin-bottom: 8px;
  }

  .no-shots {
    color: var(--text-secondary);
    font-size: 13px;
  }
</style>
