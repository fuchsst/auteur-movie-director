<script lang="ts">
  import { onMount } from 'svelte';
  import { storyVisualizationStore } from '../stores/story-visualization-store';
  import type { CharacterArcData, SceneTimelineData } from '../types/story-visualization';

  export let projectId: string;

  let characterArcs: CharacterArcData[] = [];
  let scenes: SceneTimelineData[] = [];
  let selectedCharacter: string | null = null;
  let loading = true;
  let error: string | null = null;

  let svgWidth = 800;
  let svgHeight = 400;
  let margin = { top: 40, right: 80, bottom: 60, left: 120 };

  $: if (projectId) {
    loadCharacterData();
  }

  $: selectedArc = selectedCharacter 
    ? characterArcs.find(arc => arc.id === selectedCharacter)
    : null;

  $: chartData = selectedArc ? generateChartData(selectedArc) : [];

  async function loadCharacterData() {
    try {
      loading = true;
      error = null;
      
      const [arcs, sceneData] = await Promise.all([
        storyVisualizationStore.getCharacterArcs(projectId),
        storyVisualizationStore.loadTimelineData(projectId)
      ]);
      
      characterArcs = arcs;
      scenes = sceneData;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load character data';
    } finally {
      loading = false;
    }
  }

  function generateChartData(arc: CharacterArcData) {
    const width = svgWidth - margin.left - margin.right;
    const height = svgHeight - margin.top - margin.bottom;
    
    return arc.points.map(point => ({
      x: point.position * width,
      y: height - ((point.emotionalArc + 1) * height) / 2,
      scene: scenes.find(s => s.id === point.sceneId),
      description: point.description
    }));
  }

  function handleCharacterSelect(characterId: string) {
    selectedCharacter = selectedCharacter === characterId ? null : characterId;
  }

  function getArcTypeLabel(type: string): string {
    const labels = {
      positive: 'Positive Arc',
      negative: 'Negative Arc',
      flat: 'Flat Arc',
      complex: 'Complex Arc'
    };
    return labels[type as keyof typeof labels] || type;
  }

  function getConsistencyIcon(score: number): string {
    if (score >= 0.9) return '🟢';
    if (score >= 0.7) return '🟡';
    return '🔴';
  }

  function formatArcDescription(arc: CharacterArcData): string {
    const startPoint = arc.points[0];
    const endPoint = arc.points[arc.points.length - 1];
    
    const startEmotion = startPoint?.emotionalArc || 0;
    const endEmotion = endPoint?.emotionalArc || 0;
    
    if (endEmotion > startEmotion) return 'Character grows and changes positively';
    if (endEmotion < startEmotion) return 'Character regresses or faces tragedy';
    return 'Character remains fundamentally unchanged';
  }

  function getSceneColor(scene: SceneTimelineData | undefined): string {
    if (!scene) return '#6b7280';
    return `hsl(${scene.emotionalIntensity * 120}, 70%, 50%)`;
  }
</script>

