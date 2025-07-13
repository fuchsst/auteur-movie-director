<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import type { PropertyDefinition, SelectionContext } from '$lib/types/properties';
  import { PropertyType } from '$lib/types/properties';
  import PropertyGroup from './PropertyGroup.svelte';
  import PropertyEditor from './PropertyEditor.svelte';
  import ShotTakesPanel from './ShotTakesPanel.svelte';
  import { currentProject } from '$lib/stores/app';
  import { api } from '$lib/api/client';
  import type { ProjectManifest, CharacterAsset, Asset } from '$lib/types/project';
  import type { TakeMetadata } from '$lib/api/takes';

  export let selection: SelectionContext | null = null;

  let properties: PropertyDefinition[] = [];
  let groups: Map<string, PropertyDefinition[]> = new Map();
  let loading = false;
  let errors: Record<string, string> = {};
  let searchQuery = '';

  // React to selection changes
  $: if (selection) {
    loadProperties(selection);
  } else {
    properties = [];
    groups.clear();
  }

  // Filter properties based on search
  $: filteredGroups = searchQuery ? filterProperties(groups, searchQuery) : groups;

  async function loadProperties(context: SelectionContext) {
    loading = true;
    errors = {};

    try {
      switch (context.type) {
        case 'project':
          properties = await getProjectProperties(context.id);
          break;
        case 'asset':
          properties = await getAssetProperties(context.id, context.assetType);
          break;
        case 'shot':
          properties = await getShotProperties(context.id, context.shotId);
          break;
        case 'node':
          // Future: Load node properties
          properties = [];
          break;
        default:
          properties = [];
      }

      // Group properties
      groups = groupProperties(properties);
    } catch (error) {
      console.error('Failed to load properties:', error);
      properties = [];
    } finally {
      loading = false;
    }
  }

  function groupProperties(props: PropertyDefinition[]): Map<string, PropertyDefinition[]> {
    const grouped = new Map<string, PropertyDefinition[]>();

    props.forEach((prop) => {
      const group = prop.group || 'General';
      if (!grouped.has(group)) {
        grouped.set(group, []);
      }
      grouped.get(group)!.push(prop);
    });

    return grouped;
  }

  function filterProperties(
    groups: Map<string, PropertyDefinition[]>,
    query: string
  ): Map<string, PropertyDefinition[]> {
    const filtered = new Map<string, PropertyDefinition[]>();
    const lowerQuery = query.toLowerCase();

    groups.forEach((props, groupName) => {
      const filteredProps = props.filter(
        (prop) =>
          prop.label.toLowerCase().includes(lowerQuery) ||
          prop.key.toLowerCase().includes(lowerQuery) ||
          prop.description?.toLowerCase().includes(lowerQuery)
      );

      if (filteredProps.length > 0) {
        filtered.set(groupName, filteredProps);
      }
    });

    return filtered;
  }

  async function getProjectProperties(projectId: string): Promise<PropertyDefinition[]> {
    const project = $currentProject;
    if (!project) return [];

    return [
      {
        key: 'name',
        label: 'Project Name',
        type: PropertyType.TEXT,
        value: project.name,
        editable: true,
        required: true,
        group: 'General'
      },
      {
        key: 'quality',
        label: 'Quality Preset',
        type: PropertyType.SELECT,
        value: project.quality || 'standard',
        editable: true,
        options: [
          { label: 'Low (Fast)', value: 'low' },
          { label: 'Standard', value: 'standard' },
          { label: 'High (Slow)', value: 'high' }
        ],
        description: 'Controls render quality and processing time',
        group: 'General'
      },
      {
        key: 'narrative.structure',
        label: 'Narrative Structure',
        type: PropertyType.SELECT,
        value: project.narrative?.structure || 'three-act',
        editable: true,
        options: [
          { label: 'Three Act', value: 'three-act' },
          { label: "Hero's Journey", value: 'hero-journey' },
          { label: 'Beat Sheet', value: 'beat-sheet' },
          { label: 'Story Circle', value: 'story-circle' }
        ],
        description: 'Story structure template for your project',
        group: 'Narrative'
      },
      {
        key: 'settings.fps',
        label: 'Frame Rate',
        type: PropertyType.NUMBER,
        value: project.settings?.fps || 24,
        editable: true,
        min: 12,
        max: 60,
        step: 1,
        description: 'Frames per second for video output',
        group: 'Technical'
      },
      {
        key: 'settings.resolution',
        label: 'Resolution',
        type: PropertyType.SELECT,
        value: `${project.settings?.resolution?.[0] || 1920}x${project.settings?.resolution?.[1] || 1080}`,
        editable: true,
        options: [
          { label: '1920x1080 (Full HD)', value: '1920x1080' },
          { label: '3840x2160 (4K)', value: '3840x2160' },
          { label: '1280x720 (HD)', value: '1280x720' }
        ],
        group: 'Technical'
      },
      {
        key: 'settings.aspectRatio',
        label: 'Aspect Ratio',
        type: PropertyType.SELECT,
        value: project.settings?.aspectRatio || '16:9',
        editable: true,
        options: [
          { label: '16:9 (Widescreen)', value: '16:9' },
          { label: '21:9 (Cinematic)', value: '21:9' },
          { label: '4:3 (Classic)', value: '4:3' },
          { label: '1:1 (Square)', value: '1:1' }
        ],
        group: 'Technical'
      },
      {
        key: 'created',
        label: 'Created',
        type: PropertyType.DATE,
        value: project.created,
        editable: false,
        group: 'Metadata'
      },
      {
        key: 'id',
        label: 'Project ID',
        type: PropertyType.TEXT,
        value: project.id,
        editable: false,
        group: 'Metadata'
      }
    ];
  }

  async function getShotProperties(projectId: string, shotId?: string): Promise<PropertyDefinition[]> {
    if (!shotId) return [];

    // Parse shot ID to extract components
    const shotParts = shotId.split('/');
    const shotName = shotParts[shotParts.length - 1] || shotId;
    const sceneName = shotParts.length > 1 ? shotParts[shotParts.length - 2] : 'Default Scene';
    const chapterName = shotParts.length > 2 ? shotParts[shotParts.length - 3] : 'Default Chapter';

    return [
      {
        key: 'shot.name',
        label: 'Shot Name',
        type: PropertyType.TEXT,
        value: shotName,
        editable: true,
        required: true,
        group: 'Shot Details'
      },
      {
        key: 'shot.scene',
        label: 'Scene',
        type: PropertyType.TEXT,
        value: sceneName,
        editable: false,
        group: 'Hierarchy'
      },
      {
        key: 'shot.chapter',
        label: 'Chapter',
        type: PropertyType.TEXT,
        value: chapterName,
        editable: false,
        group: 'Hierarchy'
      },
      {
        key: 'shot.description',
        label: 'Description',
        type: PropertyType.TEXTAREA,
        value: '',
        editable: true,
        placeholder: 'Describe what happens in this shot...',
        group: 'Shot Details'
      },
      {
        key: 'shot.cameraAngle',
        label: 'Camera Angle',
        type: PropertyType.SELECT,
        value: 'medium',
        editable: true,
        options: [
          { label: 'Close Up', value: 'close-up' },
          { label: 'Medium Shot', value: 'medium' },
          { label: 'Wide Shot', value: 'wide' },
          { label: 'Extreme Close Up', value: 'extreme-close-up' },
          { label: 'Extreme Wide Shot', value: 'extreme-wide' }
        ],
        group: 'Camera'
      },
      {
        key: 'shot.duration',
        label: 'Duration (seconds)',
        type: PropertyType.NUMBER,
        value: 5,
        editable: true,
        min: 0.5,
        max: 30,
        step: 0.5,
        group: 'Timing'
      },
      {
        key: 'shot.prompt',
        label: 'Generation Prompt',
        type: PropertyType.TEXTAREA,
        value: '',
        editable: true,
        placeholder: 'Enter the prompt for generating this shot...',
        description: 'Prompt used for AI generation of this shot',
        group: 'Generation'
      }
    ];
  }

  async function getAssetProperties(
    assetId: string,
    assetType?: string
  ): Promise<PropertyDefinition[]> {
    // For now, return generic asset properties
    // In a real implementation, this would fetch from the backend
    if (assetType === 'character') {
      return getCharacterProperties({
        assetId,
        assetType: 'Character',
        name: 'Character Name',
        description: 'Character description',
        triggerWord: 'charname',
        loraTrainingStatus: 'untrained',
        variations: {},
        usage: []
      } as CharacterAsset);
    }

    // Generic asset properties
    return [
      {
        key: 'name',
        label: 'Asset Name',
        type: PropertyType.TEXT,
        value: 'Asset',
        editable: true,
        required: true,
        group: 'General'
      },
      {
        key: 'type',
        label: 'Asset Type',
        type: PropertyType.TEXT,
        value: assetType || 'unknown',
        editable: false,
        group: 'General'
      }
    ];
  }

  function getCharacterProperties(character: CharacterAsset): PropertyDefinition[] {
    return [
      {
        key: 'name',
        label: 'Character Name',
        type: PropertyType.TEXT,
        value: character.name,
        editable: true,
        required: true,
        group: 'Identity'
      },
      {
        key: 'description',
        label: 'Description',
        type: PropertyType.TEXTAREA,
        value: character.description || '',
        editable: true,
        placeholder: 'Describe the character appearance and personality...',
        group: 'Identity'
      },
      {
        key: 'triggerWord',
        label: 'Trigger Word',
        type: PropertyType.TEXT,
        value: character.triggerWord || '',
        editable: true,
        description: 'LoRA activation token for this character',
        group: 'AI Model'
      },
      {
        key: 'loraTrainingStatus',
        label: 'LoRA Status',
        type: PropertyType.SELECT,
        value: character.loraTrainingStatus || 'untrained',
        editable: false,
        options: [
          { label: 'Not Trained', value: 'untrained' },
          { label: 'Training', value: 'training' },
          { label: 'Completed', value: 'completed' },
          { label: 'Failed', value: 'failed' }
        ],
        group: 'AI Model'
      },
      {
        key: 'variations',
        label: 'Variations',
        type: PropertyType.NUMBER,
        value: Object.keys(character.variations || {}).length,
        editable: false,
        group: 'Assets'
      },
      {
        key: 'usage',
        label: 'Used in Shots',
        type: PropertyType.NUMBER,
        value: character.usage?.length || 0,
        editable: false,
        group: 'Usage'
      }
    ];
  }

  async function handlePropertyChange(
    property: PropertyDefinition,
    newValue: string | number | boolean | string[] | Date | null
  ) {
    // Validate
    const error = validateProperty(property, newValue);
    if (error) {
      errors[property.key] = error;
      return;
    }

    // Clear error
    delete errors[property.key];
    errors = { ...errors }; // Trigger reactivity

    // Update based on context
    try {
      if (selection?.type === 'project' && $currentProject) {
        // Update project property
        const updated = { ...$currentProject };
        setNestedProperty(updated, property.key, newValue);

        // Save to backend
        await api.updateProject($currentProject.id, updated);

        // Update store
        currentProject.set(updated);
      } else if (selection?.type === 'asset') {
        // TODO: Implement asset property updates
        console.log('Asset property update:', property.key, newValue);
      }
    } catch (error) {
      errors[property.key] = 'Failed to update property';
      errors = { ...errors };
    }
  }

  function setNestedProperty(
    obj: Record<string, unknown>,
    path: string,
    value: string | number | boolean | string[] | Date | null
  ) {
    const keys = path.split('.');
    let current: Record<string, unknown> = obj;

    for (let i = 0; i < keys.length - 1; i++) {
      if (!current[keys[i]]) {
        current[keys[i]] = {};
      }
      current = current[keys[i]] as Record<string, unknown>;
    }

    // Special handling for resolution
    if (path === 'settings.resolution' && typeof value === 'string') {
      const [width, height] = value.split('x').map(Number);
      current.resolution = [width, height];
    } else {
      current[keys[keys.length - 1]] = value;
    }
  }

  function validateProperty(
    property: PropertyDefinition,
    value: string | number | boolean | string[] | Date | null
  ): string | null {
    if (property.required && !value) {
      return 'This field is required';
    }

    if (property.type === PropertyType.NUMBER || property.type === PropertyType.RANGE) {
      if (property.min !== undefined && value < property.min) {
        return `Value must be at least ${property.min}`;
      }
      if (property.max !== undefined && value > property.max) {
        return `Value must be at most ${property.max}`;
      }
    }

    // Custom validation rules
    if (property.validation) {
      for (const rule of property.validation) {
        if (rule.type === 'pattern' && rule.value && typeof value === 'string') {
          const regex = new RegExp(rule.value as string);
          if (!regex.test(value)) {
            return rule.message;
          }
        } else if (rule.type === 'custom' && rule.validator) {
          if (!rule.validator(value)) {
            return rule.message;
          }
        }
      }
    }

    return null;
  }

  // Take panel event handlers
  function handleTakeSelected(event: CustomEvent<{ take: TakeMetadata }>) {
    console.log('Take selected:', event.detail.take);
    // Future: Update canvas or preview with selected take
  }

  function handleGenerateTake() {
    console.log('Generate new take for shot:', selection?.shotId);
    // Future: Trigger take generation
  }

  function handleActiveTakeChanged(event: CustomEvent<{ takeId: string }>) {
    console.log('Active take changed:', event.detail.takeId);
    // Future: Update shot metadata with new active take
  }
