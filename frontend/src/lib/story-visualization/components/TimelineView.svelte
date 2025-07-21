<script lang="ts">
  import { onMount } from 'svelte';
  import { storyVisualizationStore } from '../stores/story-visualization-store';
  import { charactersStore } from '../stores/characters-store';
  import { assetsStore } from '../stores/assets-store';
  import type { SceneTimelineData, CharacterArcData, BeatData } from '../types/story-visualization';

  export let projectId: string;

  let timelineData: SceneTimelineData[] = [];
  let characterArcs: CharacterArcData[] = [];
  let beats: BeatData[] = [];
  let selectedScene: string | null = null;
  let zoomLevel = 1;
  let hoveredBeat: string | null = null;

  $: if (projectId) {
    loadTimelineData();
  }

  async function loadTimelineData() {
    try {
      const [scenes, arcs, storyBeats] = await Promise.all([
        storyVisualizationStore.getTimelineData(projectId),
        charactersStore.getCharacterArcs(projectId),
        storyVisualizationStore.getStoryBeats(projectId)
      ]);
      
      timelineData = scenes;
      characterArcs = arcs;
      beats = storyBeats;
    } catch (error) {
      console.error('Failed to load timeline data:', error);
    }
  }

  function handleSceneClick(sceneId: string) {
    selectedScene = selectedScene === sceneId ? null : sceneId;
  }

  function handleZoom(direction: 'in' | 'out') {
    zoomLevel = direction === 'in' 
      ? Math.min(zoomLevel * 1.2, 3)
      : Math.max(zoomLevel / 1.2, 0.5);
  }

  function getBeatColor(beatType: string): string {
    const colors = {
      'opening': '#3b82f6',
      'setup': '#06b6d4',
      'catalyst': '#10b981',
      'debate': '#f59e0b',
      'break_into_two': '#ef4444',
      'b_story': '#8b5cf6',
      'fun_and_games': '#ec4899',
      'midpoint': '#f97316',
      'bad_guys_close_in': '#dc2626',
      'all_is_lost': '#7c2d12',
      'dark_night_of_soul': '#1e293b',
      'break_into_three': '#059669',
      'finale': '#0891b2',
      'final_image': '#6366f1'
    };
    return colors[beatType] || '#6b7280';
  }

  function getEmotionalIntensityColor(intensity: number): string {
    if (intensity >= 0.8) return '#dc2626';
    if (intensity >= 0.6) return '#ea580c';
    if (intensity >= 0.4) return '#f59e0b';
    if (intensity >= 0.2) return '#84cc16';
    return '#22c55e';
  }
</script>

