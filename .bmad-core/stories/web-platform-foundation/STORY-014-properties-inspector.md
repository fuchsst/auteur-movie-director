# Story: Properties Inspector Implementation

**Story ID**: STORY-014  
**Epic**: EPIC-001-web-platform-foundation  
**Type**: Frontend  
**Points**: 3 (Medium)  
**Priority**: High  
**Status**: ✅ Completed

## Story Description
As a user, I need a fully functional context-sensitive properties inspector in the right panel (building on the basic PropertiesInspector component structure from STORY-007) that dynamically displays and allows editing of properties based on my current selection (project, asset, or future node), providing an intuitive interface for configuration and metadata management.

## Acceptance Criteria

### Functional Requirements
- [ ] Properties panel updates based on selection context
- [ ] Display project properties when project is selected
- [ ] Display asset properties when asset is selected
- [ ] Show character-specific properties for character assets
- [ ] Allow inline editing of editable properties
- [ ] Show read-only properties with appropriate styling
- [ ] Group related properties into collapsible sections
- [ ] Validate property changes before applying
- [ ] Show property descriptions/tooltips
- [ ] Support different property types (text, number, select, color, etc.)

### UI/UX Requirements
- [ ] Smooth transition between property contexts
- [ ] Clear visual hierarchy for property groups
- [ ] Appropriate input controls for each property type
- [ ] Loading states during property updates
- [ ] Error states for validation failures
- [ ] Undo/redo support for property changes
- [ ] Search/filter for properties (when many)
- [ ] Responsive design within panel constraints

### Technical Requirements
- [ ] Create property schema definitions
- [ ] Implement dynamic form generation
- [ ] Add property validation rules
- [ ] Create property update API calls
- [ ] Handle optimistic updates
- [ ] Implement property change debouncing
- [ ] Support nested property structures
- [ ] Create reusable property editor components

## Implementation Notes

### Property Schema Structure
```typescript
interface PropertyDefinition {
  key: string;
  label: string;
  type: PropertyType;
  value: any;
  defaultValue?: any;
  description?: string;
  editable: boolean;
  required?: boolean;
  validation?: ValidationRule[];
  options?: SelectOption[]; // For select/radio types
  min?: number; // For number types
  max?: number;
  step?: number;
  placeholder?: string;
  group?: string;
}

enum PropertyType {
  TEXT = 'text',
  NUMBER = 'number',
  SELECT = 'select',
  BOOLEAN = 'boolean',
  COLOR = 'color',
  DATE = 'date',
  FILE = 'file',
  TEXTAREA = 'textarea',
  RANGE = 'range',
  TAGS = 'tags',
  JSON = 'json'
}
```