</script>

<div class="properties-inspector">
  <div class="inspector-header">
    <h3>Properties</h3>
    {#if selection}
      <span class="selection-badge">{selection.type}</span>
    {/if}
  </div>

  {#if properties.length > 10}
    <div class="search-container">
      <input
        type="text"
        placeholder="Search properties..."
        bind:value={searchQuery}
        class="search-input"
      />
    </div>
  {/if}

  {#if loading}
    <div class="loading">
      <div class="spinner"></div>
      <span>Loading properties...</span>
    </div>
  {:else if !selection}
    <div class="empty-state">
      <svg
        width="48"
        height="48"
        viewBox="0 0 48 48"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect
          x="8"
          y="8"
          width="32"
          height="32"
          rx="4"
          stroke="currentColor"
          stroke-width="2"
          stroke-dasharray="4 4"
          opacity="0.3"
        />
        <circle cx="24" cy="24" r="8" stroke="currentColor" stroke-width="2" opacity="0.3" />
      </svg>
      <p>Select an item to view its properties</p>
    </div>
  {:else if filteredGroups.size === 0}
    <div class="empty-state">
      <p>No properties {searchQuery ? 'match your search' : 'available'}</p>
    </div>
  {:else}
    <div class="properties-content">
      {#each [...filteredGroups.entries()] as [groupName, groupProps]}
        <PropertyGroup name={groupName} defaultExpanded={groupName === 'General'}>
          {#each groupProps as property (property.key)}
            <PropertyEditor
              {property}
              error={errors[property.key]}
              on:change={(e) => handlePropertyChange(property, e.detail)}
            />
          {/each}
        </PropertyGroup>
      {/each}
      
      <!-- Show takes panel for shot selections -->
      {#if selection?.type === 'shot' && selection.id && selection.shotId}
        <div class="takes-panel-container">
          <ShotTakesPanel
            projectId={selection.id}
            shotId={selection.shotId}
            on:takeSelected={handleTakeSelected}
            on:generateTake={handleGenerateTake}
            on:activeTakeChanged={handleActiveTakeChanged}
          />
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .properties-inspector {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--color-surface-primary, #1a1a1a);
  }

  .inspector-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem;
    border-bottom: 1px solid var(--color-border, #3a3a3a);
  }

  .inspector-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: var(--color-text-primary, #fff);
  }

  .selection-badge {
    padding: 0.25rem 0.75rem;
    background: var(--color-primary, #007acc);
    color: white;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: capitalize;
  }

  .search-container {
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--color-border, #3a3a3a);
  }

  .search-input {
    width: 100%;
    padding: 0.5rem;
    background: var(--color-surface-secondary, #2a2a2a);
    border: 1px solid var(--color-border, #3a3a3a);
    border-radius: 4px;
    font-size: 0.813rem;
    color: var(--color-text-primary, #fff);
  }

  .search-input:focus {
    outline: none;
    border-color: var(--color-primary, #007acc);
  }

  .properties-content {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
  }

  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--color-text-secondary, #b0b0b0);
  }

  .spinner {
    width: 24px;
    height: 24px;
    border: 2px solid var(--color-border, #3a3a3a);
    border-top-color: var(--color-primary, #007acc);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 3rem;
    color: var(--color-text-tertiary, #808080);
    text-align: center;
  }

  .empty-state svg {
    color: var(--color-text-tertiary, #808080);
  }

  .empty-state p {
    margin: 0;
    font-size: 0.875rem;
  }

  .takes-panel-container {
    margin-top: 1.5rem;
    padding-top: 1.5rem;
    border-top: 1px solid var(--color-border, #3a3a3a);
  }
</style>