<div class="timeline-container">
  <div class="timeline-header">
    <h2>Story Timeline</h2>
    <div class="timeline-controls">
      <button on:click={() => handleZoom('in')} class="zoom-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
          <line x1="11" y1="8" x2="11" y2="14" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </button>
      <button on:click={() => handleZoom('out')} class="zoom-btn">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="11" cy="11" r="8" />
          <path d="m21 21-4.35-4.35" />
          <line x1="8" y1="11" x2="14" y2="11" />
        </svg>
      </button>
    </div>
  </div>

  <div class="timeline-content" style="transform: scale({zoomLevel}); transform-origin: top left;">
    <div class="timeline-track">
      <!-- Act boundaries -->
      <div class="act-boundaries">
        <div class="act act-1" style="left: 0%; width: 25%;">
          <span class="act-label">Act I: Setup</span>
        </div>
        <div class="act act-2" style="left: 25%; width: 50%;">
          <span class="act-label">Act II: Confrontation</span>
        </div>
        <div class="act act-3" style="left: 75%; width: 25%;">
          <span class="act-label">Act III: Resolution</span>
        </div>
      </div>

      <!-- Story beats -->
      <div class="beats-row">
        {#each beats as beat}
          <div 
            class="beat-marker"
            style="left: {beat.position * 100}%; background-color: {getBeatColor(beat.type)}"
            class:hovered={hoveredBeat === beat.id}
            on:mouseenter={() => hoveredBeat = beat.id}
            on:mouseleave={() => hoveredBeat = null}
            title="{beat.name}: {beat.description}"
          >
            {beat.name}
          </div>
        {/each}
      </div>

      <!-- Character arcs -->
      <div class="character-arcs">
        {#each characterArcs as arc, i}
          <div class="character-row" style="top: {i * 60 + 100}px">
            <div class="character-name">{arc.name}</div>
            <div class="arc-line">
              <svg width="100%" height="40">
                <path 
                  d={arc.points.map((p, idx) => 
                    `${idx === 0 ? 'M' : 'L'} ${p.position * 100} ${20 - p.emotionalArc * 15}`
                  ).join(' ')}
                  stroke={arc.color}
                  stroke-width="2"
                  fill="none"
                />
              </svg>
            </div>
          </div>
        {/each}
      </div>

      <!-- Scene timeline -->
      <div class="scenes-row">
        {#each timelineData as scene}
          <div 
            class="scene-block"
            class:selected={selectedScene === scene.id}
            style="left: {scene.startPosition * 100}%; width: {scene.duration * 100}%;"
            on:click={() => handleSceneClick(scene.id)}
          >
            <div class="scene-content">
              <div class="scene-title">{scene.title}</div>
              <div class="scene-meta">
                <span class="duration">{scene.duration}min</span>
                <span class="characters">{scene.characters.join(', ')}</span>
              </div>
              <div class="scene-intensity">
                <div 
                  class="intensity-bar"
                  style="width: {scene.emotionalIntensity * 100}%; background-color: {getEmotionalIntensityColor(scene.emotionalIntensity)}"
                ></div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    </div>
  </div>

  {#if selectedScene}
    <div class="scene-details">
      {#const scene = timelineData.find(s => s.id === selectedScene)}
      <h3>{scene?.title}</h3>
      <p>{scene?.description}</p>
      <div class="scene-stats">
        <div class="stat">
          <span class="label">Duration:</span>
          <span class="value">{scene?.duration} minutes</span>
        </div>
        <div class="stat">
          <span class="label">Characters:</span>
          <span class="value">{scene?.characters.length}</span>
        </div>
        <div class="stat">
          <span class="label">Assets:</span>
          <span class="value">{scene?.assetCount}</span>
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .timeline-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .timeline-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .timeline-controls {
    display: flex;
    gap: 0.5rem;
  }

  .zoom-btn {
    padding: 0.5rem;
    border: 1px solid var(--border-color);
    background: var(--bg-secondary);
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.2s;
  }

  .zoom-btn:hover {
    background: var(--bg-tertiary);
  }

  .timeline-content {
    flex: 1;
    overflow: auto;
    padding: 1rem;
  }

  .timeline-track {
    position: relative;
    height: 600px;
    min-width: 100%;
  }

  .act-boundaries {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 40px;
    display: flex;
  }

  .act {
    position: relative;
    border-right: 2px solid var(--border-color);
    background: rgba(59, 130, 246, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .act-2 {
    background: rgba(245, 158, 11, 0.1);
  }

  .act-3 {
    background: rgba(34, 197, 94, 0.1);
    border-right: none;
  }

  .act-label {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .beats-row {
    position: absolute;
    top: 50px;
    left: 0;
    right: 0;
    height: 30px;
  }

  .beat-marker {
    position: absolute;
    top: 0;
    transform: translateX(-50%);
    padding: 0.25rem 0.5rem;
    border-radius: 0.375rem;
    font-size: 0.75rem;
    color: white;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
  }

  .beat-marker:hover {
    transform: translateX(-50%) translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }

  .character-arcs {
    position: absolute;
    top: 100px;
    left: 0;
    right: 0;
  }

  .character-row {
    position: absolute;
    left: 0;
    right: 0;
    height: 60px;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .character-name {
    width: 120px;
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--text-secondary);
  }

  .arc-line {
    flex: 1;
    height: 40px;
  }

  .scenes-row {
    position: absolute;
    top: 300px;
    left: 0;
    right: 0;
  }

  .scene-block {
    position: absolute;
    height: 80px;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    overflow: hidden;
  }

  .scene-block:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .scene-block.selected {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px var(--accent-color);
  }

  .scene-content {
    padding: 0.5rem;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .scene-title {
    font-size: 0.875rem;
    font-weight: 600;
    margin-bottom: 0.25rem;
  }

  .scene-meta {
    font-size: 0.75rem;
    color: var(--text-secondary);
    display: flex;
    gap: 0.5rem;
  }

  .scene-intensity {
    height: 4px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }

  .intensity-bar {
    height: 100%;
    transition: width 0.3s ease;
  }

  .scene-details {
    padding: 1rem;
    border-top: 1px solid var(--border-color);
    background: var(--bg-secondary);
  }

  .scene-details h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
  }

  .scene-details p {
    margin: 0 0 1rem 0;
    color: var(--text-secondary);
  }

  .scene-stats {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
  }

  .stat {
    display: flex;
    flex-direction: column;
  }

  .stat .label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
  }

  .stat .value {
    font-size: 1.125rem;
    font-weight: 600;
  }
</style>