### Properties Inspector Component
```svelte
<!-- src/lib/components/properties/PropertiesInspector.svelte -->
<script lang="ts">
  import { getContext } from 'svelte';
  import type { PropertyDefinition, SelectionContext } from '$lib/types';
  import PropertyGroup from './PropertyGroup.svelte';
  import PropertyEditor from './PropertyEditor.svelte';
  import { projectStore } from '$lib/stores/project';
  import { assetStore } from '$lib/stores/assets';
  
  export let selection: SelectionContext | null = null;
  
  let properties: PropertyDefinition[] = [];
  let groups: Map<string, PropertyDefinition[]> = new Map();
  let loading = false;
  let errors: Record<string, string> = {};
  
  // React to selection changes
  $: if (selection) {
    loadProperties(selection);
  }
  
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
        case 'node':
          // Future: Load node properties
          properties = [];
          break;
      }
      
      // Group properties
      groups = groupProperties(properties);
    } catch (error) {
      console.error('Failed to load properties:', error);
    } finally {
      loading = false;
    }
  }
  
  function groupProperties(props: PropertyDefinition[]): Map<string, PropertyDefinition[]> {
    const grouped = new Map<string, PropertyDefinition[]>();
    
    props.forEach(prop => {
      const group = prop.group || 'General';
      if (!grouped.has(group)) {
        grouped.set(group, []);
      }
      grouped.get(group)!.push(prop);
    });
    
    return grouped;
  }
  
  async function handlePropertyChange(property: PropertyDefinition, newValue: any) {
    // Validate
    const error = validateProperty(property, newValue);
    if (error) {
      errors[property.key] = error;
      return;
    }
    
    // Clear error
    delete errors[property.key];
    
    // Update based on context
    try {
      if (selection?.type === 'project') {
        await projectStore.updateProperty(selection.id, property.key, newValue);
      } else if (selection?.type === 'asset') {
        await assetStore.updateProperty(selection.id, property.key, newValue);
      }
    } catch (error) {
      errors[property.key] = 'Failed to update property';
    }
  }
</script>

<div class="properties-inspector">
  <div class="inspector-header">
    <h3>Properties</h3>
    {#if selection}
      <span class="selection-type">{selection.type}</span>
    {/if}
  </div>
  
  {#if loading}
    <div class="loading">Loading properties...</div>
  {:else if !selection}
    <div class="empty-state">
      <p>Select an item to view its properties</p>
    </div>
  {:else if properties.length === 0}
    <div class="empty-state">
      <p>No properties available</p>
    </div>
  {:else}
    <div class="properties-content">
      {#each [...groups.entries()] as [groupName, groupProps]}
        <PropertyGroup name={groupName} defaultExpanded={groupName === 'General'}>
          {#each groupProps as property}
            <PropertyEditor
              {property}
              error={errors[property.key]}
              on:change={(e) => handlePropertyChange(property, e.detail)}
            />
          {/each}
        </PropertyGroup>
      {/each}
    </div>
  {/if}
</div>
```

### Property Editor Component
```svelte
<!-- src/lib/components/properties/PropertyEditor.svelte -->
<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import type { PropertyDefinition } from '$lib/types';
  
  export let property: PropertyDefinition;
  export let error: string | undefined = undefined;
  
  const dispatch = createEventDispatcher();
  
  function handleChange(event: Event) {
    const target = event.target as HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;
    let value: any = target.value;
    
    // Type conversion
    if (property.type === PropertyType.NUMBER || property.type === PropertyType.RANGE) {
      value = parseFloat(value);
    } else if (property.type === PropertyType.BOOLEAN) {
      value = (target as HTMLInputElement).checked;
    }
    
    dispatch('change', value);
  }
</script>

<div class="property-editor" class:has-error={!!error}>
  <label for={property.key}>
    {property.label}
    {#if property.required}
      <span class="required">*</span>
    {/if}
  </label>
  
  {#if property.description}
    <div class="description">{property.description}</div>
  {/if}
  
  <div class="property-control">
    {#if !property.editable}
      <div class="read-only-value">{property.value}</div>
    {:else if property.type === PropertyType.TEXT}
      <input
        type="text"
        id={property.key}
        value={property.value}
        placeholder={property.placeholder}
        on:change={handleChange}
      />
    {:else if property.type === PropertyType.NUMBER}
      <input
        type="number"
        id={property.key}
        value={property.value}
        min={property.min}
        max={property.max}
        step={property.step}
        on:change={handleChange}
      />
    {:else if property.type === PropertyType.SELECT}
      <select id={property.key} value={property.value} on:change={handleChange}>
        {#each property.options || [] as option}
          <option value={option.value}>{option.label}</option>
        {/each}
      </select>
    {:else if property.type === PropertyType.BOOLEAN}
      <input
        type="checkbox"
        id={property.key}
        checked={property.value}
        on:change={handleChange}
      />
    {:else if property.type === PropertyType.COLOR}
      <input
        type="color"
        id={property.key}
        value={property.value}
        on:change={handleChange}
      />
    {:else if property.type === PropertyType.TEXTAREA}
      <textarea
        id={property.key}
        value={property.value}
        placeholder={property.placeholder}
        rows="3"
        on:change={handleChange}
      />
    {:else if property.type === PropertyType.RANGE}
      <div class="range-control">
        <input
          type="range"
          id={property.key}
          value={property.value}
          min={property.min}
          max={property.max}
          step={property.step}
          on:input={handleChange}
        />
        <span class="range-value">{property.value}</span>
      </div>
    {/if}
  </div>
  
  {#if error}
    <div class="error-message">{error}</div>
  {/if}
</div>
```

