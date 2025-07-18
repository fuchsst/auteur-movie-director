<script lang="ts">
  import { onMount } from 'svelte';
  import { progressiveDisclosureService } from '$lib/canvas/services/progressive-disclosure';
  import type { DisclosureLevel } from '$lib/canvas/services/progressive-disclosure';

  export let onLevelChange: (level: DisclosureLevel) => void = () => {};

  let levels: DisclosureLevel[] = [];
  let currentLevel: DisclosureLevel | null = null;
  let autoAdjust = true;
  let isOpen = true;

  onMount(() => {
    levels = progressiveDisclosureService.getAllLevels();
    currentLevel = progressiveDisclosureService.getCurrentLevel();
    autoAdjust = progressiveDisclosureService.exportConfig().autoAdjust;

    const unsubscribe = progressiveDisclosureService.onLevelChange((level) => {
      currentLevel = level;
      onLevelChange(level);
    });

    return unsubscribe;
  });

  function handleLevelChange(levelId: string) {
    progressiveDisclosureService.setLevel(levelId);
  }

  function handleAutoAdjustChange(enabled: boolean) {
    progressiveDisclosureService.setAutoAdjust(enabled);
    autoAdjust = enabled;
  }

  function handleReset() {
    progressiveDisclosureService.resetToDefaults();
  }
</script>

<div class="progressive-disclosure-panel bg-white border-l border-gray-200 flex flex-col {isOpen ? 'w-64' : 'w-0'} transition-all duration-300 overflow-hidden">
  <div class="p-4 border-b border-gray-200">
    <div class="flex items-center justify-between mb-2">
      <h3 class="text-sm font-semibold text-gray-900">Complexity Level</h3>
      <button
        on:click={() => isOpen = !isOpen}
        class="text-gray-500 hover:text-gray-700"
      >
        <svg class="w-4 h-4 transform {isOpen ? 'rotate-180' : ''}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
    </div>
  </div>

  {#if isOpen}
    <div class="p-4 space-y-4">
      <!-- Auto-Adjust Toggle -->
      <label class="flex items-center space-x-2"
        <input
          type="checkbox"
          bind:checked={autoAdjust}
          on:change={(e) => handleAutoAdjustChange(e.target.checked)}
          class="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
        />
        <span class="text-sm text-gray-700">Auto-adjust by zoom</span>
      </label>

      <!-- Level Selection -->
      <div class="space-y-2">
        {#each levels as level}
          <label class="flex items-start space-x-3 cursor-pointer"
            <input
              type="radio"
              name="disclosure-level"
              value={level.id}
              checked={currentLevel?.id === level.id}
              on:change={() => handleLevelChange(level.id)}
              disabled={autoAdjust}
              class="mt-1 rounded-full border-gray-300 text-blue-600 focus:ring-blue-500 disabled:opacity-50"
            />
            <div class="flex-1"
              <div class="text-sm font-medium text-gray-900">{level.name}</div>
              <div class="text-xs text-gray-500">{level.description}</div>
              <div class="text-xs text-gray-400 mt-1">Zoom: {level.minZoom}x - {level.maxZoom}x</div>
            </div>
          </label>
        {/each}
      </div>

      <!-- Current Level Info -->
      {#if currentLevel}
        <div class="border-t pt-4">
          <h4 class="text-xs font-semibold text-gray-700 mb-2">Current Level Features</h4>
          <div class="space-y-1"
            {#each currentLevel.features as feature}
              <div class="text-xs text-gray-600 flex items-center"
                <svg class="w-3 h-3 mr-1 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
                {feature}
              </div>
            {/each}
          </div>
        </div>
      {/if}

      <!-- Reset Button -->
      <button
        on:click={handleReset}
        class="w-full px-3 py-2 text-sm text-gray-700 bg-gray-100 border border-gray-300 rounded hover:bg-gray-200 transition-colors"
      >
        Reset to Defaults
      </button>
    </div>
  {/if}
</div>

<style>
  .progressive-disclosure-panel {
    height: 100%;
  }
</style>