<div class="character-arc-container">
  <!-- Header -->
  <div class="arc-header">
    <h2>Character Arcs</h2>
    <div class="arc-controls">
      <button 
        class="control-btn {selectedCharacter ? 'active' : ''}"
        on:click={() => selectedCharacter = null}
      >
        All Characters
      </button>
    </div>
  </div>

  {#if loading}
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Loading character arcs...</p>
    </div>
  {:else if error}
    <div class="error-state">
      <p>{error}</p>
      <button on:click={loadCharacterData} class="retry-btn">Retry</button>
    </div>
  {:else if characterArcs.length === 0}
    <div class="empty-state">
      <p>No character arcs found</p>
    </div>
  {:else}
    <!-- Character selector -->
    <div class="character-selector">
      {#each characterArcs as arc}
        <div 
          class="character-card {selectedCharacter === arc.id ? 'selected' : ''}"
          on:click={() => handleCharacterSelect(arc.id)}
        >
          <div class="character-info">
            <h3>{arc.name}</h3>
            <p class="arc-type">{getArcTypeLabel(arc.arcType)}</p>
            <p class="arc-description">{formatArcDescription(arc)}</p>
          </div>
          
          <div class="character-metrics"
            <div class="metric">
              <span class="metric-label">Consistency</span>
              <span class="metric-value">{getConsistencyIcon(arc.consistencyScore)} {Math.round(arc.consistencyScore * 100)}%</span>
            </div>
            <div class="metric">
              <span class="metric-label">Development</span>
              <span class="metric-value">{Math.round(arc.developmentScore * 100)}%</span>
            </div>
          </div>
        </div>
      {/each}
    </div>

    {#if selectedArc}
      <!-- Arc visualization -->
      <div class="arc-visualization">
        <div class="chart-container">
          <svg 
            width={svgWidth} 
            height={svgHeight}
            viewBox="0 0 {svgWidth} {svgHeight}"
          >
            <!-- Grid lines -->
            <g class="grid">
              <line x1={margin.left} y1={margin.top} x2={margin.left} y2={svgHeight - margin.bottom} stroke="#e5e7eb" stroke-width="1"/>
              <line x1={margin.left} y1={svgHeight - margin.bottom} x2={svgWidth - margin.right} y2={svgHeight - margin.bottom} stroke="#e5e7eb" stroke-width="1"/>
              
              <!-- Horizontal emotion levels -->
              {#each [-1, -0.5, 0, 0.5, 1] as level}
                <line 
                  x1={margin.left} 
                  y1={margin.top + ((1 - level) * (svgHeight - margin.top - margin.bottom)) / 2} 
                  x2={svgWidth - margin.right} 
                  y2={margin.top + ((1 - level) * (svgHeight - margin.top - margin.bottom)) / 2} 
                  stroke="#f3f4f6" 
                  stroke-dasharray="2,2"
                />
              {/each}
            </g>

            <!-- Scene markers -->
            {#each scenes as scene}
              <circle 
                cx={margin.left + (scene.startPosition * (svgWidth - margin.left - margin.right))}
                cy={svgHeight - margin.bottom - 20}
                r="3" 
                fill={getSceneColor(scene)}
                opacity="0.7"
              >
                <title>{scene.title} - {scene.emotionalIntensity}</title>
              </circle>
            {/each}

            <!-- Character arc line -->
            <path 
              d={chartData.map((point, i) => 
                `${i === 0 ? 'M' : 'L'} ${margin.left + point.x} ${margin.top + point.y}`
              ).join(' ')}
              stroke={selectedArc.color}
              stroke-width="3"
              fill="none"
              stroke-linecap="round"
              stroke-linejoin="round"
            />

            <!-- Data points -->
            {#each chartData as point}
              <circle 
                cx={margin.left + point.x}
                cy={margin.top + point.y}
                r="5"
                fill={selectedArc.color}
                stroke="white"
                stroke-width="2"
                class="data-point"
              >
                <title>{point.scene?.title || 'Scene'}: {point.description}</title>
              </circle>
            {/each}

            <!-- Labels -->
            <g class="labels">
              <text x={margin.left - 10} y={margin.top} text-anchor="end" font-size="12" fill="#6b7280">Positive</text>
              <text x={margin.left - 10} y={svgHeight - margin.bottom} text-anchor="end" font-size="12" fill="#6b7280">Negative</text>
              <text x={margin.left - 10} y={margin.top + (svgHeight - margin.top - margin.bottom) / 2} text-anchor="end" font-size="12" fill="#6b7280">Neutral</text>
            </g>

            <!-- Timeline -->
            <g class="timeline">
              <line x1={margin.left} y1={svgHeight - margin.bottom + 30} x2={svgWidth - margin.right} y2={svgHeight - margin.bottom + 30} stroke="#374151" stroke-width="2"/>
              
              <!-- Act markers -->
              <line x1={margin.left} y1={svgHeight - margin.bottom + 25} x2={margin.left} y2={svgHeight - margin.bottom + 35} stroke="#374151" stroke-width="2"/>
              <text x={margin.left} y={svgHeight - margin.bottom + 50} text-anchor="middle" font-size="12" fill="#374151">Act I</text>
              
              <line x1={margin.left + (svgWidth - margin.left - margin.right) * 0.25} y1={svgHeight - margin.bottom + 25} x2={margin.left + (svgWidth - margin.left - margin.right) * 0.25} y2={svgHeight - margin.bottom + 35} stroke="#374151" stroke-width="2"/>
              
              <line x1={margin.left + (svgWidth - margin.left - margin.right) * 0.75} y1={svgHeight - margin.bottom + 25} x2={margin.left + (svgWidth - margin.left - margin.right) * 0.75} y2={svgHeight - margin.bottom + 35} stroke="#374151" stroke-width="2"/>
              <text x={margin.left + (svgWidth - margin.left - margin.right) * 0.75} y={svgHeight - margin.bottom + 50} text-anchor="middle" font-size="12" fill="#374151">Act III</text>
            </g>
          </svg>
        </div>

        <!-- Arc details -->
        <div class="arc-details">
          <div class="detail-section">
            <h4>Arc Type: {getArcTypeLabel(selectedArc.arcType)}</h4>
            <p>{formatArcDescription(selectedArc)}</p>
          </div>

          <div class="detail-section">
            <h4>Key Moments</h4>
            <div class="moments-list">
              {#each selectedArc.points as point, i}
                <div class="moment-item">
                  <div class="moment-indicator"
                    style="background-color: {selectedArc.color}"
                  >{i + 1}</div>
                  <div class="moment-content">
                    <span class="moment-title">{scenes.find(s => s.id === point.sceneId)?.title || 'Scene'}</span>
                    <p class="moment-description">{point.description}</p>
                  </div>
                </div>
              {/each}
            </div>
          </div>

          <div class="detail-section">
            <h4>Analytics</h4>
            <div class="analytics-grid"
              <div class="analytics-item">
                <span class="label">Consistency Score</span>
                <span class="value">{Math.round(selectedArc.consistencyScore * 100)}%</span>
              </div>
              <div class="analytics-item">
                <span class="label">Development Score</span>
                <span class="value">{Math.round(selectedArc.developmentScore * 100)}%</span>
              </div>
              <div class="analytics-item">
                <span class="label">Total Scenes</span>
                <span class="value">{selectedArc.points.length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}
  {/if}
</div>

<style>
  .character-arc-container {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    color: var(--text-primary);
    overflow: auto;
  }

  .arc-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .arc-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
  }

  .arc-controls {
    display: flex;
    gap: 0.5rem;
  }

  .control-btn {
    padding: 0.5rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .control-btn:hover,
  .control-btn.active {
    background: var(--accent-color);
    color: white;
  }

  .loading-state,
  .error-state,
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 3rem;
    color: var(--text-secondary);
  }

  .spinner {
    width: 40px;
    height: 40px;
    border: 3px solid var(--border-color);
    border-top-color: var(--accent-color);
    border-radius: 50%;
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .retry-btn {
    padding: 0.5rem 1rem;
    margin-top: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
    background: var(--bg-secondary);
    color: var(--text-primary);
    cursor: pointer;
  }

  .character-selector {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 1rem;
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .character-card {
    padding: 1rem;
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    cursor: pointer;
    transition: all 0.2s;
    background: var(--bg-secondary);
  }

  .character-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .character-card.selected {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 2px var(--accent-color);
  }

  .character-info h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1.125rem;
    font-weight: 600;
  }

  .arc-type {
    margin: 0 0 0.5rem 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .arc-description {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .character-metrics {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
    padding-top: 1rem;
    border-top: 1px solid var(--border-color);
  }

  .metric {
    display: flex;
    flex-direction: column;
  }

  .metric-label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
  }

  .metric-value {
    font-size: 0.875rem;
    font-weight: 600;
  }

  .arc-visualization {
    display: grid;
    grid-template-columns: 2fr 1fr;
    gap: 2rem;
    padding: 1rem;
    min-height: 600px;
  }

  .chart-container {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    padding: 1rem;
  }

  .arc-details {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .detail-section h4 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    font-weight: 600;
  }

  .detail-section p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  .moments-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .moment-item {
    display: flex;
    gap: 0.75rem;
    align-items: flex-start;
  }

  .moment-indicator {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 0.75rem;
    font-weight: 600;
    flex-shrink: 0;
  }

  .moment-content {
    flex: 1;
  }

  .moment-title {
    font-size: 0.875rem;
    font-weight: 600;
    display: block;
  }

  .moment-description {
    margin: 0.25rem 0 0 0;
    font-size: 0.75rem;
    color: var(--text-secondary);
    line-height: 1.3;
  }

  .analytics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }

  .analytics-item {
    display: flex;
    flex-direction: column;
    padding: 0.75rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: 0.375rem;
  }

  .analytics-item .label {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-bottom: 0.25rem;
  }

  .analytics-item .value {
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--accent-color);
  }

  .data-point {
    cursor: pointer;
    transition: all 0.2s;
  }

  .data-point:hover {
    r: 7;
  }

  @media (max-width: 768px) {
    .arc-visualization {
      grid-template-columns: 1fr;
    }

    .character-selector {
      grid-template-columns: 1fr;
    }
  }
</style>