### Property Definitions

#### Project Properties
```typescript
function getProjectProperties(projectId: string): PropertyDefinition[] {
  const project = $projectStore.getProject(projectId);
  
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
      value: project.quality,
      editable: true,
      options: [
        { label: 'Low (Fast)', value: 'low' },
        { label: 'Standard', value: 'standard' },
        { label: 'High (Slow)', value: 'high' }
      ],
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
      group: 'Technical'
    },
    {
      key: 'settings.resolution',
      label: 'Resolution',
      type: PropertyType.SELECT,
      value: `${project.settings?.resolution?.[0]}x${project.settings?.resolution?.[1]}`,
      editable: true,
      options: [
        { label: '1920x1080 (Full HD)', value: '1920x1080' },
        { label: '3840x2160 (4K)', value: '3840x2160' },
        { label: '1280x720 (HD)', value: '1280x720' }
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
      key: 'modified',
      label: 'Last Modified',
      type: PropertyType.DATE,
      value: project.modified,
      editable: false,
      group: 'Metadata'
    }
  ];
}
```

#### Character Asset Properties
```typescript
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
      value: character.description,
      editable: true,
      placeholder: 'Describe the character appearance and personality...',
      group: 'Identity'
    },
    {
      key: 'triggerWord',
      label: 'Trigger Word',
      type: PropertyType.TEXT,
      value: character.triggerWord,
      editable: true,
      description: 'LoRA activation token for this character',
      group: 'AI Model'
    },
    {
      key: 'loraTrainingStatus',
      label: 'LoRA Status',
      type: PropertyType.SELECT,
      value: character.loraTrainingStatus,
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
```

### Integration with Main Layout
```svelte
<!-- Update src/routes/+page.svelte -->
<script>
  import PropertiesInspector from '$lib/components/properties/PropertiesInspector.svelte';
  
  let currentSelection: SelectionContext | null = null;
  
  // Listen for selection events
  projectBrowser.on('select', (e) => {
    currentSelection = {
      type: 'project',
      id: e.detail.projectId
    };
  });
  
  assetBrowser.on('select', (e) => {
    currentSelection = {
      type: 'asset',
      id: e.detail.assetId,
      assetType: e.detail.assetType
    };
  });
</script>

<ThreePanelLayout>
  <!-- ... other slots ... -->
  
  <div slot="right">
    <PropertiesInspector selection={currentSelection} />
  </div>
</ThreePanelLayout>
```

## Dependencies
- Selection context management
- API endpoints for property updates
- Form validation utilities
- Property schema definitions

## Testing Criteria
- [ ] Properties load correctly for each context type
- [ ] Inline editing works for all property types
- [ ] Validation prevents invalid values
- [ ] Changes persist after reload
- [ ] Error states display appropriately
- [ ] Read-only properties cannot be edited
- [ ] Property groups expand/collapse correctly
- [ ] Search/filter works with many properties

## Definition of Done
- [ ] Properties inspector component implemented
- [ ] Dynamic property loading based on selection
- [ ] All property types supported
- [ ] Validation and error handling complete
- [ ] Integration with project/asset stores
- [ ] Unit tests for property editing
- [ ] Documentation updated
- [ ] Code reviewed and approved

## Story Links
- **Depends On**: STORY-007 (SvelteKit Setup - basic PropertiesInspector structure), STORY-008 (Project Browser with Asset Browser)
- **Blocks**: Future node property editing
- **Related PRD**: PRD-001-web-platform-foundation